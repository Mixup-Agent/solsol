"""음성 기반 면접 턴 엔드포인트 — 실제 면접 에이전트(LangGraph 노드)와 연결."""
import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.agents.meta import meta_agent
from app.agents.resume import resume_agent
from app.agents.state import InterviewState
from app.agents.stress import stress_agent
from app.agents.trend import trend_agent
from app.services.interview_db import get_agent_context, get_turns, insert_turn
from app.services.stt import transcribe_audio
from app.services.tts import synthesize_speech

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interview-sessions", tags=["turns"])

AUDIO_UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "audio"
AUDIO_TTS_DIR = Path(__file__).resolve().parents[1] / "data" / "tts"
AUDIO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_TTS_DIR.mkdir(parents=True, exist_ok=True)

_QUESTION_AGENTS = {
    "resume": resume_agent,
    "trend": trend_agent,
    "stress": stress_agent,
}
# 음성 흐름은 프론트가 종료를 제어하므로 meta가 judge로 빠지지 않게 크게 잡는다
_VOICE_MAX_ROUNDS = 99


def _doc_text(docs: dict, key: str) -> str:
    """agent_context의 candidate_documents에서 특정 문서 본문을 꺼낸다."""
    return (docs.get(key) or {}).get("text", "")


def _build_state(session_id: int, turns: list[dict]) -> InterviewState:
    """SQLite의 세션 컨텍스트 + 턴 기록으로 InterviewState를 구성한다."""
    record = get_agent_context(session_id)
    ctx = record[1] if record else {}
    docs = ctx.get("candidate_documents", {})

    messages: list[dict] = []
    for t in turns:
        if t.get("question_text"):
            messages.append({"role": "interviewer", "content": t["question_text"]})
        if t.get("transcript"):
            messages.append({"role": "candidate", "content": t["transcript"]})

    return {
        "session_id": str(session_id),
        "cover_letter": _doc_text(docs, "self_intro"),
        "resume_text": _doc_text(docs, "resume"),
        "portfolio_text": _doc_text(docs, "portfolio"),
        "company": ctx.get("company", ""),
        "role": ctx.get("role", ""),
        "job_posting_text": (ctx.get("job_posting") or {}).get("text"),
        "round": len(turns),
        "max_rounds": _VOICE_MAX_ROUNDS,
        "messages": messages,
        "agent_history": [t["agent_type"] for t in turns if t.get("agent_type")],
        "current_agent": None,
        "current_question": None,
        "last_answer": turns[-1]["transcript"] if turns else None,
        "is_done": False,
        "scores": {},
        "feedback": None,
    }


async def _generate_next_question(session_id: int) -> tuple[str, str]:
    """지금까지의 면접 기록으로 meta→질문 에이전트를 돌려 다음 질문을 만든다.

    반환: (다음 질문 텍스트, 다음 면접관 유형)
    """
    turns = get_turns(session_id)
    state = _build_state(session_id, turns)

    state = await meta_agent(state)
    agent_type = state.get("current_agent") or "resume"
    agent_fn = _QUESTION_AGENTS.get(agent_type, resume_agent)

    state = await agent_fn(state)
    return state["current_question"], agent_type


@router.post("/{session_id}/turns/first")
async def create_first_turn(session_id: int):
    """면접 첫 질문 생성 — 답변 없이 이력서 기반 오프닝 질문 + TTS 오디오를 반환한다.

    턴 기록이 0건이면 meta가 round 0으로 보고 resume 에이전트를 선택한다.
    """
    try:
        question, agent_type = await _generate_next_question(session_id)
    except Exception:
        logger.exception("첫 질문 생성 실패 — 폴백 질문 사용")
        question, agent_type = "간단히 자기소개를 부탁드립니다.", "resume"

    turn_uid = uuid.uuid4().hex[:8]
    tts_filename = f"s{session_id}_first_{turn_uid}.mp3"
    tts = synthesize_speech(question, AUDIO_TTS_DIR / tts_filename)
    tts_audio_url = (
        f"/api/audio/tts/{tts_filename}" if tts["status"] == "success" else None
    )

    return {
        "round_no": 0,
        "question": question,
        "agent_type": agent_type,
        "tts_audio_url": tts_audio_url,
        "tts_provider": tts.get("provider"),
        "tts_status": tts["status"],
    }


@router.post("/{session_id}/turns/audio")
async def create_audio_turn(
    session_id: int,
    audio_file: UploadFile = File(...),
    round_no: int = Form(...),
    question_text: str = Form(...),
    agent_type: str = Form("resume"),
):
    """음성 저장 → STT → 턴 DB 기록 → 실제 에이전트가 다음 질문 생성 → TTS.

    실패해도 partial 응답을 200으로 돌려 프론트가 죽지 않게 한다.
    """
    turn_uid = uuid.uuid4().hex[:8]
    ext = Path(audio_file.filename or "").suffix or ".webm"
    answer_path = AUDIO_UPLOAD_DIR / f"s{session_id}_r{round_no}_{turn_uid}{ext}"

    # ① 음성 파일 저장
    try:
        with answer_path.open("wb") as f:
            shutil.copyfileobj(audio_file.file, f)
    except Exception as e:
        logger.exception("Audio save failed")
        raise HTTPException(status_code=500, detail=f"audio save failed: {e}") from e

    # ② STT
    stt = transcribe_audio(answer_path, language="ko")
    if stt["status"] != "success":
        return {
            "turn_id": turn_uid,
            "transcript": "",
            "stt_status": "failed",
            "stt_error": stt.get("error"),
            "next_question": "음성 인식에 실패했습니다. 한 번 더 말씀해 주시겠어요?",
            "next_agent_type": agent_type,
            "evaluation": None,
            "tts_audio_url": None,
        }
    transcript = stt["transcript"]

    # ③ 이번 턴을 DB에 기록 (음성 답변 영속화)
    try:
        insert_turn(
            session_id=session_id,
            round_no=round_no,
            agent_type=agent_type,
            question_text=question_text,
            audio_path=str(answer_path),
            transcript=transcript,
        )
    except Exception:
        logger.exception("interview_turn 저장 실패 — 계속 진행")

    # ④ 실제 에이전트로 다음 질문 생성
    try:
        next_question, next_agent = await _generate_next_question(session_id)
    except Exception:
        logger.exception("다음 질문 생성 실패 — 폴백 질문 사용")
        next_question = "방금 답변을 조금 더 구체적으로 설명해 주시겠어요?"
        next_agent = agent_type

    # ⑤ TTS
    tts_filename = f"s{session_id}_r{round_no}_{turn_uid}.mp3"
    tts_path = AUDIO_TTS_DIR / tts_filename
    tts = synthesize_speech(next_question, tts_path)
    tts_audio_url = (
        f"/api/audio/tts/{tts_filename}" if tts["status"] == "success" else None
    )

    return {
        "turn_id": turn_uid,
        "transcript": transcript,
        "stt_status": "success",
        "stt_provider": stt["provider"],
        "next_question": next_question,
        "next_agent_type": next_agent,
        # 턴별 평가는 없음 — 최종 평가는 면접 종료 시 judge가 수행
        "evaluation": None,
        "tts_audio_url": tts_audio_url,
        "tts_provider": tts.get("provider"),
        "tts_status": tts["status"],
    }

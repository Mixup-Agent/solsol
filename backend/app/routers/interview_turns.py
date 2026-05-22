"""Audio-based interview turn endpoint."""
import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.stt import transcribe_audio
from app.services.tts import synthesize_speech


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interview-sessions", tags=["turns"])

AUDIO_UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "audio"
AUDIO_TTS_DIR = Path(__file__).resolve().parents[1] / "data" / "tts"
AUDIO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_TTS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/{session_id}/turns/audio")
async def create_audio_turn(
    session_id: int,
    audio_file: UploadFile = File(...),
    round_no: int = Form(...),
    question_text: str = Form(...),
    agent_type: str = Form("resume"),
):
    """
    1) 음성 저장 → 2) STT → 3) Agent (지금은 mock) → 4) TTS → 5) 응답
    실패해도 partial 응답을 200으로 돌려서 프론트가 죽지 않게 한다.
    """
    turn_uid = uuid.uuid4().hex[:8]
    ext = Path(audio_file.filename or "").suffix or ".webm"
    answer_path = AUDIO_UPLOAD_DIR / f"s{session_id}_r{round_no}_{turn_uid}{ext}"

    # ① 파일 저장
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
            "evaluation": None,
            "tts_audio_url": None,
        }
    transcript = stt["transcript"]

    # ③ Agent (mock — 추후 교체)
    agent_response = _mock_agent_response(transcript, question_text, agent_type)
    next_question = agent_response["next_question"]
    evaluation = agent_response["evaluation"]

    # ④ TTS
    tts_filename = f"s{session_id}_r{round_no}_{turn_uid}.mp3"
    tts_path = AUDIO_TTS_DIR / tts_filename
    tts = synthesize_speech(next_question, tts_path)
    tts_audio_url = f"/api/audio/tts/{tts_filename}" if tts["status"] == "success" else None

    return {
        "turn_id": turn_uid,
        "transcript": transcript,
        "stt_status": "success",
        "stt_provider": stt["provider"],
        "next_question": next_question,
        "evaluation": evaluation,
        "tts_audio_url": tts_audio_url,
        "tts_provider": tts.get("provider"),
        "tts_status": tts["status"],
    }


def _mock_agent_response(transcript: str, question_text: str, agent_type: str) -> dict:
    """단순 규칙 기반 mock. Solar Pro3 연결 전 데모용."""
    weakness = None
    if not any(ch.isdigit() for ch in transcript):
        weakness = "성과 수치 부족"
        nxt = "그 성과를 어떤 지표로 측정하셨나요? 구체적인 수치로 말씀해 주세요."
    elif len(transcript) < 60:
        weakness = "답변 구체성 부족"
        nxt = "조금 더 구체적으로 설명해 주시겠어요? 그 결정을 내린 근거가 궁금합니다."
    else:
        nxt = "그 선택이 최선이었다는 근거가 있나요? 다른 대안과 비교한 적이 있나요?"

    return {
        "next_question": nxt,
        "evaluation": {
            "specificity": 2 if weakness else 4,
            "logic": 3,
            "weakness": weakness,
            "agent_type": agent_type,
            "question_text": question_text,
        },
    }


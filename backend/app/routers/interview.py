import re

from fastapi import APIRouter, HTTPException

from app.agents.state import InterviewState
from app.models.interview import AnswerRequest, AnswerResponse, ReportResponse, StartResponse
from app.services.answer_quality import evaluate_answer_quality
from app.services.graph import build_interview_graph
from app.services.interview_db import get_agent_context
from app.services.session_store import get_session, update_session

router = APIRouter(tags=["interview"])


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _build_state_from_context(session_id: str, context: dict) -> InterviewState:
    docs = context.get("candidate_documents", {})
    return {
        "session_id": session_id,
        "cover_letter": _strip_html(docs.get("self_intro", {}).get("text", "")),
        "resume_text": _strip_html(docs.get("resume", {}).get("text", "")),
        "portfolio_text": _strip_html(docs.get("portfolio", {}).get("text", "")) or None,
        "company": context.get("company", ""),
        "role": context.get("role", ""),
        "job_posting_text": context.get("job_posting", {}).get("text", "") or None,
        "round": 0,
        "max_rounds": 8,
        "messages": [],
        "agent_history": [],
        "meta_decisions": [],
        "answer_quality_history": [],
        "current_agent": None,
        "current_question": None,
        "current_question_sources": [],
        "last_answer": None,
        "last_answer_quality": None,
        "is_done": False,
        "scores": {},
        "feedback": None,
    }


@router.post("/session/{session_id}/start", response_model=StartResponse)
async def start_interview(session_id: str):
    state: InterviewState | None = None

    # 신규 흐름: SQLite agent_context (integer session_id)
    try:
        record = get_agent_context(int(session_id))
        if record is not None:
            _, context = record
            state = _build_state_from_context(session_id, context)
    except (ValueError, TypeError):
        pass

    # 구 흐름: Redis (UUID session_id)
    if state is None:
        session = await get_session(session_id)
        if not session:
            raise HTTPException(404, "세션을 찾을 수 없습니다")
        if session.get("status") == "in_progress":
            raise HTTPException(400, "이미 진행 중인 면접입니다")
        state = {
            "session_id": session_id,
            "cover_letter": session["parsed"]["cover_letter"],
            "resume_text": session["parsed"]["resume_text"],
            "portfolio_text": session["parsed"].get("portfolio_text"),
            "company": session["parsed"]["company"],
            "role": session["parsed"]["role"],
            "job_posting_text": session["parsed"].get("job_posting_text"),
            "round": 0,
            "max_rounds": 8,
            "messages": [],
            "agent_history": [],
            "meta_decisions": [],
            "answer_quality_history": [],
            "current_agent": None,
            "current_question": None,
            "current_question_sources": [],
            "last_answer": None,
            "last_answer_quality": None,
            "is_done": False,
            "scores": {},
            "feedback": None,
        }

    graph = build_interview_graph()
    result = await graph.ainvoke(state)

    await update_session(session_id, {"status": "in_progress", "interview_state": result})

    return StartResponse(
        session_id=session_id,
        round=result["round"],
        question=result["current_question"],
        agent=result["current_agent"],
    )


@router.post("/session/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(session_id: str, body: AnswerRequest):
    session = await get_session(session_id)
    if not session:
        raise HTTPException(404, "세션을 찾을 수 없습니다")
    if session.get("status") != "in_progress":
        raise HTTPException(400, "진행 중인 면접이 없습니다")

    state: InterviewState = session["interview_state"]
    latest_question = state.get("current_question") or ""
    recent_answers = [
        m.get("content", "")
        for m in state.get("messages", [])
        if m.get("role") == "candidate"
    ]

    state["messages"].append({"role": "candidate", "content": body.answer})
    state["last_answer"] = body.answer
    quality = await evaluate_answer_quality(
        question_text=latest_question,
        answer_text=body.answer,
        recent_answers=recent_answers,
        session_id=state["session_id"],
    )
    state["last_answer_quality"] = quality
    state.setdefault("answer_quality_history", []).append(
        {
            "round_no": state["round"] + 1,
            "agent_type": state.get("current_agent"),
            "question_text": latest_question,
            "transcript": body.answer,
            **quality,
        }
    )
    state["round"] += 1

    graph = build_interview_graph()
    result = await graph.ainvoke(state)

    session["interview_state"] = result
    if result["is_done"]:
        session["status"] = "done"
    await update_session(session_id, session)

    return AnswerResponse(
        session_id=session_id,
        round=result["round"],
        question=result.get("current_question"),
        agent=result.get("current_agent"),
        is_done=result["is_done"],
    )


@router.post("/session/{session_id}/finalize")
async def finalize_interview(session_id: str):
    """면접을 종료할 때 judge 에이전트를 실행해 리포트를 생성한다.
    Redis(텍스트 플로우)와 SQLite(오디오 플로우) 둘 다 지원한다.
    """
    from app.agents.judge import judge_agent

    session = await get_session(session_id)
    if session and session.get("status") == "done":
        return {"status": "already_done"}

    state: InterviewState | None = None

    # Redis 플로우: interview_state가 이미 있는 경우
    if session and session.get("interview_state"):
        state = session["interview_state"]
    else:
        # SQLite 플로우: 오디오 턴 기반 세션
        try:
            int_id = int(session_id)
            from app.services.interview_db import get_agent_context, get_turns

            turns = get_turns(int_id)
            record = get_agent_context(int_id)
            if record:
                ctx = record[1]
                docs = ctx.get("candidate_documents", {})

                messages: list[dict] = []
                for t in turns:
                    if t.get("question_text"):
                        messages.append({"role": "interviewer", "content": t["question_text"]})
                    if t.get("transcript"):
                        messages.append({"role": "candidate", "content": t["transcript"]})

                state = {
                    "session_id": session_id,
                    "cover_letter": _strip_html((docs.get("self_intro") or {}).get("text", "")),
                    "resume_text": _strip_html((docs.get("resume") or {}).get("text", "")),
                    "portfolio_text": _strip_html((docs.get("portfolio") or {}).get("text", "")) or None,
                    "company": ctx.get("company", ""),
                    "role": ctx.get("role", ""),
                    "job_posting_text": (ctx.get("job_posting") or {}).get("text") or None,
                    "round": len(turns),
                    "max_rounds": 99,
                    "messages": messages,
                    "agent_history": [t["agent_type"] for t in turns if t.get("agent_type")],
                    "meta_decisions": [],
                    "answer_quality_history": [
                        {
                            "round_no": t.get("round_no"),
                            "agent_type": t.get("agent_type"),
                            "question_text": t.get("question_text") or "",
                            "transcript": t.get("transcript") or "",
                            **(t.get("answer_quality") or {}),
                        }
                        for t in turns
                        if t.get("transcript")
                    ],
                    "current_agent": None,
                    "current_question": None,
                    "current_question_sources": [],
                    "last_answer": turns[-1]["transcript"] if turns else None,
                    "last_answer_quality": (
                        (turns[-1].get("answer_quality") if turns else None) or None
                    ),
                    "is_done": False,
                    "scores": {},
                    "feedback": None,
                }
        except (ValueError, TypeError):
            pass

    if not state:
        raise HTTPException(404, "세션 상태를 찾을 수 없습니다")

    result = await judge_agent(state)
    new_session = session or {}
    new_session["interview_state"] = result
    new_session["status"] = "done"
    await update_session(session_id, new_session)

    return {"status": "done"}


@router.get("/session/{session_id}/report", response_model=ReportResponse)
async def get_report(session_id: str):
    session = await get_session(session_id)
    if not session:
        raise HTTPException(404, "세션을 찾을 수 없습니다")
    if session.get("status") != "done":
        raise HTTPException(400, "면접이 아직 완료되지 않았습니다")

    state = session["interview_state"]

    return ReportResponse(
        session_id=session_id,
        scores=state.get("scores") or {},
        feedback=state.get("feedback") or "평가 결과를 불러올 수 없습니다.",
        messages=state.get("messages") or [],
        agent_history=state.get("agent_history") or [],
    )

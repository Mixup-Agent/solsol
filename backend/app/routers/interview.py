from fastapi import APIRouter, HTTPException

from app.agents.state import InterviewState
from app.models.interview import AnswerRequest, AnswerResponse, ReportResponse, StartResponse
from app.services.graph import build_interview_graph
from app.services.session_store import get_session, update_session

router = APIRouter(tags=["interview"])


@router.post("/session/{session_id}/start", response_model=StartResponse)
async def start_interview(session_id: str):
    session = await get_session(session_id)
    if not session:
        raise HTTPException(404, "세션을 찾을 수 없습니다")
    if session.get("status") == "in_progress":
        raise HTTPException(400, "이미 진행 중인 면접입니다")

    state: InterviewState = {
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
        "current_agent": None,
        "current_question": None,
        "last_answer": None,
        "is_done": False,
        "scores": {},
        "feedback": None,
    }

    graph = build_interview_graph()
    result = await graph.ainvoke(state)

    session["status"] = "in_progress"
    session["interview_state"] = result
    await update_session(session_id, session)

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

    state["messages"].append({"role": "candidate", "content": body.answer})
    state["last_answer"] = body.answer
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
        scores=state["scores"],
        feedback=state["feedback"],
        messages=state["messages"],
        agent_history=state["agent_history"],
    )

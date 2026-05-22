from pydantic import BaseModel
from typing import Optional


class StartResponse(BaseModel):
    session_id: str
    round: int
    question: str
    agent: str


class AnswerRequest(BaseModel):
    answer: str


class AnswerResponse(BaseModel):
    session_id: str
    round: int
    question: Optional[str] = None
    agent: Optional[str] = None
    is_done: bool


class ReportResponse(BaseModel):
    session_id: str
    scores: dict
    feedback: str
    messages: list[dict]
    agent_history: list[str]

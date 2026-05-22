from typing import Any

from pydantic import BaseModel


class InterviewSessionCreateResponse(BaseModel):
    session_id: int
    company: str
    role: str
    document_parse_status: dict[str, str]
    job_posting_status: str
    agent_context_id: int


class AgentContextResponse(BaseModel):
    session_id: int
    context_id: int
    context: dict[str, Any]


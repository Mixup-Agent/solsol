from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ParsedData(BaseModel):
    cover_letter: str
    resume_text: str
    portfolio_text: Optional[str] = None
    company: str
    role: str
    job_posting_url: Optional[str] = None
    job_posting_text: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    status: str
    parsed: ParsedData
    created_at: datetime

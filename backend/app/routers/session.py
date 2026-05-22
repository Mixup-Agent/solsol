import asyncio
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Response, UploadFile, File, status

from app.models.session import SessionResponse
from app.services.crawler import crawl_job_posting
from app.services.file_parser import extract_pdf_text
from app.services.session_store import create_session, delete_session, get_session

router = APIRouter(prefix="/session", tags=["session"])


async def _none():
    return None


def _is_pdf(file: UploadFile) -> bool:
    return (
        file.content_type == "application/pdf"
        or (file.filename or "").lower().endswith(".pdf")
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SessionResponse)
async def create_session_endpoint(
    cover_letter: str = Form(...),
    resume: UploadFile = File(...),
    portfolio: Optional[UploadFile] = File(None),
    company: str = Form(...),
    role: str = Form(...),
    job_posting_url: Optional[str] = Form(None),
):
    if not _is_pdf(resume):
        raise HTTPException(status_code=400, detail="resume는 PDF 파일이어야 합니다")
    if portfolio and not _is_pdf(portfolio):
        raise HTTPException(status_code=400, detail="portfolio는 PDF 파일이어야 합니다")

    resume_bytes = await resume.read()
    portfolio_bytes = await portfolio.read() if portfolio else None

    try:
        resume_text, portfolio_text, job_posting_text = await asyncio.gather(
            extract_pdf_text(resume_bytes),
            extract_pdf_text(portfolio_bytes) if portfolio_bytes else _none(),
            crawl_job_posting(job_posting_url) if job_posting_url else _none(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")

    parsed = {
        "cover_letter": cover_letter,
        "resume_text": resume_text,
        "portfolio_text": portfolio_text,
        "company": company,
        "role": role,
        "job_posting_url": job_posting_url,
        "job_posting_text": job_posting_text,
    }

    try:
        _, payload = await create_session(parsed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis 저장 실패: {str(e)}")

    return payload


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(session_id: str):
    payload = await get_session(session_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없거나 만료되었습니다")
    return payload


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_endpoint(session_id: str):
    deleted = await delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

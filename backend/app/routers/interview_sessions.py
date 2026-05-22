from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.models.interview_session import (
    AgentContextResponse,
    InterviewSessionCreateResponse,
)
from app.services.crawler import extract_job_posting_detail
from app.services.file_parser import parse_pdf_with_upstage
from app.services.interview_db import (
    create_session,
    get_agent_context,
    insert_agent_context,
    insert_candidate_document,
    insert_job_posting,
    update_session_status,
)


router = APIRouter(prefix="/interview-sessions", tags=["interview-sessions"])

UPLOADS_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 20 * 1024 * 1024


def _validate_pdf(upload: UploadFile) -> None:
    file_name = (upload.filename or "").lower()
    content_type = upload.content_type or ""
    if not file_name.endswith(".pdf") and content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF 파일만 업로드할 수 있습니다: {upload.filename}",
        )


async def _save_upload(upload: UploadFile, session_id: int) -> tuple[str, bytes]:
    _validate_pdf(upload)
    raw = await upload.read()
    if len(raw) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"파일 크기 제한(20MB) 초과: {upload.filename}",
        )

    target_dir = UPLOADS_DIR / str(session_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid4().hex}_{Path(upload.filename or 'document.pdf').name}"
    file_path = target_dir / file_name
    file_path.write_bytes(raw)
    await upload.seek(0)
    return str(file_path), raw


@router.post("", response_model=InterviewSessionCreateResponse)
async def create_interview_session(
    company: str = Form(...),
    role: str = Form(...),
    job_posting_url: str = Form(...),
    self_intro_file: UploadFile = File(...),
    resume_file: UploadFile = File(...),
    portfolio_file: UploadFile = File(...),
):
    _validate_pdf(self_intro_file)
    _validate_pdf(resume_file)
    _validate_pdf(portfolio_file)
    session_id = create_session(company=company, role=role, job_posting_url=job_posting_url)
    parse_status: dict[str, str] = {}
    doc_context: dict[str, dict[str, str]] = {
        "self_intro": {"file_name": "", "text": "", "markdown": ""},
        "resume": {"file_name": "", "text": "", "markdown": ""},
        "portfolio": {"file_name": "", "text": "", "markdown": ""},
    }

    upload_map = {
        "self_intro": self_intro_file,
        "resume": resume_file,
        "portfolio": portfolio_file,
    }

    for doc_type, upload in upload_map.items():
        file_path, file_bytes = await _save_upload(upload, session_id)
        result = await parse_pdf_with_upstage(file_bytes, upload.filename or f"{doc_type}.pdf")
        parse_status[doc_type] = result["parse_status"]
        insert_candidate_document(
            session_id=session_id,
            document_type=doc_type,
            original_file_name=upload.filename or "",
            file_path=file_path,
            parse_status=result["parse_status"],
            parsed_text=result["parsed_text"],
            parsed_markdown=result["parsed_markdown"],
            parsed_html=result["parsed_html"],
            raw_response=result["raw_response"],
        )
        doc_context[doc_type] = {
            "file_name": upload.filename or "",
            "text": result["parsed_text"],
            "markdown": result["parsed_markdown"],
        }

    posting = await extract_job_posting_detail(job_posting_url)
    insert_job_posting(
        session_id=session_id,
        url=job_posting_url,
        title=posting["title"],
        raw_html=posting["raw_html"],
        cleaned_text=posting["cleaned_text"],
        extraction_status=posting["extraction_status"],
        error_message=posting["error_message"],
    )

    context = {
        "session_id": session_id,
        "company": company,
        "role": role,
        "job_posting": {
            "url": job_posting_url,
            "title": posting["title"],
            "text": posting["cleaned_text"],
        },
        "candidate_documents": doc_context,
    }
    agent_context_id = insert_agent_context(session_id=session_id, context=context)
    update_session_status(session_id, "completed")

    return InterviewSessionCreateResponse(
        session_id=session_id,
        company=company,
        role=role,
        document_parse_status=parse_status,
        job_posting_status=posting["extraction_status"],
        agent_context_id=agent_context_id,
    )


@router.get("/{session_id}/context", response_model=AgentContextResponse)
async def get_context(session_id: int):
    record = get_agent_context(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="context를 찾을 수 없습니다.")

    context_id, context = record
    return AgentContextResponse(session_id=session_id, context_id=context_id, context=context)


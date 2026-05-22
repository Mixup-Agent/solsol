import json
from io import BytesIO

import httpx
import pdfplumber

from app.config import settings


async def extract_pdf_text(file_bytes: bytes) -> str:
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        text = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        ).strip()
    if not text:
        raise ValueError("PDF에서 텍스트를 추출할 수 없습니다 (스캔 이미지 PDF 불가)")
    return text


async def parse_pdf_with_upstage(file_bytes: bytes, file_name: str) -> dict[str, str]:
    api_key = settings.upstage_api_key.strip()
    if not api_key:
        return {
            "parse_status": "failed",
            "parsed_text": "",
            "parsed_markdown": "",
            "parsed_html": "",
            "raw_response": "UPSTAGE_API_KEY is not configured.",
        }

    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"document": (file_name, file_bytes, "application/pdf")}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.upstage.ai/v1/document-ai/document-parse",
                headers=headers,
                files=files,
            )
    except Exception as exc:
        return {
            "parse_status": "failed",
            "parsed_text": "",
            "parsed_markdown": "",
            "parsed_html": "",
            "raw_response": f"Request error: {exc}",
        }

    if response.status_code != 200:
        return {
            "parse_status": "failed",
            "parsed_text": "",
            "parsed_markdown": "",
            "parsed_html": "",
            "raw_response": f"HTTP {response.status_code}: {response.text}",
        }

    try:
        payload = response.json()
    except Exception:
        return {
            "parse_status": "failed",
            "parsed_text": "",
            "parsed_markdown": "",
            "parsed_html": "",
            "raw_response": f"Invalid JSON response: {response.text}",
        }

    parsed_text = payload.get("text") or payload.get("content") or ""
    parsed_markdown = (
        payload.get("markdown")
        or payload.get("content_markdown")
        or payload.get("parsed_markdown")
        or ""
    )
    parsed_html = (
        payload.get("html")
        or payload.get("content_html")
        or payload.get("parsed_html")
        or ""
    )

    if not parsed_text and parsed_markdown:
        parsed_text = parsed_markdown
    if not parsed_text and parsed_html:
        parsed_text = parsed_html

    return {
        "parse_status": "success",
        "parsed_text": parsed_text if isinstance(parsed_text, str) else str(parsed_text),
        "parsed_markdown": (
            parsed_markdown if isinstance(parsed_markdown, str) else str(parsed_markdown)
        ),
        "parsed_html": parsed_html if isinstance(parsed_html, str) else str(parsed_html),
        "raw_response": json.dumps(payload, ensure_ascii=False),
    }

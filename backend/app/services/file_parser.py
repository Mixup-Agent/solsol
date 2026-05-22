import pdfplumber
from io import BytesIO


async def extract_pdf_text(file_bytes: bytes) -> str:
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        text = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        ).strip()
    if not text:
        raise ValueError("PDF에서 텍스트를 추출할 수 없습니다 (스캔 이미지 PDF 불가)")
    return text

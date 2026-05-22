import httpx
from bs4 import BeautifulSoup
from typing import Optional

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


async def crawl_job_posting(url: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url, headers=_HEADERS, follow_redirects=True)
            res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        return soup.get_text(separator="\n", strip=True)[:5000]
    except Exception:
        return None


async def extract_job_posting_detail(url: str) -> dict[str, str]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url, headers=_HEADERS, follow_redirects=True)
            res.raise_for_status()
    except Exception as exc:
        return {
            "title": "",
            "raw_html": "",
            "cleaned_text": "",
            "extraction_status": "failed",
            "error_message": str(exc),
        }

    raw_html = res.text
    soup = BeautifulSoup(raw_html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    body = soup.body if soup.body else soup
    cleaned_text = " ".join(body.get_text(separator=" ", strip=True).split())

    if not cleaned_text:
        return {
            "title": title,
            "raw_html": raw_html,
            "cleaned_text": "",
            "extraction_status": "failed",
            "error_message": "본문 추출 실패",
        }

    extraction_status = "weak" if len(cleaned_text) < 500 else "success"
    return {
        "title": title,
        "raw_html": raw_html,
        "cleaned_text": cleaned_text,
        "extraction_status": extraction_status,
        "error_message": "",
    }

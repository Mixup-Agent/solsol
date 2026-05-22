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

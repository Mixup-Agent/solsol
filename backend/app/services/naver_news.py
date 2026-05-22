"""Naver 뉴스 SQLite에서 트렌드 질문용 컨텍스트를 읽는다."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path


_ROOT_DIR = Path(__file__).resolve().parents[3]
_DEFAULT_DB_PATH = _ROOT_DIR / "data" / "news.db"


def _extract_keywords(role: str, company: str, job_posting_text: str | None) -> list[str]:
    source = " ".join([role or "", company or "", job_posting_text or ""])
    tokens = re.findall(r"[A-Za-z0-9가-힣\+\-]{2,}", source)

    # 너무 일반적인 단어는 제외
    stopwords = {
        "채용",
        "모집",
        "담당",
        "우대",
        "지원",
        "경험",
        "회사",
        "직무",
        "역할",
        "개발",
    }

    seen: set[str] = set()
    keywords: list[str] = []
    for token in tokens:
        normalized = token.lower()
        if token in stopwords or normalized in seen:
            continue
        seen.add(normalized)
        keywords.append(token)
        if len(keywords) >= 12:
            break
    return keywords


def build_trend_news_context(
    role: str,
    company: str,
    job_posting_text: str | None,
    limit: int = 5,
) -> str:
    """role/company/job posting 기준으로 뉴스를 찾아 LLM 프롬프트 텍스트를 구성한다."""
    if limit <= 0:
        return ""

    db_path = _DEFAULT_DB_PATH
    if not db_path.exists():
        return ""

    keywords = _extract_keywords(role=role, company=company, job_posting_text=job_posting_text)
    if not keywords:
        return ""

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            # 키워드가 title/summary/query에 포함되면 최신순으로 수집
            where_terms = []
            params: list[str | int] = []
            for keyword in keywords:
                where_terms.append("(query LIKE ? OR title LIKE ? OR summary LIKE ?)")
                like = f"%{keyword}%"
                params.extend([like, like, like])

            sql = f"""
                SELECT query, title, summary, published_at, url, article_content
                FROM news_articles
                WHERE {" OR ".join(where_terms)}
                ORDER BY id DESC
                LIMIT ?
            """
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
    except Exception:
        return ""

    if not rows:
        return ""

    lines = ["[네이버 뉴스 참고]"]
    for idx, row in enumerate(rows, start=1):
        article = (row["article_content"] or "").strip()
        excerpt = article[:220].replace("\n", " ")
        lines.append(
            f"{idx}. [{row['query']}] {row['title']} | {row['published_at']} | {row['url']}"
        )
        if row["summary"]:
            lines.append(f"   - 요약: {row['summary']}")
        if excerpt:
            lines.append(f"   - 본문 발췌: {excerpt}")

    return "\n".join(lines)

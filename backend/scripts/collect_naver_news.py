#!/usr/bin/env python3
import argparse
import json
import os
import re
import sqlite3
import sys
from html import unescape
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv


NAVER_NEWS_ENDPOINT = "https://openapi.naver.com/v1/search/news.json"
DB_PATH = Path("data/news.db")


def strip_html(value: str) -> str:
    if not value:
        return ""
    without_tags = re.sub(r"<[^>]+>", "", value)
    return unescape(without_tags).strip()


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            url TEXT UNIQUE NOT NULL,
            naver_url TEXT,
            published_at TEXT,
            article_content TEXT,
            collected_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    columns = conn.execute("PRAGMA table_info(news_articles)").fetchall()
    column_names = {column[1] for column in columns}
    if "article_content" not in column_names:
        conn.execute("ALTER TABLE news_articles ADD COLUMN article_content TEXT")
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_news_url
        ON news_articles(url);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_news_published_at
        ON news_articles(published_at);
        """
    )
    conn.commit()


def fetch_news(query: str, client_id: str, client_secret: str) -> list[dict]:
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": query,
        "display": 10,
        "start": 1,
        "sort": "date",
    }
    response = requests.get(
        NAVER_NEWS_ENDPOINT,
        headers=headers,
        params=params,
        timeout=10,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"네이버 API 호출 실패 ({response.status_code}): {response.text}"
        )
    payload = response.json()
    return payload.get("items", [])


def fetch_article_content(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()

    candidates = []
    selectors = [
        "article",
        "main",
        "#articleBodyContents",
        "#dic_area",
        "#newsct_article",
        ".article_body",
        ".news_end",
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            text = " ".join(node.get_text(" ", strip=True).split())
            if text:
                candidates.append(text)

    if not candidates and soup.body:
        candidates.append(" ".join(soup.body.get_text(" ", strip=True).split()))

    if not candidates:
        return ""
    return max(candidates, key=len)[:50000]


def save_articles(
    conn: sqlite3.Connection,
    query: str,
    items: Iterable[dict],
) -> tuple[int, int, int, int]:
    fetched = 0
    inserted = 0
    skipped = 0
    content_saved = 0

    for item in items:
        fetched += 1
        title = strip_html(item.get("title", ""))
        summary = strip_html(item.get("description", ""))
        original_link = (item.get("originallink") or "").strip()
        naver_link = (item.get("link") or "").strip()
        url = original_link or naver_link
        pub_date = (item.get("pubDate") or "").strip()

        if not title or not url:
            skipped += 1
            continue

        existing = conn.execute(
            "SELECT id, article_content FROM news_articles WHERE url = ?",
            (url,),
        ).fetchone()
        if existing:
            skipped += 1
            if not (existing[1] or "").strip():
                try:
                    article_content = fetch_article_content(url)
                except Exception:
                    article_content = ""
                if article_content:
                    conn.execute(
                        "UPDATE news_articles SET article_content = ? WHERE id = ?",
                        (article_content, existing[0]),
                    )
                    content_saved += 1
            continue

        try:
            article_content = fetch_article_content(url)
        except Exception:
            article_content = ""

        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO news_articles
            (query, title, summary, url, naver_url, published_at, article_content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (query, title, summary, url, naver_link, pub_date, article_content),
        )
        if cursor.rowcount == 1:
            inserted += 1
            if article_content:
                content_saved += 1
        else:
            skipped += 1

    conn.commit()
    return fetched, inserted, skipped, content_saved


def get_total_count(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) FROM news_articles").fetchone()
    return int(row[0]) if row else 0


def export_articles_to_json(
    conn: sqlite3.Connection,
    queries: list[str],
    output_path: str,
    limit: int,
) -> int:
    placeholders = ",".join("?" for _ in queries)
    sql = f"""
        SELECT
            id,
            query,
            title,
            summary,
            url,
            naver_url,
            published_at,
            article_content,
            collected_at
        FROM news_articles
        WHERE query IN ({placeholders})
        ORDER BY id DESC
        LIMIT ?
    """
    rows = conn.execute(sql, [*queries, limit]).fetchall()
    payload = [
        {
            "id": row[0],
            "query": row[1],
            "title": row[2],
            "summary": row[3],
            "url": row[4],
            "naver_url": row[5],
            "published_at": row[6],
            "article_content": row[7],
            "collected_at": row[8],
        }
        for row in rows
    ]

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="네이버 뉴스 API로 기사를 수집해 SQLite에 저장합니다."
    )
    parser.add_argument(
        "--json-output",
        default="",
        help="입력된 query 기준으로 저장 결과를 JSON 파일로 내보낼 경로",
    )
    parser.add_argument(
        "--json-limit",
        type=int,
        default=100,
        help="JSON으로 내보낼 최대 행 수 (기본값: 100)",
    )
    parser.add_argument("queries", nargs="+", help="검색어 목록")
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        print(
            "에러: NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 설정되지 않았습니다.",
            file=sys.stderr,
        )
        return 1

    args = parse_args()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)

        for query in args.queries:
            try:
                items = fetch_news(query, client_id, client_secret)
                fetched, inserted, skipped, content_saved = save_articles(conn, query, items)
                print(
                    f"[{query}] fetched={fetched}, inserted={inserted}, "
                    f"skipped={skipped}, content_saved={content_saved}"
                )
            except Exception as exc:
                print(f"[{query}] 실패: {exc}", file=sys.stderr)
                continue

        total_count = get_total_count(conn)
        print(f"전체 저장 개수: {total_count}")

        if args.json_output:
            exported = export_articles_to_json(
                conn=conn,
                queries=args.queries,
                output_path=args.json_output,
                limit=max(args.json_limit, 1),
            )
            print(f"JSON 내보내기 완료: {args.json_output} ({exported}건)")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

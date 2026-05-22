import json
import sqlite3
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = APP_DIR / "data"
DB_PATH = DATA_DIR / "interview.db"


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_interview_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS interview_sessions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              company TEXT NOT NULL,
              role TEXT NOT NULL,
              job_posting_url TEXT NOT NULL,
              status TEXT DEFAULT 'created',
              created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS candidate_documents (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_id INTEGER NOT NULL,
              document_type TEXT NOT NULL,
              original_file_name TEXT,
              file_path TEXT,
              parse_status TEXT,
              parsed_text TEXT,
              parsed_markdown TEXT,
              parsed_html TEXT,
              raw_response TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS job_postings (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_id INTEGER NOT NULL,
              url TEXT NOT NULL,
              title TEXT,
              raw_html TEXT,
              cleaned_text TEXT,
              extraction_status TEXT,
              error_message TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_contexts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_id INTEGER NOT NULL,
              context_json TEXT NOT NULL,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()


def create_session(company: str, role: str, job_posting_url: str) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO interview_sessions (company, role, job_posting_url, status)
            VALUES (?, ?, ?, ?)
            """,
            (company, role, job_posting_url, "processing"),
        )
        conn.commit()
        return int(cursor.lastrowid)


def update_session_status(session_id: int, status: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE interview_sessions SET status = ? WHERE id = ?",
            (status, session_id),
        )
        conn.commit()


def insert_candidate_document(
    session_id: int,
    document_type: str,
    original_file_name: str,
    file_path: str,
    parse_status: str,
    parsed_text: str,
    parsed_markdown: str,
    parsed_html: str,
    raw_response: str,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO candidate_documents (
                session_id,
                document_type,
                original_file_name,
                file_path,
                parse_status,
                parsed_text,
                parsed_markdown,
                parsed_html,
                raw_response
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                document_type,
                original_file_name,
                file_path,
                parse_status,
                parsed_text,
                parsed_markdown,
                parsed_html,
                raw_response,
            ),
        )
        conn.commit()


def insert_job_posting(
    session_id: int,
    url: str,
    title: str,
    raw_html: str,
    cleaned_text: str,
    extraction_status: str,
    error_message: str,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO job_postings (
                session_id,
                url,
                title,
                raw_html,
                cleaned_text,
                extraction_status,
                error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                url,
                title,
                raw_html,
                cleaned_text,
                extraction_status,
                error_message,
            ),
        )
        conn.commit()


def insert_agent_context(session_id: int, context: dict[str, Any]) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO agent_contexts (session_id, context_json)
            VALUES (?, ?)
            """,
            (session_id, json.dumps(context, ensure_ascii=False)),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_agent_context(session_id: int) -> tuple[int, dict[str, Any]] | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT id, context_json
            FROM agent_contexts
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()
    if row is None:
        return None
    return int(row["id"]), json.loads(row["context_json"])


"""SQLite persistence for jobs, QA reports, and audit logs (design §2)."""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterator, Optional

from photoai.config import DB_PATH, ensure_workspace_dirs


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    ensure_workspace_dirs()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    # High-efficiency SQLite pragmas: WAL mode, normal sync, in-memory temp store
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA cache_size = -32000;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()



def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                recipe_id TEXT NOT NULL,
                status TEXT NOT NULL,
                params_json TEXT,
                result_path TEXT,
                warnings_json TEXT,
                created_at TEXT NOT NULL,
                finished_at TEXT
            );
            CREATE TABLE IF NOT EXISTS qa_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                passed INTEGER NOT NULL,
                attempt INTEGER NOT NULL,
                metrics_json TEXT NOT NULL,
                thresholds_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            );
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL,
                detail_json TEXT,
                created_at TEXT NOT NULL
            );
            """
        )


@dataclass
class JobRecord:
    id: str
    recipe_id: str
    status: str
    params: dict[str, Any]
    result_path: Optional[str] = None
    warnings: list[str] | None = None


class LocalWorkspaceManager:
    """SQLite-backed job history for the desktop app."""

    def __init__(self) -> None:
        init_db()

    def create_job(self, recipe_id: str, params: dict[str, Any] | None = None) -> str:
        job_id = _new_id("job")
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (id, recipe_id, status, params_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (job_id, recipe_id, "running", json.dumps(params or {}), _utc_now()),
            )
        return job_id

    def finish_job(
        self,
        job_id: str,
        *,
        status: str,
        result_path: str | None,
        warnings: list[str],
        qa_report: dict[str, Any],
    ) -> None:
        with connect() as conn:
            conn.execute(
                """
                UPDATE jobs SET status=?, result_path=?, warnings_json=?, finished_at=?
                WHERE id=?
                """,
                (
                    status,
                    result_path,
                    json.dumps(warnings),
                    _utc_now(),
                    job_id,
                ),
            )
            conn.execute(
                """
                INSERT INTO qa_reports (job_id, passed, attempt, metrics_json, thresholds_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    1 if qa_report.get("passed") else 0,
                    int(qa_report.get("attempt", 1)),
                    json.dumps(qa_report.get("metrics", {})),
                    json.dumps(qa_report.get("thresholds", {})),
                    _utc_now(),
                ),
            )

    def audit(self, event: str, detail: dict[str, Any] | None = None) -> None:
        with connect() as conn:
            conn.execute(
                "INSERT INTO audit_logs (event, detail_json, created_at) VALUES (?, ?, ?)",
                (event, json.dumps(detail or {}), _utc_now()),
            )

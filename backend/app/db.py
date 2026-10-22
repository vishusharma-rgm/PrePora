"""Small SQLite persistence layer for the first production slice.

The repository can move this interface to PostgreSQL later without changing
the API handlers. SQLite keeps local development and the demo deployment
zero-configuration while still giving every account durable, isolated data.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _database_path() -> Path:
    configured = os.getenv("DATABASE_URL", "sqlite:///./prepora.db")
    if configured.startswith("sqlite:///"):
        raw_path = configured.removeprefix("sqlite:///")
        path = Path(raw_path)
        return path if path.is_absolute() else ROOT / path
    raise RuntimeError("Only SQLite DATABASE_URL is supported by this local adapter.")


DB_PATH = _database_path()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                target_exam TEXT NOT NULL DEFAULT 'NEET-UG',
                target_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS progress (
                user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                questions_solved INTEGER NOT NULL DEFAULT 0,
                study_minutes INTEGER NOT NULL DEFAULT 0,
                accuracy REAL NOT NULL DEFAULT 0,
                streak INTEGER NOT NULL DEFAULT 0,
                sessions_completed INTEGER NOT NULL DEFAULT 0,
                weekly_activity TEXT NOT NULL DEFAULT '[0, 0, 0, 0, 0, 0, 0]',
                subject_accuracy TEXT NOT NULL DEFAULT '{"Physics": 0, "Chemistry": 0, "Biology": 0}',
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS test_attempts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                test_id TEXT NOT NULL,
                score REAL NOT NULL DEFAULT 0,
                correct INTEGER NOT NULL DEFAULT 0,
                incorrect INTEGER NOT NULL DEFAULT 0,
                unanswered INTEGER NOT NULL DEFAULT 0,
                duration_seconds INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS test_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                config TEXT NOT NULL,
                questions TEXT NOT NULL,
                answers TEXT NOT NULL DEFAULT '{}',
                marked TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'active',
                started_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                submitted_at TEXT,
                score REAL
            );

            CREATE TABLE IF NOT EXISTS study_items (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                kind TEXT NOT NULL,
                subject TEXT NOT NULL,
                class_level TEXT NOT NULL,
                chapter TEXT NOT NULL,
                title TEXT NOT NULL,
                reason TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'Medium',
                duration_minutes INTEGER NOT NULL DEFAULT 15,
                status TEXT NOT NULL DEFAULT 'open',
                due_date TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                details TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_test_attempts_user_created
                ON test_attempts(user_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_study_items_user_status
                ON study_items(user_id, status, due_date);
            """
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info(study_items)").fetchall()}
        if "details" not in columns:
            connection.execute("ALTER TABLE study_items ADD COLUMN details TEXT")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return f"pbkdf2_sha256$210000${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds_text, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        rounds = int(rounds_text)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), rounds)
        return secrets.compare_digest(digest.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


def _json(value: Any, fallback: Any) -> Any:
    try:
        return json.loads(value) if value else fallback
    except (TypeError, json.JSONDecodeError):
        return fallback


def _ensure_progress(connection: sqlite3.Connection, user_id: str) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO progress (user_id, updated_at)
        VALUES (?, ?)
        """,
        (user_id, now_iso()),
    )


def create_user(email: str, name: str, password: str) -> dict[str, Any]:
    user_id = str(uuid.uuid4())
    timestamp = now_iso()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO users (id, email, name, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, email, name, hash_password(password), timestamp, timestamp),
        )
        _ensure_progress(connection, user_id)
    return get_user(user_id)  # type: ignore[return-value]


def get_user(user_id: str) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def authenticate(email: str, password: str) -> dict[str, Any] | None:
    user = get_user_by_email(email)
    return user if user and verify_password(password, user["password_hash"]) else None


def update_user(user_id: str, values: dict[str, Any]) -> dict[str, Any] | None:
    allowed = {key: value for key, value in values.items() if key in {"name", "target_exam", "target_date"}}
    if not allowed:
        return get_user(user_id)
    allowed["updated_at"] = now_iso()
    assignments = ", ".join(f"{key} = ?" for key in allowed)
    with connect() as connection:
        connection.execute(
            f"UPDATE users SET {assignments} WHERE id = ?",
            (*allowed.values(), user_id),
        )
    return get_user(user_id)


def get_progress(user_id: str) -> dict[str, Any]:
    with connect() as connection:
        _ensure_progress(connection, user_id)
        row = connection.execute("SELECT * FROM progress WHERE user_id = ?", (user_id,)).fetchone()
    data = dict(row)
    data["weekly_activity"] = _json(data["weekly_activity"], [0] * 7)
    data["subject_accuracy"] = _json(data["subject_accuracy"], {"Physics": 0, "Chemistry": 0, "Biology": 0})
    return data


def record_progress_event(user_id: str, event_type: str, value: int, subject: str | None = None) -> dict[str, Any]:
    progress = get_progress(user_id)
    questions = int(progress["questions_solved"])
    minutes = int(progress["study_minutes"])
    sessions = int(progress["sessions_completed"])
    streak = int(progress["streak"])
    if event_type == "question_solved":
        questions += max(value, 0)
    elif event_type == "study_minutes":
        minutes += max(value, 0)
    elif event_type == "session_completed":
        sessions += max(value, 0)
        streak = max(streak, 1)
    else:
        raise ValueError("Unsupported progress event")

    weekly = list(progress["weekly_activity"])
    weekly[-1] = weekly[-1] + max(value, 0)
    subject_accuracy = dict(progress["subject_accuracy"])
    if subject and subject in subject_accuracy and event_type == "question_solved":
        subject_accuracy[subject] = min(100, round(float(subject_accuracy[subject]) + 1, 1))

    with connect() as connection:
        connection.execute(
            """
            UPDATE progress
            SET questions_solved = ?, study_minutes = ?, sessions_completed = ?,
                streak = ?, weekly_activity = ?, subject_accuracy = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (questions, minutes, sessions, streak, json.dumps(weekly), json.dumps(subject_accuracy), now_iso(), user_id),
        )
    return get_progress(user_id)


def create_attempt(user_id: str, values: dict[str, Any]) -> dict[str, Any]:
    attempt = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "test_id": values["test_id"],
        "score": values.get("score", 0),
        "correct": values.get("correct", 0),
        "incorrect": values.get("incorrect", 0),
        "unanswered": values.get("unanswered", 0),
        "duration_seconds": values.get("duration_seconds", 0),
        "created_at": now_iso(),
    }
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO test_attempts
            (id, user_id, test_id, score, correct, incorrect, unanswered, duration_seconds, created_at)
            VALUES (:id, :user_id, :test_id, :score, :correct, :incorrect, :unanswered, :duration_seconds, :created_at)
            """,
            attempt,
        )
    return attempt


def list_attempts(user_id: str, limit: int = 20) -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM test_attempts WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, min(max(limit, 1), 100)),
        ).fetchall()
    return [dict(row) for row in rows]


def create_session(user_id: str, config: dict[str, Any], questions: list[dict[str, Any]], duration_minutes: int) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc)
    expires_at = started_at.timestamp() + duration_minutes * 60
    session = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "config": json.dumps(config),
        "questions": json.dumps(questions),
        "answers": "{}",
        "marked": "[]",
        "status": "active",
        "started_at": started_at.isoformat(),
        "expires_at": datetime.fromtimestamp(expires_at, timezone.utc).isoformat(),
        "submitted_at": None,
        "score": None,
    }
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO test_sessions
            (id, user_id, config, questions, answers, marked, status, started_at, expires_at, submitted_at, score)
            VALUES (:id, :user_id, :config, :questions, :answers, :marked, :status, :started_at, :expires_at, :submitted_at, :score)
            """,
            session,
        )
    return _session_public(session, include_answers=False)


def _session_public(session: dict[str, Any], include_answers: bool = False) -> dict[str, Any]:
    data = dict(session)
    data["config"] = _json(data["config"], {})
    data["questions"] = _json(data["questions"], [])
    data["answers"] = _json(data["answers"], {})
    data["marked"] = _json(data["marked"], [])
    if not include_answers:
        data["questions"] = [
            {key: value for key, value in question.items() if key not in {"answer", "explanation"}}
            for question in data["questions"]
        ]
    data.pop("user_id", None)
    return data


def get_session(user_id: str, session_id: str) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute("SELECT * FROM test_sessions WHERE id = ? AND user_id = ?", (session_id, user_id)).fetchone()
    return _session_public(dict(row), include_answers=dict(row)["status"] != "active") if row else None


def save_session_answer(user_id: str, session_id: str, question_index: int, option: int | None, marked: bool) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute("SELECT * FROM test_sessions WHERE id = ? AND user_id = ?", (session_id, user_id)).fetchone()
        if not row or row["status"] != "active":
            return None
        answers = _json(row["answers"], {})
        marks = set(_json(row["marked"], []))
        if option is None:
            answers.pop(str(question_index), None)
        else:
            answers[str(question_index)] = option
        if marked:
            marks.add(question_index)
        else:
            marks.discard(question_index)
        connection.execute(
            "UPDATE test_sessions SET answers = ?, marked = ? WHERE id = ? AND user_id = ?",
            (json.dumps(answers), json.dumps(sorted(marks)), session_id, user_id),
        )
    return get_session(user_id, session_id)


def submit_session(user_id: str, session_id: str) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute("SELECT * FROM test_sessions WHERE id = ? AND user_id = ?", (session_id, user_id)).fetchone()
        if not row:
            return None
        session = dict(row)
        questions = _json(session["questions"], [])
        answers = _json(session["answers"], {})
        correct = sum(1 for index, question in enumerate(questions) if answers.get(str(index)) == question.get("answer"))
        incorrect = sum(1 for index, question in enumerate(questions) if str(index) in answers and answers.get(str(index)) != question.get("answer"))
        unanswered = max(0, len(questions) - correct - incorrect)
        score = round((correct / len(questions)) * 100, 2) if questions else 0
        timestamp = now_iso()
        connection.execute(
            "UPDATE test_sessions SET status = 'submitted', submitted_at = ?, score = ? WHERE id = ? AND user_id = ?",
            (timestamp, score, session_id, user_id),
        )
        result = dict(session)
        result.update({"status": "submitted", "submitted_at": timestamp, "score": score})
        result["correct"] = correct
        result["incorrect"] = incorrect
        result["unanswered"] = unanswered
    return _session_public(result, include_answers=True)


def create_study_item(user_id: str, values: dict[str, Any]) -> dict[str, Any]:
    item = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "kind": values.get("kind", "queue"),
        "subject": values["subject"],
        "class_level": values.get("class_level", "Mixed"),
        "chapter": values["chapter"],
        "title": values.get("title", f"Review {values['chapter']}"),
        "reason": values.get("reason", "Added to your study plan."),
        "priority": values.get("priority", "Medium"),
        "duration_minutes": values.get("duration_minutes", 15),
        "status": "open",
        "due_date": values.get("due_date"),
        "created_at": now_iso(),
        "completed_at": None,
        "details": json.dumps(values.get("details")) if values.get("details") is not None else None,
    }
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO study_items
            (id, user_id, kind, subject, class_level, chapter, title, reason, priority, duration_minutes, status, due_date, created_at, completed_at, details)
            VALUES (:id, :user_id, :kind, :subject, :class_level, :chapter, :title, :reason, :priority, :duration_minutes, :status, :due_date, :created_at, :completed_at, :details)
            """,
            item,
        )
    return _study_item_public(item)


def _study_item_public(item: dict[str, Any]) -> dict[str, Any]:
    public = {key: value for key, value in item.items() if key != "user_id"}
    public["details"] = _json(public.get("details"), None)
    return public


def list_study_items(user_id: str, kind: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    clauses = ["user_id = ?"]
    params: list[Any] = [user_id]
    if kind:
        clauses.append("kind = ?")
        params.append(kind)
    if status:
        clauses.append("status = ?")
        params.append(status)
    with connect() as connection:
        rows = connection.execute(
            f"SELECT * FROM study_items WHERE {' AND '.join(clauses)} ORDER BY CASE priority WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END, due_date IS NULL, due_date, created_at DESC",
            params,
        ).fetchall()
    return [_study_item_public(dict(row)) for row in rows]


def complete_study_item(user_id: str, item_id: str) -> dict[str, Any] | None:
    timestamp = now_iso()
    with connect() as connection:
        connection.execute(
            "UPDATE study_items SET status = 'completed', completed_at = ? WHERE id = ? AND user_id = ?",
            (timestamp, item_id, user_id),
        )
        row = connection.execute("SELECT * FROM study_items WHERE id = ? AND user_id = ?", (item_id, user_id)).fetchone()
    return _study_item_public(dict(row)) if row else None


def analytics(user_id: str) -> dict[str, Any]:
    with connect() as connection:
        attempts = [dict(row) for row in connection.execute("SELECT * FROM test_attempts WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", (user_id,)).fetchall()]
    progress = get_progress(user_id)
    scores = [float(item["score"]) for item in attempts]
    open_items = list_study_items(user_id, status="open")
    average = round(sum(scores) / len(scores), 1) if scores else 0
    recommendation = "Complete one focused test to create evidence for your analytics." if not scores else "Review your highest-priority queue item before starting another full test."
    if scores and progress["subject_accuracy"].get("Physics", 0) < max(progress["subject_accuracy"].get("Chemistry", 0), progress["subject_accuracy"].get("Biology", 0)):
        recommendation = "Physics is your current opportunity: revise one formula set, then retry a short numerical set."
    return {"attempt_count": len(attempts), "average_score": average, "best_score": max(scores) if scores else 0, "recent_scores": list(reversed(scores[:8])), "open_items": len(open_items), "subject_accuracy": progress["subject_accuracy"], "recommendation": recommendation}


init_db()

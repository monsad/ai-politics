"""SQLite schema + sync write helpers for Phase 3 sessions (INFRA-05)."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_DB_PATH = Path("sessions.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    topic       TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    status      TEXT DEFAULT 'running',
    raw_output  TEXT,
    vote_result TEXT,
    exit_code   INTEGER
);

CREATE TABLE IF NOT EXISTS utterances (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(id),
    seq         INTEGER NOT NULL,
    speaker     TEXT NOT NULL,
    phase       TEXT NOT NULL,
    content     TEXT NOT NULL,
    node_ids    TEXT,
    UNIQUE(session_id, seq)
);

CREATE TABLE IF NOT EXISTS votes (
    session_id  TEXT NOT NULL REFERENCES sessions(id),
    party       TEXT NOT NULL,
    vote        TEXT NOT NULL,
    seats       INTEGER NOT NULL,
    PRIMARY KEY (session_id, party)
);

CREATE TABLE IF NOT EXISTS bill_drafts (
    session_id  TEXT PRIMARY KEY REFERENCES sessions(id),
    title       TEXT,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
"""

_ALLOWED_UPDATE_COLUMNS = {"status", "vote_result", "raw_output", "exit_code", "finished_at"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect(db_path: Path | str) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Create schema and enable WAL. Idempotent."""
    con = _connect(db_path)
    try:
        con.executescript(SCHEMA_SQL)
        con.commit()
    finally:
        con.close()


def insert_session(db_path: Path | str, hermes_session_id: str, topic: str) -> str:
    """Insert a new session row, return hermes_session_id."""
    con = _connect(db_path)
    try:
        con.execute(
            "INSERT INTO sessions (id, topic, started_at, status) VALUES (?, ?, ?, 'running')",
            (hermes_session_id, topic, _now_iso()),
        )
        con.commit()
    finally:
        con.close()
    return hermes_session_id


def update_session(db_path: Path | str, session_id: str, **fields) -> None:
    """Update allowed columns on sessions row. Auto-sets finished_at on terminal status."""
    unknown = set(fields) - _ALLOWED_UPDATE_COLUMNS
    if unknown:
        raise ValueError(f"Unknown columns for sessions update: {sorted(unknown)}")
    if not fields:
        return
    if "status" in fields and fields["status"] in {"complete", "error"} and "finished_at" not in fields:
        fields["finished_at"] = _now_iso()
    assignments = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [session_id]
    con = _connect(db_path)
    try:
        con.execute(f"UPDATE sessions SET {assignments} WHERE id = ?", values)
        con.commit()
    finally:
        con.close()


def insert_utterance(
    db_path: Path | str,
    session_id: str,
    seq: int,
    speaker: str,
    phase: str,
    content: str,
    node_ids: Iterable[str] | None = None,
) -> None:
    """Insert a transcript utterance. node_ids is serialised as JSON."""
    node_ids_json = json.dumps(list(node_ids or []))
    con = _connect(db_path)
    try:
        con.execute(
            "INSERT INTO utterances (session_id, seq, speaker, phase, content, node_ids) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, seq, speaker, phase, content, node_ids_json),
        )
        con.commit()
    finally:
        con.close()


def insert_vote(
    db_path: Path | str,
    session_id: str,
    party: str,
    vote: str,
    seats: int,
) -> None:
    """Insert or replace a party vote. vote must be FOR | AGAINST | ABSTAIN."""
    if vote not in {"FOR", "AGAINST", "ABSTAIN"}:
        raise ValueError(f"Invalid vote value: {vote!r}")
    con = _connect(db_path)
    try:
        con.execute(
            "INSERT OR REPLACE INTO votes (session_id, party, vote, seats) VALUES (?, ?, ?, ?)",
            (session_id, party, vote, seats),
        )
        con.commit()
    finally:
        con.close()


def insert_bill_draft(
    db_path: Path | str,
    session_id: str,
    title: str | None,
    content: str,
) -> None:
    """Insert or replace a bill draft for the session."""
    con = _connect(db_path)
    try:
        con.execute(
            "INSERT OR REPLACE INTO bill_drafts (session_id, title, content, created_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, title, content, _now_iso()),
        )
        con.commit()
    finally:
        con.close()

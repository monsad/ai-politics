"""Subprocess Hermes launcher + stdout reader + SQLite writer. Wave 2 Plan 04 fills this in."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class SessionResult:
    session_id: str | None
    stdout: str
    stderr: str
    returncode: int

def run_session(topic: str, *, db_path: str | None = None) -> SessionResult:
    """Run a full parliament session via subprocess hermes. Implemented in Plan 04."""
    raise NotImplementedError("Implemented in Phase 3 Plan 04")

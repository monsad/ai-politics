"""SQLite schema + helpers for sessions/utterances/votes/bill_drafts. Wave 1 Plan 02 fills this in."""
from __future__ import annotations
from pathlib import Path

DEFAULT_DB_PATH = Path("sessions.db")

def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Create schema and enable WAL. Implemented in Plan 02."""
    raise NotImplementedError("Implemented in Phase 3 Plan 02")

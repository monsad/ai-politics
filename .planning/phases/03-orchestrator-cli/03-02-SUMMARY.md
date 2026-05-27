---
phase: 03-orchestrator-cli
plan: "02"
subsystem: db
tags: [sqlite, schema, wal, infra]
requirements: [INFRA-05]

dependency_graph:
  requires: ["03-orchestrator-cli/01"]
  provides: ["parliament.db — init_db, insert_session, update_session, insert_utterance, insert_vote, insert_bill_draft"]
  affects: ["03-orchestrator-cli/03", "03-orchestrator-cli/04", "03-orchestrator-cli/05"]

tech_stack:
  added: []
  patterns:
    - "SQLite WAL mode via PRAGMA journal_mode=WAL in _connect helper (every connection enables it)"
    - "Connection-per-call pattern: open → operate → close in try/finally; no shared state"
    - "Column whitelist (_ALLOWED_UPDATE_COLUMNS) for update_session prevents injection via kwarg keys"
    - "node_ids serialised as JSON string; deserialise at read time"

key_files:
  created: []
  modified:
    - parliament/db.py
    - tests/test_phase3_acceptance.py

decisions:
  - "INSERT OR REPLACE used for votes and bill_drafts (idempotent upsert semantics matching contest scope)"
  - "update_session auto-sets finished_at when status transitions to complete or error"
  - "f-string used only for UPDATE SET clause built from _ALLOWED_UPDATE_COLUMNS keys — no user data enters the template"

metrics:
  duration_seconds: 88
  completed_date: "2026-05-27T07:16:48Z"
  tasks_completed: 1
  tasks_total: 1
  files_modified: 2
---

# Phase 03 Plan 02: SQLite Schema and Write Helpers Summary

**One-liner:** WAL-mode SQLite schema with four tables and parameterised sync write helpers for session transcript storage.

## What Was Built

Replaced the `parliament/db.py` stub with a complete implementation:

- `init_db(path)` — creates schema via `executescript(SCHEMA_SQL)`, enables WAL, idempotent
- `insert_session` — inserts with ISO-8601 `started_at`, returns hermes_session_id
- `update_session` — column-whitelisted UPDATE, auto-sets `finished_at` on terminal status
- `insert_utterance` — stores node_ids as JSON array
- `insert_vote` — validates vote values (FOR/AGAINST/ABSTAIN), uses INSERT OR REPLACE
- `insert_bill_draft` — INSERT OR REPLACE with `created_at` timestamp

Removed `pytest.skip` from `test_db_schema` and replaced with a full round-trip test covering WAL verification, table existence, all four insert helpers, update_session, and data integrity assertions.

## Verification Results

```
pytest tests/test_phase3_acceptance.py::test_db_schema -x -v  →  1 passed
grep PRAGMA journal_mode=WAL parliament/db.py                 →  1 match
grep executescript(SCHEMA_SQL) parliament/db.py               →  1 match
grep "VALUES (?, ?, ?" parliament/db.py                       →  4 matches (>= 3 required)
python -c "from parliament.db import ..."                     →  ok
wc -l parliament/db.py                                        →  168 lines (>= 80 required)
```

## Commits

| Hash | Message |
|------|---------|
| 432669c | feat(03-02): implement SQLite schema, WAL mode, and write helpers (INFRA-05) |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all helpers are fully implemented and tested.

## Threat Flags

None — no new network endpoints, auth paths, or file access patterns introduced beyond the sqlite3 file at DEFAULT_DB_PATH (already in threat model as T-3-02-04 accepted).

## Self-Check: PASSED

- parliament/db.py exists: FOUND
- tests/test_phase3_acceptance.py exists: FOUND
- Commit 432669c exists: FOUND (verified via git rev-parse)

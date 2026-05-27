---
phase: 03-orchestrator-cli
plan: "01"
subsystem: scaffold
tags: [setup, cli, entrypoint, stubs, testing]
dependency_graph:
  requires: []
  provides: [parliament-cli-entrypoint, phase3-stub-modules, phase3-acceptance-tests]
  affects: [03-02, 03-03, 03-04, 03-05]
tech_stack:
  added: [sse-starlette>=3.0]
  patterns: [typer-app-skeleton, notimplementederror-stubs, pytest-skip-progressive]
key_files:
  created:
    - parliament/cli.py
    - parliament/db.py
    - parliament/session.py
    - parliament/api.py
    - parliament/agent_factory.py
    - parliament/citation_validator.py
    - tests/test_phase3_acceptance.py
  modified:
    - pyproject.toml
decisions:
  - "Fixed python-dotenv pin from 1.2.2 to 1.2.1 (hermes-agent==0.14.0 requires 1.2.1)"
  - "Created .venv with Python 3.11 via uv venv (uv manages the project install)"
  - "markers section added to [tool.pytest.ini_options] as part of Task 1 (not Task 3) to keep pyproject.toml changes atomic"
metrics:
  duration_seconds: 228
  completed_date: "2026-05-27T07:12:49Z"
  tasks_completed: 3
  tasks_total: 3
  files_created: 7
  files_modified: 1
---

# Phase 3 Plan 01: Wave 0 Scaffold — Entry Point, Stub Modules, Acceptance Tests

**One-liner:** Fixed `parliament` CLI entry point in pyproject.toml, created six importable Phase 3 stub modules, and scaffolded 13-test acceptance file with 2 passing and 11 skipped pending Wave 1-3 implementations.

## What Was Built

Wave 0 establishes the scaffold every later Phase 3 plan depends on:

1. **Entry point fixed** — `pyproject.toml` now registers `parliament = "parliament.cli:app"` (was `hermes-parliament`). Running `pip install -e ".[dev]"` in the `.venv` makes `which parliament` resolve to the venv bin.

2. **Six stub modules created** — each imports cleanly and raises `NotImplementedError` only when called (never on import), so `pytest --collect-only` succeeds without triggering stubs:
   - `parliament/cli.py` — typer app skeleton, `DISCLAIMER` constant, `_placeholder` command
   - `parliament/db.py` — `init_db()` stub, `DEFAULT_DB_PATH`
   - `parliament/session.py` — `SessionResult` dataclass, `run_session()` stub
   - `parliament/api.py` — FastAPI skeleton with `/health` endpoint (no stubs needed here)
   - `parliament/agent_factory.py` — `build_hermes_cmd()` stub, `ModelTier` type alias
   - `parliament/citation_validator.py` — `validate_citations()` async stub

3. **Acceptance test file created** — `tests/test_phase3_acceptance.py` with 13 tests: `test_entry_point` and `test_disclaimer_constant` pass immediately; 11 tests skip with `pytest.skip("Plan NN: ...")` until their implementing plan arrives.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed python-dotenv version conflict**
- **Found during:** Task 1 (pip install)
- **Issue:** `pyproject.toml` pinned `python-dotenv==1.2.2` but `hermes-agent==0.14.0` requires `python-dotenv==1.2.1`, making dependency resolution impossible
- **Fix:** Changed pin to `python-dotenv==1.2.1`
- **Files modified:** `pyproject.toml`
- **Commit:** cb3a66b

**2. [Rule 3 - Blocking] Created .venv with Python 3.11**
- **Found during:** Task 1 (pip install attempt)
- **Issue:** No virtual environment existed; uv refused to install into the managed system Python; the plan assumed `pip install -e ".[dev]"` would work in an existing venv
- **Fix:** Created `.venv` with `uv venv .venv --python 3.11` before running install
- **Commit:** (part of cb3a66b — venv created as prerequisite)

## Verification Results

All wave 0 criteria passed:

```
which parliament     → .venv/bin/parliament  ✓
python -c "import parliament.cli, parliament.db, parliament.session,
           parliament.api, parliament.agent_factory,
           parliament.citation_validator; print('ok')"  → ok  ✓
pytest tests/test_phase3_acceptance.py -m "not slow"
  → 2 passed, 7 skipped, 4 deselected  ✓ (exit 0)
pytest --collect-only  → 13 collected  ✓ (≥ 12 required)
grep 'sse-starlette'   → matches in pyproject.toml  ✓
grep '^parliament ='   → parliament = "parliament.cli:app"  ✓
grep 'hermes-parliament' pyproject.toml → no match  ✓
```

## Commits

| Task | Commit | Message |
|------|--------|---------|
| Task 1 | cb3a66b | chore(03-01): fix entry point, add sse-starlette, fix python-dotenv pin |
| Task 2 | f55e503 | feat(03-01): create Phase 3 stub modules |
| Task 3 | 32d6bb4 | test(03-01): create Phase 3 acceptance test stubs |

## Known Stubs

The following stubs are intentional and tracked for later plans:

| File | Symbol | Reason | Resolving Plan |
|------|--------|--------|----------------|
| parliament/db.py | `init_db()` | Wave 1 DB schema work | Plan 02 |
| parliament/session.py | `run_session()` | Wave 2 subprocess launcher | Plan 04 |
| parliament/agent_factory.py | `build_hermes_cmd()` | Wave 1 hermes integration | Plan 03 |
| parliament/citation_validator.py | `validate_citations()` | Wave 1 citation check | Plan 03 |
| parliament/cli.py | `_placeholder()` | Wave 2 full CLI command | Plan 04 |

These stubs do NOT prevent this plan's goal (scaffold + test collection). They are the intended outcome.

## Threat Flags

None. Wave 0 is config + scaffold only; no network endpoints, auth paths, or secrets touched.

## Self-Check: PASSED

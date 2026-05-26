---
phase: "01"
plan: "01"
subsystem: scaffold
tags: [license, pyproject, makefile, package-skeleton, token-budget, tdd]
dependency_graph:
  requires: []
  provides:
    - MIT LICENSE at repo root (INFRA-01)
    - pyproject.toml with hermes-agent==0.14.0 and Python 3.11 pins (INFRA-02)
    - .env.example documenting PAGEINDEX_API_KEY
    - .gitignore excluding .env
    - Makefile with setup/smoke/validate-skills/demo/clean targets
    - parliament package importable with TokenBudget interface stub
    - tests/test_token_budget.py (6 passing tests)
  affects:
    - All subsequent plans (can now uv pip install -e ".[dev]" and run make smoke)
    - Plan 01-02 (skills-ref tooling uses package.json from this plan)
    - Plan 01-03 (hermes gate tests use parliament package from this plan)
tech_stack:
  added:
    - hatchling (build backend)
    - pytest==8.3.4 + pytest-asyncio==0.24.0 (test framework)
    - ruff==0.8.4 (linter)
    - pre-commit==4.0.1 (hook framework)
  patterns:
    - PEP 621 pyproject.toml for all Python metadata
    - TDD for interface stubs (RED commit then GREEN commit)
    - Exact version pinning for all transitive hermes-agent deps
key_files:
  created:
    - LICENSE
    - .gitignore
    - .env.example
    - README.md
    - package.json
    - pyproject.toml
    - Makefile
    - parliament/__init__.py
    - parliament/second_brain/__init__.py
    - parliament/guards.py
    - tests/__init__.py
    - tests/test_token_budget.py
    - skills/.gitkeep
  modified: []
decisions:
  - "TokenBudget implemented as dataclass with raise-on-exceed semantics (fail loud) per plan spec"
  - "Python 3.11 exact (not 3.12/3.13) per hermes-agent compatibility constraint"
  - "No hermes-agent[all] extras — base package only as mandated by CLAUDE.md"
  - "mcp==1.27.1 included in base deps for Phase 3 Python-side MCP client"
metrics:
  duration_minutes: 15
  completed_date: "2026-05-26"
  tasks_completed: 3
  files_created: 13
---

# Phase 1 Plan 01: Repo Scaffold Summary

MIT license + pyproject.toml + Makefile + parliament package skeleton + TokenBudget stub (dataclass, raise-on-exceed) wired to 6 passing unit tests.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | LICENSE, .gitignore, .env.example, README.md, package.json | d203efe | LICENSE, .gitignore, .env.example, README.md, package.json |
| 2 | pyproject.toml with locked pins | a218bbf | pyproject.toml |
| 3 (RED) | Failing TokenBudget tests | 10fb334 | tests/__init__.py, tests/test_token_budget.py |
| 3 (GREEN) | parliament skeleton + TokenBudget + Makefile | 0d4244e | Makefile, parliament/__init__.py, parliament/guards.py, parliament/second_brain/__init__.py, skills/.gitkeep |

## Decisions Made

1. **TokenBudget as dataclass with raise semantics** — Plan specified "raise for fail-loud semantics". Implemented as `@dataclass` with `_total: int = 0` field. `add()` raises `TokenBudgetExceeded` when `_total + tokens > max_tokens`.

2. **Python 3.11 exact (`>=3.11,<3.12`)** — Enforced via pyproject.toml `requires-python`. hermes-agent 0.14.0 tested on 3.11, surya-ocr lacks 3.13 wheels on all platforms.

3. **No `hermes-agent[all]`** — Only base `hermes-agent==0.14.0`. The `[all]` extras include voice/TTS/browser/modal/daytona which are not needed and would bloat the install. Mandated by CLAUDE.md.

4. **mcp==1.27.1 in base dependencies** — Added now for Phase 3 fail-fast conflict detection rather than discovering conflicts when Phase 3 begins.

5. **Makefile smoke target runs each gate test file separately** — One pytest invocation per gate file so individual gate failures are immediately identifiable without running the full suite.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

| Stub | File | Line | Reason |
|------|------|------|--------|
| `TokenBudget` (full production enforcement) | parliament/guards.py | entire file | Phase 1 establishes interface only; Phase 3 wires into LLM call path per CONTEXT.md locked decision |
| `hermes-parliament` CLI entry point | pyproject.toml | `[project.scripts]` | Entry point reserved but `parliament.cli:app` not yet implemented; Phase 3 delivers the CLI |

## Threat Flags

No new threat surface introduced beyond what the plan's threat model covers. `.env` is gitignored (T-01-01 mitigated). Dependency pins are exact (T-01-03 mitigated). LICENSE committed (T-01-04 mitigated).

## Self-Check: PASSED

All created files verified to exist and pass acceptance criteria:
- `LICENSE`: MIT License text present, "Permission is hereby granted" present
- `.gitignore`: `.env` as exact line (not `.env.example`), `node_modules/`, `.venv/` present
- `.env.example`: `PAGEINDEX_API_KEY` documented
- `package.json`: valid JSON, `skills-ref@0.1.5` pinned, `engines.node >= 20.8.1`
- `README.md`: "Virtual Parliament" heading, `make setup` in quickstart
- `pyproject.toml`: valid TOML, all required pins present, no `hermes-agent[all]`
- `Makefile`: `setup:` and `smoke:` targets, TAB-indented, all 7 gate tests listed
- `parliament/guards.py`: `TokenBudget` and `TokenBudgetExceeded` importable
- `tests/test_token_budget.py`: 6 tests all pass (`PYTHONPATH=. python3 -m pytest tests/test_token_budget.py -x`)
- Commits exist: d203efe, a218bbf, 10fb334, 0d4244e

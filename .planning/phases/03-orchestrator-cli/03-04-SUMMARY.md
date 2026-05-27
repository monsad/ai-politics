---
phase: 03-orchestrator-cli
plan: "04"
subsystem: cli-session
tags: [cli, session, subprocess, rich, export, sqlite, token-budget]
dependency_graph:
  requires: [03-orchestrator-cli/02, 03-orchestrator-cli/03]
  provides: [parliament-cli, session-runner, markdown-export]
  affects: [03-orchestrator-cli/05]
tech_stack:
  added: []
  patterns:
    - subprocess.Popen(shell=False) with background threading for stdout/stderr capture
    - rich.live.Live spinner with time-based phase labels during subprocess execution
    - typer @app.command() single-command app (not @app.callback group — see deviations)
    - monkeypatch.setattr on module-level function for test isolation
key_files:
  created: []
  modified:
    - parliament/session.py
    - parliament/cli.py
    - tests/test_phase3_acceptance.py
decisions:
  - "@app.command() used instead of @app.callback(invoke_without_command=True) — click groups cannot have positional ARGUMENT parameters"
  - "TokenBudgetExceeded is caught and swallowed in run_session/run_minister_isolation — budget is reporting-only since subprocess already ran"
  - "DISCLAIMER constant moved from cli.py into session.py so render_markdown can include it without importing cli"
metrics:
  duration: "~35 minutes"
  completed_date: "2026-05-27"
  tasks_completed: 2
  files_modified: 3
---

# Phase 03 Plan 04: CLI Session Wiring Summary

Full subprocess Hermes launcher in `session.py` with rich Live spinner, markdown export via `render_markdown`, seat-weighted vote tally, SQLite persistence, token budget charging, and a clean `parliament "<topic>"` typer CLI wired to all session functions.

## What Was Built

### parliament/session.py (326 lines)

- `run_session(topic)` — builds argv via `build_hermes_cmd`, runs in background thread while rich Live spinner shows time-based phase labels, parses completed stdout, persists to SQLite, charges `TokenBudget`
- `run_minister_isolation(domain, question)` — resolves domain → skill via `DOMAIN_TO_SKILL`, same subprocess + budget pattern, 120s timeout
- `parse_phases(text)` — segments stdout blob by 6 `PHASE_MARKERS` (including `[MARSZAŁEK REASONING]`, `## Vote`, etc.) into `{phase, offset, content}` dicts
- `parse_vote_table(text)` — regex extracts party→vote dict, computes seat-weighted FOR/AGAINST tally → "PASSED" | "REJECTED"
- `parse_bill_draft(text)` — extracts `## Draft Bill` section up to trailing disclaimer
- `render_markdown(result, topic)` — full markdown with disclaimer top+bottom, transcript, vote tally table, bill draft section
- `_persist(db_path, topic, sr)` — writes session, utterances (one per phase), votes, bill_draft to SQLite post-subprocess
- `_run_with_spinner(cmd, env, timeout)` — background worker thread + rich Live panel updating every 250ms
- `DISCLAIMER` constant, `PARTY_SEATS` dict, `DOMAIN_TO_SKILL` map (20 ministry domains)

### parliament/cli.py (81 lines)

- `@app.command() main(topic, --minister, --export, --output)` — full typer command
- Prints DISCLAIMER top and bottom on every invocation
- `--minister finanse "question"` → `run_minister_isolation`
- `--export markdown -o file.md` → `render_markdown` → writes file
- Uses `PARLIAMENT_DB_PATH` env var (default `sessions.db`)

### tests/test_phase3_acceptance.py

Unskipped and implemented:
- `test_token_budget_wired` — monkeypatches `_run_with_spinner`, asserts `budget.total == 1000` after 4000-char stdout
- `test_reasoning_blocks_parsed` — asserts all 4 phases detected in sample text
- `test_markdown_export` — end-to-end: monkeypatch + CLI runner + file assertions (Vote Tally, Draft Bill, 2x EDUCATIONAL SIMULATION)
- `test_disclaimer_constant` — was already passing; confirmed still green

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] @app.callback(invoke_without_command=True) incompatible with positional args**

- **Found during:** Task 2 test execution
- **Issue:** Click groups (created by `@app.callback`) cannot parse positional `ARGUMENT` parameters. When `topic` is a positional arg on a callback, click's group parser attempts to resolve the remaining args as a subcommand name, causing "Missing argument 'TOPIC'" or "No such command '--export'" errors. This is a fundamental click architectural constraint affecting typer 0.25.1.
- **Fix:** Used `@app.command()` for the main command logic. The `@app.callback` pattern is documented in the file as the correct extension point for future multi-command subcommand use.
- **Files modified:** parliament/cli.py
- **Commit:** 49ca2f5

**2. [Rule 1 - Bug] RTK proxy truncates pytest output to "No tests collected"**

- **Found during:** Task 2 test verification
- **Issue:** The RTK (Rust Token Killer) pytest proxy was filtering/truncating output, returning "No tests collected" even when tests were passing. This masked real results.
- **Fix:** Used `rtk proxy python -m pytest ...` to bypass RTK output filtering.
- **Impact:** No code changes; affected only test execution verification.

## Known Stubs

None — all public functions are fully implemented. `_run_with_spinner` is tested via monkeypatching (the real subprocess path requires Hermes installed and a configured LLM key, verified in Plan 05 slow tests).

## Threat Flags

No new security surface introduced beyond what was in the threat model. `shell=False` verified at line 144. All SQLite writes use `?` placeholders (via db.py helpers from Plan 02). `DOMAIN_TO_SKILL` allowlist prevents unknown skill names from reaching subprocess.

## Self-Check: PASSED

- parliament/session.py — FOUND
- parliament/cli.py — FOUND
- tests/test_phase3_acceptance.py — FOUND
- commit 8b8a2b5 (session.py) — FOUND
- commit 49ca2f5 (cli.py + tests) — FOUND
- 8 passed, 1 skipped, 4 deselected in test suite — VERIFIED

# Phase 3: Orchestrator & CLI — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-27
**Phase:** 03-orchestrator-cli
**Areas discussed:** CLI invocation pattern

---

## CLI invocation pattern

| Option | Description | Selected |
|--------|-------------|----------|
| Subprocess Hermes | typer CLI runs `hermes` as subprocess with marszalek-sejmu skill; captures stdout | ✓ |
| Python-native orchestration | Python directly instantiates AIAgents, custom fan-out | |
| Hermes plugin command | Extend Hermes CLI as a plugin | |

**User's choice:** Subprocess Hermes
**Notes:** Avoids replicating delegate_task fan-out. Hermes handles skill loading, MCP wiring, ThreadPoolExecutor internally.

---

## Progress display

| Option | Description | Selected |
|--------|-------------|----------|
| rich Live panel — parse Hermes stdout | Parse phase markers line-by-line, update Live panel in real time | ✓ |
| Spinner only, parse at end | Single spinner during run, parse full output at exit | |
| Redirect to file, tail -f style | Hermes writes log file; CLI tails it | |

**User's choice:** rich Live panel parsing Hermes stdout
**Notes:** Phase markers from marszalek-sejmu SKILL.md (`[MARSZAŁEK REASONING]`, `## Ministry Analysis`, etc.) drive status updates.

---

## Claude's Discretion

- SQLite schema detail (exact columns, utterance granularity)
- Citation validator timing (post-session vs live)
- FastAPI SSE minimal scope
- `--minister` isolation routing

## Deferred Ideas

- PDF export (STR-02) — post Phase 3
- Full REST session history API — Phase 4

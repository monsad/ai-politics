---
phase: 3
slug: orchestrator-cli
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-27
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `pytest tests/test_phase3_acceptance.py -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~120 seconds (subprocess Hermes calls) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_phase3_acceptance.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 0 | CLI-01 | — | N/A | unit | `pytest tests/test_phase3_acceptance.py::test_cli_entry_point -q` | ❌ W0 | ⬜ pending |
| 3-01-02 | 01 | 1 | ORCH-01 | T-3-01 | subprocess stdin not exposed to user | integration | `pytest tests/test_phase3_acceptance.py::test_full_simulation -q` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 1 | INFRA-05 | — | WAL mode set | unit | `pytest tests/test_phase3_acceptance.py::test_sqlite_schema -q` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 1 | ORCH-09 | — | N/A | integration | `pytest tests/test_phase3_acceptance.py::test_citation_validator -q` | ❌ W0 | ⬜ pending |
| 3-04-01 | 04 | 1 | INFRA-04 | T-3-02 | SSE endpoint no auth bypass | integration | `pytest tests/test_phase3_acceptance.py::test_sse_endpoint -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase3_acceptance.py` — acceptance test stubs for all Phase 3 success criteria
- [ ] `tests/conftest.py` — update with Phase 3 fixtures (mock hermes subprocess, SQLite temp DB)

*Existing infrastructure (pytest, conftest.py) covers framework; only test file additions needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `rich` Live panel updates during simulation | CLI-03 | Cannot automate terminal rendering | Run `parliament "4-day work week"` in a real terminal, observe spinner/phase labels |
| Political coherence of vote result | ORCH-05 | LLM output, non-deterministic | Check vote table: Lewica supports, Konfederacja opposes "4-day work week" |
| Educational disclaimer visible in output | ETHICS-01 | Terminal rendering | Observe ⚠️ EDUCATIONAL SIMULATION at top and bottom of output |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

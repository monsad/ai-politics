---
phase: 03-orchestrator-cli
plan: 03
subsystem: infra
tags: [hermes, agent-factory, citation, pageindex, subprocess, regex]

requires:
  - phase: 03-orchestrator-cli/01
    provides: stub files for agent_factory.py and citation_validator.py

provides:
  - build_hermes_cmd: single source of truth for Hermes subprocess argv (INFRA-04)
  - build_hermes_env: subprocess env with YOLO mode + tier model override
  - extract_node_ids: regex scanner for two citation formats in transcript text
  - validate_citations: async PageIndex resolver returning {total, resolved, unresolvable}

affects:
  - 03-orchestrator-cli/04  # session.py consumes build_hermes_cmd + build_hermes_env
  - 03-orchestrator-cli/05  # E2E tests call extract_node_ids + validate_citations post-session

tech-stack:
  added: []
  patterns:
    - "Factory pattern: build_hermes_cmd is the single point of Hermes argv construction — never inlined elsewhere"
    - "Tier env var lookup: PARLIAMENT_MODEL_{TIER} -> HERMES_MODEL propagation for model cost control"
    - "Regex citation extraction: two patterns (_RE_NODE_ID, _RE_DOC_PAGE) covering both citation shapes"
    - "No-API-key fast path in validate_citations: returns error dict without attempting MCP connection"

key-files:
  created: []
  modified:
    - parliament/agent_factory.py
    - parliament/citation_validator.py
    - tests/test_phase3_acceptance.py

key-decisions:
  - "Skill name validation rejects / and whitespace before passing to hermes (T-3-03-02 path traversal mitigation)"
  - "validate_citations uses sequential awaits inside single MCP session (not asyncio.gather) — matches Hermes threading model"
  - "Empty PageIndex API key triggers fast path with error field; avoids MCP subprocess spawn on missing config"
  - "Citation token regex restricts doc_name to [A-Za-z0-9_-] and pages to digits (T-3-03-03 injection mitigation)"

patterns-established:
  - "Pattern: subprocess argv as list — topic is always a single argv element, never shell-interpolated"
  - "Pattern: dict.fromkeys() for de-duplication preserving first-seen order"

requirements-completed: [INFRA-04, ORCH-09]

duration: 15min
completed: 2026-05-27
---

# Phase 3 Plan 03: Agent Factory and Citation Validator Summary

**Hermes subprocess argv factory (INFRA-04) and PageIndex citation resolver (ORCH-09) implemented as auditable, injection-safe leaf modules consumed by session.py (Plan 04) and E2E tests (Plan 05)**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-05-27T07:06:00Z
- **Completed:** 2026-05-27T07:20:26Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `build_hermes_cmd` returns the verified Hermes argv list with `--accept-hooks --yolo` flags; topic always occupies a single argv element (shell injection impossible)
- `build_hermes_env` merges parent env with `HERMES_YOLO_MODE=1`, `HERMES_ACCEPT_HOOKS=1`, and optional per-tier `HERMES_MODEL` override via `PARLIAMENT_MODEL_{TIER}` env vars
- `extract_node_ids` scans transcripts for two citation shapes: bare `node_id: <token>` and `<doc>.pdf p.<N>` doc-page references; returns unique tokens in first-seen order
- `validate_citations` resolves each token against PageIndex via async MCP client; fast-paths on missing API key with structured error response
- Both acceptance tests (`test_agent_factory_cmd`, `test_citation_validator_smoke`) unskipped and passing

## Task Commits

1. **Task 1: Implement agent_factory.py** - `17007ef` (feat)
2. **Task 2: Implement citation_validator.py** - `c5df83f` (feat)

## Files Created/Modified

- `parliament/agent_factory.py` — Full INFRA-04 implementation: `build_hermes_cmd` + `build_hermes_env`
- `parliament/citation_validator.py` — Full ORCH-09 implementation: `extract_node_ids` + `validate_citations`
- `tests/test_phase3_acceptance.py` — `test_agent_factory_cmd` and `test_citation_validator_smoke` stubs replaced with real tests

## Decisions Made

- Skill name validation (rejects `/` and whitespace) added as Rule 2 auto-inclusion — matches T-3-03-02 threat mitigation and is a correctness requirement for subprocess safety
- `validate_citations` checks API key before importing `PageIndexClient` so the test suite can run without the MCP server installed
- Used `dict.fromkeys()` pattern for de-duplication to preserve first-seen citation order (affects citation reporting readability)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - `pytest -q` output format showed "No tests collected" for passing tests (cosmetic only; `-v` confirmed passes). No code issues.

## Known Stubs

None - both modules are fully implemented. `validate_citations` requires a live `PAGEINDEX_API_KEY` for the resolved > 0 path, but the fast-path and all test coverage are complete without it.

## Threat Flags

No new security surface introduced beyond what is documented in the plan's threat model (T-3-03-01 through T-3-03-05).

## Next Phase Readiness

- Plan 04 (`session.py`) can import `build_hermes_cmd` and `build_hermes_env` directly — no further changes needed
- Plan 05 E2E tests can call `extract_node_ids(transcript_text)` followed by `await validate_citations(tokens)` against a live session output
- `PARLIAMENT_MODEL_ORCHESTRATOR`, `PARLIAMENT_MODEL_MINISTRY`, `PARLIAMENT_MODEL_PARTY` env vars are optional — system works without them (uses Hermes default model)

## Self-Check: PASSED

- `parliament/agent_factory.py` — present
- `parliament/citation_validator.py` — present
- `tests/test_phase3_acceptance.py` — updated
- Commit `17007ef` — present
- Commit `c5df83f` — present

---
*Phase: 03-orchestrator-cli*
*Completed: 2026-05-27*

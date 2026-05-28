---
phase: quick-260528-ea6
plan: "01"
subsystem: web-research
tags: [web-search, agent-skill, ddgs, hermes, toolsets]
dependency_graph:
  requires: [parliament/agent_factory.py, hermes-agent]
  provides: [skills/web-research/SKILL.md, ddgs backend, toolsets parameter]
  affects: [parliament/session.py (future callers of build_hermes_cmd)]
tech_stack:
  added: [ddgs]
  patterns: [TDD red-green, Agent Skills spec frontmatter, Hermes -t toolsets flag]
key_files:
  created:
    - skills/web-research/SKILL.md
    - tests/test_web_search_agent.py
  modified:
    - parliament/agent_factory.py
    - pyproject.toml
    - .env.example
decisions:
  - "Use ddgs (DuckDuckGo, keyless) as web.search_backend — fits $5 VPS budget and zero-secret clean clone requirement"
  - "Toolsets appended after query, before base flags (-Q --accept-hooks --yolo) in build_hermes_cmd argv"
  - "Multiple toolsets joined as comma-separated value per Hermes -t flag convention"
metrics:
  duration_minutes: 15
  completed_date: "2026-05-28"
  tasks_completed: 3
  files_changed: 5
---

# Quick Task 260528-ea6: Install Agent CLI and Build Web Search Agent Summary

**One-liner:** Keyless DuckDuckGo web-search backend wired to Hermes `web` toolset via ddgs, with a spec-valid `web-research` skill and backward-compatible `toolsets` parameter in `build_hermes_cmd`.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Install keyless web-search backend and wire Hermes config | c313f53 | pyproject.toml, .env.example |
| 2 | Create the web-research agent skill | e05862b | skills/web-research/SKILL.md |
| 3 (RED) | Add failing tests for toolset wiring | d2636d4 | tests/test_web_search_agent.py |
| 3 (GREEN) | Implement toolsets parameter in agent_factory | fc257dc | parliament/agent_factory.py |

## What Was Built

### Task 1 — Keyless search backend
- Added `ddgs` to `pyproject.toml` dependencies and installed into the active Python 3.11 environment.
- Configured `~/.hermes/config.yaml`: `web.backend = ddgs`, `web.search_backend = ddgs` via `hermes config set`.
- Documented optional API key upgrades (Brave, Tavily, Exa) in `.env.example` as non-required OPTIONAL block.

### Task 2 — web-research agent skill
- Created `skills/web-research/SKILL.md` with frontmatter matching the Agent Skills spec and existing project conventions.
- Instructs the agent to use `web_search` (and `web_extract` for full-page reads), cite every claim with a source URL, and stay non-partisan.
- Includes `## Output Constraints` section: no real MP names, no hate speech, source URL per claim, simulation disclaimer.
- Passes `skills-ref@0.1.5 validate` with exit 0.

### Task 3 — toolsets parameter (TDD)
- Followed TDD: wrote 13 failing tests (RED), then implemented the feature (GREEN), all 13 pass.
- Extended `build_hermes_cmd` with `toolsets: list[str] | None = None` keyword-only parameter.
- When `toolsets` is non-empty: validates each id (non-empty, no whitespace/slash), appends `-t <comma-joined>` to argv.
- When `toolsets` is None or `[]`: no `-t` flag — fully backward compatible with all existing `session.py` callers.
- Test coverage: backward compat, single toolset, multi-toolset comma-join, empty list, invalid ids, base flag preservation, SKILL.md frontmatter parsing, body assertions.

## Deviations from Plan

None — plan executed exactly as written.

Note: `skills-ref@0.1.5` required global npm install (`npm install -g skills-ref@0.1.5`) because `npx -y skills-ref@0.1.5` failed on this system's npm version. The validate command itself works correctly; the deviation is in invocation method only.

## Known Stubs

None. The web-research skill is complete and wired to the ddgs backend. Downstream integration (wiring web-research into Marszałek `delegate_task` flow) is explicitly deferred per plan scope — not a stub.

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema changes introduced. The `ddgs` package makes outbound-only HTTP requests to DuckDuckGo — no server surface added.

## Self-Check: PASSED

- `skills/web-research/SKILL.md` exists: FOUND
- `tests/test_web_search_agent.py` exists: FOUND
- `parliament/agent_factory.py` modified: FOUND (toolsets parameter present)
- Commit c313f53 (ddgs backend): FOUND
- Commit e05862b (web-research skill): FOUND
- Commit d2636d4 (failing tests): FOUND
- Commit fc257dc (toolsets implementation): FOUND
- 13/13 non-slow tests pass: CONFIRMED

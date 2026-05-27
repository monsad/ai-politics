# Phase 3: Orchestrator & CLI — Context

**Gathered:** 2026-05-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Day 4 of the contest (2026-05-29). This phase wires the 25 SKILL.md agents into a live end-to-end CLI session:

- `parliament "<topic>"` (typer CLI) runs a full parliamentary simulation in ≤ 5 minutes
- `parliament --minister <domain> "<question>"` runs a single ministry in isolation
- `parliament ... --export markdown <file>` writes the transcript to disk
- `rich` progress display updates live as the session runs
- SQLite records session, utterances, votes, bill_draft for Phase 4 web streaming
- FastAPI SSE endpoint emits session events as newline-delimited JSON (consumed by Phase 4)
- Educational disclaimer on every CLI output surface (ETHICS-01)
- `citation_validator.py` reports 0 unresolvable node_ids per session

Phase 3 does NOT deliver:
- Next.js web UI (Phase 4)
- PDF export (stretch STR-02)
- Full Hermes long-term memory wiring (stretch STR-01)

</domain>

<decisions>
## Implementation Decisions

### D-01: CLI invocation pattern — subprocess Hermes

**Locked:** `parliament "<topic>"` is a Python typer CLI that launches Hermes as a subprocess.

```
parliament "4-day work week"
  └─ subprocess: hermes --skill marszalek-sejmu "<topic>"
      └─ Hermes AIAgent (marszalek-sejmu SKILL.md)
          ├─ delegate_task → ministry-finansow
          ├─ delegate_task → ministry-zdrowia (parallel via ThreadPoolExecutor)
          └─ party debate → vote → bill draft
```

**Why subprocess, not Python-native orchestration:**
- Hermes `delegate_task` is the only safe fan-out pattern (asyncio.gather over AIAgent instances deadlocks — CLAUDE.md anti-pattern)
- Hermes handles skill loading, MCP tool wiring, and ThreadPoolExecutor fan-out internally
- Python-native orchestration would require replicating all of this and bypass Hermes's tool registry

**CLI entry point:** Register in `pyproject.toml`:
```toml
[project.scripts]
parliament = "parliament.cli:app"
```

**Hermes invocation flag research needed:** Researcher must confirm the exact `hermes` CLI flag to load a specific skill and pass a topic string (e.g., `hermes --skill marszalek-sejmu "topic"` or equivalent).

### D-02: Progress display — rich Live panel parsing Hermes stdout

**Locked:** CLI reads Hermes subprocess stdout line-by-line. Known phase markers emitted by the marszalek-sejmu SKILL.md are used to update a `rich.live.Live` panel in real time.

Phase markers to detect from SKILL.md output:
- `[MARSZAŁEK REASONING]` → update status: "Classifying topic / selecting ministries"
- `## Ministry Analysis` → update status: "Consulting ministries (parallel)"
- `## Party Debate — First Reading` → update status: "First reading"
- `## Party Debate — Second Reading` → update status: "Second reading"
- `## Vote` → update status: "Voting"
- `## Draft Bill` → update status: "Drafting bill"

Simultaneously: accumulate full stdout into a buffer for SQLite write + markdown export at session end.

### Claude's Discretion (planner decides)

- **SQLite schema detail:** INFRA-05 requires `sessions`, `utterances`, `votes`, `bill_drafts` tables with WAL mode. Planner decides exact column set and whether utterances are parsed line-by-line or written as a single transcript blob.
- **Citation validator timing:** ORCH-09 requires `citation_validator.py` to report 0 unresolvable citations. Planner decides whether validation runs post-session (simpler) or live per-utterance. Post-session is sufficient for Phase 3.
- **FastAPI SSE scope:** Phase 3 must expose an SSE endpoint "ready for Phase 4." Planner decides minimal viable: single `GET /stream/{session_id}` endpoint that emits accumulated session events from SQLite as `text/event-stream`. The Phase 4 Next.js app will consume this.
- **`--minister` isolation mode:** CLI-02 says `parliament --minister finanse "<question>"` runs one ministry in isolation. Planner decides whether this subprocess Hermes with the ministry skill directly, or whether it routes through a minimal marszalek skill.
- **Token budget wiring (INFRA-06):** Phase 1 stub exists in `parliament/guards.py`. Planner wires it into the subprocess launcher — estimated token count from output length as a proxy, or via Hermes usage output if available.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase context
- `.planning/ROADMAP.md` — Phase 3 section, success criteria, and cut criteria
- `.planning/REQUIREMENTS.md` — INFRA-04..06, ORCH-01..09, CLI-01..05, EXPORT-01, ETHICS-01
- `.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md` — stack decisions (Python 3.11, typer, hermes-agent==0.14.0, delegate_task pattern)
- `.planning/phases/02-agent-skills-corpus/02-CONTEXT.md` — Marszałek skill design, ministry routing table, session output format

### Existing code to read before writing Phase 3 code
- `parliament/__init__.py` — package root (add CLI entry point here or in cli.py)
- `parliament/guards.py` — TokenBudget stub that must be wired into LLM call path
- `parliament/doc_registry.py` — `get_filter(agent_id)` returns domain filter for PageIndex queries
- `parliament/second_brain/pageindex_client.py` — async MCP client (for citation validator)
- `skills/marszalek-sejmu/SKILL.md` — orchestration protocol, phase markers, session output format
- `skills/marszalek-sejmu/assets/bill-draft-template.md` — bill draft template (ORCH-07 output)

### Hermes Agent API surface
- `https://github.com/NousResearch/hermes-agent` — `run_agent.py`, `cli.py`, `tools/delegate_tool.py` — confirm subprocess invocation flags and skill-load CLI args
- `CLAUDE.md` — What NOT to Use table: asyncio.gather over AIAgent = deadlock; delegate_task = correct fan-out

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `parliament/guards.py` TokenBudget — Phase 3 wires this; interface is complete
- `parliament/doc_registry.py` get_filter() — used by citation validator to map node_ids to domains
- `parliament/second_brain/pageindex_client.py` — async MCP client; citation validator uses `get_page_content(node_id)` to verify resolvability

### Established Patterns
- Subprocess + stdout parsing: the conftest.py test infra shows how to invoke subprocesses and check output
- PageIndex MCP client: `async with PageIndexClient.connect() as client:` — reuse in citation_validator.py

### Integration Points
- `pyproject.toml` needs `[project.scripts] parliament = "parliament.cli:app"` entry point
- `parliament/cli.py` (new) is the typer app; imports from `parliament.session` (new) for orchestration
- `parliament/session.py` (new) handles subprocess launch, stdout streaming, SQLite writes
- `parliament/api.py` (new) FastAPI SSE endpoint, reads from SQLite sessions table
- `tests/` — Phase 3 adds `test_phase3_acceptance.py` parallel to the Phase 2 acceptance suite

</code_context>

<specifics>
## Specific Requirements

### CLI surface (exact commands)
```bash
# Full simulation
parliament "4-day work week"
parliament "OZE expansion"
parliament "tax simplification"

# Ministry isolation
parliament --minister finanse "ile kosztuje 800+"

# With export
parliament "test" --export markdown output.md

# Expected behavior
# - rich Live panel updates with phase labels during run
# - ⚠️ EDUCATIONAL SIMULATION disclaimer at top and bottom of every output
# - Vote table printed to stdout on completion
# - If --export: writes clean markdown to file
```

### Session output format (marszalek-sejmu SKILL.md defines this — CLI just captures it)
```
⚠️ EDUCATIONAL SIMULATION — This is not a political forecast...

[MARSZAŁEK REASONING] ... [END MARSZAŁEK REASONING]

## Ministry Analysis
## Party Debate — First Reading
## Party Debate — Second Reading
## Vote
| Party | Vote | Seats |
## Draft Bill

⚠️ EDUCATIONAL SIMULATION — ...
```

### Phase 3 success criteria (from ROADMAP.md)
1. `parliament "4-day work week"`, `"OZE expansion"`, `"tax simplification"` each complete ≤ 5 min with politically coherent vote (Lewica and Konfederacja oppose on 4-day work week)
2. citation_validator.py reports 0 unresolvable node_ids
3. `parliament --minister finanse "..."` returns structured Finance analysis in < 60s
4. `parliament "test" --export markdown output.md` produces readable markdown with all sections
5. `[MARSZAŁEK REASONING]` blocks present; every output has educational disclaimer

</specifics>

<deferred>
## Deferred Ideas

- **PDF export (STR-02):** Only after markdown export is solid. Not in Phase 3 scope.
- **Web UI reasoning side-panel (STR-03):** Phase 4 only.
- **Full SQLite query API:** Phase 3 only needs the write side and one SSE read endpoint. Full REST API is Phase 4.
- **Multi-session concurrency:** Phase 3 is single-session CLI. Concurrency is a Phase 4/post-contest concern.

</deferred>

---

*Phase: 03-orchestrator-cli*
*Context gathered: 2026-05-27 via gsd-discuss-phase*

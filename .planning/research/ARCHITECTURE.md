# Architecture Research

**Domain:** Multi-agent legal simulation (Polish parliament, 25 agents, Hermes Agent + PageIndex RAG over MCP)
**Researched:** 2026-05-26
**Confidence:** MEDIUM — Hermes Agent and PageIndex are new integrations; patterns below are grounded in Python asyncio multi-agent conventions and MCP protocol spec, but Day-1 prototype will surface surprises.

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                         ENTRY POINTS                                  │
│   CLI (typer)  ←→  parliament/cli.py   Next.js UI  ←→  FastAPI+SSE  │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│                      ORCHESTRATOR LAYER                               │
│                  parliament/orchestrator.py                           │
│   (Marszałek Hermes Agent loaded from skills/marszalek-sejmu/)       │
│   Decides: which ministries, reading order, vote tallying            │
└──────┬──────────────────────────────────┬────────────────────────────┘
       │ sequential (debate order)         │ parallel fan-out
       │                                   │
┌──────▼────────────┐       ┌─────────────▼────────────────────────────┐
│  PARTY AGENTS (5) │       │        MINISTRY AGENTS (2-3 active)       │
│  KO / PiS / TD    │       │  Finance / Health / Justice / etc.        │
│  Konfed / Lewica  │       │  (selected per topic by Marszałek)        │
│                   │       │  asyncio.gather() for consultations       │
│  skills/party-*/  │       │  skills/ministerstwo-*/                   │
└──────┬────────────┘       └─────────────┬────────────────────────────┘
       │                                  │
       └──────────────┬───────────────────┘
                      │  all agents call identically via MCP
┌─────────────────────▼────────────────────────────────────────────────┐
│                    KNOWLEDGE LAYER (MCP)                              │
│              Single PageIndex MCP Server                              │
│   tools: tree_search / doc_search / fetch_node / list_docs           │
│   per-agent filter: metadata param {"ministry": "finanse"} etc.      │
└──────────────────────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────────────────────────┐
│                    PERSISTENCE LAYER                                  │
│  SQLite (sessions.db)             Hermes long-term memory store       │
│  sessions / transcripts / votes   (per-agent, separate from SQLite)  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `parliament/cli.py` | Parse user input; call `run_session()`; stream output to terminal | `orchestrator.py` |
| `parliament/api.py` | FastAPI app; POST /session → SSE stream; GET /sessions | `orchestrator.py`, `sessions.db` |
| `parliament/orchestrator.py` | Marszałek: select ministries, manage debate phases, tally votes, emit final doc | `agent_factory.py`, `second_brain/`, `sessions.db` |
| `parliament/agent_factory.py` | Load a SKILL.md folder → instantiate a Hermes Agent with correct tools and memory namespace | `skills/*/SKILL.md`, Hermes Agent SDK |
| `parliament/session.py` | Session state machine: CONSULTING → READING_1 → READING_2 → VOTING → CLOSED | `orchestrator.py`, `sessions.db` |
| `parliament/second_brain/ingest.py` | PDF/HTML → PageIndex tree; one-time + incremental | PageIndex MCP server |
| `parliament/second_brain/pageindex_client.py` | Thin wrapper to call PageIndex MCP tools | PageIndex MCP server |
| `parliament/second_brain/doc_registry.py` | Maps agent_id → relevant doc IDs / category filters | read by `agent_factory.py` |
| `skills/<agent-id>/SKILL.md` | Agent identity: ideology, format, tools, references | loaded by `agent_factory.py` |
| `sessions/` | Flat-file JSON transcript dumps (export target) | written by `session.py` |
| `web/` (Next.js) | Chamber visualization; party-colored live transcript | FastAPI SSE endpoint |

---

## Architectural Decision Records

### ADR-1: Single asyncio process, not worker pool

**Decision:** One Python process with asyncio. Ministry consultations fan out with `asyncio.gather()`. Party speeches run sequentially in a single coroutine loop.

**Alternative rejected:** Separate worker processes per agent class (e.g. `multiprocessing.Pool` or Celery workers).

**Why rejected:** Inter-process communication overhead adds ~100-200ms per message boundary and requires a broker (Redis/RabbitMQ) that doesn't exist in the stack. For a 5-minute total runtime target, LLM API latency (2-5 seconds per call) dominates completely. A single process with asyncio yields near-identical wall-clock time with far less operational complexity. On a $5/month VPS, a separate broker process would also compete for RAM.

**Survives 2-3 parallel ministry consultations:** `asyncio.gather(*[consult(m) for m in selected_ministries])` is the correct primitive. All three MCP calls are I/O-bound (HTTP to PageIndex + LLM API call); asyncio handles them without threads.

**Confidence:** HIGH — standard Python async I/O reasoning.

---

### ADR-2: Hermes Agent instantiated per session, not cached across sessions

**Decision:** Call `agent_factory.create_agent(skill_id, session_id)` at session start. Instantiate one Hermes Agent per active agent role per session. Tear down (allow GC) when session ends.

**Why not cached singletons:** Hermes Agent's long-term memory is session-aware — the agent accumulates context during a session. Re-using an agent across sessions risks context bleed ("last session's bill influences this session's vote"). Clean instantiation prevents that.

**Why not one agent per skill always running:** 25 always-on agents each with an open MCP connection and in-memory context would consume significant RAM on a $5/month VPS with no benefit (sessions are synchronous from the user's perspective — one session at a time for a demo).

**Long-term memory persistence:** Hermes Agent uses its own memory store (typically a local SQLite or embedded key-value store under its data directory). This is separate from the session `sessions.db`. The pattern is: `agent_factory` passes a `memory_namespace=skill_id` so each party's long-term memory (voting history, rhetorical patterns) persists across sessions but doesn't leak between party agents. Ministry agents do not need persistent memory (they are stateless experts); their `memory_namespace` can be ephemeral or omitted.

**Concrete split:**

| Store | What lives there | Managed by |
|-------|-----------------|------------|
| `sessions.db` (SQLite) | Session records, full transcripts, vote tallies, citations index | `session.py` |
| Hermes memory store (per agent) | Party voting history, rhetorical style evolution, cross-session context | Hermes Agent SDK |
| `sessions/<id>.json` | Exported transcript for Markdown/PDF | `session.py` on session close |

**Confidence:** MEDIUM — assumes Hermes Agent SDK exposes a `memory_namespace` parameter or equivalent. Verify on Day 1.

---

### ADR-3: Single PageIndex MCP server consumed by all 25 agents

**Decision:** One PageIndex MCP server process, shared. Per-agent document scope enforced at the query level via metadata filters (e.g., `{"ministry": "finanse"}` or `{"category": "kodeksy"}`).

**Alternative rejected:** One PageIndex instance per agent group (parties pool, each ministry silo).

**Why rejected:**
- 20+ MCP server processes on a $5/month VPS is operationally absurd.
- PageIndex's `doc_search` already accepts metadata parameters; filtering is the purpose of the `doc_registry.py` component.
- A shared server means one ingest pipeline, one index to maintain, one place to add documents.

**How per-agent filtering works:**
- `doc_registry.py` maps `agent_id → {ministry: str, categories: list[str], doc_ids: list[str]}`.
- `agent_factory` passes the registry entry into the agent's tool call defaults.
- Party agents get broad access (all categories); ministry agents get narrow access (their domain + kodeksy + konstytucja).
- Filter is enforced at call time in `pageindex_client.py`, not at the MCP server level. This is intentional: it keeps the MCP server generic and puts policy in Python where it can be tested.

**Confidence:** MEDIUM — PageIndex MCP tool signature assumed to accept metadata filter params per PRD §5.1; verify against actual API on Day 1.

---

### ADR-4: FastAPI + SSE for web front-end, not file-tail

**Decision:** FastAPI app (`parliament/api.py`) with a `POST /session` endpoint that returns a Server-Sent Events stream. Next.js `EventSource` client consumes the stream.

**Alternative A rejected:** File-tail of generated transcripts (e.g., `tail -f sessions/<id>.jsonl` via a WebSocket shim).

**Why A rejected:** File-tail requires polling or inotify + a WebSocket bridge, which is more code than FastAPI + SSE and introduces filesystem coupling. The transcript file is the export artifact, not the transport layer.

**Alternative B rejected:** WebSocket (bidirectional).

**Why B rejected:** The data flow is unidirectional (server pushes debate lines to browser). SSE is simpler, works over HTTP/1.1, needs no upgrade handshake, and Next.js `EventSource` handles reconnection natively. Full WebSocket is overkill for read-only visualization.

**API surface (minimal):**

```
POST /session          body: {topic: str}    → SSE stream of {event, data} lines
GET  /sessions         → list of past sessions
GET  /sessions/{id}    → full transcript JSON
GET  /sessions/{id}/export → Markdown download
```

**SSE event types emitted during a session:**

```
event: session_start   data: {session_id, topic, timestamp}
event: ministries_selected  data: {ids: [...]}
event: ministry_opinion  data: {ministry_id, text, citations: [...]}
event: speech          data: {party_id, reading, text, citations: [...]}
event: vote            data: {party_id, vote, justification}
event: session_end     data: {result, vote_summary, bill_draft}
```

**Next.js layer is thin:** It only needs to render party-colored lines and an SVG chamber seating diagram. No GraphQL, no tRPC, no state management library beyond React state + `EventSource`. The visualization is static seating + dynamic transcript feed.

**Confidence:** HIGH — SSE + FastAPI is a well-established pattern; Next.js `EventSource` is standard browser API.

---

### ADR-5: SQLite is sufficient for session persistence

**Decision:** One SQLite database (`sessions.db`) with three tables: `sessions`, `transcript_lines`, `votes`.

**Alternative rejected:** PostgreSQL.

**Why rejected:** A $5/month VPS demo with one user at a time has no concurrent write pressure. SQLite with WAL mode handles the write-append pattern (each debate line is an INSERT) without issue. Switching to Postgres adds a service dependency, connection pooling, and migration tooling with zero benefit at demo scale.

**Schema sketch:**

```sql
sessions(id TEXT PK, topic TEXT, started_at REAL, ended_at REAL, status TEXT)
transcript_lines(id INTEGER PK, session_id TEXT, seq INTEGER, speaker_id TEXT,
                 reading INTEGER, text TEXT, citations JSON, created_at REAL)
votes(session_id TEXT, party_id TEXT, vote TEXT, justification TEXT)
```

**Confidence:** HIGH — SQLite is appropriate for single-user demo applications.

---

## Data Flow — Full Session Lifecycle

### Notation
- `→` sequential step
- `‖` steps that run in parallel (asyncio.gather)
- `↺` loop over collection

```
[1] User input
    CLI: hermes parliament "<topic>"
    Web: POST /session {topic}
         ↓
[2] orchestrator.run_session(topic, session_id)
    → session.py: INSERT sessions (status=OPEN)
    → Orchestrator agent: "Given topic, select 2-3 relevant ministries"
      (LLM call with pageindex doc_search for topic context)
         ↓
[3] Ministry consultation phase   [PARALLEL]
    asyncio.gather(
      ‖ ministerstwo_A.consult(topic)   → MCP: doc_search + tree_search + fetch_node → LLM → ExpertiseReport
      ‖ ministerstwo_B.consult(topic)   → MCP: doc_search + tree_search + fetch_node → LLM → ExpertiseReport
      ‖ ministerstwo_C.consult(topic)   → MCP: doc_search + tree_search + fetch_node → LLM → ExpertiseReport
    )
    → Each ministry result: session.py INSERT transcript_lines (speaker=ministry_id, reading=0)
    → SSE event: ministry_opinion × 3
         ↓
[4] First reading — party speeches  [SEQUENTIAL — transcript order matters]
    ↺ for party in [KO, PiS, TD, Konfed, Lewica]:
        INTERNAL PARALLELISM per party:
        asyncio.gather(
          ‖ party.memory_lookup("analogous past bills")   [Hermes long-term memory]
          ‖ second_brain.doc_search(topic, party_filter)  [PageIndex MCP — ideology-relevant docs]
        )
        → LLM: generate speech using ministry expertise + own memory + docs
        → session.py INSERT transcript_lines (reading=1)
        → SSE event: speech
         ↓
[5] Second reading — responses  [SEQUENTIAL]
    ↺ for party in debate_order:
        INTERNAL PARALLELISM per party:
        asyncio.gather(
          ‖ party.memory_lookup("responses to opponent args")
          ‖ second_brain.tree_search(cited_doc_id, rebuttal_query)
        )
        → LLM: generate rebuttal/amendment
        → session.py INSERT transcript_lines (reading=2)
        → SSE event: speech
         ↓
[6] Voting phase  [PARALLEL collection, sequential display]
    asyncio.gather(
      ‖ party_KO.vote(bill_summary)     → {vote, justification, citations}
      ‖ party_PiS.vote(bill_summary)    → ...
      ‖ party_TD.vote(bill_summary)     → ...
      ‖ party_Konfed.vote(bill_summary) → ...
      ‖ party_Lewica.vote(bill_summary) → ...
    )
    → session.py INSERT votes × 5
    → SSE event: vote × 5
         ↓
[7] Session close
    → Orchestrator: generate bill draft + vote summary
    → session.py UPDATE sessions (status=CLOSED, ended_at)
    → Write sessions/<session_id>.json  (export artifact)
    → SSE event: session_end
    → Hermes memory store: each party writes voting decision to long-term memory
```

**Key parallel-vs-sequential rationale:**

| Phase | Mode | Why |
|-------|------|-----|
| Ministry consultations | Parallel | I/O-bound, independent, no ordering dependency |
| Party internal prep (memory + doc lookup) | Parallel | Both are MCP/memory reads; LLM call waits for both |
| Party speeches | Sequential | Transcript ordering; later parties react to earlier ones in reading 2 |
| Votes | Parallel collection | Parties vote independently; display can be sequential after gather |

---

## Recommended Repo Structure (refined from PRD §6.2)

```
virtual-parliament/
├── pyproject.toml               # single package, dev deps include pytest, ruff
├── parliament/
│   ├── __init__.py
│   ├── cli.py                   # typer app; calls orchestrator.run_session()
│   ├── api.py                   # FastAPI + SSE; wraps same run_session()
│   ├── orchestrator.py          # Marszałek agent; session phase state machine
│   ├── session.py               # SQLite writes; transcript_lines INSERT helpers
│   ├── agent_factory.py         # SKILL.md → Hermes Agent instance
│   └── second_brain/
│       ├── ingest.py            # PDF/HTML → PageIndex; run once before demo
│       ├── pageindex_client.py  # thin wrapper: tree_search / doc_search / fetch_node
│       └── doc_registry.py      # agent_id → {ministry, categories, doc_ids}
├── skills/
│   ├── pageindex-rag/           # installed via: npx skills add mmtmr/pageindex-rag
│   ├── marszalek-sejmu/
│   │   ├── SKILL.md
│   │   └── references/regulamin-sejmu.md
│   ├── party-ko/
│   │   ├── SKILL.md
│   │   ├── references/{elektorat,historia-glosowan}.md
│   │   └── assets/przykladowe-przemowienia.md
│   ├── party-pis/ party-td/ party-konfederacja/ party-lewica/  # same structure
│   └── ministerstwo-{finansow,zdrowia,...}/   # 19 skills, shared template
│       ├── SKILL.md
│       ├── references/
│       ├── assets/szablon-ekspertyzy.md
│       └── scripts/policz-skutek.py          # optional per ministry
├── web/                         # Next.js app
│   ├── app/page.tsx             # chamber visualization + EventSource client
│   └── app/api/                 # proxy to FastAPI if needed for CORS
├── data/                        # corpus PDFs + PageIndex index output (gitignored heavy files)
├── sessions/                    # JSON transcript exports
├── sessions.db                  # SQLite (gitignored)
├── tests/
│   ├── test_skills_valid.py     # skills-ref validate each skill folder
│   ├── test_session_smoke.py    # 1 party + 1 ministry + mocked MCP
│   └── test_data_flow.py        # assert SSE events emitted in correct order
└── scripts/
    └── ingest_corpus.py         # convenience wrapper: runs second_brain/ingest.py
```

**Structure rationale:**

- `parliament/` is the Python package. `cli.py` and `api.py` are thin entry points that both call `orchestrator.run_session()` — this ensures CLI and web share the same logic, not separate code paths.
- `skills/` is not imported by Python. It is read by `agent_factory.py` as filesystem data. This separation keeps the Agent Skills format honest — skills are data, not code modules.
- `second_brain/` is a sub-package of `parliament/` because the knowledge layer is internal infrastructure, not a standalone service. Promoting it to a top-level service would add a network boundary with no benefit.
- `sessions.db` is gitignored. `sessions/` JSON exports are gitignored for large corpora but can be committed for demo samples.
- `web/` is a sibling to `parliament/`, not nested inside it. They are different runtimes (Node vs Python).

---

## Architectural Patterns

### Pattern 1: Skill Loader — Data-Driven Agent Construction

**What:** `agent_factory.py` reads `skills/<id>/SKILL.md`, parses the YAML frontmatter (name, type, metadata), constructs Hermes Agent with skill body as system prompt, attaches MCP tools filtered by `doc_registry`, and sets memory namespace.

**When to use:** Every agent instantiation. The factory is the single point where Skill format → Hermes Agent config mapping is defined. Adding a new agent means adding a skill folder, not touching factory logic.

**Trade-offs:** If the SKILL.md format changes, only `agent_factory.py` needs updating. Con: YAML parsing error in one skill breaks that agent silently if not validated — hence `test_skills_valid.py` runs `skills-ref validate` as a test.

```python
# parliament/agent_factory.py (sketch)
async def create_agent(skill_id: str, session_id: str) -> HermesAgent:
    skill_path = Path("skills") / skill_id
    frontmatter, body = parse_skill_md(skill_path / "SKILL.md")
    doc_filter = doc_registry.get(skill_id)
    memory_ns = skill_id if frontmatter["metadata"]["type"] == "party" else None
    return HermesAgent(
        system_prompt=body,
        tools=[pageindex_client.make_tools(doc_filter)],
        memory_namespace=memory_ns,
        session_id=session_id,
    )
```

### Pattern 2: Orchestrator as State Machine

**What:** `orchestrator.py` implements a linear state machine: `INIT → CONSULTING → READING_1 → READING_2 → VOTING → CLOSED`. Each state transition is async and yields SSE events. The Marszałek Hermes Agent is only invoked for decisions requiring judgment (ministry selection, bill draft generation). Mechanical steps (loop over parties, tally votes) are plain Python.

**When to use:** Always — don't let the Marszałek LLM call drive the loop. The LLM decides what, Python decides when/how.

**Trade-offs:** Keeps LLM calls targeted and predictable. A pure LLM-driven orchestrator is unpredictable and harder to test. Con: state machine is more code upfront, but the states map 1:1 to PRD §5.5 steps.

### Pattern 3: Generator-Based SSE Streaming

**What:** `orchestrator.run_session()` is an `async_generator` that `yield`s SSE-formatted strings as each debate step completes. `api.py` wraps it in a `StreamingResponse`. `cli.py` iterates and prints to terminal.

**When to use:** This pattern means CLI and web share zero-extra code. The generator is the canonical output; both consumers just iterate it differently.

```python
# parliament/orchestrator.py (sketch)
async def run_session(topic: str, session_id: str) -> AsyncGenerator[str, None]:
    yield sse("session_start", {"topic": topic, "session_id": session_id})
    ministries = await marszalek.select_ministries(topic)
    yield sse("ministries_selected", {"ids": ministries})
    opinions = await asyncio.gather(*[consult(m, topic) for m in ministries])
    for op in opinions:
        yield sse("ministry_opinion", op)
    for party in PARTY_ORDER:
        speech = await party_agent.speak(topic, opinions, reading=1)
        yield sse("speech", speech)
    ...
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Giving Each Ministry a Separate MCP Server Process

**What people do:** Stand up one PageIndex MCP server per ministry to enforce document isolation.
**Why it's wrong:** 19 MCP server processes exhaust RAM on a $5/month VPS; ingest runs 19 times; operational complexity is unbounded; PageIndex's metadata filter param already provides the isolation.
**Do this instead:** Single MCP server + `doc_registry.py` metadata filters at call time.

### Anti-Pattern 2: Letting the Orchestrator LLM Drive the Loop

**What people do:** Ask the Marszałek LLM "what should happen next?" at each step, letting it decide whether to call parties, count votes, etc.
**Why it's wrong:** Non-deterministic session structure, impossible to test, wastes tokens on mechanical decisions, and breaks transcript ordering.
**Do this instead:** Mechanical loop in Python; LLM only for content-generation decisions (ministry selection, speech generation, bill draft).

### Anti-Pattern 3: Shared Hermes Agent Instance Across Sessions

**What people do:** Instantiate one `HermesAgent` per skill at startup and reuse it.
**Why it's wrong:** Hermes Agent accumulates session context in-memory. Cross-session context bleed means a debate about energy policy leaks into the next session about healthcare.
**Do this instead:** `agent_factory.create_agent()` per session; long-term memory persists via `memory_namespace`, short-term context is scoped to session.

### Anti-Pattern 4: WebSocket for One-Way Transcript Feed

**What people do:** Add WebSocket for "real-time" feel.
**Why it's wrong:** More protocol overhead, requires explicit message framing, complicates CORS, and provides bidirectionality nobody needs (the debate is not interactive mid-session).
**Do this instead:** SSE (`text/event-stream`). `EventSource` in Next.js handles reconnection automatically.

### Anti-Pattern 5: Ingest Inside the Hot Path

**What people do:** Trigger PageIndex ingest when a user starts a session (on-demand ingest of new documents).
**Why it's wrong:** OCR + tree-building for a 50-document corpus takes minutes. A user waiting 3 minutes before the 5-minute simulation starts is a failed demo.
**Do this instead:** `scripts/ingest_corpus.py` runs once before demo. Ingest is a setup step, not a runtime step. The `data/` directory holds pre-built indexes.

---

## Build Order — 5-Day Dependency Chain

### Dependency graph

```
[A] Hermes Agent smoke test (1 agent, 1 MCP tool)
 └─► [B] agent_factory.py (SKILL.md → Hermes Agent)
      ├─► [C] skills/party-ko (1 party skill, minimal)
      │    └─► [D] All 5 party skills (template from C)
      └─► [E] PageIndex MCP + ingest (1 doc smoke test)
           └─► [F] All 19 ministry skills + doc_registry
                └─► [G] orchestrator.py (full session flow)
                     ├─► [H] CLI (cli.py thin wrapper)
                     ├─► [I] FastAPI + SSE (api.py)
                     │    └─► [J] Next.js web front
                     └─► [K] marszalek-sejmu skill + session.py
```

### Day-by-day assignment

| Day | Date | Build targets | Why this order |
|-----|------|---------------|----------------|
| Day 1 | 2026-05-26 | [A] Hermes smoke test with 1 agent + [E] PageIndex ingest smoke test on 1 doc (Konstytucja) | Must de-risk both new APIs before committing architecture. If either fails, pivot same day. |
| Day 2 | 2026-05-27 | [B] `agent_factory.py` + [C] `party-ko` skill + `doc_registry.py` skeleton. End of day: `party-ko` debates a topic with real PageIndex citations. | Party skills are the template for ministry skills. Get one working end-to-end before scaling. |
| Day 3 | 2026-05-28 | [D] Remaining 4 party skills + [F] All 19 ministry skills (use shared `ministry_template.md`). [G] `orchestrator.py` state machine — ministries-consulted + first reading with 2 parties. | 19 ministries are content work, not new code. Factory + registry already exist. Orchestrator partial flow by EOD. |
| Day 4 | 2026-05-29 | [K] `marszalek-sejmu` skill + full orchestrator (both readings + voting) + [H] `cli.py` E2E. Full session on 3 topics via CLI. [I] `api.py` FastAPI SSE baseline. | CLI done before web — it is also the demo fallback if Next.js slips. SSE endpoint is ~50 lines once orchestrator generator exists. |
| Day 5 | 2026-05-30 | [J] Next.js chamber visualization + polish + export. Buffer for Hermes/PageIndex API surprises. | Web front is schedule risk; Day 5 leaves one day for slippage before deadline day. |
| Deadline day | 2026-05-31 | Ingest full 50-doc corpus, E2E test 3 topics, README, demo video, DEV.to post. | No new code. Only content, polish, and submission. |

**Critical path:** A → E → B → G → H. If the critical path slips on Day 1 (Hermes or PageIndex integration takes longer), cut Next.js and submit CLI-only. CLI is a complete demo.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| PageIndex MCP server | `parliament/second_brain/pageindex_client.py` calls MCP tools over stdio or HTTP transport | Single server process; all agents share. Verify transport type (stdio vs HTTP) on Day 1 — affects how `agent_factory` attaches tools. |
| Hermes Agent SDK | `agent_factory.py` imports SDK; agents run in-process | Memory store location is SDK-controlled. Check `HERMES_DATA_DIR` env var for VPS path. |
| LLM API (via Hermes) | Hermes handles routing (Nous Portal / OpenRouter) | Use cheaper models (Llama-3-8B or similar) for ministries, stronger model (Claude or GPT-4 class) for Marszałek + parties. Model-per-agent config in SKILL.md metadata or agent_factory. |
| Next.js → FastAPI | `EventSource` to `http://localhost:8000/session` | CORS header required on FastAPI. In production, nginx reverse-proxy eliminates CORS. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `orchestrator.py` ↔ `agent_factory.py` | Direct Python function call | Synchronous instantiation; agent methods are async |
| `orchestrator.py` ↔ `session.py` | Direct Python function call | session.py is a thin SQLite helper, not a service |
| `orchestrator.py` ↔ SSE consumers | `async_generator` yield | `api.py` wraps in `StreamingResponse`; `cli.py` iterates with `async for` |
| `parliament/` ↔ `skills/` | Filesystem reads only | Skills are data. Python never imports from `skills/`. |
| `parliament/` ↔ PageIndex MCP | MCP protocol (subprocess or HTTP) | `pageindex_client.py` is the only code that crosses this boundary |

---

## Scaling Considerations

This system is scoped for demo / single-user use. Scaling notes are relevant only if the project continues post-contest.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 concurrent user (demo) | Current design is correct. SQLite, single process, single MCP server. |
| 5-10 concurrent users | SQLite WAL mode handles concurrent reads fine. Main bottleneck: LLM API rate limits, not infrastructure. Add simple request queue (asyncio.Queue) to serialize sessions. |
| 100+ concurrent users | Replace SQLite with PostgreSQL. Add process-per-session worker pool. PageIndex MCP behind an HTTP proxy (not stdio). Next.js SSE needs connection pooling. |

---

## Sources

- PRD §5–6 (project document, `/Users/xpll081/ai-politics/prd.md`)
- PROJECT.md (`/Users/xpll081/ai-politics/.planning/PROJECT.md`)
- Python asyncio documentation — `asyncio.gather()` for fan-out parallel I/O
- MCP protocol specification — stdio and HTTP transport modes, tool call conventions
- Anthropic Agent Skills specification — YAML frontmatter, progressive disclosure loading model
- FastAPI `StreamingResponse` + SSE pattern — standard Python async web pattern
- SQLite WAL mode documentation — write-ahead logging for single-writer multi-reader
- CONFIDENCE NOTE: Hermes Agent SDK specifics (memory_namespace param name, MCP attachment API) are inferred from the project description and general Hermes Agent design goals. Actual parameter names must be verified against SDK source on Day 1.

---

*Architecture research for: Virtual Parliament (multi-agent Polish parliament simulation)*
*Researched: 2026-05-26*

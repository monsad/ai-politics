# Project Research Summary

**Project:** Virtual Parliament (Wirtualny Parlament)
**Domain:** Multi-agent political simulation — Polish Sejm, 25 Hermes agents, vectorless RAG, contest submission
**Researched:** 2026-05-26
**Confidence:** MEDIUM-HIGH (STACK: HIGH — live-verified; FEATURES: MEDIUM; ARCHITECTURE: MEDIUM; PITFALLS: MEDIUM)

---

## Executive Summary

Virtual Parliament is a 5-day contest entry for the Hermes Agent Challenge (deadline 2026-05-31). The product simulates Polish Sejm sessions: a user submits a bill topic and receives a source-cited transcript of ministry expertise, party debates across two readings, a vote tally, and a draft bill — all in under five minutes. The core differentiator is that every argument cites a real node from a 50-document Polish legal corpus (PageIndex vectorless RAG), which distinguishes it from generic LLM roleplay simulators. The jury cares explicitly about effective Hermes Agent use, and this project exercises long-term memory, MCP tool use, multi-step reasoning, model switching, and parallel fan-out — all of which must be visible in the demo.

The recommended approach, validated by STACK research against live repos and PyPI, is: Hermes Agent 0.14.0 as the framework (contest-locked), PageIndex Cloud for the contest (free tier covers 1000 pages, eliminating OCR infrastructure risk), `delegate_task(tasks=[...])` batch mode for ministry fan-out (the Hermes-native pattern — not `asyncio.gather`), and Next.js 16.2.6 App Router + SSE for the web front-end (not Streamlit). The ARCHITECTURE research proposed `asyncio.gather()` for ministry fan-out before STACK research completed; STACK contradicts this — use `delegate_task`. See the contradictions section below for resolution.

The single greatest risk is the Day-1 integration spike. Both Hermes Agent and PageIndex are new integrations for this team. If the smoke tests (Hermes `AIAgent` instantiation + PageIndex OCR on one Polish PDF) do not pass on Day 1, the entire 25-agent architecture is at risk. Every researcher independently flags this gate. Do not write a single party skill or ministry template before both smoke tests are green. Secondary risks are cost runaway across 25 LLM agents (wire model tiers into `agent_factory.py` on Day 1, not Day 4) and context-window blow-out from a naively concatenated transcript (use structured `Utterance` objects from the start). With those three risks mitigated on Day 1, the remaining work is primarily content (writing 25 SKILL.md files) plus orchestration wiring — achievable in the remaining days.

---

## Contradictions and Resolution

These are explicit conflicts between research files, or between research and the PRD/PROJECT.md. The higher-confidence answer is selected and annotated.

### Contradiction 1: Ministry Fan-Out — `asyncio.gather` vs `delegate_task`

| Source | Claim | Confidence |
|--------|-------|------------|
| ARCHITECTURE.md (ADR-1, data flow step 3, step 6) | Use `asyncio.gather(*[consult(m) for m in ministries])` for parallel ministry consultation | MEDIUM — authored before STACK research completed; based on general Python async patterns |
| STACK.md (alternatives table, "What NOT to Use") | Use `delegate_task(tasks=[...])` batch mode — this is the documented Hermes fan-out API. Hermes runs subagents on `ThreadPoolExecutor`. Mixing `asyncio.gather` with threaded `AIAgent` instances causes deadlocks on prompt_toolkit TUI stdin. | HIGH — verified against `tools/delegate_tool.py` source in live repo |

**Resolution: Use `delegate_task`.** STACK is higher confidence (live-verified). The ARCHITECTURE data flow diagrams must be updated to replace `asyncio.gather()` with `delegate_task(tasks=[...])` at the ministry consultation step. The Marszalek SKILL.md instructs the agent to call `delegate_task` with a list of ministry goal/context/toolset dicts. The orchestrator Python code does not call `asyncio.gather` for ministry fan-out.

The ARCHITECTURE pattern of `asyncio.gather` for party internal prep (memory lookup + doc search simultaneously) may still apply — those are pure I/O calls, not Hermes agent invocations. Verify on Day 1.

### Contradiction 2: PageIndex — Self-Host vs Cloud

| Source | Claim |
|--------|-------|
| PRD §5.1, PROJECT.md constraints | "self-hosted PageIndex (open source, MIT-friendly stack) on the same VPS" as the primary path; cloud as backup |
| STACK.md (stack patterns, PageIndex section) | Use PageIndex Cloud for the contest. Free tier (1000 pages) covers ~50 statutes at 20 pages average. No OCR infrastructure needed. Self-host path requires cloning VectifyAI/PageIndex (no PyPI), building a custom FastMCP wrapper, and handling Polish OCR via surya-ocr or pre-processing. |

**Resolution: Use PageIndex Cloud for the contest.** The PRD's self-host preference predates STACK research discovering that `pageindex-mcp@1.6.3` (npm cloud client) is the production-ready path and that self-host has no PyPI package, requires OCR infrastructure, and adds 0.5+ dev days. For a 5-day deadline this is the right call. The PROJECT.md "cloud as backup" framing should be reversed — cloud is primary, self-host is post-contest. Install `pageindex-mcp@1.6.3` and add it to `~/.hermes/config.yaml` as an MCP server.

**PRD items to correct before roadmap:**
- PRD §5.1 "MVP: self-hosted PageIndex" — correct to "PageIndex Cloud (pageindex-mcp@1.6.3) for contest; self-host post-contest"
- PRD §6.1 stack table — add `pageindex-mcp@1.6.3` version

### Contradiction 3: Web Front-End — Streamlit vs Next.js

| Source | Claim |
|--------|-------|
| PRD §6.1 stack table | "Streamlit (najszybciej) lub Next.js" — Streamlit listed first as fastest |
| STACK.md | Streamlit is NOT recommended. It introduces a second Python web process duplicating the CLI pipeline. Next.js 16.2.6 with App Router + SSE Route Handlers is the correct pattern. |

**Resolution: Next.js 16.2.6.** Streamlit is eliminated. The ARCHITECTURE.md already proposes FastAPI + SSE, which maps cleanly to Next.js Route Handlers. The PRD's mention of Streamlit should be treated as withdrawn.

### Contradiction 4: Hermes Import Path

| Source | Claim |
|--------|-------|
| PRD/PROJECT.md | Hermes Agent install path unspecified; implied importable as a conventional package |
| STACK.md | `hermes-agent` is a CLI/TUI tool. Programmatic API is `from run_agent import AIAgent` — importable after `pip install hermes-agent==0.14.0` places the module. Day-1 spike must verify this works in a fresh venv. |

**Resolution: STACK is authoritative.** The import is `from run_agent import AIAgent`. Day-1 gate must verify this in an isolated venv before any `agent_factory.py` code is written.

### Contradiction 5: `skills-ref validate` CLI Command

| Source | Claim |
|--------|-------|
| PRD §5.0 | Mentions `skills validate` as the validation command |
| STACK.md | The correct CLI is `npx skills-ref@0.1.5 validate ./skills/<agent-id>` (from `npm install -g skills-ref@0.1.5`), not `skills validate` |

**Resolution: STACK is authoritative.** Use `npx skills-ref@0.1.5 validate`. Add as a pre-commit hook on Day 1.

---

## PRD Items That Need Correction Before Roadmap

| PRD Location | Current Text | Correction |
|---|---|---|
| §5.1, §6.1 | Self-hosted PageIndex as MVP | Switch to PageIndex Cloud (`pageindex-mcp@1.6.3`) for contest |
| §6.1 stack | "Streamlit (najszybciej) lub Next.js" | Remove Streamlit; use Next.js 16.2.6 only |
| §5.5 step 4 | Ministry parallel consultation (asyncio implied) | Fan-out via `delegate_task(tasks=[...])`, not `asyncio.gather` |
| §5.0 | `skills validate` command | Correct to `npx skills-ref@0.1.5 validate` |
| §8 day 26 | "ingest 100 najwazniejszych ustaw" | Ingest ~50 docs (1000-page free tier limit); Constitution + KK + KC + KP first |
| §6.1 stack | No hermes-agent version | Pin `hermes-agent==0.14.0`, Python 3.11 (exact) |

---

## Stack at a Glance

| Technology | Version | Role |
|---|---|---|
| hermes-agent | 0.14.0 | Agent framework, fan-out via `delegate_task`, MCP client, long-term memory |
| pageindex-mcp | 1.6.3 (npm) | PageIndex Cloud MCP server — vectorless RAG, Polish OCR handled server-side |
| skills-ref | 0.1.5 (npm) | SKILL.md frontmatter validation — run as pre-commit hook |
| skills (CLI) | 1.5.7 (npm) | Install `mmtmr/pageindex-rag` skill |
| Python | 3.11 (exact) | Orchestration, CLI, ingest; `hermes-agent` requires `>=3.11` |
| typer | 0.25.1 | `hermes parliament "<topic>"` CLI entry point |
| Next.js | 16.2.6 | Web chamber visualization; App Router + SSE Route Handlers |
| SQLite (aiosqlite) | latest | Session and transcript storage |
| mcp | 1.27.1 (PyPI) | Python MCP client SDK (only needed if self-hosting PageIndex later) |

**What to avoid:**
- `asyncio.gather` for Hermes agent fan-out (deadlocks with `ThreadPoolExecutor`)
- `pageindex-mcp` npm used as a self-host solution (it is a cloud client)
- Streamlit (duplicates Python web process, poor SSE story)
- Python 3.12/3.13 (surya-ocr wheels, Hermes compat)
- `hermes-agent[all]` extras (installs voice/TTS/browser — irrelevant)

---

## Key Findings

### From STACK.md

The stack is fully verified against live repos. The two most important findings that deviate from PRD assumptions:

1. `delegate_task(tasks=[...])` is the only correct fan-out primitive. It uses `ThreadPoolExecutor` internally. Any asyncio-based fan-out of Hermes `AIAgent` instances will deadlock.
2. PageIndex Cloud (`pageindex-mcp@1.6.3`, npm) is the correct tool for the contest — free tier handles 1000 pages (~50 statutes), Polish OCR is server-side, zero infrastructure. Self-hosting requires cloning VectifyAI/PageIndex (no PyPI), building a custom FastMCP wrapper, and running surya-ocr locally.

The `from run_agent import AIAgent` import must be verified on Day 1 in a clean venv before any orchestration code is built around it.

### From FEATURES.md

Confidence: MEDIUM (web search blocked; analysis from PRD + comparable project patterns).

**Table stakes (P1, non-negotiable):**
- `hermes parliament "<topic>"` CLI — single command, full run, <=5 min (TS-7)
- Source citations on every argument — cites a real PageIndex node (TS-4, most important quality signal)
- Party-attributed speech with colour coding (TS-2)
- Vote tally with seat-weighted result (TS-3)
- Ministry expertise phase, parallel, 2-3 ministries (TS-5)
- Two reading structure — first reading + second reading + vote (TS-9)
- Session transcript, markdown export, educational disclaimer (TS-1, TS-8, TS-6)

**High-value differentiators (P1, include in contest submission):**
- `--minister <domain> "<question>"` single-agent mode — best early validation path AND journalist use case (D-2)
- English debate / Polish citations split with `(orig. PL: "...")` notation (D-9)
- Parallel ministry consultation timing display with `rich` progress (D-7)
- Draft bill output post-vote (D-3)

**P2 stretch (Day 4-5 only if CLI is solid):**
- Next.js chamber visualization (D-1) — highest demo impact, highest schedule risk
- Party long-term memory — spike Day 1, implement Day 4 if clean (D-4)
- Hermes reasoning trace in transcript (D-5)

**Defer to post-contest:**
- PDF export, session share URL, TTS, RSS news ingest, 6th party, fine-tuning

**Critical anti-feature enforcement:** no real MP names, no hate speech (especially Konfederacja agent). These require explicit `## Output Constraints` sections in SKILL.md, not just a README statement.

**Missing from PRD §5 (must add):** `--minister` mode in CLI spec; party colour system config file; seat count in vote tally logic; bill draft template; Hermes reasoning trace in transcript.

### From ARCHITECTURE.md

Confidence: MEDIUM — written before STACK research completed; the `asyncio.gather` fan-out pattern must be replaced. Remaining architecture is sound.

The correct architecture is a single Python process with a state machine orchestrator (`INIT -> CONSULTING -> READING_1 -> READING_2 -> VOTING -> CLOSED`). The orchestrator's `run_session()` is an `async_generator` that yields SSE-formatted strings — both `cli.py` and `api.py` iterate it. This eliminates code duplication between CLI and web paths.

**Major components:**
1. `parliament/orchestrator.py` — Marszalek state machine; calls `delegate_task` for ministry fan-out; plain Python loops for sequential party speeches; LLM only for content decisions (ministry selection, speech generation, bill draft)
2. `parliament/agent_factory.py` — reads `skills/<id>/SKILL.md`, constructs Hermes `AIAgent` with correct tools and memory namespace; unique instance per role per session
3. `parliament/second_brain/` — thin Python wrappers around PageIndex Cloud MCP tools; `doc_registry.py` maps agent_id to metadata filters for per-agent document scoping
4. `skills/<agent-id>/SKILL.md` — agent identity as data, not code; loaded by factory; 25 files
5. `web/` — Next.js 16.2.6 App Router; `EventSource` consuming SSE from FastAPI or Next.js Route Handler proxy

**Key architectural rules:**
- One `AIAgent` instance per role per session — no singletons, no caching across sessions (context bleed)
- `skills/` is filesystem data, never imported as Python
- Transcript is structured `Utterance` objects, never a concatenated string (context budget)
- Orchestrator mechanical steps (loop over parties, tally) are Python; LLM decisions are targeted and bounded
- Ministry agents get `skip_memory=True` / ephemeral namespace; party agents get persistent `memory_namespace=skill_id`

**Note on ARCHITECTURE ADR-1:** The `asyncio.gather` reasoning is valid for pure I/O calls (PageIndex queries, party internal prep) but NOT for Hermes `AIAgent` fan-out, which uses threads. The ministry consultation step must use `delegate_task`.

### From PITFALLS.md

Confidence: MEDIUM (web tools blocked; analysis from PRD/architecture pattern knowledge). The top pitfalls are independently consistent with STACK and ARCHITECTURE findings.

**Top 5 pitfalls by S×L score:**

1. **OCR ingest fails on Day 1 with no fallback (S×L: 25)** — RESOLVED by switching to PageIndex Cloud as primary. The STACK research eliminates the highest-rated pitfall entirely.
2. **25-agent cost runaway (S×L: 20)** — Wire model tiers into `agent_factory.py` on Day 1. Ministries get cheapest model; orchestrator + parties get mid-tier. Add `MAX_TOKENS_PER_SESSION` cap and per-session token logging. Cache ministry responses by `(topic_hash, ministry_id)`.
3. **Context-window blow-out from growing transcript (S×L: 20)** — Design transcript as structured `Utterance` objects from the first line of orchestrator code. Enforce 8K token budget per agent call. Each party in reading 2 receives: its own SKILL.md metadata only + ministry summaries truncated to 200 tokens each + last 2 utterances per opposing party.
4. **Scope-creep trap: "almost works on Day 4" (S×L: 16)** — Establish explicit Day 3 EOD cut criteria. If CLI E2E is not passing: (1) cut Next.js entirely, (2) cut 19 to 7 ministries, (3) cut second reading.
5. **Hermes Agent API underdocumented — multi-agent breaks on Day 3 (S×L: 16)** — Day 1 spike must test tool failure explicitly (bad query to PageIndex; verify Hermes surfaces error vs. hallucinating). Write `test_agent_memory_isolation.py` on Day 1.

---

## Critical Day-1 Spike Gates

**All four researchers agree: do not write a single party skill or ministry template until all of these gates are green.** If any gate fails, pivot immediately — do not attempt to fix the underlying issue under a 5-day deadline.

| Gate | Command / Test | Pass Criteria | Fail Action |
|---|---|---|---|
| **G-1: Hermes import** | `python -c "from run_agent import AIAgent; print('ok')"` in fresh venv after `pip install hermes-agent==0.14.0` | Prints "ok", no ImportError | Check if install path differs; read pyproject.toml entry_points |
| **G-2: AIAgent single-agent run** | Instantiate `AIAgent` with one MCP tool; call `run_conversation()` with a simple question | Response received, no crash | Debug Hermes API surface; check `tools/delegate_tool.py` source |
| **G-3: delegate_task fan-out** | Call `delegate_task(tasks=[{...}, {...}])` with 2 dummy tasks; assert both results returned | 2 results, parallel completion | If delegate_task is broken, escalate immediately — this is load-bearing |
| **G-4: PageIndex Cloud MCP** | Add `pageindex-mcp` to `~/.hermes/config.yaml`; call `doc_search("konstytucja")` via Hermes tool dispatch | Returns at least 1 non-empty result with a node_id | Re-check API key; verify Node >=20.8.1 |
| **G-5: Polish diacritics in corpus** | Upload the Constitution PDF via PageIndex Cloud API; call `fetch_node` on root; verify diacritics present in output | Character hit rate >90% (spot-check ą ę ó ź ż ś ń ć ł) | Contact PageIndex support; check encoding in API response |
| **G-6: skills-ref validate** | Write `skills/party-ko/SKILL.md` with ASCII-only `name` field; run `npx skills-ref@0.1.5 validate ./skills/party-ko` | Exits 0, no schema errors | Fix canonical template before writing any other skills |
| **G-7: concurrent MCP queries** | Fire 3 simultaneous `doc_search` calls via Hermes; observe responses | All 3 return results, no timeout or connection error | Serialize ministry calls (adds latency but stays in 5-min budget) |

These gates should take roughly half of Day 1 morning (15-30 min each). The afternoon is for `agent_factory.py` skeleton and the first party skill.

---

## Implications for Roadmap

### Phase 1: Foundation and Smoke Tests (Day 1 — 2026-05-26)

**Rationale:** Both new APIs (Hermes, PageIndex) must be de-risked before any content work begins. This is the most unanimous finding across all 4 research files.

**Delivers:**
- All 7 Day-1 gates green
- `agent_factory.py` skeleton (SKILL.md to AIAgent mapping)
- `party-ko` SKILL.md validated with `skills-ref@0.1.5`
- Pre-commit hook: `skills-ref validate` on every commit
- `Makefile` with `make setup` and `make demo` targets
- `.env.example` with all required env vars
- `MIT LICENSE` file committed
- Background ingest started for Constitution + KK + KC + KP via PageIndex Cloud API
- Model tier config in `agent_factory.py` (not Day 4)
- Token logging from first agent call

**Avoids:** Pitfall 1 (OCR), Pitfall 2 (cost), Pitfall 4 (Hermes API), Pitfall 5 (skills validation), Pitfall 17 (LICENSE)

**Research flag:** Needs live verification — do not assume `from run_agent import AIAgent` works until tested.

### Phase 2: Agent Content (Days 2-3 — 2026-05-27 to 2026-05-28)

**Rationale:** Party skills are the template for ministry skills. Build one party end-to-end (party-ko debates a topic with real PageIndex citations) before scaling. 19 ministry skills are content work, not code — they share one template. Party divergence must be tested explicitly before the orchestrator is built.

**Delivers:**
- 5 party skills with distinct red lines, attack vectors, and default vote stances
- 19 ministry skills from shared template (7 core + 12 extended)
- `doc_registry.py` — agent_id to PageIndex metadata filter mapping
- Party divergence test: "400+ benefit" topic, assert KO and Konfederacja on opposite sides
- Ethics review of Konfederacja profile (hard gate before Phase 3)
- `## Output Constraints` section in every SKILL.md (no real MP names, no slurs, `(orig. PL: "...")` format)
- `test_agent_memory_isolation.py` passes

**Cut criteria:** If 19 ministries are not done by Day 3 EOD, cut to 7 (Finance, Health, Justice, Education, Climate, Infrastructure, Foreign Affairs).

**Avoids:** Pitfall 7 (party convergence), Pitfall 8 (MP impersonation), Pitfall 12 (hate speech), Pitfall 13 (PL/EN mixing)

### Phase 3: Orchestrator and CLI E2E (Day 4 — 2026-05-29)

**Rationale:** Orchestrator is the most complex single component and depends on all agents from Phase 2. The CLI is the demo fallback if Next.js slips. Full E2E on 3 topics must pass by Day 4 EOD.

**Delivers:**
- `parliament/orchestrator.py` — state machine: `INIT -> CONSULTING -> READING_1 -> READING_2 -> VOTING -> CLOSED`
- `marszalek-sejmu` SKILL.md — includes `delegate_task` fan-out instructions
- `parliament/session.py` — SQLite writes, structured `Utterance` objects (not string concat)
- `parliament/cli.py` — `hermes parliament "<topic>"` and `--minister` mode
- Full E2E session on 3 topics: vote result politically coherent, citations have real node_ids, session completes in <=5 minutes
- `rich` progress display: `[1/4] Consulting ministries...`
- `citation_validator.py` — verifies every node_id in transcript resolves
- `MAX_ROUNDS = 2`, `session_timeout_seconds = 300` hard limits
- Golden-run cache recorded before Day 4 ends (for demo video)
- FastAPI + SSE endpoint (`parliament/api.py`) — wrapping the same `run_session()` generator

**Cut criteria at Day 3 EOD:** If CLI E2E not passing with full 5-party debate: (1) cut Next.js, (2) cut 19->7 ministries, (3) cut second reading.

**Avoids:** Pitfall 3 (context blow-out), Pitfall 6 (debate loop), Pitfall 9 (rate limit), Pitfall 11 (scope creep), Pitfall 19 (legal hallucination)

**Research flag:** `delegate_task` exact API surface must be verified from Hermes source during Phase 1 smoke test, before Phase 3 orchestrator code is written.

### Phase 4: Web Front and Demo Prep (Day 5 — 2026-05-30)

**Rationale:** Web is the highest schedule risk item. Day 5 is the right placement — if it slips, deadline day is for submission only, not new code.

**Delivers:**
- Next.js 16.2.6 chamber visualization — hemicycle SVG + party-coloured transcript stream fed by `EventSource`
- Demo video recorded on Day 5 (NOT deadline day) using golden-run cache
- DEV.to post drafted with all 5 required sections
- Clean-clone test: `make demo` from a clean clone in under 5 minutes
- Markdown export (`--export markdown`) working

**Fallback if Next.js is not ready by Day 5 noon:** Replace with a static HTML + JavaScript transcript viewer reading the JSON export (2-hour task vs. 2-day task).

**Avoids:** Pitfall 9 (rate limit on demo day), Pitfall 15 (reproducibility), Pitfall 16 (video > 3 min)

**Research flag:** Next.js 16.2.6 is a major version jump. Use Context7 for App Router + SSE Route Handler patterns during implementation — do not rely on training-data Next.js patterns.

### Phase 5: Deadline Day (2026-05-31)

**Rationale:** No new code. Submission work only.

**Delivers:**
- Full 50-doc corpus ingested and verified
- E2E test on 3 topics (pass)
- README finalized
- Demo video published
- DEV.to post submitted with correct tags: `hermesagentchallenge`, `devchallenge`, `agents`
- GitHub repo public, MIT LICENSE visible

### Phase Ordering Rationale

- Phase 1 before everything because both core APIs are new. The ARCHITECTURE.md was written before STACK research and contains one architectural error as a result. Day-1 gates catch further surprises before they propagate.
- Phase 2 before Phase 3 because party skill quality determines whether the orchestrator is testing orchestration or testing ideology writing. Divergence tests on party skills require no orchestrator.
- Phase 3 before Phase 4 because CLI is the demo fallback and the SSE endpoint is trivial once `run_session()` is a working generator.
- Phase 4 is intentionally the last buildable day, leaving Phase 5 as a clean submission day.

### Research Flags

Phases needing deeper research during planning:
- **Phase 1 (Hermes API):** `delegate_task` parameter names, `AIAgent` constructor signature, `memory_namespace` param — verify against `tools/delegate_tool.py` and `run_agent.py` source on Day 1
- **Phase 4 (Next.js 16.2.6):** Major version jump. Use Context7 `resolve-library-id` + `query-docs` for App Router SSE Route Handler patterns before writing any Next.js code

Phases with well-documented patterns (no research phase needed):
- **SQLite schema design** — standard; ADR-5 in ARCHITECTURE.md is correct and HIGH confidence
- **typer CLI** — standard; no surprises expected
- **FastAPI SSE** — standard pattern; ARCHITECTURE ADR-4 is correct
- **skills-ref validate** — STACK.md verified against live npm registry

---

## Top 5 Risks

| Rank | Risk | Mitigation | Phase |
|---|---|---|---|
| 1 | **Hermes `delegate_task` API differs from documentation** — entire ministry fan-out depends on it | Read `tools/delegate_tool.py` source on Day 1; add to Gate G-3 | Phase 1 |
| 2 | **25-agent cost runaway** — 33-49 LLM calls per session at strong-model pricing = $5-20/session | Wire model tiers Day 1; `MAX_TOKENS_PER_SESSION` cap; cache ministry responses | Phase 1-2 |
| 3 | **Context-window blow-out** — naive transcript concatenation fails in round 2 | Structured `Utterance` objects from first line; 8K token budget in `agent_factory.py` | Phase 2-3 |
| 4 | **Next.js 16.2.6 App Router integration** — major version, SSE pattern may differ from older docs in training data | Use Context7 for Next.js 16 docs; build SSE Route Handler before chamber visualization | Phase 4 |
| 5 | **Scope creep / "almost works" trap** — contest psychology makes cutting features feel like failure | Hard cut criteria at Day 3 23:00; prioritized cut list defined in advance | Phase 3 |

Note: Pitfall 1 (OCR failure, originally S×L: 25) is effectively resolved by switching to PageIndex Cloud as primary. It does not appear in the top 5 because the STACK research already eliminated it.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All critical components verified against live repos, PyPI, npm registries on 2026-05-26. Version numbers, import paths, and API patterns are authoritative. |
| Features | MEDIUM | Web search was blocked during FEATURES research. Analysis derived from PRD §5, PROJECT.md, and training knowledge of comparable agent simulation projects. Feature priorities are well-reasoned but not externally validated. |
| Architecture | MEDIUM | Written before STACK research completed. One architectural error (asyncio fan-out) has been corrected. Remaining patterns (state machine, SSE generator, SQLite) are well-established and HIGH confidence. Hermes-specific API surface (memory_namespace param name, MCP attachment API) remains MEDIUM until Day-1 spike. |
| Pitfalls | MEDIUM | Web tools were unavailable. Analysis derives from architectural reasoning and training knowledge. The top pitfalls are independently consistent with STACK findings. Confidence is HIGH for risk categories, MEDIUM for exact mitigation steps that depend on Hermes internal behaviour. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address During Implementation

- **`delegate_task` exact API surface** — parameter names, batching behaviour, error propagation. Read `NousResearch/hermes-agent/tools/delegate_tool.py` source on Day 1 before writing any orchestrator code.
- **Hermes `memory_namespace` parameter** — ARCHITECTURE assumes this parameter exists. Verify against `run_agent.py` constructor on Day 1. If absent, implement memory scoping via `ephemeral_system_prompt` with session ID.
- **PageIndex Cloud rate limits** — free tier (1000 pages) should cover ~50 statutes but actual rate limits on concurrent queries are not documented. Test concurrent connections (Gate G-7) before committing to parallel ministry consultations.
- **Next.js 16.2.6 SSE Route Handler pattern** — training data may not reflect this version. Use Context7 during Phase 4 implementation.
- **`metadata` custom fields in skills-ref validate** — PRD uses `seats: 157` in frontmatter metadata. PITFALLS notes this may cause validation failure if the spec uses `additionalProperties: false`. Verify during Gate G-6 (first SKILL.md validation).

---

## Sources

### Primary (HIGH confidence — live-verified 2026-05-26)

- `github.com/NousResearch/hermes-agent` — `pyproject.toml`, `run_agent.py`, `tools/delegate_tool.py`, `tools/mcp_tool.py`
- PyPI registry — `hermes-agent@0.14.0`, `pymupdf@1.27.2.3`, `surya-ocr@0.17.1`, `typer@0.25.1`, `mcp@1.27.1`, `litellm@1.83.7`
- npm registry — `skills-ref@0.1.5`, `skills@1.5.7`, `pageindex-mcp@1.6.3`, `next@16.2.6`
- `agentskills.io/specification` — frontmatter schema, directory structure
- `github.com/VectifyAI/PageIndex` — `requirements.txt`, `pageindex/utils.py`
- `github.com/mmtmr/pageindex-rag` — skill exists, install command confirmed

### Secondary (MEDIUM confidence)

- PRD §5-9 and PROJECT.md — project requirements, constraints, key decisions
- Training knowledge: Python asyncio multi-agent patterns, FastAPI SSE, SQLite WAL mode, Polish ISAP PDF OCR failure modes, DEV.to Build challenge patterns, AI Simulacra / AI Town / AutoGen comparables

### Tertiary (LOW confidence — web access was blocked)

- DEV.to Hermes Agent Challenge specific judging weights — inferred from contest description; not independently verified
- PageIndex Cloud rate limits and SLA — not documented in accessible sources; test on Day 1

---

*Research completed: 2026-05-26*
*Ready for roadmap: yes*
*Critical blocker: all Day-1 gates must pass before Phase 2 work begins*

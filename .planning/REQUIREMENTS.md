# Virtual Parliament — Requirements

**Version:** v1 (contest submission)
**Deadline:** 2026-05-31 23:59 PDT
**Created:** 2026-05-26
**Status:** Roadmap mapped — 64 requirements across 5 phases

This document is the authoritative scope for the Hermes Agent Challenge submission. Every Active requirement here must map to exactly one roadmap phase. Out of Scope items are deliberately excluded; re-adding requires explicit discussion.

---

## v1 Requirements

### GATE — Day-1 Spike Gates

All 7 gates must pass before scaling to 25 agents. Unanimous recommendation from STACK/FEATURES/ARCHITECTURE/PITFALLS research.

- [ ] **GATE-01**: `from run_agent import AIAgent` works in a fresh Python 3.11 venv after `pip install hermes-agent==0.14.0`
- [ ] **GATE-02**: `AIAgent.run_conversation()` instantiated with a minimal SKILL.md returns a non-empty response
- [ ] **GATE-03**: `delegate_task(tasks=[task1, task2])` executes 2 dummy tasks in parallel and returns both results
- [ ] **GATE-04**: PageIndex Cloud MCP server attached to a Hermes Agent; `doc_search("konstytucja")` returns a `node_id` via Hermes tool dispatch
- [ ] **GATE-05**: Polish diacritics fidelity — Constitution PDF uploaded to PageIndex Cloud, `fetch_node` output contains `ą ę ó ź ż ś ń ć ł` at ≥ 90% expected occurrences
- [ ] **GATE-06**: `npx skills-ref@0.1.5 validate skills/party-ko` exits 0 on a minimal SKILL.md
- [ ] **GATE-07**: 3 simultaneous `doc_search` calls from one Hermes session complete without timeout or rate-limit error

### INFRA — Foundation

- [ ] **INFRA-01**: Public GitHub repo with MIT LICENSE committed at root
- [ ] **INFRA-02**: `pyproject.toml` pinning `hermes-agent==0.14.0`, Python 3.11+, typer, rich, fastapi, uvicorn, sqlite (stdlib)
- [ ] **INFRA-03**: `npx skills-ref validate skills/` runs in pre-commit hook and CI; commit fails if any skill is invalid
- [ ] **INFRA-04**: `agent_factory.py` creates a Hermes `AIAgent` from any `skills/<id>/` folder with explicit model-tier config (orchestrator/parties → stronger model; ministries → cheaper model)
- [ ] **INFRA-05**: SQLite schema for sessions (`sessions/`, `utterances`, `votes`, `bill_drafts`) with WAL mode for concurrent reads
- [ ] **INFRA-06**: Project-level "kill switch" — every LLM call goes through a single token-budget guard that aborts a session if cumulative cost crosses a configurable cap

### BRAIN — Second Brain (PageIndex)

- [ ] **BRAIN-01**: PageIndex Cloud account provisioned; MCP server credentials stored in `.env` (gitignored); `pageindex-mcp` configured in Hermes
- [ ] **BRAIN-02**: `mmtmr/pageindex-rag` skill installed via `npx skills add mmtmr/pageindex-rag -g -y` and loaded by every agent that consults the brain
- [ ] **BRAIN-03**: Ingest 4 core legal documents — Konstytucja RP, Kodeks Karny, Kodeks Cywilny, Kodeks Pracy — verified via `tree_search`
- [ ] **BRAIN-04**: Ingest ~46 additional statutes/regulations curated to cover typical debate topics (OZE, podatki, ochrona zdrowia, edukacja, klimat, cyfryzacja, etc.) — ~50 docs total
- [ ] **BRAIN-05**: `doc_registry.py` maps `agent_id → {ministry, categories, doc_ids}`; every `doc_search` call injects metadata filters so each ministry sees only relevant documents
- [ ] **BRAIN-06**: PageIndex Cloud free-tier page-budget verified to cover the curated corpus (≤ 1000 pages); fall-back plan documented if budget exceeded

### SKILL — Agent Skills Format

- [ ] **SKILL-01**: All 25 agents packaged as `skills/<lowercase-hyphen-id>/SKILL.md` per [agentskills.io/specification](https://agentskills.io/specification)
- [ ] **SKILL-02**: Each skill has the required YAML frontmatter (`name`, `description`) and a body following the structure: Identity / Red lines / Style / Decision process / Sources
- [ ] **SKILL-03**: Ministry skills derive from a single shared template (`skills/_template-ministry/`) so the 19 deltas are content, not structure

### PARTY — Party Agents (5)

- [ ] **PARTY-01**: Five party skills — `party-ko`, `party-pis`, `party-td`, `party-konfederacja`, `party-lewica` — each with ideological profile, electorate notes, historical-positions reference, and rhetorical style notes
- [ ] **PARTY-02**: Each party SKILL.md frontmatter carries `metadata.seats` (KO 157, PiS 194, TD 65, Konfederacja 18, Lewica 26) used by vote-tally logic
- [ ] **PARTY-03**: Each party profile reviewed by ≥ 2 people from different political sides before its first commit on `main`
- [ ] **PARTY-04**: Rhetorical profiles produce visibly different language across parties (verified by running the same prompt across all 5 and diffing output style)
- [ ] **PARTY-05**: Hate-speech guardrails enforced in every party SKILL.md ("Never advocate violence, never dehumanize, never name real MPs")

### MINISTRY — Ministry Agents (19)

- [ ] **MIN-01**: Nineteen ministry skills — finansow, zdrowia, edukacji, sprawiedliwosci, obrony-narodowej, spraw-zagranicznych, klimatu-i-srodowiska, infrastruktury, rozwoju-i-technologii, rolnictwa, rodziny-pracy-i-polityki-spolecznej, cyfryzacji, kultury-i-dziedzictwa-narodowego, nauki-i-szkolnictwa-wyzszego, energii, spraw-wewnetrznych-i-administracji, aktywow-panstwowych, funduszy-i-polityki-regionalnej, sportu-i-turystyki
- [ ] **MIN-02**: All ministries share an expertise output format — `1. Legal analysis (with PageIndex citations) / 2. Budget impact / 3. Risks / 4. Technical recommendation`
- [ ] **MIN-03**: Each ministry's `doc_registry` entry restricts `doc_search` to documents tagged with its domain (no Finance ministry citing the Health regulation index)
- [ ] **MIN-04**: Ministries are stateless experts — no long-term memory, no ideology in prompts ("You have data, not opinions")

### ORCH — Marszałek Orchestrator

- [ ] **ORCH-01**: One `marszalek-sejmu` skill exists and is the only agent allowed to call `delegate_task`
- [ ] **ORCH-02**: Ministry selection — Marszałek classifies the topic and picks 2–3 most relevant ministries; selection is deterministic given the same topic and corpus
- [ ] **ORCH-03**: Ministry consultation runs via `delegate_task(tasks=[...])` (Hermes-native, not custom asyncio); 3 parallel ministries complete in ≤ 30 s wall-clock
- [ ] **ORCH-04**: First reading — each of the 5 parties speaks once, sequentially, in declared order; each speech cites ≥ 1 PageIndex node
- [ ] **ORCH-05**: Second reading — each party may amend its position or rebut another party; ≥ 1 cross-reference per second-reading turn
- [ ] **ORCH-06**: Vote tally — each party's FOR/AGAINST/ABSTAIN is weighted by seat count; final result computed and printed as a markdown table
- [ ] **ORCH-07**: Draft bill output — orchestrator synthesizes an article-by-article bill draft after the vote, using a template stored in `skills/marszalek-sejmu/assets/bill-draft-template.md`
- [ ] **ORCH-08**: `[MARSZAŁEK REASONING]` blocks appear in the transcript at every routing/selection decision (visible Hermes multi-step reasoning)
- [ ] **ORCH-09**: Vote-direction sanity guardrail — orchestrator rejects an obviously incoherent outcome (e.g., KO + Konfederacja both voting FOR on a tax-hike topic) and prompts re-deliberation

### CLI — Command-Line Surface

- [ ] **CLI-01**: `hermes parliament "<topic>"` runs a full session end-to-end in ≤ 5 minutes on a $5/month-class VPS
- [ ] **CLI-02**: `hermes parliament --minister <domain> "<question>"` runs a single ministry in isolation (validation path + journalist persona)
- [ ] **CLI-03**: `hermes parliament ... --export markdown <file>` writes the session transcript to disk
- [ ] **CLI-04**: `rich` progress bar shows phase labels (`Consulting ministries`, `First reading`, `Second reading`, `Voting`, `Drafting bill`) with parallelism count where applicable
- [ ] **CLI-05**: First run from a clean clone — `pip install -e . && hermes parliament "test"` — succeeds in ≤ 2 minutes per jury DoD

### WEB — Next.js Chamber Visualization

- [ ] **WEB-01**: Next.js 16.2.6 App Router project at `web/` with a Route Handler exposing SSE that consumes the same orchestrator async generator the CLI uses (zero pipeline duplication)
- [ ] **WEB-02**: Hemicycle seating layout with 5 party blocs sized to seat counts; party colors loaded from a shared `config/parties.json` (also used by CLI ANSI colors)
- [ ] **WEB-03**: Live-highlighted speaker + party-colored transcript stream during a running session
- [ ] **WEB-04**: Static fallback — if SSE/web work is blocked on Day 4 EOD per the cut criteria, ship a static hemicycle PNG in the README and demo CLI only

### EXPORT — Output Artifacts

- [ ] **EXPORT-01**: Markdown transcript export with session header (topic, timestamp, agents consulted), full ordered utterances, vote tally table, and draft bill section

### ETHICS — Ethical Floor

- [ ] **ETHICS-01**: Educational disclaimer ("This is an educational simulation, not a political forecast or endorsement") rendered at the top and bottom of every session output and on every CLI/web surface
- [ ] **ETHICS-02**: No real MPs named anywhere — enforced via guardrail prompt in every party/ministry SKILL.md and verified by a regex check in the test suite
- [ ] **ETHICS-03**: Hate-speech refusal — every agent refuses to generate content that dehumanizes, advocates violence, or targets protected groups
- [ ] **ETHICS-04**: Party profiles framed from the party's *own* electorate's perspective, not caricatured (verified in PARTY-03 bias review)

### LANG — Language Discipline

- [ ] **LANG-01**: All debate text, transcript, CLI output, and web UI is in English
- [ ] **LANG-02**: Every citation preserves the original Polish quote with the notation `(orig. PL: "…")` so a Polish reader can verify fidelity
- [ ] **LANG-03**: Agents quote PageIndex `node_id` references verbatim (never paraphrase) and translate the surrounding analysis to English

### DEMO — Submission DoD

- [ ] **DEMO-01**: Public GitHub repo with MIT LICENSE, working README, and a single-command run path
- [ ] **DEMO-02**: README contains: 30-second pitch, install steps, "Try it" command, architecture diagram (`5 parties + 19 ministries + Marszałek + PageIndex`), credits
- [ ] **DEMO-03**: 3-minute demo video recorded following the segment plan in research/FEATURES.md (Hook → Ministry expertise → Party debate → Vote → `--minister` quick demo → Architecture → Closing)
- [ ] **DEMO-04**: DEV.to post published with required sections: What I Built / Demo / Code / Tech Stack / How I Used Hermes Agent / License
- [ ] **DEMO-05**: System verified on ≥ 3 distinct bill topics (e.g., "4-day work week", "OZE expansion", "tax simplification") with reasonable outputs
- [ ] **DEMO-06**: DEV.to post tagged `hermesagentchallenge, devchallenge, agents`
- [ ] **DEMO-07**: Submission published before 2026-05-31 23:59 PDT

---

## v2 Requirements (Stretch — Add If Time Allows on Day 4–5)

- [ ] **STR-01**: Party long-term memory — Hermes memory API records how each party voted on past topics and influences current session (spike planned for Day 1 alongside GATE-02; ship Day 4 if spike clean)
- [ ] **STR-02**: PDF export (`--export pdf`) using weasyprint, only if EXPORT-01 markdown export is rock-solid
- [ ] **STR-03**: Reasoning trace surfaced in web UI (not just CLI transcript) — chamber view shows `[MARSZAŁEK REASONING]` as a side-panel
- [ ] **STR-04**: Self-host PageIndex variant — replace PageIndex Cloud with self-hosted instance, post-contest

---

## Out of Scope (v2+) — With Reasoning

- **6th party / non-affiliated faction** — 5 parties already cover full ideological spread; one more skill is +1 day of writing for negligible value in a Polish Sejm context
- **Real MP names and quotes** — defamation risk, contest rules violation, ethics floor breach
- **Voice / TTS** — 5-day timeline cannot absorb TTS integration + latency + audio sync work; adds no analytical value
- **Real-time political forecasting** — misleads users about system capability; requires polling data and calibration we cannot do honestly
- **Full ISAP corpus (thousands of statutes)** — OCR + ingest would consume the whole deadline; ~50 curated docs cover 95% of plausible topics
- **Streaming token output to CLI during 25-agent turns** — race conditions and display complexity for cosmetic gain; batch-per-turn with spinner is richer UX
- **Session share URL** — requires hosted infra + accounts + routing; markdown export + gist achieves the goal with zero overhead
- **Polish-language runtime UI** — DEV.to jury is international; Polish-only output prevents quality evaluation
- **Per-MP voting model** — 460 MPs requires a different architecture; party-bloc voting with seat weights is more analytically honest and matches PRD scope
- **Custom LLM fine-tuning** — weeks of work, not days; Hermes ships usable defaults; prompt engineering + RAG + long-term memory achieves political consistency
- **RSS news ingest** — fragile pipeline, negligible demo value, adds freshness/reliability risk
- **`policz-skutek.py` budget calculator** — implies real fiscal modelling we cannot deliver; ministries cite figures from PageIndex, they don't calculate
- **Self-hosted PageIndex in MVP** — Tesseract Polish OCR on a $5 VPS is a known failure mode; PageIndex Cloud free tier (1000 pages, Polish OCR included) is the correct contest-day choice
- **Custom asyncio fan-out for ministries** — Hermes Agent has native `delegate_task(tasks=[...])` with ThreadPoolExecutor; building a parallel asyncio implementation duplicates Hermes work and deadlocks on the same shared LLM client
- **Streamlit web variant** — Next.js 16.2.6 was chosen; Streamlit is excluded to prevent split focus

---

## Traceability — Requirement → Phase

Populated by `gsd-roadmapper` on 2026-05-26. 64 v1 requirements mapped across 5 phases.

| REQ-ID | Phase | Status |
|--------|-------|--------|
| GATE-01 | Phase 1 | Pending |
| GATE-02 | Phase 1 | Pending |
| GATE-03 | Phase 1 | Pending |
| GATE-04 | Phase 1 | Pending |
| GATE-05 | Phase 1 | Pending |
| GATE-06 | Phase 1 | Pending |
| GATE-07 | Phase 1 | Pending |
| INFRA-01 | Phase 1 | Pending |
| INFRA-02 | Phase 1 | Pending |
| INFRA-03 | Phase 1 | Pending |
| BRAIN-01 | Phase 1 | Pending |
| BRAIN-02 | Phase 1 | Pending |
| BRAIN-06 | Phase 1 | Pending |
| SKILL-01 | Phase 2 | Pending |
| SKILL-02 | Phase 2 | Pending |
| SKILL-03 | Phase 2 | Pending |
| PARTY-01 | Phase 2 | Pending |
| PARTY-02 | Phase 2 | Pending |
| PARTY-03 | Phase 2 | Pending |
| PARTY-04 | Phase 2 | Pending |
| PARTY-05 | Phase 2 | Pending |
| MIN-01 | Phase 2 | Pending |
| MIN-02 | Phase 2 | Pending |
| MIN-03 | Phase 2 | Pending |
| MIN-04 | Phase 2 | Pending |
| BRAIN-03 | Phase 2 | Pending |
| BRAIN-04 | Phase 2 | Pending |
| BRAIN-05 | Phase 2 | Pending |
| ETHICS-02 | Phase 2 | Pending |
| ETHICS-03 | Phase 2 | Pending |
| ETHICS-04 | Phase 2 | Pending |
| LANG-01 | Phase 2 | Pending |
| LANG-02 | Phase 2 | Pending |
| LANG-03 | Phase 2 | Pending |
| INFRA-04 | Phase 3 | Pending |
| INFRA-05 | Phase 3 | Pending |
| INFRA-06 | Phase 3 | Pending |
| ORCH-01 | Phase 3 | Pending |
| ORCH-02 | Phase 3 | Pending |
| ORCH-03 | Phase 3 | Pending |
| ORCH-04 | Phase 3 | Pending |
| ORCH-05 | Phase 3 | Pending |
| ORCH-06 | Phase 3 | Pending |
| ORCH-07 | Phase 3 | Pending |
| ORCH-08 | Phase 3 | Pending |
| ORCH-09 | Phase 3 | Pending |
| CLI-01 | Phase 3 | Pending |
| CLI-02 | Phase 3 | Pending |
| CLI-03 | Phase 3 | Pending |
| CLI-04 | Phase 3 | Pending |
| CLI-05 | Phase 3 | Pending |
| EXPORT-01 | Phase 3 | Pending |
| ETHICS-01 | Phase 3 | Pending |
| WEB-01 | Phase 4 | Pending |
| WEB-02 | Phase 4 | Pending |
| WEB-03 | Phase 4 | Pending |
| WEB-04 | Phase 4 | Pending |
| DEMO-01 | Phase 5 | Pending |
| DEMO-02 | Phase 5 | Pending |
| DEMO-03 | Phase 5 | Pending |
| DEMO-04 | Phase 5 | Pending |
| DEMO-05 | Phase 5 | Pending |
| DEMO-06 | Phase 5 | Pending |
| DEMO-07 | Phase 5 | Pending |

---

*Last updated: 2026-05-26 — traceability populated by gsd-roadmapper. Source documents: PROJECT.md, research/SUMMARY.md, research/FEATURES.md, research/STACK.md, research/ARCHITECTURE.md, research/PITFALLS.md, prd.md.*

# Roadmap: Virtual Parliament

## Overview

Five calendar days from today (2026-05-26) to a contest deadline (2026-05-31 23:59 PDT). The roadmap front-loads risk: Phase 1 is entirely a de-risking exercise — both new APIs (Hermes Agent, PageIndex Cloud) must prove themselves before a single party skill is written. Phase 2 is the content sprint that produces all 25 agent skills and completes the corpus. Phase 3 wires everything into a working CLI end-to-end. Phase 4 adds the web chamber visualization (highest schedule risk, explicit cut criteria). Phase 5 is submission day — no new code.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation & Smoke Tests** - De-risk both new APIs, scaffold the repo, start corpus ingest (Day 1 — 2026-05-26)
- [ ] **Phase 2: Agent Skills & Corpus** - Write all 25 SKILL.md files, complete corpus, ethics review (Days 2–3 — 2026-05-27 to 2026-05-28)
- [ ] **Phase 3: Orchestrator & CLI** - Build orchestrator state machine, wire CLI, validate E2E on 3 topics (Day 4 — 2026-05-29)
- [ ] **Phase 4: Web & Demo Prep** - Next.js chamber visualization, golden-run cache, DEV.to draft (Day 5 — 2026-05-30)
- [ ] **Phase 5: Submission Day** - Full corpus verified, README finalized, demo video published, DEV.to post submitted (Day 6 — 2026-05-31)

## Phase Details

### Phase 1: Foundation & Smoke Tests
**Goal**: Both new APIs are proven to work in this exact project context — Hermes Agent runs agents with MCP tool use, PageIndex Cloud returns Polish diacritics correctly, and the repo scaffold is in place with cost and quality guards wired in from minute one
**Target end**: 2026-05-26 (Day 1)
**Depends on**: Nothing (first phase)
**Requirements**: GATE-01, GATE-02, GATE-03, GATE-04, GATE-05, GATE-06, GATE-07, INFRA-01, INFRA-02, INFRA-03, BRAIN-01, BRAIN-02, BRAIN-06
**Success Criteria** (what must be TRUE):
  1. Running `python -c "from run_agent import AIAgent; print('ok')"` in a fresh Python 3.11 venv after `pip install hermes-agent==0.14.0` prints "ok" — no ImportError
  2. A Hermes Agent with the PageIndex Cloud MCP server attached returns a non-empty `node_id` in response to `doc_search("konstytucja")`, and a `fetch_node` on the Constitution root contains `ą ę ó ź ż ś ń ć ł` at ≥ 90% expected occurrences
  3. `delegate_task(tasks=[task1, task2])` with two dummy tasks returns both results without deadlock
  4. `npx skills-ref@0.1.5 validate skills/party-ko` exits 0 on the canonical SKILL.md template (pre-commit hook installed)
  5. The public GitHub repo has MIT LICENSE at root, `.env.example` documents all required env vars, and `make setup && make demo` targets exist
**Plans**: TBD

### Phase 2: Agent Skills & Corpus
**Goal**: All 25 agents are written, validated, and ideologically differentiated; the full curated corpus (~50 docs) is ingested and scoped per-ministry; ethics review is complete; agents output English with Polish citations in `(orig. PL: "...")` format
**Target end**: 2026-05-28 (Day 3)
**Depends on**: Phase 1
**Requirements**: SKILL-01, SKILL-02, SKILL-03, PARTY-01, PARTY-02, PARTY-03, PARTY-04, PARTY-05, MIN-01, MIN-02, MIN-03, MIN-04, BRAIN-03, BRAIN-04, BRAIN-05, ETHICS-02, ETHICS-03, ETHICS-04, LANG-01, LANG-02, LANG-03
**Success Criteria** (what must be TRUE):
  1. `npx skills-ref@0.1.5 validate skills/` exits 0 for all 25 skill folders (no schema errors, no ASCII violations in frontmatter)
  2. Running the same "4-day work week" prompt through `party-ko` and `party-konfederacja` in isolation produces visibly opposing positions — KO argues social policy benefits, Konfederacja argues market/economic objections — with ≥ 1 cited PageIndex `node_id` per response
  3. Every ministry skill's `doc_search` call only returns documents tagged with that ministry's domain — Finance does not cite health regulations; tested via `doc_registry.py` assertions
  4. All 50 corpus documents are ingested; `tree_search("Konstytucja")` and `tree_search("Kodeks Karny")` each return nodes with valid Polish diacritics
  5. The Konfederacja SKILL.md has been reviewed by ≥ 2 people from different political perspectives and every party/ministry SKILL.md has an `## Output Constraints` section prohibiting real MP names and slurs
**Plans**: TBD
**Cut criteria (Day 3 EOD)**: If 19 ministries are not complete, cut to 7 (Finance, Health, Justice, Education, Climate, Infrastructure, Foreign Affairs). If party divergence test fails, do not proceed to Phase 3.

### Phase 3: Orchestrator & CLI
**Goal**: A single command — `hermes parliament "<topic>"` — runs a full, source-cited, politically coherent Polish parliament simulation end-to-end in ≤ 5 minutes, with `rich` progress display, markdown export, and a FastAPI SSE endpoint ready for the web phase
**Target end**: 2026-05-29 (Day 4)
**Depends on**: Phase 2
**Requirements**: INFRA-04, INFRA-05, INFRA-06, ORCH-01, ORCH-02, ORCH-03, ORCH-04, ORCH-05, ORCH-06, ORCH-07, ORCH-08, ORCH-09, CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, EXPORT-01, ETHICS-01
**Success Criteria** (what must be TRUE):
  1. `hermes parliament "4-day work week"`, `hermes parliament "OZE expansion"`, and `hermes parliament "tax simplification"` each complete in ≤ 5 minutes with a vote result that is politically coherent (Lewica and Konfederacja are on opposite sides on "4-day work week")
  2. Every utterance in the session transcript carries a `node_id` that resolves via `fetch_node` — `citation_validator.py` reports 0 unresolvable citations
  3. `hermes parliament --minister finanse "ile kosztuje 800+"` returns a structured Finance ministry analysis in isolation in < 60 seconds
  4. `hermes parliament "test" --export markdown output.md` produces a readable Markdown file with session header, ordered utterances, vote tally table, and draft bill section
  5. `[MARSZAŁEK REASONING]` blocks appear in the transcript at every ministry-selection and routing decision; every session output begins with the educational disclaimer
**Plans**: TBD
**Cut criteria (Day 3 23:00)**: If CLI E2E is not passing: (1) cut Phase 4 Next.js entirely, (2) cut to 7 ministries, (3) cut second reading. Do not start Phase 4 with a broken CLI.

### Phase 4: Web & Demo Prep
**Goal**: The Next.js chamber visualization is live and fed by the same SSE pipeline as the CLI; a golden-run transcript is cached for the demo video; the DEV.to post is drafted and ready to publish
**Target end**: 2026-05-30 (Day 5)
**Depends on**: Phase 3
**Requirements**: WEB-01, WEB-02, WEB-03, WEB-04
**Success Criteria** (what must be TRUE):
  1. Opening `http://localhost:3000`, submitting a topic, and watching the chamber shows a hemicycle with 5 party blocs sized to seat counts, a live-highlighted active speaker, and party-colored transcript lines appearing as the session runs — powered by the same `run_session()` generator as the CLI
  2. A clean-clone test (`git clone` → `make setup` → `make demo`) completes without errors in ≤ 5 minutes on a machine that has never run the project before
  3. A golden-run transcript for "4-day work week" is cached to disk and playable; the demo video is recorded on this day (not on May 31)
  4. The DEV.to post draft has all 5 required sections populated (What I Built, Demo, Code, Tech Stack, How I Used Hermes Agent), all 3 required tags present, and is under 3-minute video length confirmed by watching the recording
**Plans**: TBD
**UI hint**: yes
**Cut criteria (Day 5 noon)**: If SSE/Next.js integration is blocked, replace with static hemicycle PNG in README + CLI-only demo. A polished CLI beats a broken web UI every time. WEB-04 is the explicit cut requirement.

### Phase 5: Submission Day
**Goal**: The project is publicly submitted to the Hermes Agent Challenge before the 2026-05-31 23:59 PDT deadline — no new code, only verification, final content, and publishing
**Target end**: 2026-05-31 (Day 6)
**Depends on**: Phase 4
**Requirements**: DEMO-01, DEMO-02, DEMO-03, DEMO-04, DEMO-05, DEMO-06, DEMO-07
**Success Criteria** (what must be TRUE):
  1. The public GitHub repo has MIT LICENSE visible at root, a working README with install steps and a single-command run path, and the architecture diagram showing 5 parties + 19 ministries + Marszałek + PageIndex
  2. `hermes parliament` passes an end-to-end smoke test on ≥ 3 distinct topics with politically reasonable vote outcomes — the jury can clone and run it
  3. The DEV.to post is live with all required sections, tagged `hermesagentchallenge, devchallenge, agents`, with the demo video embedded — published before 2026-05-31 23:59 PDT
**Plans**: TBD

---

## Stretch (If Time Permits — Day 4–5 Only)

These requirements are outside the phase structure. Implement only after Phase 3 CLI is solid and Phase 4 web is not blocked.

- **STR-01**: Party long-term memory — Hermes memory API records past votes and influences current session (spike on Day 1 alongside GATE-02; implement Day 4 if spike is clean)
- **STR-02**: PDF export (`--export pdf`) using weasyprint, only if EXPORT-01 markdown export is rock-solid
- **STR-03**: Hermes reasoning trace surfaced in web UI side-panel (not just CLI transcript)
- **STR-04**: Self-hosted PageIndex variant — replace PageIndex Cloud post-contest

---

## Progress

**Execution Order:**
Phases execute in strict calendar order: 1 (May 26) → 2 (May 27–28) → 3 (May 29) → 4 (May 30) → 5 (May 31)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Smoke Tests | 0/TBD | Not started | - |
| 2. Agent Skills & Corpus | 0/TBD | Not started | - |
| 3. Orchestrator & CLI | 0/TBD | Not started | - |
| 4. Web & Demo Prep | 0/TBD | Not started | - |
| 5. Submission Day | 0/TBD | Not started | - |

---

## Requirement Coverage

All 64 v1 requirements mapped across 5 phases.

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

*Last updated: 2026-05-26 — roadmap created by gsd-roadmapper*

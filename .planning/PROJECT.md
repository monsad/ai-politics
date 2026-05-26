# Virtual Parliament

## What This Is

Virtual Parliament is a multi-agent simulation of the Polish Sejm. Five party agents (KO, PiS, TD, Konfederacja, Lewica), nineteen ministry-expert agents, and a Marszałek orchestrator debate, consult, and vote on user-submitted bills. A Second Brain (PageIndex) holds the Polish Constitution, criminal/civil codes, ~50 statutes and EU regulations so every argument cites a real legal source. It is a competition entry for the [Hermes Agent Challenge](https://dev.to/devteam/join-the-hermes-agent-challenge-1000-in-prizes-13cd) targeting journalists, law/political-science students, hobbyist voters, and the contest jury.

## Core Value

Type in a bill topic → get a full, source-cited parliamentary simulation (ministry expertise → party debate → vote → draft bill) in ≤ 5 minutes, with every argument traceable to a real Polish legal document.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] **REQ-RUN**: User runs the system end-to-end on a single bill topic via a `hermes parliament "<topic>"` CLI in ≤ 5 minutes
- [ ] **REQ-BRAIN**: Second Brain ingests Constitution + KK + KC + KP + ~46 other key statutes/EU acts via self-hosted PageIndex (tree-based, vectorless RAG) exposed over MCP
- [ ] **REQ-AGENTS-FORMAT**: Every agent (25 total) is packaged as an Anthropic Agent Skill (`skills/<id>/SKILL.md`) that passes `skills-ref validate`
- [ ] **REQ-PARTIES**: Five party agents (KO, PiS, TD, Konfederacja, Lewica) with distinct ideology, electorate, rhetorical style references
- [ ] **REQ-MINISTRIES**: Nineteen ministry agents (Finance, Health, Education, Justice, Defense, Foreign Affairs, Climate, Infrastructure, Development, Agriculture, Family/Labor, Digitalization, Culture, Science, Energy, Interior, State Assets, Funds/Regional, Sport/Tourism) sharing a common expertise template
- [ ] **REQ-ORCHESTRATOR**: Marszałek orchestrator agent that selects 2–3 relevant ministries per topic, runs first/second readings, tallies votes, and emits a final session document
- [ ] **REQ-RAG-SKILL**: `mmtmr/pageindex-rag` skill installed as the shared navigation know-how loaded by every agent that touches Second Brain
- [ ] **REQ-CITATIONS**: Every argument in the transcript carries a citation pointing to a specific PageIndex node (e.g. "art. 12 ust. 3, Ustawa o OZE")
- [ ] **REQ-LANG**: Runtime debate, transcripts and CLI/web UI are in English, while the legal corpus stays in original Polish — agents read PL, quote EN with `(orig. PL: "…")` notes
- [ ] **REQ-WEB**: Next.js front-end visualizing the parliament chamber with live, party-colored transcript fed by the same orchestrator pipeline as the CLI
- [ ] **REQ-EXPORT**: User can export a session transcript to Markdown (PDF stretch)
- [ ] **REQ-ETHICS**: Each session emits a disclaimer ("educational simulation, not a forecast"), never names real MPs, refuses hate-speech generation, and all party profiles are reviewed by ≥ 2 people
- [ ] **REQ-DEMO**: 3-minute demo video and DEV.to submission published before 2026-05-31 23:59 PDT with required template sections (What I Built / Demo / Code / Tech Stack / How I Used Hermes Agent)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Real MPs and named individuals — only parties as constructs (ethics: avoid impersonation/defamation)
- 6th party / non-affiliated faction — deferred post-contest (scope vs. 5-day deadline)
- Polish-language runtime UI/debate — scope choice (English-only for international DEV.to jury)
- Full ISAP corpus (thousands of statutes) — OCR/ingest would consume the entire deadline; we ship a curated ~50-document set
- Real political forecasting — this is an educational simulation, not a predictive tool
- Custom LLM fine-tuning — Hermes Agent ships with usable defaults; we use them as-is
- Voice / TTS in MVP — visualization is text-only with party-colored transcript
- Voting beyond party-bloc level — no per-MP modeling (matches the "parties as constructs" decision)

## Context

- **Competition:** Hermes Agent Challenge on DEV.to, category "Build With Hermes Agent", prize pool $1000, deadline **2026-05-31 23:59 PDT**. Today is **2026-05-26** → 5 calendar days to ship.
- **Hermes Agent (Nous Research):** MIT-licensed framework providing long-term memory, MCP-native tool use, multi-step reasoning, model switching. Repo: <https://github.com/NousResearch/hermes-agent> (HTTP 200 verified). New to us — Day-1 prototype required before scaling to 25 agents.
- **Agent Skills (Anthropic spec):** Each agent is a versioned, reviewable folder with `SKILL.md` + references/assets/scripts. Progressive disclosure means Hermes loads ~100 tokens of metadata per skill on session start; full body (~5000 tokens) only on activation.
- **PageIndex (vectorless RAG):** TOC-style tree index of legal documents, exposed via MCP. Chosen over Chroma/FAISS because legal docs have native hierarchy (rozdział → artykuł → ustęp), traceable citations, and reasoning-over-similarity is critical for "two parties asking the same question, needing different sections". Self-host on the contest VPS; PageIndex Cloud as Polish-OCR fallback.
- **Bias mitigation:** Every party profile reviewed by minimum 2 people from different political sides before commit. Profiles framed from the party's *own* electorate's perspective, not caricatured.
- **Polish ↔ English split:** Corpus stays in original Polish (legal authority); debate/UI is English (jury). Each quote carries `(orig. PL: "…")` so a Polish reader can verify fidelity.
- **Filozofia Hermes Agent:** Local-first, runnable on a ~$5/month VPS — informs choice of self-hosted PageIndex and SQLite for sessions.

## Constraints

- **Timeline**: Hard deadline 2026-05-31 23:59 PDT — 5 calendar days from today. Drives all scope/granularity decisions.
- **Tech stack — Agents**: Hermes Agent (Nous Research, MIT). No other agent framework allowed by contest category "Build With Hermes Agent".
- **Tech stack — Format**: Anthropic Agent Skills spec (lowercase-hyphen names, YAML frontmatter, references/assets/scripts subdirs). Validated by `skills-ref validate`.
- **Tech stack — RAG**: PageIndex (vectorless, MCP-native). No Chroma/FAISS.
- **Tech stack — Runtime**: Python 3.11+, asyncio for parallel ministry consultations, SQLite for sessions/transcripts, typer for CLI, Next.js for the web visualization.
- **Tech stack — RAG fundament skill**: External `mmtmr/pageindex-rag` skill must be installed via `npx skills add mmtmr/pageindex-rag`.
- **Budget**: Self-hosted runnable on ~$5/month VPS. Implies smaller models for ministries, stronger model for orchestrator/parties.
- **License**: MIT — code must be public and auditable per contest rules and ethics commitment.
- **Compliance**: No real MP names, no hate speech, mandatory disclaimer per session.
- **Submission**: Public GitHub repo + DEV.to post with tags `hermesagentchallenge, devchallenge, agents` + ≤ 3 min demo video.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Full 5 parties + 19 ministries (no MVP shrink) | User choice — stronger jury impression than reduced scope, and PRD §8 already accounts for it via a shared `Ministry` template | — Pending |
| Next.js with chamber visualization in MVP (not deferred) | User choice — visual demo carries DEV.to submissions; Next.js can wrap the same orchestrator pipeline as the CLI | — Pending (highest schedule risk) |
| Corpus = Constitution + KK + KC + KP + ~46 statutes (~50 docs) | Coverage of typical debate topics without burning the deadline on OCR | — Pending |
| English-only runtime, PL corpus untranslated | International jury + preserve legal authority of original sources | — Pending |
| 6th party / non-affiliated faction excluded | Out-of-scope to keep 5-day delivery realistic | ✓ Good |
| PageIndex over vector stores | Legal docs have native hierarchy; citation-grade traceability mandatory | — Pending |
| Hermes Agent (Nous Research) as required framework | Contest category "Build With Hermes Agent" | ✓ Good (locked by contest) |
| Anthropic Agent Skills format for all 25 agents | Progressive disclosure saves context, git-reviewable, validatable | — Pending |
| Workflow: GSD (new-project → discuss → plan → execute per phase) | User choice over freeform PRD-driven execution | — Pending |
| GSD config: Interactive / Standard granularity / Parallel / Commit / Sonnet / Researcher-only | Balance speed vs. quality at 5-day deadline; researcher kept because Hermes + PageIndex are new APIs | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-26 after initialization*

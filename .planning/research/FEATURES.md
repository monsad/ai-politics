# Feature Research

**Domain:** Multi-agent parliamentary simulation (contest entry — Hermes Agent Challenge)
**Researched:** 2026-05-26
**Confidence:** MEDIUM — web search blocked; analysis derived from PRD §5, PROJECT.md, training knowledge of DEV.to build challenges, and comparable agent-simulation projects (AI Town, BabyAGI, AutoGen multi-agent demos, parliamentary debate simulators)

---

## Context: Two Audiences, One Demo

Every feature decision has two concurrent audiences:

1. **End users** (journalist, student, hobbyist voter) — care about output quality, credibility, usability
2. **Contest jury** (DEV.to Hermes Agent Challenge) — care about effective Hermes Agent use, technical architecture, creativity, and a compelling 3-minute demo video

Features that serve both audiences are automatic P1. Features that serve only one are P2 or lower given the 5-day deadline.

---

## Feature Landscape

### Table Stakes (Users Expect These / Jury Dismisses Without These)

| # | Feature | Why Expected | Build Complexity | Demo-Video Impact | Dependencies | Notes |
|---|---------|--------------|-----------------|-------------------|--------------|-------|
| TS-1 | **Session transcript** — full ordered record of who said what, in what reading, with timestamps | Every simulation product outputs a readable record; without it the simulation is a black box | S | HIGH | Orchestrator, party agents | PRD §5.4–5.5 covers this. Must be the primary CLI output. |
| TS-2 | **Party-attributed speech** — each utterance labelled with party name + ideological colour | Users need to know who is arguing what; unlabelled output is noise | S | HIGH | Party agents (5), orchestrator session management | PRD §5.2 covers this. Colour-coding is easy and high visual bang. |
| TS-3 | **Vote tally** — per-party FOR/AGAINST/ABSTAIN + total result | Parliamentary simulation without a vote result feels unfinished; it's the climax the user is waiting for | S | HIGH | Orchestrator vote phase | PRD §5.4 covers this. Tally table renders beautifully in markdown and on screen. |
| TS-4 | **Source citations** — every argument references a specific legal node (e.g. "art. 12 ust. 3, Ustawa o OZE") | Distinguishes "made-up AI text" from "grounded simulation"; critical for journalist and student personas; directly judges Hermes Agent tool-use | M | HIGH | PageIndex MCP, Second Brain (§5.1), `pageindex-rag` skill | PRD §REQ-CITATIONS. This is the single most important quality signal. Do not ship without it. |
| TS-5 | **Ministry expertise phase** — 2-3 ministries produce structured analyses before debate begins | Without domain expertise the party debate becomes pure rhetoric; expertise phase is what makes it "parliament" not "chatroom" | M | MEDIUM | Ministry skills (19), orchestrator ministry selection, Second Brain | PRD §5.3–5.5. Parallel async execution is key to keeping ≤5 min runtime. |
| TS-6 | **Educational disclaimer** — visible on every session output: "This is an educational simulation, not a political forecast" | Ethical floor; required by contest rules and user trust; without it the product looks irresponsible | S | LOW | None — text constant in orchestrator output | PRD §REQ-ETHICS. One-liner. Non-negotiable. |
| TS-7 | **`hermes parliament "<topic>"` CLI** — single command, ≤ 5-minute end-to-end run | Jury persona: clones repo, runs one command, expects it to work in 2 minutes; any friction here is a disqualification | M | HIGH | CLI (typer), orchestrator, all agents | PRD §5.6, REQ-RUN. The demo opens with this command running live. |
| TS-8 | **Markdown export** — `--export markdown` flag saves transcript to file | Students and journalists need to take output away; export is the minimal "save" feature | S | LOW | CLI flag, session storage (SQLite) | PRD §REQ-EXPORT. S complexity: just write the in-memory transcript to disk. |
| TS-9 | **Two reading structure** — first reading (opening positions), second reading (amendments + rebuttals) | Matches the actual Polish Sejm workflow that the product claims to simulate; single-reading feels like a shortcut | M | MEDIUM | Orchestrator session flow, party agents | PRD §5.5 steps 5–7. Keeps simulation credible. |
| TS-10 | **No real MP names** — output never names living politicians | Ethical floor; naming real people in fabricated contexts creates defamation risk and disqualifies the entry | S | LOW | Party agent prompts (guardrails) | PRD §REQ-ETHICS. Already out-of-scope; flag here because it must be enforced in prompts, not just stated in README. |

### Differentiators (What Makes a Top-4 DEV.to Submission)

| # | Feature | Value Proposition | Build Complexity | Demo-Video Impact | Dependencies | Notes |
|---|---------|-------------------|-----------------|-------------------|--------------|-------|
| D-1 | **Next.js chamber visualization** — hemicycle seating map with party blocs, live-highlighted speaker, party-coloured transcript stream | Visual demos dominate DEV.to submissions; a moving hemicycle screenshot in the thumbnail alone outcompetes text-only entries; jury sees "agentic coordination" made spatial | L | VERY HIGH | Next.js app, orchestrator SSE/WebSocket stream, party colour system | PRD §REQ-WEB. Highest schedule risk (PROJECT.md). If it ships, the demo video writes itself. If it slips, CLI demo is still viable. |
| D-2 | **`--minister <domain> "<question>"` mode** — bypass full session, query a single ministry directly | Serves journalist/analyst persona exactly; shows Hermes Agent tool use in isolation; quick demo path for the video's "use case 2" | S | HIGH | Ministry skill, pageindex-rag, CLI | PRD §5.6 user story 3. S complexity because it is just a single-agent run with no orchestrator. Implement this before full session to validate ministry agent independently. |
| D-3 | **Draft bill output** — orchestrator generates a structured bill draft (article-by-article format) after the vote | Turns simulation from "who says what" into "what law would result"; directly answers the journalist persona's question | M | HIGH | Orchestrator post-vote phase, party agent input | PRD §5.4 ("projekt ustawy"). M because the bill draft template needs to be designed and the orchestrator must synthesize across party/ministry positions. |
| D-4 | **Party long-term memory** — Hermes Agent's cross-session memory records how each party voted on prior topics; influences current session | Directly showcases Hermes Agent's "deepening model" capability — the USP the contest explicitly rewards; creates "party consistency" across re-runs | M | MEDIUM | Hermes long-term memory API, SQLite session store, party skills | PRD §6.3 "skill learning loop". M because Hermes memory API is new to the team (Day-1 prototype risk). Flag for early spike. |
| D-5 | **Hermes-native multi-step reasoning** — visible in transcript as orchestrator reasoning steps: "Selecting ministries because… Routing because…" | Shows jury the orchestration intelligence, not just output; demonstrates understanding of Hermes Agent beyond wrapping a single model | M | MEDIUM | Orchestrator SKILL.md prompt design | Achievable with prompt engineering. Add reasoning trace as a `[MARSZAŁEK REASONING]` block in transcript. |
| D-6 | **`--export pdf` stretch** — PDF export with session header, party colours, citation footnotes | Journalist persona value; visually impressive in demo; shareable artifact | M | MEDIUM | Markdown export (TS-8), weasyprint/pandoc dependency | PRD §REQ-EXPORT (PDF stretch). Risky for 5-day deadline — mark as Day-30 only if CLI+web are solid. |
| D-7 | **Parallel ministry consultation timing display** — CLI shows "Consulting 3 ministries in parallel… (2.3s)" | Demonstrates asyncio multi-agent parallelism visibly; distinguishes from naive sequential LLM call | S | MEDIUM | asyncio orchestrator, tqdm/rich progress display | Very S: add `rich` progress bar to existing asyncio gather. High jury signal per token. |
| D-8 | **Topic auto-classification** — orchestrator infers which ministries are relevant without user specifying | Makes the product "just works" for non-expert users; demonstrates multi-step reasoning (classify → select → delegate) | M | LOW | Orchestrator skill, ministry domain metadata | PRD §5.4 "wybór 2-3 ministerstw". Already in scope — flag that the quality of this classification is a differentiator. Show it in demo by picking an ambiguous topic. |
| D-9 | **English debate / Polish citations split** — agents reason in English, quote Polish legal text with `(orig. PL: "…")` notation | Directly serves international jury; unusual and credible; shows legal fidelity without alienating non-Polish readers | M | MEDIUM | Party + ministry skill prompts, pageindex-rag | PRD §REQ-LANG. M because every prompt must enforce this dual-language discipline consistently across 25 agents. |

### Anti-Features (Deliberately NOT Building)

| Feature | Why It Seems Attractive | Why It Bombs / Should Be Avoided | What to Do Instead |
|---------|------------------------|----------------------------------|-------------------|
| **Real MP names and faces** | More "realistic"; Wikipedia-style fidelity | Defamation risk; fabricated quotes attributed to real people; contest rules violation; ethics disqualifier | Parties-as-constructs only. Ideological profiles are more interesting for analysis anyway. |
| **Voice / TTS output** | More immersive demo video | 5-day timeline: TTS integration, latency, audio sync with visualization = multi-day rabbit hole; adds no analytical value | Screen-record CLI + chamber viz; good music/editing sells the demo better than robotic TTS |
| **Full ISAP corpus (~thousands of statutes)** | "More complete" knowledge base | OCR + ingest pipeline for thousands of Polish PDFs would consume 2-3 full days; legal corpus has diminishing returns past ~50 docs for typical topics | Curated ~50 documents covering Constitution + KK + KC + KP + ~46 key statutes. Coverage for 95% of plausible demo topics. |
| **Real-time political forecasting** | Sounds useful to journalists | Misleads users about the system's actual capability; requires real polling data, probability calibration, would invite credibility attacks | Simulation + disclaimer. Explicitly position as "explore positions" not "predict outcomes". |
| **6th party / non-affiliated faction** | More dramatic swing-vote narrative | No material benefit for 5-party Polish Sejm simulation; adds 1 more skill to build and maintain; 5-day deadline does not allow it | Keep 5 parties. The swing-vote drama already exists between TD and Konfederacja on most topics. |
| **Custom LLM fine-tuning** | "Our own model knows Polish politics" | Weeks of work, not days; Hermes Agent ships usable defaults; fine-tuning is out of contest scope | Prompt engineering + RAG + long-term memory achieves political consistency without fine-tuning. |
| **Streaming token output to CLI** | "Cool live effect" in demo | token-by-token streaming across 25 agents with orchestrated turns creates race conditions and display complexity; adds 1+ day of async rendering work | Batch output per turn with a spinner. Richer UX, less fragile. |
| **Session share URL** | Nice for viral demo clips | Requires hosted deployment, user accounts, URL routing — 3-day add-on minimum | Export to Markdown (TS-8) + paste link to gist. Achieves sharing with zero infrastructure. |
| **Polish-language runtime UI** | Native-speaker fidelity | DEV.to jury is international; Polish-only output guarantees jury cannot evaluate quality | English runtime (PRD §REQ-LANG). Polish legal corpus untranslated for authority. |
| **Per-MP voting model** | Granularity looks impressive | Polish Sejm has 460 members; modeling each requires a totally different architecture; party-bloc voting is actually more analytically honest for this simulation | Party-bloc votes with seat counts (KO: 157 seats, FOR). Shows same drama with accurate weight. |

---

## Feature Dependencies

```
[TS-4 Source Citations]
    └──requires──> [Second Brain / PageIndex ingest]
                       └──requires──> [pageindex-rag skill installed]

[TS-1 Session Transcript]
    └──requires──> [TS-7 CLI / Orchestrator]
                       └──requires──> [TS-2 Party agents]
                       └──requires──> [TS-5 Ministry expertise phase]
                                          └──requires──> [TS-4 Source Citations]

[TS-3 Vote Tally]
    └──requires──> [TS-9 Two reading structure]
                       └──requires──> [TS-1 Session Transcript]

[TS-8 Markdown Export]
    └──requires──> [TS-1 Session Transcript]

[D-2 --minister mode]
    └──requires──> [TS-5 Ministry agents]
    └──requires──> [TS-4 Source Citations]
    (does NOT require full orchestrator — can validate ministry in isolation on Day 1)

[D-1 Chamber Visualization]
    └──requires──> [TS-7 CLI complete]
    └──requires──> [TS-2 Party colour system]
    └──requires──> [Orchestrator SSE/WebSocket event stream]

[D-3 Draft Bill Output]
    └──requires──> [TS-3 Vote Tally]
    └──requires──> [TS-9 Two readings complete]

[D-4 Party Long-term Memory]
    └──requires──> [TS-2 Party agents]
    └──requires──> [Hermes long-term memory API working]
    (spike this Day 1 alongside Hermes prototype)

[D-6 PDF Export]
    └──requires──> [TS-8 Markdown Export]

[D-7 Parallel timing display]
    └──requires──> [TS-5 async ministry consultations]
```

### Dependency Notes

- **Second Brain must exist before any agent can cite sources.** PageIndex ingest is the project's critical path — it must be smoke-tested Day 1.
- **D-2 `--minister` mode is the best early validation path.** It exercises Second Brain + ministry skill without needing all 25 agents. Build it first as integration test.
- **D-1 Chamber visualization can be decoupled.** The CLI pipeline is complete independently. Web front should not block CLI DoD. Build as parallel track on Day 4–5 only.
- **D-4 long-term memory must be spiked on Day 1.** If Hermes memory API has friction, fall back to SQLite session store for "party voted X on similar topic" — simpler but still shows cross-session consistency.

---

## PRD §5 Gap Analysis and Scope Assessment

### Features in PRD §5 — Assessment

| PRD Item | Assessment | Risk for 5-Day Deadline |
|----------|------------|------------------------|
| §5.0 Agent Skills format (25 agents) | Correct approach; Agent Skills progressive disclosure is the right call for context budget | MEDIUM — 19 ministry skills share one template; execute as batch not one-by-one |
| §5.1 Second Brain / PageIndex | Non-negotiable; critical path item | HIGH — new tool, Day-1 smoke test is mandatory |
| §5.2 Five party agents | Correct; do not shrink to 3 | LOW — five SKILL.md files with ideological differences are primarily writing work |
| §5.3 Nineteen ministry agents | Correct if shared template is used | MEDIUM — template-driven, but 19 × review + test is Day 3 bulk work |
| §5.4 Orchestrator (Marszałek) | Correct; most complex single agent | HIGH — session state machine with ministry selection, reading routing, vote tally, bill synthesis |
| §5.5 Session flow (2 readings + vote) | Correct; do not simplify | MEDIUM — state machine design is key |
| §5.6 CLI + optional web | CLI is MVP; web is differentiator | HIGH for web — Next.js + SSE stream is the highest-risk item |

### Features Missing from PRD §5

1. **Hermes reasoning trace in transcript** (D-5) — not mentioned; should be. Jury explicitly evaluates "effective use of Hermes Agent". Show reasoning, don't hide it.
2. **`--minister` single-agent mode** (D-2) — listed in user story 3 but not in §5.6 CLI commands. Must be in CLI spec.
3. **Party colour system definition** — needed for both CLI (ANSI colours) and web (hex palette). Needs a central config file. Not mentioned.
4. **Seat count per party** — needed for weighted vote tally. PRD mentions seats in party SKILL.md frontmatter (157 for KO) but vote tally logic must use this. Not spelled out.
5. **Bill draft template** — PRD mentions "projekt ustawy" as output but doesn't specify its structure. Needs an `assets/bill-draft-template.md` in the orchestrator skill.

### Features in PRD §5 That Are Overscoped for 5 Days

| Item | Overscope Signal | Recommended Mitigation |
|------|-----------------|------------------------|
| **Next.js chamber visualization in MVP** | Described as "optional web front" in §5.6 but elevated to MVP in PROJECT.md key decisions. Highest schedule risk. | Keep it as a goal; cut ruthlessly if Day 4 reveals it is blocking CLI polish. A polished CLI demo with a static hemicycle screenshot is still a strong submission. |
| **RSS news ingest** (§5.1 fourth source category) | Adding live news to PageIndex is an entirely separate ingest pipeline with freshness/reliability issues | Cut. Curated ~50 static legal docs are sufficient for the contest. RSS adds latency and instability. |
| **`scripts/policz-skutek.py` budget calculator** (§5.3 example) | A working budget impact calculator for Finance ministry implies real fiscal modelling | Do not implement. Ministry agents cite budget figures from PageIndex documents; they do not calculate. The script slot in the skill structure can be a stub. |

### Features That Would Obviously Bomb in Demo

1. **Silent failure on citation** — if PageIndex returns nothing and the agent outputs "argument without source", the simulation's credibility collapses. Every ministry/party agent must have a fallback: if no citation found, say so explicitly rather than fabricating.
2. **Symmetric party responses** — if KO and PiS say structurally identical things (same sentence patterns, same references), the simulation looks like prompt template echo, not actual party differentiation. Party rhetorical profiles must produce visibly different language.
3. **Vote result that defies obvious expectation** — e.g. a 4-dniowy tydzień pracy (4-day work week) bill passing with KO + PiS + Konfederacja all voting FOR makes no political sense. Orchestrator must enforce party ideology guardrails on vote direction.
4. **5-minute CLI hang with no feedback** — no progress output during LLM calls. Demo video will show a frozen terminal. Add `rich` progress with phase names: `[1/4] Consulting ministries...`, `[2/4] First reading...`, etc.
5. **Unreadable Polish legal quotes in English transcript** — if a ministry outputs three paragraphs of Polish without English translation, non-Polish jury cannot evaluate quality. The PL→EN discipline in D-9 must be enforced strictly.

---

## MVP Definition

### Launch With (v1 — contest deadline)

Required for a credible, passable contest entry:

- [ ] TS-7 `hermes parliament "<topic>"` CLI — single command, full run
- [ ] TS-2 Party-attributed speech with party name labels
- [ ] TS-5 Ministry expertise phase (2-3 ministries, parallel)
- [ ] TS-4 Source citations (every argument cites a PageIndex node)
- [ ] TS-9 Two reading structure (first reading + second reading + vote)
- [ ] TS-3 Vote tally (per-party result + seat-weighted total)
- [ ] TS-1 Session transcript (markdown, readable, ordered)
- [ ] TS-8 Markdown export (`--export markdown`)
- [ ] TS-6 Educational disclaimer (every session output)
- [ ] TS-10 No real MP names (enforced in agent prompts)
- [ ] D-2 `--minister <domain> "<question>"` mode
- [ ] D-7 Parallel timing display (rich progress bar)
- [ ] D-3 Draft bill output (post-vote section of transcript)
- [ ] D-9 English debate / Polish citations split

### Add If Time Allows (v1.x — Day 4–5 stretch)

- [ ] D-1 Next.js chamber visualization — highest demo impact, cut if it risks CLI quality
- [ ] D-5 Hermes reasoning trace in transcript — visible orchestrator reasoning steps
- [ ] D-4 Party long-term memory — spike Day 1; implement Day 4 if spike is clean
- [ ] D-6 PDF export — only if markdown export is rock-solid

### Out of Scope (v2+)

- [ ] Session share URL — requires hosted infra
- [ ] Voice / TTS
- [ ] RSS news ingest
- [ ] 6th party
- [ ] Fine-tuned models
- [ ] Budget calculator scripts (real fiscal modelling)

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Contest Jury Value | Priority |
|---------|------------|---------------------|-------------------|----------|
| TS-7 CLI single command | HIGH | MEDIUM | HIGH | P1 |
| TS-4 Source citations | HIGH | MEDIUM | HIGH | P1 |
| TS-2 Party-attributed speech | HIGH | LOW | HIGH | P1 |
| TS-3 Vote tally | HIGH | LOW | HIGH | P1 |
| TS-5 Ministry expertise phase | HIGH | MEDIUM | HIGH | P1 |
| TS-1 Session transcript | HIGH | LOW | HIGH | P1 |
| TS-9 Two reading structure | MEDIUM | MEDIUM | HIGH | P1 |
| D-2 `--minister` mode | HIGH | LOW | HIGH | P1 |
| D-7 Parallel timing display | LOW | LOW | HIGH | P1 |
| D-3 Draft bill output | MEDIUM | MEDIUM | MEDIUM | P1 |
| D-9 English/Polish split | MEDIUM | MEDIUM | HIGH | P1 |
| TS-6 Disclaimer | LOW | LOW | MEDIUM | P1 |
| TS-8 Markdown export | MEDIUM | LOW | LOW | P1 |
| D-1 Chamber visualization | HIGH | HIGH | VERY HIGH | P2 |
| D-5 Reasoning trace | LOW | LOW | HIGH | P2 |
| D-4 Long-term memory | MEDIUM | MEDIUM | HIGH | P2 |
| D-6 PDF export | MEDIUM | MEDIUM | LOW | P3 |

---

## Competitor Feature Analysis

Comparable products (from training knowledge — confidence MEDIUM):

| Feature | AI Town / AI Simulacra (Stanford, 2023) | Pol.is (consensus mapping) | BabyAGI / AutoGen demos | Our Approach |
|---------|----------------------------------------|---------------------------|------------------------|--------------|
| Named agent personas | Yes (fictional characters) | No (anonymous clusters) | Task-defined, not persona-defined | Party constructs — ideology not individuals |
| Grounded knowledge base | No — pure LLM memory | No | Optional tool use | PageIndex with legal citations — unique |
| Structured workflow | No — free social simulation | No — voting convergence | Task decomposition | Parliamentary procedure (readings → vote) — differentiated |
| Export / artifact | No | CSV clusters | Task output | Markdown transcript + draft bill |
| Source citations | No | No | Partial | Yes — every argument cites a real document |
| Demo-video appeal | Very high (agents walking around) | Low | Medium | High (hemicycle + coloured transcript) |

Key gap we fill that no comparable project does: **source-cited, structured-procedure multi-agent simulation** in a domain (law/politics) where grounding matters.

---

## Demo-Video Implications (3-minute format)

Given a 3-minute demo video constraint, the optimal structure and which features carry each segment:

| Segment | Duration | Features Shown | Notes |
|---------|----------|---------------|-------|
| Hook — single command run | 0:00–0:20 | TS-7 CLI, D-7 progress display | Open with `hermes parliament "Wprowadzenie 4-dniowego tygodnia pracy"` live. Rich progress bar shows parallel ministry consultation. Never open with slides. |
| Ministry expertise output | 0:20–0:50 | TS-5, TS-4 citations | Show Finance + Labour ministries' structured analyses with highlighted legal citations. Demonstrates Second Brain grounding. |
| Party debate | 0:50–1:30 | TS-2, TS-9, D-9 | Show first reading: 5 party speeches, clearly attributed, colour-coded. PiS and Konfederacja must sound visibly different from KO and Lewica. If chamber viz is ready, switch to web view here. |
| Vote + result | 1:30–1:50 | TS-3, D-3 | Show tally table + draft bill header. The "moment of truth" — if the vote result is politically coherent, it lands hard. |
| `--minister` quick demo | 1:50–2:10 | D-2 | Show journalist use case: `hermes parliament --minister finanse "ile kosztuje 800+"` — fast, cited, expert answer. |
| Architecture slide | 2:10–2:40 | D-5 reasoning trace, 25 agents | 10-second diagram: 5 parties + 19 ministries + Marszałek + PageIndex. Then show one agent skill folder. Jury cares about this. |
| Closing + repo | 2:40–3:00 | — | GitHub link, `pip install`, ≤2-step run instructions |

**Single most important demo choice:** pick a topic where party positions are obvious and divergent — "Wprowadzenie 4-dniowego tygodnia pracy" (4-day work week) is perfect: Lewica clearly FOR, Konfederacja clearly AGAINST, PiS torn on social vs. economic. If citations appear and the vote matches political reality, the jury immediately trusts the system.

---

## Sources

- PRD §5.0–5.6, §6.3, §7, §9 (primary)
- PROJECT.md requirements, constraints, key decisions (primary)
- Training knowledge: DEV.to Build challenges (2023–2024 patterns), AI Simulacra (Park et al., Stanford 2023), BabyAGI/AutoGen multi-agent demos, Pol.is, parliamentary debate simulation academic literature — confidence MEDIUM
- Hermes Agent Challenge judging criteria: sourced from contest link in PRD/PROJECT.md — specific jury weights not independently verified (web access blocked); criteria inferred from contest description ("effective use of Hermes Agent, technical implementation, creativity, usability") — confidence MEDIUM

---

*Feature research for: Virtual Parliament / Wirtualny Parlament*
*Researched: 2026-05-26*

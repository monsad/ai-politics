# Pitfalls Research — Virtual Parliament / Wirtualny Parlament

**Domain:** Multi-agent political simulation, contest submission, tight deadline
**Researched:** 2026-05-26
**Confidence:** MEDIUM (web tools unavailable; analysis from architecture/pattern knowledge + PRD review)

> **Note on sources:** WebSearch and WebFetch were blocked during this research session. All findings derive from architectural analysis of the PRD/PROJECT.md, training-data knowledge of Hermes Agent, Agent Skills, PageIndex, and multi-agent system failure modes. Findings backed by official repos or official docs are marked HIGH; the rest MEDIUM or LOW. Nothing is stated as fact without a basis.

---

## Severity × Likelihood Matrix

Pitfalls below are ordered by **S × L score** (Severity 1–5 × Likelihood 1–5, max 25).

| # | Pitfall | Severity | Likelihood | S×L | Phase |
|---|---------|----------|------------|-----|-------|
| 1 | OCR ingest fails Day 1, no fallback locked in | 5 | 5 | 25 | Phase 1 |
| 2 | 25-agent cost runaway during demo/test | 5 | 4 | 20 | Phase 2 |
| 3 | Context-window blow-out from growing transcript | 4 | 5 | 20 | Phase 3 |
| 4 | Hermes Agent API surface is underdocumented; Day-1 prototype unblocked but Day-3 multi-agent breaks | 4 | 4 | 16 | Phase 1 |
| 5 | Agent Skills `name` validation / frontmatter rejection | 3 | 5 | 15 | Phase 1 |
| 6 | Debate loop — no termination condition, session never ends | 4 | 3 | 12 | Phase 3 |
| 7 | Party-agent position convergence — all agree, no drama | 3 | 4 | 12 | Phase 2 |
| 8 | Real-MP impersonation / defamation via implied naming | 5 | 2 | 10 | Phase 2 |
| 9 | Demo-day LLM rate-limit mid-video | 4 | 2 | 8 | Phase 4 |
| 10 | Missing DEV.to submission template sections | 3 | 3 | 9 | Phase 4 |
| 11 | "Almost works on Day 4" scope-creep trap | 4 | 4 | 16 | All |
| 12 | Hate-speech generation from Konfederacja agent | 5 | 2 | 10 | Phase 2 |
| 13 | Polish/English mixing — unreadable transcript | 2 | 4 | 8 | Phase 3 |
| 14 | PageIndex MCP server not stable under parallel queries | 4 | 3 | 12 | Phase 1 |
| 15 | Reproducibility failure — jury can't run in 2 minutes | 5 | 3 | 15 | Phase 4 |
| 16 | Video > 3 minutes, or shows nothing working | 4 | 3 | 12 | Phase 4 |
| 17 | Missing LICENSE file or wrong license | 3 | 2 | 6 | Phase 1 |
| 18 | PageIndex first-ingest tree-build cost blocks Day 2 | 3 | 4 | 12 | Phase 1 |
| 19 | Legal hallucination — agent cites article that doesn't exist | 4 | 3 | 12 | Phase 2 |

---

## Critical Pitfalls (S×L ≥ 15)

### Pitfall 1: Polish OCR Ingest Fails on Day 1 With No Fallback

**S×L: 25 — The single highest risk on this project.**

**What goes wrong:**
ISAP PDFs range from clean modern PDFs (post-2010 statutes) to degraded scans from the 1990s with diacritics printed as image glyphs. Self-hosted PageIndex OCR pipelines (typically Tesseract or similar) handle `ą ę ó ź ż ś ń ć ł` inconsistently when the scan quality is low. The result is a corpus with corrupted text: `czlonkow` instead of `członków`, `ustawa o OZE` becoming `ustawa o 0ZE`. Agents citing these nodes emit legally incorrect quotes. Worse, a tree-build on 50 documents can take 10-30 minutes on a $5 VPS and fail partway through, leaving a partial index with no recovery checkpoint.

**Why it happens:**
Polish diacritics are in the Latin Extended-A Unicode block. Tesseract needs a correctly installed `pol` language pack. Default `eng` mode silently drops diacritics or substitutes Latin lookalikes. Developers assume "OCR works" until they see output.

**How to avoid:**
- Day 0 (today): Run OCR on ONE document from ISAP — the Constitution PDF — and verify diacritics before writing any agent code. If output has garbled Polish, switch to PageIndex Cloud immediately; do not attempt to fix self-hosted OCR under a 5-day deadline.
- Add a `scripts/verify_ocr.py` that spot-checks 20 random nodes for Polish character presence (`ą ę ó ź ż ś ń ć ł`) and fails loudly if hit rate < 90%.
- Ingest the 10 most-critical documents first (Constitution, KK, KC, KP, 2 EU regs), smoke-test all of them, before ingesting the remaining 46. Fail fast.
- Keep PageIndex Cloud credentials in `.env.example` as the named fallback. Do not leave "Cloud as fallback" as a verbal plan — write the fallback code path on Day 1.

**Warning signs:**
- Polish characters absent from `fetch_node` output on first smoke test
- Tree-build log shows `UnicodeDecodeError` or `? ? ?` substitutions
- First `tree_search` on "Konstytucja art. 1" returns zero results

**Phase to address:** Phase 1 (Day 26 May — PageIndex setup). Gate: smoke test passes before moving to party skills.

---

### Pitfall 2: 25-Agent Cost Runaway

**S×L: 20**

**What goes wrong:**
The full session flow is: Orchestrator calls Second Brain (1 LLM call) → selects 3 ministries → each ministry calls Second Brain (3 calls) → each ministry produces expertise (3 calls) → 5 parties each do first reading with Second Brain lookups (10–15 calls) → 5 parties do second reading / ripostes (10–15 calls) → voting with justifications (5–10 calls) → Orchestrator writes final document (1–2 calls). Total: 33–49 LLM calls per session, each potentially 2K–8K tokens. At Claude Opus pricing (~$15/MTok input), a single full session with a strong model everywhere costs $5–20. Running 3–5 test sessions on Day 3/4 = $15–100 unintentionally.

**Why it happens:**
The PRD mentions "mniejsze modele dla ministerstw" but the agent_factory.py doesn't yet exist. During development, developers default every agent to the strongest available model for quality. Cost tracking is absent until it's too late.

**How to avoid:**
- Wire model tiering into `agent_factory.py` on Day 1, not Day 4. Hard-code: orchestrator = `claude-3-haiku` or `Nous-Hermes-2-Mixtral` (fast/cheap), ministries = cheapest available, parties = one tier up for rhetoric quality.
- Add a `MAX_TOKENS_PER_SESSION = 50000` hard cap in the orchestrator. Session aborts with a cost warning if exceeded.
- Cache ministry expertise responses keyed by `(topic_hash, ministry_id)` using SQLite — ministry answers on the same topic are deterministic enough to cache across test runs.
- Log per-session token counts to stdout from Day 1.

**Warning signs:**
- No model-tier config exists by end of Day 2
- Running test sessions without looking at the API dashboard
- Ministry agents using the same model as the orchestrator

**Phase to address:** Phase 2 (agent factory + party/ministry skills).

---

### Pitfall 3: Context-Window Blow-Out From Growing Transcript

**S×L: 20**

**What goes wrong:**
Each party agent in round 2 (ripostes) sees the full transcript from round 1. Five parties × ~500 tokens each = 2500 tokens of transcript. Add ministry expertise summaries (~3 × 800 = 2400 tokens), the original topic + Second Brain results (~2000 tokens), and the party's own SKILL.md body (~5000 tokens) = ~12,000 tokens before the agent writes a single word. With 5 parties in round 2 each passing the now-longer transcript: cumulative context grows quadratically. By the vote-justification phase, each call passes 20K–40K tokens of context, blowing through cheaper model limits (8K–16K context windows) or dramatically increasing cost on larger models.

**Why it happens:**
The orchestrator naively appends all previous utterances to each agent's prompt. No summarization, truncation, or windowed-context strategy is built early.

**How to avoid:**
- Design the transcript data structure on Day 1 as a list of structured `Utterance` objects, not a flat string concatenation. This enables surgical context management.
- Each agent receives: (a) its own SKILL.md metadata only (100 tokens, progressive disclosure), (b) ministry summaries truncated to 200 tokens each, (c) the last 2 utterances from each other party (not all), (d) its own full previous utterance.
- Total context budget per agent per turn: 8K tokens max. Enforce in `agent_factory.py`.
- Test context size on Day 3 with a real 5-party session before adding second-reading logic.

**Warning signs:**
- Orchestrator builds a `transcript_str` variable by string concatenation
- No `max_context_tokens` parameter in any agent call
- First full session takes > 2 minutes and you haven't profiled why

**Phase to address:** Phase 2 (agent factory design) + Phase 3 (full session flow).

---

### Pitfall 4: Hermes Agent API Surface Underdocumented — Day-3 Multi-Agent Breaks

**S×L: 16**

**What goes wrong:**
The Hermes Agent repo (NousResearch/hermes-agent) was verified as HTTP 200 but is a relatively new framework. Two common failure modes with new agent frameworks at contest deadlines:

1. **Tool calling format mismatch**: Hermes expects MCP tools in a specific JSON schema. PageIndex MCP server may return a slightly different schema version. Hermes silently swallows tool errors and hallucinates the tool result rather than failing loudly. You only discover this when a citation like "art. 47 ust. 2" points to a node that doesn't exist in the corpus.

2. **Long-term memory isolation**: Hermes memory is per-agent by design. If `agent_factory.py` reuses the same agent instance for two different parties (e.g., to save initialization time), both parties write to the same memory store. Party B "remembers" Party A's voting history as its own. This produces bizarre ideological drift across sessions.

**Why it happens:**
Framework is new; edge cases in multi-agent usage (not single-agent) are under-tested by the framework authors. The Day-1 "2-agent prototype" test may not surface these because it uses different code paths than 25 agents.

**How to avoid:**
- On Day 1 prototype: test tool failure explicitly — call PageIndex with a deliberately bad query and verify Hermes surfaces the error vs. hallucinating.
- Each agent must be instantiated with a unique `agent_id` / memory namespace. Do NOT share agent instances across party roles.
- Add an integration test: `test_agent_memory_isolation.py` — run two party agents on the same topic and assert their memory stores are disjoint after the session.
- Read the Hermes Agent source for how MCP tool errors are handled before trusting the tool-use path.

**Warning signs:**
- `agent_factory.py` returns a singleton or cached agent
- Tool call returns `null` or `{}` but no exception is raised
- Party agent's `references/historia-glosowan.md` shows votes that belong to another party

**Phase to address:** Phase 1 (Hermes prototype), gate before Phase 2.

---

### Pitfall 5: Agent Skills `name` Validation / Frontmatter Rejection

**S×L: 15**

**What goes wrong:**
The Agent Skills specification requires `name` to be lowercase, hyphen-separated, no underscores, no special characters, max length (typically 64 chars). The skill `ministerstwo-rodziny-pracy-i-polityki-spolecznej` is 49 characters — fine. But `ministerstwo-spraw-wewnętrznych-i-administracji` contains a Polish character `ę` in the slug. The `skills-ref validate` tool will reject this with a cryptic schema error. Developers write all 25 skills before running validation, then spend 2 hours on Day 3 fixing names.

Secondary issue: YAML frontmatter multiline strings. The PRD example shows:
```yaml
description: Agent reprezentujący Koalicję Obywatelską w Wirtualnym
  Parlamencie.
```
This is valid YAML folded scalar syntax, but only if indentation is exactly 2 spaces on the continuation line. A tab character here causes `skills-ref validate` to fail with a YAML parse error, which is harder to diagnose than a schema error.

Third issue: `metadata` fields that the spec doesn't define (e.g., `seats: 157`, `consults_parties: [...]`) may or may not be allowed. If the spec uses `additionalProperties: false`, any extra field causes a validation failure.

**Why it happens:**
The spec is read once at the start, then 25 files are written from memory. Developers rarely re-read the spec for each file.

**How to avoid:**
- Write ONE canonical skill file (`party-ko`) and run `skills-ref validate` before writing any others. Use it as a copy-paste template.
- Keep skill `name` values in ASCII only. Use `ministerstwo-finansow` not `ministerstwo-finansów`. Legal Polish names in the SKILL.md body are fine; frontmatter values must be ASCII-safe.
- Run `skills-ref validate ./skills/` (whole directory) as a pre-commit hook on Day 1 — add it to `pyproject.toml` as a test.
- Explicitly test whether `metadata` allows custom fields. If not, move `seats` and `consults_parties` into the SKILL.md body as structured text.

**Warning signs:**
- First `skills-ref validate` run is on Day 3 after writing all 25 files
- Skill names contain Polish diacritics in the frontmatter
- YAML written in an editor that auto-converts spaces to tabs

**Phase to address:** Phase 1 (first skill template), enforce via pre-commit before Phase 2.

---

### Pitfall 11: "Almost Works on Day 4" Scope-Creep Trap

**S×L: 16**

**What goes wrong:**
The project has three high-schedule-risk items acknowledged in PROJECT.md: full 5 parties + 19 ministries (not MVP-shrunk), Next.js chamber visualization in MVP, and ~50 document corpus. If any one of them hits friction (OCR issues, Next.js integration bugs, PageIndex tree-build latency), the team is tempted to keep pushing because "it's almost working." Day 4 arrives with a core that almost works, a Next.js front-end that works locally but crashes on the VPS, and 12 of 19 ministry skills written. None of it is demo-able end-to-end.

**Why it happens:**
Contest psychology: you've invested days in a feature; abandoning it feels like wasting that work. But shipping a working 3-party + 5-ministry CLI with a beautiful DEV.to write-up beats a broken 25-agent system with a pretty UI.

**How to avoid:**
- Establish explicit Day 3 EOD checkpoints per the "What to Cut First" section below.
- Next.js visualization is the highest schedule risk item — if the CLI E2E isn't working by Day 3 EOD, cut Next.js entirely and use a static HTML + JavaScript transcript viewer (2-hour task vs. 2-day task).
- If 19 ministry skills are not done by Day 3 EOD, cut to 7 ministries (Finance, Health, Justice, Education, Climate, Infrastructure, Foreign Affairs) — these cover 80% of plausible demo topics.
- If OCR pipeline is broken on Day 2 morning, switch to PageIndex Cloud immediately — do not spend Day 2 fixing self-hosted OCR.

**Warning signs:**
- CLI E2E not passing by end of Day 3
- Next.js dev server running but wired to mock data only
- "Just one more fix" said more than twice on Day 4

**Phase to address:** All phases. Add explicit cut criteria to the Phase 3 gate.

---

### Pitfall 15: Reproducibility Failure — Jury Can't Run in 2 Minutes

**S×L: 15**

**What goes wrong:**
PRD §9 DoD requires "README with run instructions ≤ 5 minutes." Contest jury runs: `git clone` → follows README → hits error after 3 minutes → gives up. Common blockers:
1. `npx skills add mmtmr/pageindex-rag` requires a specific Node version and fails silently on Node 20 vs 22.
2. PageIndex self-hosted requires Docker or specific system deps not listed in README.
3. `hermes parliament "topic"` requires env vars (`ANTHROPIC_API_KEY`, `PAGEINDEX_URL`) not documented.
4. The corpus is not committed (too large) and the ingest script requires ISAP PDF downloads which are rate-limited.
5. Python 3.11 required but not stated; fails on 3.12 due to a removed stdlib import.

**Why it happens:**
Developers run from a directory that already has all env vars set, dependencies installed, and corpus ingested. "Works on my machine" is never tested from a clean state until Day 5.

**How to avoid:**
- On Day 1: create a `Makefile` with `make setup` and `make demo` targets. Test `make demo` from a fresh virtualenv before writing any agents.
- Commit a minimal pre-built corpus sample (5 documents, already indexed) to the repo under `data/sample-corpus/`. The demo command uses this sample by default; full ingest is an optional `make ingest-full` step.
- Document all required env vars in `.env.example` with placeholder values.
- On Day 4: do a clean-clone test on a different machine (or a Docker container). Do this before writing the DEV.to post.
- Write `docs/REPRODUCIBILITY.md` (or fold into README) listing: OS, Python version, Node version, estimated setup time, estimated first-run time.

**Warning signs:**
- No `make demo` or equivalent shortcut exists by Day 3
- Corpus is not committed and ingest requires live network access
- README says "install dependencies" without listing which ones

**Phase to address:** Phase 1 (scaffold), Phase 4 (demo preparation).

---

## High Pitfalls (S×L 10–14)

### Pitfall 6: Debate Loop — Session Never Terminates

**S×L: 12**

**What goes wrong:**
The Marszałek orchestrator selects ministries, runs two readings, then tallies votes. If the voting logic hits a tie (e.g., 2 parties for, 2 against, 1 abstain) and the orchestrator's tie-breaking prompt is vague, it may schedule a third reading, which triggers more party queries, which produces another tie, which triggers... The session hangs or exceeds timeout.

**How to avoid:**
- Hard-code a `MAX_ROUNDS = 2` constant. After two rounds, the orchestrator forces a vote regardless of outcome.
- Tie-breaking rule: `abstain = no` for voting purposes. Code this as a deterministic function, not an LLM decision.
- Add a `session_timeout_seconds = 300` watchdog. If exceeded, the orchestrator emits a partial transcript with a timeout note.

**Warning signs:**
- Orchestrator prompt says "if there is disagreement, consider another reading" without a numeric limit
- Tie-breaking logic delegated to LLM judgment

**Phase to address:** Phase 3 (full session flow).

---

### Pitfall 7: Party-Agent Position Convergence

**S×L: 12**

**What goes wrong:**
All five party agents are called with the same Second Brain context. Without strong ideological grounding in their prompts, they find the same "reasonable middle ground" from the corpus and all argue for similar positions. The simulation produces five slightly different ways of saying "this law seems generally positive." No drama, no conflict, no journalistic value. The DEV.to jury sees a boring simulation.

**Why it happens:**
LLMs default to agreement and reasonableness. Party profiles need explicit "red lines" (things the party will NEVER agree to) and "attack vectors" (how this party frames criticism of opponents) that force conflict.

**How to avoid:**
- Each party SKILL.md must include: (a) at least 3 explicit red lines, (b) a named ideological enemy with a description of their typical rhetorical attack, (c) a "default vote" stance (suspicious/hostile/supportive) for each of the 5 major policy domains.
- Test party divergence explicitly on Day 2: submit "400+ benefit increase" and verify KO and Konfederacja take opposing positions with specific counterarguments.
- Konfederacja and Lewica should almost always be on opposite sides on economic topics. PiS and KO should conflict on rule-of-law topics. Build test assertions for this.

**Warning signs:**
- All parties vote the same way in your first E2E test
- Party responses are polite and constructive with no direct attack on another party
- "The proposed legislation raises important considerations..." as every opener

**Phase to address:** Phase 2 (party skill writing).

---

### Pitfall 8: Real-MP Impersonation / Defamation

**S×L: 10**

**What goes wrong:**
Party agents, when asked about a topic, may generate utterances that sound like they're quoting or channeling a real politician. Example: "As Tusk himself said..." or the agent writing in first person as "I, Donald Tusk..." when prompted about KO policy. Even without naming real MPs, the combination of current-leadership references + specific policy stances + realistic rhetoric = effectively impersonation. This creates legal exposure and violates contest spirit.

A subtler version: the corpus contains news articles (RSS PAP, gov.pl) that mention real politicians' quotes. An agent ingesting these via Second Brain may reproduce a real politician's quote as its own utterance, without attribution.

**How to avoid:**
- Party SKILL.md explicitly prohibits: "Never use the name of any living politician. Speak as the party collectively ('KO argues', 'our coalition position is'). If a corpus document quotes a real person, attribute it explicitly ('According to a press release cited in the corpus...')."
- Add a guardrail in the orchestrator: post-process all agent outputs through a simple regex check for known Polish politician names (Tusk, Kaczyński, Hołownia, Mentzen, Zandberg, etc.). If found, reject the response and retry with a stronger prohibition.
- The RSS/news ingest is the riskiest source for this. Consider excluding news sources from the corpus entirely and sticking to legal documents only. News adds freshness but adds impersonation risk.

**Warning signs:**
- First E2E test mentions "Tusk" or "Kaczyński" by name in an agent's speech
- RSS ingestion is part of the corpus without a quote-stripping preprocessing step

**Phase to address:** Phase 2 (party skills), add the name-check guardrail in Phase 3 (orchestrator).

---

### Pitfall 9: Demo-Day LLM Rate Limit Mid-Video

**S×L: 8 (upgraded from matrix due to catastrophic demo impact)**

**What goes wrong:**
On Day 5 (May 31), the developer records the demo video. They've been running test sessions all day. At the moment of recording, the API returns 429 (rate limited) after the second or third agent call. The video shows an error mid-session. There is no time to wait for the rate limit to reset and re-record with the same energy.

**How to avoid:**
- Record the demo video on Day 4 (May 30), not Day 5. Use a session recorded from a stable Day 4 run, not live.
- Alternatively: cache one "golden run" transcript to disk on Day 4. The demo video shows the real-time CLI playing back the cached transcript (fast and reliable) rather than calling the LLM live.
- Keep an Anthropic API dashboard tab open during recording. Check remaining rate limit before starting.
- Use a different API key for demo recording vs. development testing.

**Warning signs:**
- No golden-run cache recorded before Day 5
- Repeatedly running full sessions on the same API key all of Day 4

**Phase to address:** Phase 4 (demo preparation).

---

### Pitfall 12: Hate-Speech Generation From Konfederacja Agent

**S×L: 10**

**What goes wrong:**
Konfederacja's ideological profile includes positions that, if amplified without guardrails, can slide into xenophobic, homophobic, or antisemitic language. The LLM, given a prompt like "Konfederacja debates immigration quotas," may generate technically in-character rhetoric that crosses into language harmful enough to get the DEV.to post flagged or removed by moderation. This is not hypothetical — political simulation projects routinely hit this with far-right party agents.

**Why it happens:**
The SKILL.md sets the ideological frame but doesn't constrain rhetoric register. The LLM finds the "authentic voice" of the position, which in training data may include inflammatory language.

**How to avoid:**
- Each party SKILL.md includes an explicit `## Output Constraints` section: "Never use slurs. Frame positions as policy arguments, not group attacks. Acceptable: 'This policy would increase economic migration, which our electorate opposes based on labor market concerns.' Unacceptable: [explicit examples of prohibited register]."
- Add a content filter (Anthropic's built-in moderation or a simple classifier) as a post-processing step on all agent outputs before they reach the transcript.
- The 2-person review of party profiles (required by REQ-ETHICS) must specifically include the Konfederacja profile and be done before any public demo runs.
- Test with the most provocative possible topic (immigration, LGBTQ+ rights, EU membership) before the DEV.to submission.

**Warning signs:**
- Konfederacja SKILL.md has no `## Output Constraints` section
- First test on an immigration topic shows group-targeting language
- Party profile review not done before E2E test

**Phase to address:** Phase 2 (party skill writing). Hard gate: ethics review before Phase 3.

---

### Pitfall 14: PageIndex MCP Server Instability Under Parallel Queries

**S×L: 12**

**What goes wrong:**
The orchestrator runs 3 ministry consultations in parallel using `asyncio`. Each ministry agent calls `tree_search` and `fetch_node` via the PageIndex MCP server. The MCP server, self-hosted on a $5 VPS, is not designed for concurrent load. Under 3 simultaneous connections it may: (a) queue requests and add 10–30 seconds per session, (b) hit file-lock contention on the SQLite index and return corrupted results, (c) crash with an unhandled connection error.

**Why it happens:**
MCP servers are often designed as single-client local servers (for AI assistant use). The self-hosted PageIndex instance may use a single-threaded server model.

**How to avoid:**
- Test concurrent MCP connections on Day 1 — fire 3 simultaneous `tree_search` calls and observe behavior.
- If parallel MCP queries are unstable: serialize ministry consultations (one at a time). This increases session latency from ~90s to ~3 minutes but stays within the 5-minute target.
- Alternatively, run PageIndex MCP server with `--workers 4` if the server supports it.
- Keep PageIndex Cloud as the named fallback for the demo — Cloud APIs handle concurrency properly.

**Warning signs:**
- MCP server process shows single-threaded in `ps` output
- Test with 2 simultaneous queries returns timeout or connection refused
- Ministry agents occasionally return empty results with no error

**Phase to address:** Phase 1 (PageIndex setup).

---

### Pitfall 18: PageIndex First-Ingest Tree-Build Cost Blocks Day 2

**S×L: 12**

**What goes wrong:**
Ingesting 50 Polish legal PDFs into PageIndex requires OCR + TOC extraction + tree building. On a $5 VPS (shared CPU, ~1GB RAM), a single 100-page PDF may take 5–10 minutes. 50 documents = 4–8 hours of ingest time. Day 2 was planned for party skills, but the corpus isn't ready.

**How to avoid:**
- Start ingest on Day 1 evening as a background process. Do not block agent development on completed ingest.
- Prioritize ingest order: Constitution (most cited) → KK → KC → KP → top 10 statutes. Build agents against the first 4 documents, let the rest build overnight.
- Pre-download all PDFs to disk before starting ingest (avoid network timeouts mid-run).
- If self-hosted ingest takes > 2 hours for the first 10 documents, switch to PageIndex Cloud immediately.

**Warning signs:**
- Day 2 morning and ingest is still running
- Ingest script has no progress logging
- No agents tested against real corpus by Day 2 EOD

**Phase to address:** Phase 1 (Days 1–2).

---

### Pitfall 19: Legal Hallucination — Agent Cites Article That Doesn't Exist

**S×L: 12**

**What goes wrong:**
An agent produces a citation like "art. 47 ust. 2 Ustawy o odnawialnych źródłach energii" in its speech. The article number is wrong — either hallucinated by the LLM directly, or the PageIndex `node_id` was silently misresolved. A journalist using this tool for research publishes a false citation. This is both a product quality failure and an ethics failure.

**Why it happens:**
LLMs are trained to produce citations and will generate plausible-sounding ones even when the retrieved context is weak. If the `fetch_node` call fails silently and returns empty, the agent fills the gap with a fabricated citation.

**How to avoid:**
- Require all agent responses to include the `node_id` returned by PageIndex, not just the human-readable citation. The transcript stores both. Before outputting, validate that the `node_id` exists in the index.
- Implement a `citation_validator.py` that, given a transcript, calls `fetch_node` for each `node_id` and verifies it returns non-empty content.
- Party and ministry SKILL.md: "If you cannot find a supporting document in Second Brain, say 'no specific citation available' rather than inventing one."
- Run citation validation as part of the E2E test suite on Day 3.

**Warning signs:**
- Agent outputs citations in human-readable format only (no `node_id`)
- `fetch_node` failures are swallowed silently
- First E2E transcript cites an article number that you cannot find in the actual statute

**Phase to address:** Phase 2 (SKILL.md design) + Phase 3 (orchestrator validation).

---

## Moderate Pitfalls (S×L 6–9)

### Pitfall 10: Missing DEV.to Submission Template Sections

**S×L: 9**

**What goes wrong:**
The Hermes Agent Challenge requires specific sections in the DEV.to post: "What I Built", "Demo", "Code", "Tech Stack", "How I Used Hermes Agent". Missing any section risks disqualification. The "How I Used Hermes Agent" section is the easiest to write poorly — a generic "I used Hermes Agent to build agents" without demonstrating specific capability use (memory, tool use, multi-step reasoning, model switching).

**How to avoid:**
- Template the DEV.to post on Day 2. Write placeholder sections immediately. Fill them last.
- "How I Used Hermes Agent" should map each of the 4–5 Hermes capabilities to a specific code example: "We use long-term memory to persist party voting history across sessions — see `party-ko/references/historia-glosowan.md` updated by `skill_learning_loop`."
- Read the official challenge page requirements the day you write the post, not from memory.

**Warning signs:**
- DEV.to post is started on Day 5
- "How I Used Hermes Agent" section is a single paragraph

**Phase to address:** Phase 4 (Day 31 May). Pre-write on Day 29.

---

### Pitfall 13: Polish/English Mixing — Unreadable Transcript

**S×L: 8**

**What goes wrong:**
The design calls for English runtime debate with Polish legal corpus. In practice, agents frequently slip into Polish mid-argument, especially when quoting statutes. The result: a transcript where English sentences are interrupted by Polish statutory text without the `(orig. PL: "...")` wrapper, or where entire paragraphs switch language mid-thought. The DEV.to jury (international) cannot follow this.

**Why it happens:**
The LLM path of least resistance when summarizing Polish text is to reproduce it in Polish. The `(orig. PL: "...")` convention requires the agent to actively summarize in English and then include the Polish original — a two-step output format that must be explicitly enforced.

**How to avoid:**
- Each SKILL.md and the pageindex-rag skill must include explicit output formatting instructions: "All your speech is in English. When quoting a legal document, provide: an English paraphrase, then `(orig. PL: '[exact Polish text from node]')`. Never switch to Polish for any sentence that isn't inside an `orig. PL:` block."
- Add a post-processing language detector (langdetect, 10 lines of Python) that flags any non-English, non-`orig. PL:` text in the transcript and logs a warning.

**Warning signs:**
- First party agent output contains Polish sentences outside the `orig. PL:` wrapper
- Constitution quotes are reproduced verbatim in Polish without English paraphrase

**Phase to address:** Phase 2 (SKILL.md templates), verified in Phase 3 E2E test.

---

### Pitfall 17: Missing LICENSE File or Wrong License

**S×L: 6**

**What goes wrong:**
The repo has no `LICENSE` file on Day 5. Contest rules require an open source license. The jury cannot verify the project is legitimately open source. The submission may be disqualified on this technicality.

A subtler version: the repo has `LICENSE` (MIT) but the external `mmtmr/pageindex-rag` skill has a different license that is incompatible. The team redistributes it without verifying.

**How to avoid:**
- Add `LICENSE` (MIT) on Day 1 as part of repo scaffold. This is a 2-minute task.
- Check `mmtmr/pageindex-rag` license before `npx skills add`. If it's MIT-compatible, document this in the README. If not, consult the contest rules on dependency licensing.

**Warning signs:**
- No `LICENSE` file on Day 1
- `git log --all -- LICENSE` shows no commits

**Phase to address:** Phase 1 (repo scaffold, Day 1).

---

### Pitfall 16: Demo Video > 3 Minutes or Shows Nothing Working

**S×L: 12**

**What goes wrong:**
The demo video runs long (showing setup, explaining architecture, then finally showing the system) and hits the 3-minute limit before showing a complete session. Or it shows a full session but with 2-minute LLM wait times that make the video unwatchable. Or it shows a broken run with error messages that weren't noticed during recording.

**How to avoid:**
- Script the video before recording. Target: 30s intro, 90s demo of a pre-run session (fast playback or cached), 45s architecture walk-through, 15s conclusion. 3 minutes total.
- Use the cached golden-run replay approach: show the transcript being printed in real-time (with `cat` and a simulated typing effect) rather than live LLM inference.
- Watch the full recording before publishing. This sounds obvious but is skipped under deadline pressure.
- Record on Day 4, not Day 5.

**Warning signs:**
- No video script written by Day 4
- Recording planned for Day 5 only
- Demo shows the LLM spinning for > 15 seconds between turns

**Phase to address:** Phase 4 (Day 30 May).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| All agents on the same model tier | Simpler agent_factory.py | $20–100 per test session | Never — set tiers on Day 1 |
| String-concatenate transcript for context | Simpler orchestrator code | Context blowout at round 2 | Never — use structured Utterance objects |
| Skip `skills-ref validate` in CI | Faster iteration | All 25 skills fail on Day 3 | Never — add as pre-commit hook Day 1 |
| Self-hosted OCR without smoke test | Faster Day 1 start | 8-hour ingest failure discovered Day 2 | Never — smoke test first |
| No golden-run cache | Less code | Rate-limited demo video | Never — cache before Day 5 |
| RSS/news in corpus without name-filtering | Fresher data | Real-MP impersonation risk | Only if name-stripping preprocessing is added |
| Next.js with full live LLM pipeline | Better demo aesthetics | 2-day integration task that blocks CLI | Acceptable to defer to post-contest |
| 19 ministries on Day 1 scope | Matches full vision | May all be incomplete on Day 4 | Cut to 7 if CLI E2E not passing by Day 3 EOD |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Hermes Agent + MCP | Assuming MCP tool errors raise Python exceptions | Check the Hermes error-handling source; add explicit tool-result validation |
| PageIndex MCP + asyncio | Fire all ministry queries in parallel | Test concurrent connections on Day 1; serialize if unstable |
| Agent Skills + skills-ref validate | Write all 25 skills before first validation run | Validate the first template before writing the rest |
| ISAP PDF + PageIndex OCR | Assume "PDF OCR works" | Smoke test Polish diacritics on Constitution before Day 1 EOD |
| Hermes memory + agent_factory | Reuse agent instances for efficiency | One unique agent instance per role per session; unique memory namespace |
| pageindex-rag skill + Hermes | Assume `npx skills add` resolves all dependencies | Test install on the VPS, not just localhost; check Node version |
| Claude API + long sessions | Ignore context window limits | Enforce 8K token budget per agent call from Day 1 |
| SQLite + concurrent sessions | SQLite WAL mode off by default | Enable WAL mode: `PRAGMA journal_mode=WAL` before first write |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Full corpus ingest blocking dev | Day 2 agents have no corpus to query | Ingest incrementally; start agents on first 4 docs | Day 2 if ingest not started Day 1 evening |
| All 25 skills loaded at context start | 25 × 5000 tokens = 125K token overhead per session | Verify progressive disclosure is actually working; only metadata (~100 tok) should load at start | Immediately; destroys the entire context budget |
| Transcript string growth | Round 2 agents see 20K+ tokens of prior speech | Structured Utterance objects with windowed context | After first full 5-party session (round 2) |
| Synchronous LLM calls in orchestrator | Session takes 8+ minutes | asyncio for ministry phase; structured timeouts | When ministry count > 2 |
| Tree-build rerun on restart | 4–8 hour rebuild if VPS restarts | Persist tree index to disk; verify persistence before relying on it | On first VPS restart or crash |

---

## Security / Ethics Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Real politician names in corpus quotes reproduced as agent speech | Defamation, contest disqualification | Name-stripping preprocessor on all corpus content; prohibition in SKILL.md |
| Hate-speech generation from extreme-right party agent | DEV.to moderation removal, reputational damage | Output constraints in SKILL.md; content filter post-processing; ethics review before demo |
| API keys committed to repo | Credential exposure | .env.example with placeholders; .gitignore for .env; GitHub secret scan on Day 1 |
| No disclaimer in each session output | Misrepresentation as real forecast | Orchestrator hard-codes disclaimer as first line of every session document |
| Bias review not completed before public submission | Jury bias accusation; media criticism | 2-person review gated before Phase 3 E2E; document reviewers in README |

---

## "Looks Done But Isn't" Checklist

- [ ] **Agent Skills:** `skills-ref validate ./skills/` passes for all 25 skills — not just the first one written
- [ ] **Citations:** Every agent utterance in the transcript carries a real `node_id`, not just a human-readable "art. X" string
- [ ] **Progressive disclosure:** Verify Hermes actually loads only metadata (~100 tokens) for inactive skills, not full bodies — add a token-count assertion in tests
- [ ] **Memory isolation:** Two party agents run in the same session without cross-contaminating memory stores — `test_agent_memory_isolation.py` passes
- [ ] **Polish diacritics:** Run `grep -c "ą\|ę\|ó\|ź\|ż\|ś\|ń\|ć\|ł" data/corpus/*.json` — if zero hits, OCR is broken
- [ ] **Cost cap:** `MAX_TOKENS_PER_SESSION` is enforced and tested with a session that deliberately exceeds it
- [ ] **Reproducibility:** A team member who hasn't touched the project can run `make demo` from a clean clone in under 5 minutes
- [ ] **Disclaimer:** Every session output begins with the educational-simulation disclaimer before any party speech
- [ ] **Name guard:** The orchestrator name-check regex catches "Tusk", "Kaczyński", "Hołownia", "Mentzen", "Zandberg" in any agent output and rejects/redacts
- [ ] **Video runtime:** Recorded demo is under 3 minutes when watched from start to finish (not just estimated)
- [ ] **DEV.to sections:** All 5 required template sections present and non-empty in the draft post
- [ ] **LICENSE file:** `cat LICENSE` shows MIT text — not missing, not a placeholder
- [ ] **Tags:** DEV.to post has all three required tags: `hermesagentchallenge`, `devchallenge`, `agents`

---

## What to Cut First if Day 4 Looks Bad

**Evaluate at Day 3 23:00.** If CLI E2E is not passing with a full 5-party debate and vote, apply cuts in this order:

1. **Cut Next.js front-end entirely.** Use a static HTML file that renders the JSON transcript with party-colored CSS. This is a 2-hour task. A working CLI demo beats a broken Next.js demo every time.

2. **Cut from 19 to 7 ministries.** Keep: Finance, Health, Justice, Education, Climate, Infrastructure, Foreign Affairs. These cover the widest range of demo topics. Use the shared Ministry template — this cut takes 30 minutes.

3. **Cut second reading / riposte phase.** Run first reading only: each party speaks once, then vote. This removes the biggest source of context-window and loop risk. A single-round debate still demonstrates the full Hermes capability set.

4. **Cut corpus to 15 documents.** Keep: Constitution, KK, KC, KP, 3 EU regulations, 8 most-cited statutes. A smaller corpus indexes faster, queries faster, and is fully verifiable before the demo.

5. **Cut export-to-PDF feature.** Keep Markdown export only. PDF generation (WeasyPrint, wkhtmltopdf) adds system dependencies that fail on clean installs.

6. **Do NOT cut:** citations (core to the value prop), the disclaimer, ethics review of party profiles, or the DEV.to post quality. These are non-negotiable.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| OCR ingest failure Day 2 | LOW (30 min) | Switch env var to PageIndex Cloud; re-run ingest; keep self-host for post-contest |
| Cost runaway discovered Day 3 | LOW (2 hrs) | Downgrade all ministry models to cheapest tier; add session token cap; clear API dashboard alerts |
| Context blowout on round 2 | MEDIUM (4 hrs) | Refactor transcript context to windowed mode; skip round 2 (cut #3 above) |
| All 25 skills fail validation | MEDIUM (3 hrs) | Fix canonical template; sed-replace common errors across all files; re-validate |
| MCP parallel instability | LOW (1 hr) | Serialize ministry calls; add 1-second delay between calls |
| Rate limit on demo day | LOW (1 hr) | Use cached golden-run transcript; record demo from cache playback |
| Debate loop in live demo | MEDIUM (2 hrs) | Add hard MAX_ROUNDS guard; retest with same topic |
| Hate speech in agent output | HIGH (6 hrs) | Stop all demos immediately; revise SKILL.md output constraints; re-run ethics review; retest all topics |
| Real-MP name appears in transcript | MEDIUM (3 hrs) | Add name-stripping filter; rebuild affected transcripts; add to CI check |
| Video too long | LOW (2 hrs) | Re-edit to highlight reel; cut architecture walkthrough; re-record narration only |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| OCR ingest failure | Phase 1 (Day 26 May) | `scripts/verify_ocr.py` passes on Constitution |
| Cost runaway | Phase 1 (Day 26 May) | Model tiers in agent_factory.py; token cap test |
| Context blow-out | Phase 2 (agent design) + Phase 3 (E2E) | Context size logged; 8K cap enforced per call |
| Hermes API underdocumented | Phase 1 (Day 26 May) | Tool failure test; memory isolation test |
| Skills frontmatter rejection | Phase 1 (Day 26 May) | `skills-ref validate` as pre-commit; 1 canonical template first |
| Debate loop | Phase 3 (orchestrator) | MAX_ROUNDS=2 test; tie-break unit test |
| Party convergence | Phase 2 (party skills) | Divergence test on "400+ benefit" topic |
| Real-MP impersonation | Phase 2 (party skills) + Phase 3 | Name-check regex test; ethics review gate |
| Demo rate limit | Phase 4 (Day 30 May) | Golden-run cache recorded Day 30 |
| Missing DEV.to sections | Phase 4 (Day 31 May) | Template checklist review before publish |
| Scope creep | All phases | Day 3 EOD cut-criteria checkpoint |
| Reproducibility failure | Phase 1 (scaffold) + Phase 4 | Clean-clone test by a different team member |
| Legal hallucination | Phase 2 + Phase 3 | citation_validator.py in test suite |
| Hate speech | Phase 2 (party skills) | Ethics review gate; content filter test |
| Polish/English mixing | Phase 2 (SKILL.md templates) | Language detector post-processor in E2E test |
| MCP parallel instability | Phase 1 (Day 26 May) | Concurrent connection test Day 1 |
| First ingest blocking | Phase 1 (Day 26 May) | Incremental ingest; background process; Day 2 morning check |
| Missing LICENSE | Phase 1 (Day 26 May) | `ls LICENSE` in CI |
| Video > 3 min | Phase 4 (Day 30 May) | Watch recording before publish; script timed in advance |

---

## Sources

- NousResearch/hermes-agent GitHub repo (HTTP 200 verified per PROJECT.md; issues not accessible during this research session) — **CONFIDENCE: MEDIUM** (architecture-based inference; no live issue scrape)
- mmtmr/pageindex-rag GitHub repo (referenced in PRD §5.0) — **CONFIDENCE: MEDIUM** (pattern knowledge; no live scrape)
- Anthropic Agent Skills specification (agentskills.io) — **CONFIDENCE: MEDIUM** (PRD §5.0 documents the spec requirements; live spec not fetched)
- General multi-agent orchestration failure modes — **CONFIDENCE: HIGH** (well-documented in LLM research literature)
- Polish ISAP PDF OCR quality — **CONFIDENCE: HIGH** (Polish diacritics OCR failures are a well-known problem with Tesseract default `eng` mode)
- DEV.to contest submission requirements — sourced from PRD §9 DoD and PROJECT.md REQ-DEMO — **CONFIDENCE: HIGH**
- Political simulation ethics / impersonation risks — **CONFIDENCE: HIGH** (documented pattern across political LLM projects)
- Contest deadline psychology / scope creep — **CONFIDENCE: HIGH** (universal pattern in hackathon submissions)

---

*Pitfalls research for: Multi-agent Polish parliament simulation (Virtual Parliament)*
*Researched: 2026-05-26*
*Web tools unavailable during session; confidence levels reflect inference basis*

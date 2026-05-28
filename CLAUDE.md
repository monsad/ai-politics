<!-- GSD:project-start source:PROJECT.md -->
## Project

**Virtual Parliament**

Virtual Parliament is a multi-agent simulation of the Polish Sejm. Five party agents (KO, PiS, TD, Konfederacja, Lewica), nineteen ministry-expert agents, and a Marszałek orchestrator debate, consult, and vote on user-submitted bills. A Second Brain (PageIndex) holds the Polish Constitution, criminal/civil codes, ~50 statutes and EU regulations so every argument cites a real legal source. It is a competition entry for the [Hermes Agent Challenge](https://dev.to/devteam/join-the-hermes-agent-challenge-1000-in-prizes-13cd) targeting journalists, law/political-science students, hobbyist voters, and the contest jury.

**Core Value:** Type in a bill topic → get a full, source-cited parliamentary simulation (ministry expertise → party debate → vote → draft bill) in ≤ 5 minutes, with every argument traceable to a real Polish legal document.

### Constraints

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
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## PRD Assumptions vs Reality — Corrections First
| PRD Claim | Reality | Action |
|-----------|---------|--------|
| Hermes Agent install path unspecified | PyPI: `pip install hermes-agent==0.14.0`; OR install script (installs its own Python 3.11 + uv). NOT importable as a Python library for programmatic spawning — it is a CLI/TUI agent framework. | Day 1 prototype must verify how Hermes exposes a programmable API. See note below. |
| `agentskills.io/specification` as spec URL | CONFIRMED real. Spec is at `agentskills.io/specification`. Frontmatter fields verified. CLI for validation is `skills-ref` not `skills validate`. | Use `skills-ref validate` (from `npm install -g skills-ref@0.1.5`). |
| `npx skills add mmtmr/pageindex-rag` install command | CONFIRMED real. Skill exists at `github.com/mmtmr/pageindex-rag`, installs via `npx skills add mmtmr/pageindex-rag -g -y`. | Install command is correct. |
| PageIndex = self-hosted open source RAG | TWO separate projects exist. (1) `VectifyAI/PageIndex` (32k stars, MIT, Python, self-hostable, `pip install`) uses PyMuPDF + LiteLLM. (2) `VectifyAI/pageindex-mcp` (npm `pageindex-mcp@1.6.3`) is the MCP server wrapping PageIndex Cloud API. For self-host, use the Python library directly + expose a custom MCP wrapper, NOT the npm package. | See PageIndex section below. |
| PageIndex MCP server = `pageindex-mcp` npm package | `pageindex-mcp` on npm is a **cloud client** requiring a PageIndex Cloud API key (https://dash.pageindex.ai). Free tier: 1000 pages. For self-host: run VectifyAI/PageIndex Python library + build an MCP wrapper, or use PageIndex Cloud as primary (fits contest budget). | Decide: Cloud (easier, 1000 pages free) vs self-host (more work, zero cloud cost). |
| Hermes `delegate_task` for parallel ministry fan-out | CONFIRMED: `delegate_task(tasks=[...])` in batch mode uses `ThreadPoolExecutor` to spawn parallel `AIAgent` child instances. This is the correct fan-out pattern — use it, don't build asyncio fan-out separately. | The Marszałek skill calls `delegate_task(tasks=[{goal, context, toolsets}, ...])` to consult 2-3 ministries in parallel. |
| Next.js "optional, Streamlit first" | Next.js 16.2.6 is latest stable (major version jump since most training data). App Router + Route Handlers with `text/event-stream` is the correct streaming pattern. Streamlit is NOT recommended — it introduces a Python web framework that duplicates the CLI pipeline instead of wrapping it cleanly. | Use Next.js 16.2.6 with App Router from Day 1. |
## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **hermes-agent** | 0.14.0 (PyPI, released 2026-05-16) | Agent framework, skills loading, MCP client, long-term memory, delegate_task fan-out | Contest requirement; `pip install hermes-agent==0.14.0`. Python 3.11+ required. MIT. 167k stars, actively maintained. |
| **VectifyAI/PageIndex** | head (MIT, no PyPI package, install from source) | Self-hosted vectorless RAG: PDF ingestion, hierarchical tree index, LLM-driven retrieval | Avoids cloud dependency for 50-doc corpus. Uses PyMuPDF + LiteLLM. Run `git clone + pip install -r requirements.txt`. |
| **pageindex-mcp (Cloud)** | 1.6.3 (npm, `npx pageindex-mcp`) | PageIndex Cloud MCP server — fallback if self-host fails before deadline | Free tier: 1000 pages. OCR handled by PageIndex Cloud (Polish PDFs solved). Node.js >=20.8.1. |
| **skills-ref** | 0.1.5 (npm) | Validate Agent Skills SKILL.md frontmatter before each commit | `npx skills-ref validate ./skills/<agent-id>`. Required per REQ-AGENTS-FORMAT. |
| **skills (CLI)** | 1.5.7 (npm, `vercel-labs/skills`) | Install external skills including `mmtmr/pageindex-rag` | `npx skills add mmtmr/pageindex-rag -g -y`. Maintained by Vercel Labs, lists hermes-agent as supported. |
| **Python** | 3.11 (exact — hermes-agent requires `>=3.11`, installer defaults to 3.11) | Orchestration, ingest, CLI | hermes-agent pyproject.toml: `requires-python = ">=3.11"`. Use 3.11 not 3.12/3.13 for maximum compat. |
| **Next.js** | 16.2.6 | Web visualization — parliament chamber with party-colored transcript | Latest stable. App Router with Route Handlers for SSE transcript streaming. React 19. |
| **SQLite** | built-in (use via `aiosqlite 0.20+`) | Session and transcript storage | Sufficient for contest scope (hundreds of sessions max). Hermes itself uses SQLite for session DB (`hermes_state.py`). |
| **typer** | 0.25.1 (PyPI) | Python CLI — `hermes parliament "<topic>"` | Standard choice for Python CLIs with rich help output. Type-hinted. |
### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `mcp` | 1.27.1 (PyPI) | MCP client SDK — connect Python code to pageindex-mcp server | When building a Python-side MCP client wrapper around PageIndex or any MCP server |
| `pymupdf` | 1.27.2.3 (PyPI) | PDF text extraction from Polish legal PDFs | Primary path for text-based ISAP PDFs (most modern statutes are born-digital). Used directly by VectifyAI/PageIndex. |
| `litellm` | 1.83.7 (per PageIndex requirements.txt) | LLM-agnostic wrapper — PageIndex uses it internally; also useful for model-switching in ministries vs orchestrator | PageIndex ingest pipeline; also use for cheaper ministry model vs stronger orchestrator model. |
| `aiosqlite` | 0.20+ (PyPI) | Async SQLite access | Session writes during concurrent ministry consultations |
| `python-dotenv` | 1.2.2 (pinned by hermes-agent) | Load `.env` for API keys | Both hermes-agent and PageIndex use it; pin to same version |
| `httpx` | 0.28.1 (pinned by hermes-agent) | HTTP client for PageIndex Cloud API fallback | Already a hermes-agent dep; no extra install |
| `pyyaml` | 6.0.3 (pinned by hermes-agent) | Parse SKILL.md frontmatter in Python tests | Already a hermes-agent dep |
| `surya-ocr` | 0.17.1 (PyPI) | OCR for scanned Polish PDFs that PyMuPDF cannot extract | Only needed for pre-2000 ISAP scans; Surya supports Polish diacritics natively. Avoid Tesseract (requires system install + lang pack). |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| `uv` | Python venv + install (hermes-agent uses it internally) | Hermes installer sets up uv automatically. Use `uv venv .venv --python 3.11 && uv pip install -e ".[all]"` for dev setup. |
| `skills-ref validate` | Validate SKILL.md before commit | Run as pre-commit hook: `npx skills-ref validate ./skills/<agent-id>` |
| `npx skills add` | Install external skills | `npx skills add mmtmr/pageindex-rag -g -y` — puts skill in `~/.hermes/skills/` |
| `hermes model` | Switch LLM provider/model | No code changes needed. Use `Nous Portal` (one sub for all tools) or `OpenRouter` for cheaper ministry models. |
| `hermes doctor` | Diagnose install issues | Run after install to verify MCP, tools, skills are loaded. |
## Installation
# 1. Hermes Agent (via installer — sets up uv + Python 3.11 automatically)
# OR: pip install into existing Python 3.11 venv
# 2. Agent Skills tooling
# 3. PageIndex self-host (Python, from source)
# 4. PageIndex Cloud MCP server (fallback, Node.js >=20.8.1)
# Add to ~/.hermes/config.yaml under mcp_servers:
# pageindex:
#   command: npx
#   args: ["-y", "pageindex-mcp"]
#   env:
#     PAGEINDEX_API_KEY: "your_key_from_dash.pageindex.ai"
# 5. Python project dependencies
# 6. Next.js frontend
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `hermes-agent` via PyPI | Source clone `NousResearch/hermes-agent` | Only if you need to patch hermes internals. Contest use: PyPI. |
| VectifyAI/PageIndex (self-host, Python) | `pageindex-mcp` cloud only | Cloud is easier for the contest (5-day deadline). Use cloud if self-host OCR fails on any ISAP scan before 2026-05-28. |
| PyMuPDF for PDF text | pdfplumber 0.11.9 | pdfplumber is better for table-heavy PDFs; PageIndex uses PyMuPDF, so stay consistent. |
| surya-ocr for scanned PDFs | pytesseract 0.3.13 | Tesseract requires system-level install (`apt install tesseract-ocr tesseract-ocr-pol`) and is slower. Surya is pure Python. But Surya needs a GPU or is slow on CPU. On a $5 VPS: use PageIndex Cloud (handles OCR server-side) instead of either. |
| SQLite (aiosqlite) | PostgreSQL | PostgreSQL only when multi-process writes become a bottleneck. Not needed for contest. |
| Next.js 16 App Router + SSE | Streamlit | Streamlit introduces a second Python web process that must replicate or proxy the orchestrator pipeline. Next.js wraps the same Python pipeline via subprocess or a lightweight FastAPI bridge, and produces a better visual demo. |
| Next.js Route Handler SSE | WebSockets | SSE is unidirectional (server→client), which is all we need for transcript streaming. Simpler to implement in Next.js Route Handlers without a separate WS server. |
| `delegate_task(tasks=[...])` batch mode | asyncio.gather with manual AIAgent instantiation | `delegate_task` is the blessed Hermes API for fan-out. Manual `AIAgent` instantiation bypasses hermes-agent's tool registry, approval callbacks, and context isolation. Do not replicate it. |
| litellm (via PageIndex) | Direct OpenAI SDK | litellm provides model-switching without code changes — critical for using cheaper models (e.g., `Nous Portal:hermes-3-8b`) for ministries and stronger models (e.g., `claude-opus-4`) for the orchestrator. |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `ChromaDB` / `FAISS` / any vector store | Contest constraint (REQ-BRAIN) and architecture constraint: legal documents have native hierarchy that chunking destroys. Citation traceability is mandatory and impossible with opaque vector search. | VectifyAI/PageIndex (vectorless tree RAG) |
| `streamlit` | Creates a second Python web process duplicating the pipeline; TUI-style, not parliament-chamber-style; poor SSE/streaming story; jury expects a real web app for a visual demo. | Next.js 16 App Router |
| `pytesseract` on VPS | Requires `apt install tesseract-ocr-pol` (Polish language pack), slow on CPU, Polish diacritic quality is inconsistent. | surya-ocr (Python-only, no system deps) OR PageIndex Cloud (recommended for time-constrained contest) |
| `hermes-agent[all]` extras in prod | `[all]` installs voice, TTS, browser, modal, daytona — none needed for this project. Significantly larger install. | `hermes-agent` base + `anthropic` extra only if using Claude directly (not via OpenRouter) |
| `asyncio.gather` for ministry fan-out | Tempting but wrong layer. Hermes subagents run on threads (ThreadPoolExecutor), not coroutines. Mixing asyncio tasks with threaded AIAgent instances causes deadlocks on the prompt_toolkit TUI stdin. | `delegate_task(tasks=[...])` batch mode — this is the documented Hermes fan-out pattern |
| Pinning `python>=3.12` | hermes-agent is tested on 3.11. PyMuPDF wheels are available for 3.11+. surya-ocr has no 3.13 wheels on all platforms. 3.11 is safest. | Python 3.11 (exact) |
| `next@canary` | 16.3.0-canary.* versions are untested. Latest stable is 16.2.6. | `next@16.2.6` |
| Custom MCP server implementation | Building a custom Python MCP server from scratch for PageIndex costs 0.5+ dev days. PageIndex Cloud MCP is production-ready. | `pageindex-mcp` npm package (cloud) or the existing Python `pageindex` client directly from orchestrator code |
## Stack Patterns by Variant
- Install `pageindex-mcp@1.6.3` as an MCP server in `~/.hermes/config.yaml`
- Each agent accesses it via Hermes MCP tool dispatch (zero Python integration code)
- Free tier: 1000 pages — sufficient for ~50 statutes at ~20 pages average
- Pricing beyond free: check `dash.pageindex.ai` (API key required)
- Polish OCR handled server-side — no local OCR infrastructure needed
- Clone `VectifyAI/PageIndex`, run ingest pipeline locally
- Use `litellm` with a cheap model (e.g., `gpt-4o-mini` via OpenRouter) for tree building
- Output: JSON tree files stored in `data/indices/`
- Build a thin Python MCP wrapper using `mcp==1.27.1` (`FastMCP`) to expose `tree_search`, `doc_search`, `fetch_node`
- Add to hermes config as a `command: python` stdio server
- Polish OCR: use `surya-ocr` for scanned PDFs, fall back to PageIndex Cloud for problem files
- `hermes setup --portal` handles OAuth + Tool Gateway
- Single subscription covers all model API calls (no OpenRouter account needed)
- `hermes model` to switch between Nous models
- Ministry agents: `hermes-3-8b` (fast, cheap)
- Orchestrator + parties: `hermes-3-70b` or `claude-opus-4`
- Set `OPENROUTER_API_KEY` in `.env`
- 200+ models accessible via `openrouter/model-name` format in litellm
- Useful for cost optimization: `openrouter/mistral-7b-instruct` for ministries
- No subscription needed, pay-per-token
## Agent Skills Specification — Verified Fields
# Required fields
# Optional fields
## Hermes Agent — Verified API Surface
# OR via curl installer (sets up uv + Python 3.11 + Node.js)
# This is the Hermes-native pattern — invoked as a tool by the Marszałek agent
# In the Marszałek SKILL.md, instruct the agent to call:
# Hermes runs these in parallel via ThreadPoolExecutor, collects results
## PageIndex — Verified Architecture
## Polish PDF OCR — Decision Tree
## Version Compatibility
| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `hermes-agent==0.14.0` | Python `>=3.11` | Use 3.11 for broadest wheel availability |
| `pymupdf==1.27.2.3` | Python 3.8-3.13 | wheels on all platforms; use version matching PageIndex requirements |
| `litellm==1.83.7` | Python 3.9+ | Used by PageIndex; pin this exact version to avoid conflicts |
| `mcp==1.27.1` | Python 3.10+, `@modelcontextprotocol/sdk ^1.17.3` | Python MCP SDK; version used by pageindex-mcp npm |
| `pageindex-mcp@1.6.3` | Node.js `>=20.8.1` | Must have Node 20 LTS or newer |
| `next@16.2.6` | Node.js >=18 (recommend >=20 for consistency with pageindex-mcp) | React 19 included |
| `skills-ref@0.1.5` | Node.js >=18 | Validation CLI |
| `skills@1.5.7` | Node.js >=18 | `npx skills add` command |
| `typer==0.25.1` | Python 3.7+ | Works with hermes-agent Python 3.11 |
| `aiosqlite` | Python 3.7+ | Use latest; no version conflicts |
## Sources
- `github.com/NousResearch/hermes-agent` — `pyproject.toml`, `run_agent.py`, `tools/delegate_tool.py`, `tools/mcp_tool.py`, `RELEASE_v0.14.0.md`, `cli-config.yaml.example` — verified live 2026-05-26
- PyPI registry — `hermes-agent` versions 0.13.0, 0.14.0 confirmed — verified live 2026-05-26
- `agentskills.io/specification` — frontmatter schema, directory structure, progressive disclosure spec — verified live 2026-05-26
- npm registry — `skills-ref@0.1.5`, `skills@1.5.7`, `pageindex-mcp@1.6.3`, `next@16.2.6` — verified live 2026-05-26
- `github.com/mmtmr/pageindex-rag` — skill exists, install command confirmed — verified live 2026-05-26
- `github.com/VectifyAI/PageIndex` — `requirements.txt`, `pageindex/utils.py`, `run_pageindex.py` — verified live 2026-05-26
- `github.com/VectifyAI/pageindex-mcp` — README, cloud vs local MCP setup — verified live 2026-05-26
- PyPI registry — `pymupdf@1.27.2.3`, `surya-ocr@0.17.1`, `typer@0.25.1`, `mcp@1.27.1`, `litellm@1.83.7` — verified live 2026-05-26
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

<!-- BEGIN @przeprogramowani/10x-cli -->

## 10xDevs AI Toolkit — Module 1, Lesson 1

Bootstrap a greenfield project end-to-end with the **shaping chain**:

```
/10x-init  →  /10x-shape  →  /10x-prd  →  (10x-tech-stack-selector)  →  (bootstrapper)
```

The first three skills ship in this lesson; the last two are the next links in the chain.

### Task Router — Where to start

| Skill | Use it when |
| --- | --- |
| **Project setup** | |
| `/10x-init` | The project directory is fresh. Scaffolds `context/foundation/lessons.md` and `docs/reference/contract-surfaces.md` so the rest of the workflow has somewhere to write. Run this once per project. |
| **Discovery** | |
| `/10x-shape` | You have an idea and need to turn it into structured shape-notes BEFORE writing a PRD. Greenfield only. Walks vision → persona/access → MVP → FRs (with Socratic challenge) → business logic & data → stack-openness sketch. Surfaces empty-CRUD and MVP-too-big anti-patterns by name. Output: `context/foundation/shape-notes.md` with a resumable `checkpoint:` block. |
| **Document generation** | |
| `/10x-prd` | You have shape-notes (or raw notes) and want a schema-conformant `context/foundation/prd.md`. Generates against the locked schema, routes every gap verbatim into `## Open Questions`, and refuses to invent domain decisions. On collision, prompts overwrite vs. versioned save (`prd-vN.md`). |

### How the chain hands off

- `/10x-init` produces the workflow v2 scaffold (`context/foundation/`, `lessons.md`, `contract-surfaces.md`). `/10x-shape` requires this and will offer to delegate to `/10x-init` if it's missing.
- `/10x-shape` writes `context/foundation/shape-notes.md` with frontmatter `checkpoint:` (current_phase, phases_completed, frs_drafted, quality_check_status). On re-entry, it resumes from the next unfinished phase.
- `/10x-prd` reads `shape-notes.md` (default) or any path you pass, scores the input on a 4-signal heuristic, warns on thin input, and writes `context/foundation/prd.md` against the schema at `skills/10x-shape/references/prd-schema.md` (frontmatter aligned 1:1 with 10x-tech-stack-selector's Q1–Q7).

### What the PRD captures (and what it does NOT)

- **Captured**: vision, persona, success criteria, user stories (Given/When/Then), FRs (FR-NNN), NFRs, business logic (one-sentence rule first), data model, access control, durable implementation decisions, testing strategy, deployment & CI/CD strategy, non-goals, open questions.
- **NOT captured (deliberate)**: framework choices, database choices, file paths, deployment platform. Stack openness is binding — only `product_type` and `tech_preferences.language_family` capture stack-shaped intent. Frameworks are 10x-tech-stack-selector's job.

### Anti-patterns surfaced during shaping

- **Empty-CRUD**: business logic that reduces to "users add and remove records" with no domain rule. `/10x-shape` names it explicitly and prompts for a real rule shape (recommendation, prioritization, classification, validation, scoring, workflow, calculation).
- **MVP-too-big**: first-flow estimate exceeds ~1 week of after-hours work, or > 4 distinct user actions before user-visible value, or requires multiple integrations before payoff. Skill names the expensive pieces and offers concrete scope-down moves.

Both are **soft gates**: they warn but allow override. Overrides are recorded in the checkpoint and surfaced in the PRD's `## Open Questions`.

### Foundation paths used by this lesson

- `context/foundation/shape-notes.md` — `/10x-shape` output
- `context/foundation/prd.md` (or `prd-vN.md`) — `/10x-prd` output
- `context/foundation/lessons.md` — recurring rules & pitfalls (scaffolded by `/10x-init`)
- `docs/reference/contract-surfaces.md` — load-bearing names registry (scaffolded by `/10x-init`)

### Universal language

The shipped skills carry no 10xDevs / cohort / certification references. The mechanics (Socratic challenge, gray-area discovery, recommended-answer fatigue mitigation, soft quality gate) are universal indicators of a well-scoped greenfield project.

Skills must not write to `context/archive/`. Archived changes are immutable; if a resolved target path starts with `context/archive/`, abort with: "This change is archived. Open a new change with `/10x-new` instead."

<!-- END @przeprogramowani/10x-cli -->

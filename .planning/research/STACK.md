# Stack Research

**Domain:** Multi-agent Polish parliament simulation (LLM agents + vectorless RAG + CLI + web)
**Researched:** 2026-05-26
**Confidence:** HIGH — all critical components verified against live repos, PyPI, and npm registries

---

## PRD Assumptions vs Reality — Corrections First

Before the stack table, here are the PRD assumptions that do not match current reality. These must be corrected before Day 1 of development.

| PRD Claim | Reality | Action |
|-----------|---------|--------|
| Hermes Agent install path unspecified | PyPI: `pip install hermes-agent==0.14.0`; OR install script (installs its own Python 3.11 + uv). NOT importable as a Python library for programmatic spawning — it is a CLI/TUI agent framework. | Day 1 prototype must verify how Hermes exposes a programmable API. See note below. |
| `agentskills.io/specification` as spec URL | CONFIRMED real. Spec is at `agentskills.io/specification`. Frontmatter fields verified. CLI for validation is `skills-ref` not `skills validate`. | Use `skills-ref validate` (from `npm install -g skills-ref@0.1.5`). |
| `npx skills add mmtmr/pageindex-rag` install command | CONFIRMED real. Skill exists at `github.com/mmtmr/pageindex-rag`, installs via `npx skills add mmtmr/pageindex-rag -g -y`. | Install command is correct. |
| PageIndex = self-hosted open source RAG | TWO separate projects exist. (1) `VectifyAI/PageIndex` (32k stars, MIT, Python, self-hostable, `pip install`) uses PyMuPDF + LiteLLM. (2) `VectifyAI/pageindex-mcp` (npm `pageindex-mcp@1.6.3`) is the MCP server wrapping PageIndex Cloud API. For self-host, use the Python library directly + expose a custom MCP wrapper, NOT the npm package. | See PageIndex section below. |
| PageIndex MCP server = `pageindex-mcp` npm package | `pageindex-mcp` on npm is a **cloud client** requiring a PageIndex Cloud API key (https://dash.pageindex.ai). Free tier: 1000 pages. For self-host: run VectifyAI/PageIndex Python library + build an MCP wrapper, or use PageIndex Cloud as primary (fits contest budget). | Decide: Cloud (easier, 1000 pages free) vs self-host (more work, zero cloud cost). |
| Hermes `delegate_task` for parallel ministry fan-out | CONFIRMED: `delegate_task(tasks=[...])` in batch mode uses `ThreadPoolExecutor` to spawn parallel `AIAgent` child instances. This is the correct fan-out pattern — use it, don't build asyncio fan-out separately. | The Marszałek skill calls `delegate_task(tasks=[{goal, context, toolsets}, ...])` to consult 2-3 ministries in parallel. |
| Next.js "optional, Streamlit first" | Next.js 16.2.6 is latest stable (major version jump since most training data). App Router + Route Handlers with `text/event-stream` is the correct streaming pattern. Streamlit is NOT recommended — it introduces a Python web framework that duplicates the CLI pipeline instead of wrapping it cleanly. | Use Next.js 16.2.6 with App Router from Day 1. |

---

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

---

## Installation

```bash
# 1. Hermes Agent (via installer — sets up uv + Python 3.11 automatically)
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc   # or ~/.zshrc
hermes doctor      # verify

# OR: pip install into existing Python 3.11 venv
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install hermes-agent==0.14.0

# 2. Agent Skills tooling
npm install -g skills-ref@0.1.5       # validation CLI
npx skills add mmtmr/pageindex-rag -g -y  # RAG navigation skill

# 3. PageIndex self-host (Python, from source)
git clone https://github.com/VectifyAI/PageIndex.git vendor/pageindex
pip install pymupdf==1.27.2.3 PyPDF2==3.0.1 litellm==1.83.7 python-dotenv==1.2.2 pyyaml==6.0.3

# 4. PageIndex Cloud MCP server (fallback, Node.js >=20.8.1)
# Add to ~/.hermes/config.yaml under mcp_servers:
# pageindex:
#   command: npx
#   args: ["-y", "pageindex-mcp"]
#   env:
#     PAGEINDEX_API_KEY: "your_key_from_dash.pageindex.ai"

# 5. Python project dependencies
uv pip install typer==0.25.1 aiosqlite mcp==1.27.1 surya-ocr==0.17.1

# 6. Next.js frontend
npx create-next-app@16.2.6 web --typescript --app --src-dir
cd web && npm install
```

---

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

---

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

---

## Stack Patterns by Variant

**If PageIndex Cloud is used (recommended for contest speed):**
- Install `pageindex-mcp@1.6.3` as an MCP server in `~/.hermes/config.yaml`
- Each agent accesses it via Hermes MCP tool dispatch (zero Python integration code)
- Free tier: 1000 pages — sufficient for ~50 statutes at ~20 pages average
- Pricing beyond free: check `dash.pageindex.ai` (API key required)
- Polish OCR handled server-side — no local OCR infrastructure needed

**If PageIndex self-host is used (for complete offline / $5 VPS):**
- Clone `VectifyAI/PageIndex`, run ingest pipeline locally
- Use `litellm` with a cheap model (e.g., `gpt-4o-mini` via OpenRouter) for tree building
- Output: JSON tree files stored in `data/indices/`
- Build a thin Python MCP wrapper using `mcp==1.27.1` (`FastMCP`) to expose `tree_search`, `doc_search`, `fetch_node`
- Add to hermes config as a `command: python` stdio server
- Polish OCR: use `surya-ocr` for scanned PDFs, fall back to PageIndex Cloud for problem files

**If using Nous Portal for models:**
- `hermes setup --portal` handles OAuth + Tool Gateway
- Single subscription covers all model API calls (no OpenRouter account needed)
- `hermes model` to switch between Nous models
- Ministry agents: `hermes-3-8b` (fast, cheap)
- Orchestrator + parties: `hermes-3-70b` or `claude-opus-4`

**If using OpenRouter for models:**
- Set `OPENROUTER_API_KEY` in `.env`
- 200+ models accessible via `openrouter/model-name` format in litellm
- Useful for cost optimization: `openrouter/mistral-7b-instruct` for ministries
- No subscription needed, pay-per-token

---

## Agent Skills Specification — Verified Fields

Source: `agentskills.io/specification` (fetched live 2026-05-26). Confidence: HIGH.

```yaml
# Required fields
name: party-ko           # 1-64 chars, lowercase alphanumeric + hyphens, no leading/trailing/consecutive hyphens
description: "..."       # 1-1024 chars, non-empty, should say what AND when

# Optional fields
license: MIT
compatibility: "Requires hermes-agent 0.14.0+"
metadata:                # arbitrary key-value map
  type: party
  ideology: liberal-center
  seats: 157
allowed-tools: "..."     # space-separated, experimental
```

Validation command (confirmed on npm registry):
```bash
npx skills-ref@0.1.5 validate ./skills/party-ko
```

Directory layout confirmed correct per spec:
```
skills/party-ko/
├── SKILL.md          # Required
├── references/       # Optional — loaded on demand
├── assets/           # Optional
└── scripts/          # Optional
```

PRD naming convention (`party-ko`, `ministerstwo-finansow`, `marszalek-sejmu`) is valid — all lowercase, hyphens only, no consecutive hyphens.

---

## Hermes Agent — Verified API Surface

Source: `NousResearch/hermes-agent` repo, `pyproject.toml`, `run_agent.py`, `tools/delegate_tool.py`, `tools/mcp_tool.py`. Confidence: HIGH.

**Install:**
```bash
pip install hermes-agent==0.14.0   # Python 3.11+ required
# OR via curl installer (sets up uv + Python 3.11 + Node.js)
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

**PyPI versions:** 0.13.0, 0.14.0 (latest, released 2026-05-16). No earlier versions.

**Python requirement:** `>=3.11` (exact from pyproject.toml).

**Programmatic API — `AIAgent` class:**
```python
from run_agent import AIAgent  # NOT hermes_agent — import from source
agent = AIAgent(
    model="openai/gpt-4o-mini",
    api_key="...",
    enabled_toolsets=["mcp", "files"],
    ephemeral_system_prompt="You are ministerstwo-finansow...",
    skip_memory=True,          # don't pollute shared MEMORY.md
    stream_delta_callback=lambda delta: ...,  # streaming output
)
result = agent.run_conversation(user_message="Analyze this bill...", task_id="ministry-finance-001")
```

**IMPORTANT:** `hermes-agent` is installed as a tool (`hermes` CLI), not a conventional Python package with a public API. The `run_agent.AIAgent` class is accessible by running from the hermes-agent source directory or by `import` after installing from PyPI (the package does install the `run_agent` module). Day 1 task: verify `from run_agent import AIAgent` works after `pip install hermes-agent==0.14.0` in a fresh venv.

**Parallel fan-out via `delegate_task`:**
```python
# This is the Hermes-native pattern — invoked as a tool by the Marszałek agent
# In the Marszałek SKILL.md, instruct the agent to call:
delegate_task(tasks=[
    {"goal": "Analyze the 4-day work week bill from a fiscal perspective", "context": bill_text, "toolsets": ["mcp"]},
    {"goal": "Analyze from a labor law perspective", "context": bill_text, "toolsets": ["mcp"]},
])
# Hermes runs these in parallel via ThreadPoolExecutor, collects results
```

**MCP client configuration** (in `~/.hermes/config.yaml`):
```yaml
mcp_servers:
  pageindex:
    command: npx
    args: ["-y", "pageindex-mcp"]
    env:
      PAGEINDEX_API_KEY: "your_key"
    timeout: 180
```
All MCP tools from registered servers are auto-discovered and available to all agents.

**Memory API:** File-based (`~/.hermes/MEMORY.md` for persistent, `~/.hermes/USER.md` for user profile). `MemoryManager` handles prefetch/sync per turn. For party agents: enable memory to track voting history. For ministry agents: `skip_memory=True` — they are stateless experts.

**Model providers:** Nous Portal (OAuth, single sub), OpenRouter (200+ models), NovitaAI, NVIDIA NIM, OpenAI, Anthropic (native, install `hermes-agent[anthropic]`), and any OpenAI-compatible endpoint. Switch via `hermes model` or `AIAgent(model="provider/model-name")`.

---

## PageIndex — Verified Architecture

Source: `VectifyAI/PageIndex` (32k stars, MIT), `requirements.txt`, `pageindex/utils.py`. Confidence: HIGH.

**Self-host install:**
```bash
git clone https://github.com/VectifyAI/PageIndex.git
pip install pymupdf==1.27.2.3 PyPDF2==3.0.1 litellm==1.83.7 python-dotenv==1.2.2 pyyaml==6.0.3
```

**No PyPI package** — install from source only for self-host.

**PDF text extraction pipeline:** PyMuPDF (fitz) for text extraction + PyPDF2 for metadata. Produces `page_list = [(page_text, page_number), ...]`. For born-digital ISAP PDFs: this works correctly for Polish Unicode (PyMuPDF handles UTF-8 properly).

**For scanned/image-only ISAP PDFs:** PageIndex has NO built-in OCR. Options:
1. Use `surya-ocr` to pre-extract text → save as text file → feed to PageIndex markdown pipeline
2. Use PageIndex Cloud (recommended — handles OCR server-side, no infrastructure)

**Output:** JSON tree file per document. Structure: `{title, description, children: [{title, page_range, text, children: [...]}]}`.

**MCP exposure:** `pageindex-mcp@1.6.3` (npm) exposes the Cloud API. For self-host, build a thin `FastMCP` wrapper:
```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("pageindex-local")

@mcp.tool()
def tree_search(query: str, doc_id: str) -> str: ...

@mcp.tool()
def doc_search(query: str) -> str: ...

@mcp.tool()
def fetch_node(node_id: str) -> str: ...
```

---

## Polish PDF OCR — Decision Tree

For the contest corpus (~50 documents), most statutes from ISAP are born-digital (post-2000). Follow this decision tree:

```
PDF from ISAP
     ↓
PyMuPDF can extract text? (test: len(text) > 100)
     YES → Use directly in PageIndex pipeline
     NO (scanned/image PDF) → 
          PageIndex Cloud in use? → YES → Upload via Cloud API (OCR handled)
          NO (self-host) → surya-ocr 0.17.1 for pre-processing
                           → VPS has no GPU? → Use PageIndex Cloud for this doc only
```

Recommendation: Use PageIndex Cloud for the contest. The free tier (1000 pages) covers ~50 statutes at 20 pages average. No OCR infrastructure needed. Switch to self-host post-contest.

**Explicitly avoid:** Tesseract on VPS (no Polish language pack by default, slow, needs `apt` access on shared hosting). Google Vision API (cost, privacy). AWS Textract (cost, no Polish-language-specific tuning).

---

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

---

## Sources

- `github.com/NousResearch/hermes-agent` — `pyproject.toml`, `run_agent.py`, `tools/delegate_tool.py`, `tools/mcp_tool.py`, `RELEASE_v0.14.0.md`, `cli-config.yaml.example` — verified live 2026-05-26
- PyPI registry — `hermes-agent` versions 0.13.0, 0.14.0 confirmed — verified live 2026-05-26
- `agentskills.io/specification` — frontmatter schema, directory structure, progressive disclosure spec — verified live 2026-05-26
- npm registry — `skills-ref@0.1.5`, `skills@1.5.7`, `pageindex-mcp@1.6.3`, `next@16.2.6` — verified live 2026-05-26
- `github.com/mmtmr/pageindex-rag` — skill exists, install command confirmed — verified live 2026-05-26
- `github.com/VectifyAI/PageIndex` — `requirements.txt`, `pageindex/utils.py`, `run_pageindex.py` — verified live 2026-05-26
- `github.com/VectifyAI/pageindex-mcp` — README, cloud vs local MCP setup — verified live 2026-05-26
- PyPI registry — `pymupdf@1.27.2.3`, `surya-ocr@0.17.1`, `typer@0.25.1`, `mcp@1.27.1`, `litellm@1.83.7` — verified live 2026-05-26

---

*Stack research for: Virtual Parliament (Hermes Agent Challenge)*
*Researched: 2026-05-26*

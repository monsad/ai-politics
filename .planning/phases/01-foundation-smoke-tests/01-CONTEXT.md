# Phase 1: Foundation & Smoke Tests — Context

**Gathered:** 2026-05-26
**Status:** Ready for planning
**Source:** PRD Express Path (`./prd.md`) + ROADMAP.md Phase 1 section + REQUIREMENTS.md (Phase 1 REQ-IDs)

<domain>
## Phase Boundary

Day 1 of the contest. **Risk de-risking only — no agent skill content yet.** This phase exists to prove that the two new APIs (Hermes Agent 0.14.0 PyPI package, PageIndex Cloud MCP server) behave as the stack research promised, before a single party or ministry SKILL.md is written.

Phase 1 delivers:

1. A public GitHub repo with MIT license, gitignored `.env`, `pyproject.toml` pinning the stack, and a `Makefile` with `setup` and `demo` targets.
2. A working Python 3.11 dev environment with `hermes-agent==0.14.0` installed and verifiable import (`from run_agent import AIAgent`).
3. A PageIndex Cloud account with an API key, the `pageindex-mcp` Node server wired into `~/.hermes/config.yaml`, the Polish Konstytucja PDF uploaded, and a Hermes Agent that can dispatch `doc_search` / `fetch_node` through MCP and round-trip Polish diacritics correctly.
4. The `mmtmr/pageindex-rag` external skill installed via `npx skills add -g -y` so every future agent inherits PageIndex navigation know-how without local duplication.
5. A `skills-ref` validator wired into pre-commit and CI so every later SKILL.md is rejected at the gate if its frontmatter is invalid.
6. A passing parallel-fan-out smoke test for `delegate_task(tasks=[...])` — proves the Hermes-native ministry fan-out works *before* we depend on it in Phase 3.
7. A 3-concurrent-`doc_search` smoke test against PageIndex Cloud — proves the free tier doesn't rate-limit a single session running 2–3 ministries in parallel.

Phase 1 explicitly does NOT deliver:

- Any party or ministry SKILL.md content (Phase 2)
- The orchestrator / Marszałek logic or `agent_factory.py` (Phase 3)
- Any web UI work (Phase 4)
- Document ingest beyond the single Konstytucja smoke-test upload — full ~50-doc corpus is BRAIN-03 / BRAIN-04 in Phase 2

</domain>

<decisions>
## Implementation Decisions

All decisions below are **locked** — sourced from PRD §5–§6, REQUIREMENTS.md GATE/INFRA/BRAIN sections, ROADMAP.md Phase 1, and CLAUDE.md (Recommended Stack table). Treat them as constraints, not suggestions.

### Stack — Python side
- **Python: 3.11 exact** (not 3.12 or 3.13). hermes-agent requires `>=3.11`; surya-ocr has no 3.13 wheels on all platforms; PyMuPDF wheels are most stable on 3.11.
- **Package manager: `uv`**. Hermes installer sets it up automatically. Use `uv venv .venv --python 3.11 && uv pip install -e ".[dev]"`.
- **Hermes Agent: `hermes-agent==0.14.0`** from PyPI. Do NOT install `hermes-agent[all]` — voice/TTS/browser/modal/daytona extras are not needed and bloat install.
- **`pyproject.toml` pins (mandatory):**
  - `hermes-agent==0.14.0`
  - `python_requires = ">=3.11,<3.12"`
  - `typer==0.25.1`
  - `rich` (latest)
  - `fastapi`, `uvicorn` (for Phase 3 SSE; install now to fail fast on conflicts)
  - `aiosqlite>=0.20` (Phase 3 sessions; install now)
  - `python-dotenv==1.2.2` (pinned to hermes-agent dep)
  - `httpx==0.28.1` (pinned to hermes-agent dep)
  - `pyyaml==6.0.3` (pinned to hermes-agent dep)
- **Hermes import path: `from run_agent import AIAgent`**. Verified by stack research, MUST be re-verified in a fresh venv as GATE-01.

### Stack — Node side
- **Node.js: `>=20.8.1`** (required by `pageindex-mcp@1.6.3`).
- **`skills-ref@0.1.5`** (npm) — validator. Install globally OR pin to repo as devDependency. Use as: `npx skills-ref@0.1.5 validate skills/<id>`.
- **`skills@1.5.7`** (npm, Vercel Labs) — for installing external skills. Use: `npx skills add mmtmr/pageindex-rag -g -y`.
- **`pageindex-mcp@1.6.3`** — configured in `~/.hermes/config.yaml`, NOT installed as a project dep (it's a globally-runnable MCP server invoked via `npx -y`).

### Knowledge base — PageIndex
- **Mode: Cloud, not self-host.** Free tier (1000 pages) covers the curated ~50-doc corpus. Polish OCR is handled server-side — eliminates the surya-ocr / Tesseract decision. Self-host is documented as STR-04 (post-contest).
- **Account: `dash.pageindex.ai`**. Email/password OAuth, no team setup required.
- **API key storage: `.env`**, gitignored. `.env.example` documents the key name (`PAGEINDEX_API_KEY`).
- **MCP wiring: edit `~/.hermes/config.yaml`** to add a `pageindex` MCP server entry under `mcp_servers:`:
  ```yaml
  mcp_servers:
    pageindex:
      command: npx
      args: ["-y", "pageindex-mcp"]
      env:
        PAGEINDEX_API_KEY: ${PAGEINDEX_API_KEY}
  ```
- **Smoke-test corpus on Day 1: Konstytucja RP PDF only.** The full 50-doc ingest happens in Phase 2 (BRAIN-03 / BRAIN-04). Konstytucja is the diacritics gauntlet — every Polish diacritic appears in the document.
- **Diacritic acceptance threshold: ≥ 90% expected occurrences of `ą ę ó ź ż ś ń ć ł`** in `fetch_node` output for the Konstytucja root node. Lower = OCR is broken, escalate before Phase 2.

### Hermes fan-out — `delegate_task`
- **Use `delegate_task(tasks=[{goal, context, toolsets}, ...])` for parallel agent spawning.** Hermes runs these via internal `ThreadPoolExecutor`. Documented in PROJECT.md "What NOT to Use".
- **Never `asyncio.gather` over `AIAgent` instances.** This is an explicit anti-pattern in PROJECT.md — it deadlocks on the prompt_toolkit TUI stdin.
- **Day-1 smoke test: 2 dummy tasks** (e.g., `tasks=[{"goal": "say hello", ...}, {"goal": "say world", ...}]`) returning both results. GATE-03.

### Agent Skills format
- **Specification: `agentskills.io/specification`** — verified live 2026-05-26.
- **Naming: lowercase-hyphen** (`party-ko`, not `Party_KO`). Validated by `skills-ref`.
- **Required frontmatter fields: `name`, `description`.** Optional fields: `license`, `metadata`.
- **Directory structure:** `skills/<id>/SKILL.md` + optional `references/`, `assets/`, `scripts/` subdirs.
- **`mmtmr/pageindex-rag` skill** is installed globally (`-g`) and `-y` (yes to prompts), so every Hermes session loads it.
- **Validator command: `npx skills-ref@0.1.5 validate skills/<id>`** — exits 0 on valid, non-zero on invalid. Wired into pre-commit and CI.

### Repository layout (Phase 1 scope)
```
ai-politics/                          # this repo, public, MIT
├── .planning/                        # GSD planning artifacts (already exists)
├── LICENSE                           # MIT, INFRA-01
├── README.md                         # 30-second pitch + quickstart
├── pyproject.toml                    # pins above, INFRA-02
├── Makefile                          # setup, demo, validate-skills, smoke
├── .env.example                      # documents PAGEINDEX_API_KEY (and any OpenRouter/Nous keys later)
├── .gitignore                        # .env, .venv, __pycache__, node_modules, sessions/, data/
├── .pre-commit-config.yaml           # runs skills-ref validate
├── .github/workflows/ci.yml          # skills-ref validate + import test
├── package.json                      # devDeps: skills-ref@0.1.5
├── skills/                           # EMPTY in Phase 1 except .gitkeep
│   └── .gitkeep
├── parliament/                       # EMPTY in Phase 1 except package marker
│   ├── __init__.py
│   └── second_brain/__init__.py
├── tests/
│   ├── test_gate_01_hermes_import.py
│   ├── test_gate_02_minimal_agent.py
│   ├── test_gate_03_delegate_task.py
│   ├── test_gate_04_pageindex_doc_search.py
│   ├── test_gate_05_diacritics.py
│   ├── test_gate_06_skills_ref.py
│   └── test_gate_07_concurrent_search.py
└── scripts/
    └── seed_pageindex_konstytucja.py # uploads Konstytucja PDF to PageIndex Cloud
```

### Cost & quality guards (INFRA-related, scoped to Phase 1 only)
- **Token-budget kill switch (INFRA-06):** Full implementation lives in Phase 3, but Phase 1 establishes the *interface* — a single `parliament/guards.py` module with a `TokenBudget` class that all later code must import. Phase 1 just defines the contract + writes a unit test; production wiring is Phase 3.
- **Cost smoke check:** Day 1 budget cap of $1 total spend across all gate tests. Document in README.

### Cut criteria (locked, from ROADMAP.md Phase 1)
- **If GATE-01 fails (`from run_agent import AIAgent` errors in fresh venv):** STOP. Open issue on hermes-agent repo, do not attempt to patch internals.
- **If GATE-04 / GATE-05 fail (PageIndex Cloud returns no `node_id` or strips Polish diacritics):** Pivot — try Polish PDF via OCR fallback once; if still failing, fall back to self-host VectifyAI/PageIndex with `surya-ocr`. Decide by end of Day 1.
- **If GATE-03 fails (delegate_task deadlocks):** Re-architect Phase 3 to sequential ministry consultations (slower but works); update ROADMAP.

### Claude's Discretion (PRD/REQUIREMENTS did not specify — planner chooses)
- Exact test runner (pytest vs unittest) — recommend pytest 8.x with `pytest-asyncio`
- Pre-commit hook framework — recommend [`pre-commit`](https://pre-commit.com) with `.pre-commit-config.yaml`
- CI provider — recommend GitHub Actions (matches public-repo + MIT story)
- Linter — recommend `ruff` (Python) only, no black/isort separately
- README structure — follow DEMO-02 spec from REQUIREMENTS.md even though that REQ-ID is Phase 5; Phase 1 produces a *draft* README to be polished in Phase 5
- Whether the `pageindex-rag` external skill installs to `~/.hermes/skills/` or a project-local `skills/` — `-g` flag implies global, so use global
- Whether `parliament/guards.py` is class-based or context-manager-based — planner picks; locked decision is only that the module exists with a `TokenBudget` symbol

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents (planner, executor) MUST read these before planning or implementing.**

### Project planning artifacts
- `.planning/PROJECT.md` — overall project mission, stakeholders, success metrics
- `.planning/ROADMAP.md` — 5-phase roadmap; this phase = Phase 1 section
- `.planning/REQUIREMENTS.md` — full v1 requirement list; Phase 1 covers GATE-01..07, INFRA-01..03, BRAIN-01/02/06
- `./prd.md` — original Polish-language PRD (treat as historical context — REQUIREMENTS.md is the operational spec)
- `./CLAUDE.md` — project-level Claude instructions; **Recommended Stack** table and **What NOT to Use** table are canonical

### Stack research outputs (in `.planning/research/`)
- `.planning/research/STACK.md` — verified package versions and import paths
- `.planning/research/ARCHITECTURE.md` — system architecture (relevant: PageIndex MCP wiring, delegate_task fan-out)
- `.planning/research/PITFALLS.md` — known-bad patterns and their alternatives
- `.planning/research/FEATURES.md` — feature breakdown (Phase 1 mostly orthogonal; useful for forward visibility)

### External authoritative docs
- `https://agentskills.io/specification` — Agent Skills frontmatter + directory spec (verified live 2026-05-26)
- `https://github.com/NousResearch/hermes-agent` — `pyproject.toml`, `run_agent.py`, `tools/delegate_tool.py`, `tools/mcp_tool.py`, `RELEASE_v0.14.0.md`
- `https://github.com/VectifyAI/pageindex-mcp` — Cloud MCP server README, env var conventions
- `https://github.com/mmtmr/pageindex-rag` — the external skill installed via `npx skills add`
- `https://dash.pageindex.ai` — PageIndex Cloud dashboard for API key + usage

### Validation tooling
- `skills-ref@0.1.5` (npm) — validates SKILL.md frontmatter; Phase 1 sets it up, Phase 2 uses it heavily

</canonical_refs>

<specifics>
## Specific Ideas

### Concrete frontmatter for the smoke-test SKILL.md (used by GATE-06)

```yaml
---
name: party-ko
description: Minimal placeholder skill used to validate skills-ref tooling.
  Real content lands in Phase 2.
license: MIT
metadata:
  type: party
  ideology: liberal-center
  seats: 157
---

# Koalicja Obywatelska — placeholder for GATE-06

This file exists only to prove `skills-ref validate` exits 0 on a minimal
frontmatter. Phase 2 replaces the body wholesale.
```

This minimal SKILL.md is the artifact for GATE-06. It also lets us delete-and-rewrite in Phase 2 without affecting Phase 1's pass record.

### Concrete commands the executor should run (and bake into the Makefile)

```makefile
setup:
    uv venv .venv --python 3.11
    uv pip install -e ".[dev]"
    npm install
    npx skills add mmtmr/pageindex-rag -g -y
    pre-commit install

smoke:
    pytest tests/test_gate_01_hermes_import.py
    pytest tests/test_gate_02_minimal_agent.py
    pytest tests/test_gate_03_delegate_task.py
    pytest tests/test_gate_04_pageindex_doc_search.py
    pytest tests/test_gate_05_diacritics.py
    pytest tests/test_gate_06_skills_ref.py
    pytest tests/test_gate_07_concurrent_search.py

validate-skills:
    npx skills-ref@0.1.5 validate skills/

demo:
    @echo "Phase 1: nothing to demo yet — run 'make smoke' to verify gates"
```

### PageIndex Cloud seed script — concrete responsibilities
- Read `PAGEINDEX_API_KEY` from `.env`
- Download Konstytucja RP PDF from ISAP (`isap.sejm.gov.pl`) — URL to be confirmed by researcher
- POST to PageIndex Cloud ingest endpoint
- Wait for indexing to complete (poll status)
- Print the resulting `doc_id` for use in tests
- Idempotent — if doc already exists, return existing `doc_id`

### Test acceptance criteria (concrete grep targets the planner must include in tasks)

| Gate | Acceptance |
|------|-----------|
| GATE-01 | `pytest tests/test_gate_01_hermes_import.py` exit code 0; test asserts `AIAgent` is importable |
| GATE-02 | Test asserts `agent.run_conversation("ping")` returns a non-empty string (mock model OK if cheaper) |
| GATE-03 | Test asserts both task results are non-None within 30s wall-clock |
| GATE-04 | Test asserts `doc_search("konstytucja")` returns a dict with a non-empty `node_id` field |
| GATE-05 | Test asserts `fetch_node(root_id)` text contains each of `ą ę ó ź ż ś ń ć ł` at ≥ 90% of expected counts (counts derived from the source PDF text) |
| GATE-06 | `npx skills-ref@0.1.5 validate skills/party-ko` exits 0 |
| GATE-07 | Test fires 3 concurrent `doc_search` calls via `asyncio.gather` on the MCP client (NOT on AIAgent — only the MCP client is async-safe) and asserts all 3 return within 60s |

</specifics>

<deferred>
## Deferred Ideas

These appear in PRD/REQUIREMENTS but explicitly belong to later phases or to v2. Phase 1 must NOT implement them:

- **Any party/ministry/marszalek SKILL.md content** — Phase 2 (SKILL-01..03, PARTY-01..05, MIN-01..04)
- **`doc_registry.py` per-ministry filtering** — Phase 2 (BRAIN-05)
- **Full corpus ingest (~50 docs)** — Phase 2 (BRAIN-03 / BRAIN-04). Phase 1 ingests Konstytucja only.
- **`agent_factory.py`** — Phase 3 (INFRA-04)
- **SQLite session/transcript schema** — Phase 3 (INFRA-05). Phase 1 only declares the dependency in pyproject.toml.
- **Token-budget enforcement (INFRA-06)** — Phase 3. Phase 1 stubs the interface only.
- **Hermes long-term memory (STR-01)** — v2 stretch, spike in Phase 1 as a side-quest IF and only if all 7 gates pass before lunch on Day 1
- **Self-hosted PageIndex (STR-04)** — post-contest
- **PDF export, web UI, demo video** — Phases 4 and 5
- **Per-MP voting model** — Out of scope (REQUIREMENTS.md)
- **Streamlit alternative** — Out of scope (REQUIREMENTS.md)

</deferred>

---

*Phase: 01-foundation-smoke-tests*
*Context gathered: 2026-05-26 via PRD Express Path (`./prd.md` + REQUIREMENTS.md Phase 1)*

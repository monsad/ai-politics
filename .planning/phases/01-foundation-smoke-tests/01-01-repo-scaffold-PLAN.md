---
phase: 01-foundation-smoke-tests
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - LICENSE
  - .gitignore
  - .env.example
  - pyproject.toml
  - Makefile
  - README.md
  - package.json
  - parliament/__init__.py
  - parliament/second_brain/__init__.py
  - parliament/guards.py
  - tests/__init__.py
  - tests/test_token_budget.py
  - skills/.gitkeep
autonomous: true
requirements: [INFRA-01, INFRA-02]
requirements_addressed: [INFRA-01, INFRA-02]
must_haves:
  truths:
    - "Public GitHub repo has MIT LICENSE at root"
    - "pyproject.toml pins hermes-agent==0.14.0 and Python 3.11"
    - ".env.example documents PAGEINDEX_API_KEY"
    - "make setup and make demo targets exist"
    - "parliament/guards.py defines TokenBudget contract"
  artifacts:
    - path: "LICENSE"
      provides: "MIT license at root"
      contains: "MIT License"
    - path: "pyproject.toml"
      provides: "Python package metadata + pins"
      contains: "hermes-agent==0.14.0"
    - path: ".env.example"
      provides: "Required env var documentation"
      contains: "PAGEINDEX_API_KEY"
    - path: "Makefile"
      provides: "setup + demo + smoke + validate-skills targets"
      contains: "setup:"
    - path: ".gitignore"
      provides: "Excludes secrets and build artifacts"
      contains: ".env"
    - path: "parliament/guards.py"
      provides: "TokenBudget interface (stub, full wiring Phase 3)"
      exports: ["TokenBudget"]
  key_links:
    - from: "tests/test_token_budget.py"
      to: "parliament/guards.py"
      via: "from parliament.guards import TokenBudget"
      pattern: "from parliament.guards import TokenBudget"
---

<objective>
Lay down the repo scaffold required by INFRA-01 (MIT LICENSE) and INFRA-02 (pyproject.toml pinning hermes-agent==0.14.0, Python 3.11, typer, rich, fastapi, uvicorn, aiosqlite, python-dotenv, httpx, pyyaml). This is Wave 1 — no Hermes or PageIndex dependency yet — so it can run in parallel with Plan 02 (skills-ref tooling).

Purpose: Establish the legal/dependency/build foundation so every subsequent plan can `uv pip install -e ".[dev]"` and run `make smoke`.
Output: 13 files created at repo root (LICENSE, .gitignore, .env.example, pyproject.toml, Makefile, README.md, package.json + parliament package skeleton + TokenBudget interface stub + matching test).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md
@.planning/REQUIREMENTS.md
@CLAUDE.md
@.planning/research/STACK.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Write LICENSE, .gitignore, .env.example, README draft, package.json</name>
  <files>LICENSE, .gitignore, .env.example, README.md, package.json</files>
  <read_first>
    - /Users/xpll081/ai-politics/.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md (sections: Stack — Python side, Stack — Node side, Knowledge base — PageIndex, Repository layout)
    - /Users/xpll081/ai-politics/CLAUDE.md (Recommended Stack table)
    - /Users/xpll081/ai-politics/prd.md (for the 30-second pitch wording)
  </read_first>
  <action>
Create five files at /Users/xpll081/ai-politics/ root.

1) `LICENSE` — standard MIT license text, copyright holder `Copyright (c) 2026 Monika Sadlok`, year 2026. Use the canonical OSI MIT text (Permission is hereby granted, free of charge...). The full text from https://opensource.org/license/mit verbatim.

2) `.gitignore` — must contain these lines (one per line):
```
.env
.venv/
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.ruff_cache/
node_modules/
sessions/
data/
*.db
.DS_Store
dist/
build/
*.egg-info/
.coverage
htmlcov/
```

3) `.env.example` — documents every env var the project will read. Content verbatim:
```
# PageIndex Cloud API key — get from https://dash.pageindex.ai
# Free tier: 1000 pages. Required for BRAIN-01 / GATE-04 / GATE-05 / GATE-07.
PAGEINDEX_API_KEY=replace-with-your-pageindex-cloud-api-key

# Model provider (Phase 2+). Pick one. Hermes Agent reads these via `hermes model`.
# OPENROUTER_API_KEY=sk-or-...
# ANTHROPIC_API_KEY=sk-ant-...
# NOUS_PORTAL_TOKEN=...

# Token budget guard (INFRA-06 stub — Phase 3 enforces). Optional override.
# MAX_TOKENS_PER_SESSION=50000
```

4) `README.md` — Phase 1 DRAFT (DEMO-02 polish is Phase 5). Include these sections:

```markdown
# Virtual Parliament

> Multi-agent simulation of the Polish Sejm. Five party agents debate user-submitted bills, consulting nineteen ministry experts and a Second Brain (PageIndex) holding the Polish Constitution and ~50 statutes. Every argument cites a real Polish legal document.

**Contest entry:** [Hermes Agent Challenge](https://dev.to/devteam/join-the-hermes-agent-challenge-1000-in-prizes-13cd) (deadline 2026-05-31 23:59 PDT).
**License:** MIT.

## Quickstart

```bash
git clone <repo-url>
cd ai-politics
cp .env.example .env   # then edit .env and add PAGEINDEX_API_KEY
make setup             # uv venv + pip install + npm install + skills install + pre-commit
make smoke             # run all 7 day-1 gate tests
```

## Status

Phase 1 — Foundation & Smoke Tests (Day 1 of 5). De-risking Hermes Agent 0.14.0 + PageIndex Cloud before agent skill writing begins in Phase 2.

## Stack

- Python 3.11 (exact) + uv + hermes-agent==0.14.0
- PageIndex Cloud (free tier, MCP server `pageindex-mcp@1.6.3`)
- Node.js >=20.8.1 for `skills-ref@0.1.5` validation
- Future: Next.js 16.2.6 (Phase 4), FastAPI + SSE (Phase 3)

Full stack rationale: see `CLAUDE.md` "Recommended Stack" table.
```

5) `package.json` — minimal, devDependencies only:
```json
{
  "name": "ai-politics",
  "version": "0.1.0",
  "private": true,
  "license": "MIT",
  "description": "Virtual Parliament — Hermes Agent Challenge entry",
  "engines": {
    "node": ">=20.8.1"
  },
  "devDependencies": {
    "skills-ref": "0.1.5"
  },
  "scripts": {
    "validate-skills": "skills-ref validate ./skills"
  }
}
```
  </action>
  <verify>
    <automated>test -f /Users/xpll081/ai-politics/LICENSE && grep -q "MIT License" /Users/xpll081/ai-politics/LICENSE && grep -qx ".env" /Users/xpll081/ai-politics/.gitignore && grep -q "PAGEINDEX_API_KEY" /Users/xpll081/ai-politics/.env.example && grep -q "skills-ref" /Users/xpll081/ai-politics/package.json && node -e "JSON.parse(require('fs').readFileSync('/Users/xpll081/ai-politics/package.json'))"</automated>
  </verify>
  <acceptance_criteria>
    - `test -f /Users/xpll081/ai-politics/LICENSE` exit 0
    - `grep -c "MIT License" /Users/xpll081/ai-politics/LICENSE` >= 1
    - `grep -c "Permission is hereby granted" /Users/xpll081/ai-politics/LICENSE` >= 1
    - `grep -Fxq ".env" /Users/xpll081/ai-politics/.gitignore` (exact line, prevents `.env.example` from being ignored)
    - `grep -Fxq "node_modules/" /Users/xpll081/ai-politics/.gitignore`
    - `grep -Fxq ".venv/" /Users/xpll081/ai-politics/.gitignore`
    - `grep -c "PAGEINDEX_API_KEY" /Users/xpll081/ai-politics/.env.example` >= 1
    - `python3 -c "import json; d=json.load(open('/Users/xpll081/ai-politics/package.json')); assert d['devDependencies']['skills-ref']=='0.1.5'"` exit 0
    - `grep -q "engines" /Users/xpll081/ai-politics/package.json` exit 0
    - `grep -q "Virtual Parliament" /Users/xpll081/ai-politics/README.md` exit 0
    - `grep -q "make setup" /Users/xpll081/ai-politics/README.md` exit 0
  </acceptance_criteria>
  <done>All five files exist with the exact contents above. `.gitignore` excludes `.env` but not `.env.example`. `package.json` parses as JSON.</done>
</task>

<task type="auto">
  <name>Task 2: Write pyproject.toml with locked pins</name>
  <files>pyproject.toml</files>
  <read_first>
    - /Users/xpll081/ai-politics/.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md (section: Stack — Python side — pyproject.toml pins (mandatory))
    - /Users/xpll081/ai-politics/.planning/research/STACK.md (Version Compatibility table)
  </read_first>
  <action>
Create /Users/xpll081/ai-politics/pyproject.toml with the locked pins from CONTEXT.md verbatim. Use PEP 621 metadata. Build backend: hatchling (no compiled extensions needed; lightweight).

Full file content:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "parliament"
version = "0.1.0"
description = "Virtual Parliament — multi-agent simulation of the Polish Sejm (Hermes Agent Challenge entry)"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11,<3.12"
authors = [{ name = "Monika Sadlok" }]
dependencies = [
  "hermes-agent==0.14.0",
  "typer==0.25.1",
  "rich",
  "fastapi",
  "uvicorn",
  "aiosqlite>=0.20",
  "python-dotenv==1.2.2",
  "httpx==0.28.1",
  "pyyaml==6.0.3",
  "mcp==1.27.1",
]

[project.optional-dependencies]
dev = [
  "pytest==8.3.4",
  "pytest-asyncio==0.24.0",
  "ruff==0.8.4",
  "pre-commit==4.0.1",
]

[project.scripts]
hermes-parliament = "parliament.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["parliament"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "W", "B"]
ignore = ["E501"]
```

Notes encoded in CONTEXT.md locked decisions:
- `hermes-agent==0.14.0` exact (NOT `hermes-agent[all]`)
- `python_requires = ">=3.11,<3.12"` per CONTEXT.md "Python: 3.11 exact (not 3.12 or 3.13)"
- `typer==0.25.1` exact
- `python-dotenv==1.2.2`, `httpx==0.28.1`, `pyyaml==6.0.3` pinned to hermes-agent's transitive pins
- `mcp==1.27.1` for the future Python-side MCP client (used by GATE-07 test if needed)
- `fastapi`, `uvicorn`, `aiosqlite` installed now to fail fast on conflicts (locked decision in CONTEXT.md)
- `[project.scripts]` reserves the `hermes-parliament` entry point (real CLI implemented Phase 3); Phase 1 doesn't need a stub.
- `[tool.pytest.ini_options]` uses asyncio_mode=auto so async gate tests work without per-test decorators.
  </action>
  <verify>
    <automated>python3 -c "import tomllib; d=tomllib.load(open('/Users/xpll081/ai-politics/pyproject.toml','rb')); assert d['project']['name']=='parliament'; assert 'hermes-agent==0.14.0' in d['project']['dependencies']; assert d['project']['requires-python']=='>=3.11,<3.12'; assert 'typer==0.25.1' in d['project']['dependencies']; print('ok')"</automated>
  </verify>
  <acceptance_criteria>
    - `python3 -c "import tomllib; tomllib.load(open('/Users/xpll081/ai-politics/pyproject.toml','rb'))"` exit 0 (valid TOML)
    - `grep -q 'hermes-agent==0.14.0' /Users/xpll081/ai-politics/pyproject.toml` exit 0
    - `grep -q 'requires-python = ">=3.11,<3.12"' /Users/xpll081/ai-politics/pyproject.toml` exit 0
    - `grep -q 'typer==0.25.1' /Users/xpll081/ai-politics/pyproject.toml` exit 0
    - `grep -q 'python-dotenv==1.2.2' /Users/xpll081/ai-politics/pyproject.toml` exit 0
    - `grep -q 'httpx==0.28.1' /Users/xpll081/ai-politics/pyproject.toml` exit 0
    - `grep -q 'pyyaml==6.0.3' /Users/xpll081/ai-politics/pyproject.toml` exit 0
    - `grep -q 'fastapi' /Users/xpll081/ai-politics/pyproject.toml` exit 0
    - `grep -q 'aiosqlite' /Users/xpll081/ai-politics/pyproject.toml` exit 0
    - `grep -q 'mcp==1.27.1' /Users/xpll081/ai-politics/pyproject.toml` exit 0
    - `grep -q 'pytest' /Users/xpll081/ai-politics/pyproject.toml` exit 0
    - NOT-present check: `! grep -q 'hermes-agent\[all\]' /Users/xpll081/ai-politics/pyproject.toml` (the [all] extra is explicitly forbidden)
  </acceptance_criteria>
  <done>pyproject.toml exists, parses as valid TOML, contains every required pin verbatim, does NOT contain `hermes-agent[all]`.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Write Makefile, parliament package skeleton, TokenBudget stub + test</name>
  <files>Makefile, parliament/__init__.py, parliament/second_brain/__init__.py, parliament/guards.py, tests/__init__.py, tests/test_token_budget.py, skills/.gitkeep</files>
  <read_first>
    - /Users/xpll081/ai-politics/.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md (sections: Repository layout, Cost & quality guards — Token-budget kill switch INFRA-06, Concrete commands the executor should run)
  </read_first>
  <behavior>
    - Test 1: `from parliament.guards import TokenBudget` succeeds (module is importable)
    - Test 2: `TokenBudget(max_tokens=100).add(50)` returns True (under budget, allowed)
    - Test 3: `TokenBudget(max_tokens=100).add(150)` raises `TokenBudgetExceeded` (or returns False — see action; we pick raise for fail-loud semantics)
    - Test 4: `TokenBudget(max_tokens=100).remaining` after one `add(30)` equals 70
    - Test 5: `TokenBudget(max_tokens=100).total` after `add(30); add(20)` equals 50
  </behavior>
  <action>
Create six files. Locked decision (CONTEXT.md): Phase 1 only defines the *interface* of TokenBudget; Phase 3 wires production enforcement. So we keep TokenBudget minimal, in-memory, sync, fully unit-tested.

1) `Makefile` (use TAB indentation, not spaces — Makefile requires this):
```makefile
.PHONY: setup smoke validate-skills demo clean

setup:
	uv venv .venv --python 3.11
	. .venv/bin/activate && uv pip install -e ".[dev]"
	npm install
	npx skills add mmtmr/pageindex-rag -g -y
	. .venv/bin/activate && pre-commit install

smoke:
	. .venv/bin/activate && pytest tests/test_gate_01_hermes_import.py
	. .venv/bin/activate && pytest tests/test_gate_02_minimal_agent.py
	. .venv/bin/activate && pytest tests/test_gate_03_delegate_task.py
	. .venv/bin/activate && pytest tests/test_gate_04_pageindex_doc_search.py
	. .venv/bin/activate && pytest tests/test_gate_05_diacritics.py
	. .venv/bin/activate && pytest tests/test_gate_06_skills_ref.py
	. .venv/bin/activate && pytest tests/test_gate_07_concurrent_search.py

validate-skills:
	npx skills-ref@0.1.5 validate skills/

demo:
	@echo "Phase 1: nothing to demo yet — run 'make smoke' to verify gates"

clean:
	rm -rf .venv node_modules .pytest_cache .ruff_cache __pycache__ dist build *.egg-info
```

2) `parliament/__init__.py` — empty file (just `""""""` docstring):
```python
"""Virtual Parliament — multi-agent simulation of the Polish Sejm."""

__version__ = "0.1.0"
```

3) `parliament/second_brain/__init__.py` — empty package marker:
```python
"""PageIndex-backed knowledge layer (Second Brain)."""
```

4) `parliament/guards.py` — TokenBudget contract stub. Class-based (Claude's discretion per CONTEXT.md). Raise on exceed (fail loud). Verbatim:
```python
"""Token budget kill switch (INFRA-06).

Phase 1 establishes only the *interface* — Phase 3 wires this into the
orchestrator's LLM call path. All later code must import TokenBudget from
this module.
"""

from __future__ import annotations

from dataclasses import dataclass


class TokenBudgetExceeded(Exception):
    """Raised when a token addition would push cumulative usage past the cap."""


@dataclass
class TokenBudget:
    """Tracks cumulative LLM token usage against a configurable cap.

    Phase 1: interface stub. Phase 3: wired into every LLM call so a
    runaway session is aborted before billing damage.
    """

    max_tokens: int
    _total: int = 0

    def add(self, tokens: int) -> bool:
        """Record `tokens` of usage. Raises TokenBudgetExceeded if cap would be passed.

        Returns True on success (call may proceed).
        """
        if tokens < 0:
            raise ValueError("tokens must be non-negative")
        if self._total + tokens > self.max_tokens:
            raise TokenBudgetExceeded(
                f"Token budget exceeded: {self._total + tokens} > {self.max_tokens}"
            )
        self._total += tokens
        return True

    @property
    def total(self) -> int:
        return self._total

    @property
    def remaining(self) -> int:
        return self.max_tokens - self._total
```

5) `tests/__init__.py` — empty file (single newline):
```python
```

6) `tests/test_token_budget.py` — the RED-then-GREEN tests:
```python
"""Unit tests for parliament.guards.TokenBudget (INFRA-06 interface contract)."""

import pytest

from parliament.guards import TokenBudget, TokenBudgetExceeded


def test_import_works():
    """Test 1: module is importable."""
    assert TokenBudget is not None
    assert TokenBudgetExceeded is not None


def test_under_budget_returns_true():
    """Test 2: add() under cap returns True."""
    b = TokenBudget(max_tokens=100)
    assert b.add(50) is True


def test_over_budget_raises():
    """Test 3: add() that exceeds cap raises TokenBudgetExceeded."""
    b = TokenBudget(max_tokens=100)
    with pytest.raises(TokenBudgetExceeded):
        b.add(150)


def test_remaining_decrements():
    """Test 4: remaining property reflects added tokens."""
    b = TokenBudget(max_tokens=100)
    b.add(30)
    assert b.remaining == 70


def test_total_accumulates():
    """Test 5: total property accumulates across multiple add() calls."""
    b = TokenBudget(max_tokens=100)
    b.add(30)
    b.add(20)
    assert b.total == 50


def test_negative_tokens_rejected():
    """Defensive: negative tokens raise ValueError, not silently accepted."""
    b = TokenBudget(max_tokens=100)
    with pytest.raises(ValueError):
        b.add(-1)
```

7) `skills/.gitkeep` — empty file (zero bytes is fine):
```
```

After creating files, verify the test runs against the stub: `python -m pytest tests/test_token_budget.py -x` from repo root with `parliament/` on PYTHONPATH. (Executor: if no venv yet, run `PYTHONPATH=. python -m pytest tests/test_token_budget.py -x`.)
  </action>
  <verify>
    <automated>cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -m pytest tests/test_token_budget.py -x --tb=short</automated>
  </verify>
  <acceptance_criteria>
    - `test -f /Users/xpll081/ai-politics/Makefile` exit 0
    - `grep -P "^setup:" /Users/xpll081/ai-politics/Makefile` exit 0 (literal tab + colon after `setup`)
    - `grep -q "make smoke" /Users/xpll081/ai-politics/Makefile || grep -q "^smoke:" /Users/xpll081/ai-politics/Makefile` exit 0
    - `grep -q "pytest tests/test_gate_01_hermes_import.py" /Users/xpll081/ai-politics/Makefile` exit 0
    - `grep -q "pytest tests/test_gate_07_concurrent_search.py" /Users/xpll081/ai-politics/Makefile` exit 0
    - `grep -q "npx skills add mmtmr/pageindex-rag -g -y" /Users/xpll081/ai-politics/Makefile` exit 0
    - `test -f /Users/xpll081/ai-politics/parliament/__init__.py` exit 0
    - `test -f /Users/xpll081/ai-politics/parliament/second_brain/__init__.py` exit 0
    - `test -f /Users/xpll081/ai-politics/parliament/guards.py` exit 0
    - `test -f /Users/xpll081/ai-politics/tests/__init__.py` exit 0
    - `test -f /Users/xpll081/ai-politics/skills/.gitkeep` exit 0
    - `cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -c "from parliament.guards import TokenBudget, TokenBudgetExceeded; print('ok')"` exit 0
    - `cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -m pytest tests/test_token_budget.py -x` exit 0 (all 6 tests pass)
  </acceptance_criteria>
  <done>Makefile is real and tab-indented; parliament package importable; TokenBudget stub exists with class + exception + add/total/remaining; all 6 token budget tests pass.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| filesystem → git history | `.env` (with real API keys) must never cross into committed artifacts |
| developer machine → public GitHub | Anything in the working tree that is `git add`-ed becomes public the moment the repo is published |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-01-01 | Information Disclosure | `.env` file | mitigate | `.gitignore` contains literal `.env` (exact-line grep enforced in acceptance criteria); `.env.example` is committed instead with placeholder values only |
| T-01-02 | Information Disclosure | `PAGEINDEX_API_KEY` env var | mitigate | Documented in `.env.example` with placeholder text "replace-with-your-pageindex-cloud-api-key"; real key only lives in untracked `.env`; no log or test prints the value |
| T-01-03 | Tampering | dependency supply chain | mitigate | All Python deps pinned to exact versions (`==`) in `pyproject.toml`; Node `skills-ref` pinned to `0.1.5` in `package.json`; transitive pins inherit from hermes-agent's locked versions |
| T-01-04 | Repudiation | LICENSE absence at submission | mitigate | INFRA-01 acceptance criterion: `grep "MIT License" /LICENSE` exits 0; commit happens in this plan, well before submission day |
| T-01-05 | Denial of Service | runaway LLM cost (future, Phase 3) | accept (Phase 1) | TokenBudget interface stub created here so Phase 3 has a single import point; full enforcement is Phase 3 scope per CONTEXT.md |
</threat_model>

<verification>
After all three tasks complete, run from repo root:

```bash
# Repo legality
test -f LICENSE && grep -q "MIT License" LICENSE
test -f .gitignore && grep -Fxq ".env" .gitignore
test -f .env.example && grep -q "PAGEINDEX_API_KEY" .env.example

# Dependency pins
python3 -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); \
  assert 'hermes-agent==0.14.0' in d['project']['dependencies']; \
  assert d['project']['requires-python']=='>=3.11,<3.12'"

# Build skeleton
test -f parliament/guards.py && test -f tests/test_token_budget.py
PYTHONPATH=. python3 -m pytest tests/test_token_budget.py -x

# Makefile
grep -P "^setup:" Makefile && grep -P "^smoke:" Makefile
```

All commands must exit 0.
</verification>

<success_criteria>
- LICENSE present with MIT text (INFRA-01)
- pyproject.toml pins hermes-agent==0.14.0, Python 3.11, all locked deps from CONTEXT.md (INFRA-02)
- .env.example documents PAGEINDEX_API_KEY (gates BRAIN-01 in Plan 04)
- .gitignore excludes .env (security T-01-01)
- Makefile has `setup`, `smoke`, `validate-skills`, `demo`, `clean` targets
- parliament package importable, TokenBudget interface stub passes its unit tests
- Plan 02, 03, 04 can begin once these files exist
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation-smoke-tests/01-01-SUMMARY.md`.
</output>

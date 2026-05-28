---
project: parliament
assessed_at: 2026-05-28T08:30:00Z
agent_readiness: ready-with-compensation
context_type: brownfield
stack_components:
  language: Python 3.11
  framework: FastAPI + typer
  build_tool: hatchling
  test_runner: pytest 8.3.4 + pytest-asyncio
  package_manager: pip
  ci_provider: null
  deployment_target: null
gates_passed: 4
gates_failed: 1
---

## Stack Components

**Language — Python 3.11.**  Pinned via `pyproject.toml` (`requires-python = ">=3.11,<3.12"`). Required because `hermes-agent==0.14.0` is tested on 3.11 only. Type hints are used in some modules but not enforced by tooling.

**Web framework — FastAPI.**  Used for the `/health` + `/stream/{session_id}` SSE endpoint in `parliament/api.py`. Pydantic-based request/response shapes, auto-OpenAPI, sse-starlette for streaming.

**CLI framework — typer 0.25.1.**  Used for the `parliament` entry point in `parliament/cli.py`. Decorator-based command registration, type-hint-driven argument parsing.

**Build tool — hatchling.**  Standard PEP 621 build backend declared in `pyproject.toml`. Produces wheels via `pip install -e .` in <15s on this machine.

**Test runner — pytest 8.3.4 + pytest-asyncio 0.24.0.**  13 acceptance tests across 3 phases. Slow tests marked `@pytest.mark.slow` and gated behind `-m slow`.

**Package manager — pip** (no lockfile committed).  All deps pinned in `pyproject.toml`. Reproducibility relies on exact `==` pins; no `uv.lock` / `poetry.lock` / `requirements.txt` snapshot in repo.

**Linter — ruff 0.8.4** (`pyproject.toml [tool.ruff]`).

**CI/CD — none.**  No `.github/workflows/`, no `.gitlab-ci.yml`. Tests run locally only.

**Deployment — none yet.**  PRD Scope of Change adds PaaS deployment (Railway/Fly.io) in the upcoming phase.

**Instruction files — `CLAUDE.md` only** (project-level, ~200 lines, dense — covers stack tables, install commands, anti-patterns, version compatibility matrix).

## Quality Gate Assessment

| Component | Typed | Convention | Training Data | Documented | Verdict |
|-----------|:-----:|:----------:|:-------------:|:----------:|---------|
| Python 3.11 (language) | ✗ | — | — | — | fail |
| FastAPI (framework) | — | ✓ | ✓ | ✓ | pass |
| typer (CLI framework) | — | ✓ | ✓ | ✓ | pass |
| hatchling (build) | — | ✓ | ✓ | ✓ | pass |
| pytest (tests) | — | — | ✓ | ✓ | pass |

Legend: ✓ = pass, ✗ = fail, — = not applicable

### Gate Details

**Typed (Python: fail).**  `pyproject.toml` has no `[tool.mypy]` or `[tool.pyright]` section. No `mypy` or `pyright` in dev dependencies. Type annotations exist in production code (e.g. `def run_session(topic: str, *, ...) -> SessionResult:`) but nothing enforces them. An agent reading the code can reason about most function shapes, but cross-module contract drift (e.g. `SessionResult` dataclass fields changing) would not be caught at edit time.

**Convention (FastAPI/typer/hatchling: pass).**  FastAPI carries strong opinions about routing (decorators), DI (Depends), and Pydantic-based shapes. typer ships with Click conventions for CLI argument parsing. hatchling follows PEP 621. All three are agent-discoverable from minimal context.

**Training data (all components: pass).**  FastAPI, typer, pytest, hatchling, ruff — all are top-tier within the Python ecosystem. Hermes Agent 0.14.0 is the outlier (released 2026-05-16, niche framework) but `CLAUDE.md` already carries verified-fact tables compensating for this.

**Documented (all: pass).**  FastAPI auto-OpenAPI; typer mirrors Click docs; pytest has comprehensive guides; hermes-agent has version-pinned `RELEASE_v0.14.0.md` in its repo.

## Gaps & Compensation

**Gap 1 — Python typing not enforced.**  Without mypy/pyright in CI or pre-commit, an agent editing a dataclass field name (e.g. `SessionResult.vote_result` → `vote_outcome`) can ship a broken contract that only surfaces at runtime. Agent-friendly compensation: enforce types at boundaries (Pydantic at HTTP layer already does this) and document the type-hint expectation in `CLAUDE.md`.

**Secondary gap — no CI, no lockfile.**  Not a quality-gate failure (these aren't tracked gates), but worth flagging now that deployment is imminent. Without a lockfile, `pip install -e .` on a PaaS may resolve transitive deps differently than locally. Without CI, regressions in the acceptance suite go unnoticed.

### Recommended Instruction File Additions

Paste into `CLAUDE.md` under a new `## Type Conventions` section:

```markdown
## Type Conventions

This project uses Python type hints but does NOT run mypy/pyright in CI. When editing:

- **Public APIs (FastAPI handlers, CLI commands)** — fully annotated, including return types. Pydantic models at HTTP boundaries.
- **Dataclasses** (e.g. `SessionResult` in `parliament/session.py`) — treat field names and types as a contract. When you rename a field, grep the codebase for every read site before committing.
- **Internal helpers** — annotate function signatures at minimum. Body-internal locals may stay inferred.
- **No `from __future__ import annotations` removal** without checking call sites — many dataclasses rely on string-forward-refs.

If you need cross-module guarantees, add the type-checker to `pyproject.toml [dependency-groups.dev]` and CI in a follow-up change. For now, treat dataclass changes as breaking until proven otherwise.
```

Paste into `CLAUDE.md` under `## Deployment` (new section for upcoming PaaS phase):

```markdown
## Deployment

Target: Railway or Fly.io (decided per /10x-tech-stack-selector handoff).

Environment variables required on the platform:
- `OPENROUTER_API_KEY` — LLM access for Hermes subprocess
- `PAGEINDEX_API_KEY` — citation validator (PageIndex Cloud)
- `PARLIAMENT_MODEL_ORCHESTRATOR`, `_MINISTRY`, `_PARTY` — per-tier model overrides (optional)
- `PARLIAMENT_DB_PATH` — SQLite location (default: `sessions.db` in cwd)
- `PARLIAMENT_TOKEN_CAP` — token budget cap per session (default: 200000)

Python 3.11 exact — Hermes Agent 0.14.0 requires it. Provide via PaaS runtime config.
Hermes config (`~/.hermes/config.yaml`) must exist on the server with `provider: openrouter` and a working model id. The runtime image must ship a hermes-agent-compatible config OR mount one at startup.
```

Paste into `CLAUDE.md` under `## CI/CD` (new section):

```markdown
## CI/CD

No automated CI yet. Pre-deploy checklist (run locally):

1. `pytest tests/test_phase3_acceptance.py -q -m "not slow"` — must be 9/9 green
2. `ruff check parliament/ tests/` — lint clean
3. `pip install -e .` from a clean clone — verifies pyproject.toml integrity
4. `uvicorn parliament.api:app --port 8765` + `curl /health` — sanity check

After Phase 4 deploy lands, wire these into GitHub Actions so PR branches gate on them before merge to main.
```

## Summary

**Overall verdict: ready-with-compensation.**  4/5 gates pass cleanly. The one failing gate (Python typing) is well-known and the codebase already mitigates it at the layer that matters most for this product — FastAPI's Pydantic boundary and typer's type-hint-driven CLI. The compensation entries above close the gap for cross-module dataclass contracts.

**Key strengths:**
- FastAPI + typer + pytest + hatchling = mainstream Python stack with strong agent-pattern coverage
- Existing `CLAUDE.md` already compensates for the Hermes-Agent niche-ness with verified version pins
- Pydantic at HTTP boundaries already enforces types where it counts

**Key gaps:**
- No mypy/pyright — dataclass contract drift can ship un-caught
- No CI — regressions in acceptance suite go unnoticed
- No lockfile — `pip install` on PaaS may resolve transitive deps differently than local

**Recommended next step:** `/10x-tech-stack-selector` for the new components (Next.js frontend + PaaS deploy target) being added in the upcoming change, then `/10x-health-check` once the deploy lands.

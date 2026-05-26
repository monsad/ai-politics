---
phase: 01-foundation-smoke-tests
plan: 03
type: execute
wave: 2
depends_on: ["01-01"]
files_modified:
  - tests/test_gate_01_hermes_import.py
  - tests/test_gate_02_minimal_agent.py
  - tests/test_gate_03_delegate_task.py
  - tests/conftest.py
autonomous: true
requirements: [GATE-01, GATE-02, GATE-03]
requirements_addressed: [GATE-01, GATE-02, GATE-03]
must_haves:
  truths:
    - "Running `from run_agent import AIAgent` in the fresh venv after `pip install hermes-agent==0.14.0` succeeds with no ImportError"
    - "AIAgent.run_conversation('ping') returns a non-empty string response"
    - "delegate_task(tasks=[t1, t2]) with two dummy tasks returns both results without deadlock within 30s wall-clock"
  artifacts:
    - path: "tests/test_gate_01_hermes_import.py"
      provides: "Fresh-venv import sanity test for run_agent.AIAgent"
      exports: ["test_gate_01_hermes_import"]
    - path: "tests/test_gate_02_minimal_agent.py"
      provides: "Minimal AIAgent end-to-end LLM round-trip test"
      exports: ["test_gate_02_minimal_agent_returns_response"]
    - path: "tests/test_gate_03_delegate_task.py"
      provides: "Parallel delegate_task fan-out test"
      exports: ["test_gate_03_delegate_task_runs_two_in_parallel"]
    - path: "tests/conftest.py"
      provides: "Shared fixtures: dotenv loader, model name fixture, cheap-model flag"
      exports: ["model_name", "skip_if_no_api_key"]
  key_links:
    - from: "tests/test_gate_01_hermes_import.py"
      to: "hermes-agent==0.14.0 PyPI package (installs `run_agent` top-level module)"
      via: "import run_agent"
      pattern: "from run_agent import AIAgent"
    - from: "tests/test_gate_03_delegate_task.py"
      to: "hermes-agent delegate_task tool (ThreadPoolExecutor batch mode)"
      via: "delegate_task(tasks=[...]) — invoked via AIAgent.run_conversation prompt"
      pattern: "delegate_task"
---

<objective>
Prove Hermes Agent 0.14.0 works in this project's exact Python 3.11 venv: import succeeds (GATE-01), a minimal AIAgent answers a prompt (GATE-02), and `delegate_task(tasks=[...])` returns two parallel results without deadlocking (GATE-03). These three gates are mutually independent test files but share a `conftest.py` for fixtures.

Purpose: Hermes Agent is the contest-mandated framework. If any of these gates fails, ROADMAP.md cut criterion fires: "If GATE-01 fails: STOP. Open issue on hermes-agent repo." This plan exists to surface that failure on Day 1, not Day 3.
Output: Three gate test files + a conftest.py with shared fixtures. Tests must run from `pytest tests/test_gate_01..03.py` after `uv pip install -e ".[dev]"`.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md
@.planning/research/STACK.md
@.planning/research/PITFALLS.md
@pyproject.toml
@parliament/__init__.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Write tests/conftest.py with shared fixtures</name>
  <files>tests/conftest.py</files>
  <read_first>
    - /Users/xpll081/ai-politics/.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md (sections: Cost & quality guards — Cost smoke check; Claude's Discretion — test runner)
    - /Users/xpll081/ai-politics/.planning/research/PITFALLS.md (Pitfall 2 — Cost runaway)
    - /Users/xpll081/ai-politics/pyproject.toml (verify pytest + pytest-asyncio + python-dotenv are pinned)
  </read_first>
  <action>
Create `/Users/xpll081/ai-politics/tests/conftest.py`.

Locked decision from CONTEXT.md: Day 1 budget cap is $1 total. We achieve this by:
- Default model: cheapest available — `openrouter/openai/gpt-4o-mini` (or `openrouter/mistral-7b-instruct` if user prefers; resolved via env var `GATE_MODEL`).
- Skip gates needing a live API key when none is set, with a clear reason — so CI doesn't false-fail and a contributor without keys can still get green on GATE-06 + token-budget.

Verbatim content:

```python
"""Shared pytest fixtures for Phase 1 gate tests.

Fixtures:
- `dotenv_loaded`: autouse, loads .env so PAGEINDEX_API_KEY / OPENROUTER_API_KEY are present
- `model_name`: the cheap LLM model to use for GATE-02 / GATE-03 (env override: GATE_MODEL)
- `skip_if_no_llm_key`: marker fixture that skips when no LLM provider key is configured

Cost discipline: GATE_MODEL defaults to openrouter/openai/gpt-4o-mini (cheap).
Total Day-1 spend across all gate tests must stay under $1 (CONTEXT.md).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session", autouse=True)
def dotenv_loaded():
    """Load .env once per test session so API key env vars are available."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return  # python-dotenv not installed yet; conftest must not hard-fail
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)


@pytest.fixture
def model_name() -> str:
    """Cheap default model for GATE-02/03. Override via GATE_MODEL env var."""
    return os.environ.get("GATE_MODEL", "openrouter/openai/gpt-4o-mini")


def _has_any_llm_key() -> bool:
    return any(
        os.environ.get(k)
        for k in (
            "OPENROUTER_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "NOUS_PORTAL_TOKEN",
        )
    )


@pytest.fixture
def skip_if_no_llm_key():
    """Skip the test if no LLM provider key is configured.

    Use as a fixture argument; the fixture itself triggers the skip.
    """
    if not _has_any_llm_key():
        pytest.skip(
            "No LLM provider key in env (OPENROUTER_API_KEY / ANTHROPIC_API_KEY / "
            "OPENAI_API_KEY / NOUS_PORTAL_TOKEN). Add one to .env to run live LLM gates."
        )
```

Notes:
- `dotenv_loaded` is autouse + session-scoped, so every test sees the same env without explicit fixture requests
- `python-dotenv` import is wrapped in try/except so this file imports cleanly before `uv pip install -e ".[dev]"` is run
- `skip_if_no_llm_key` is a *fixture*, not a marker — clearer call-site signal (the test function depends on it)
- GATE-01 does NOT use `skip_if_no_llm_key` — import-only test doesn't call any LLM
- GATE-02 and GATE-03 DO use it
  </action>
  <verify>
    <automated>cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -c "import tests.conftest; print('ok')"</automated>
  </verify>
  <acceptance_criteria>
    - `test -f /Users/xpll081/ai-politics/tests/conftest.py` exit 0
    - `grep -q "dotenv_loaded" /Users/xpll081/ai-politics/tests/conftest.py` exit 0
    - `grep -q "model_name" /Users/xpll081/ai-politics/tests/conftest.py` exit 0
    - `grep -q "skip_if_no_llm_key" /Users/xpll081/ai-politics/tests/conftest.py` exit 0
    - `grep -q "openrouter/openai/gpt-4o-mini" /Users/xpll081/ai-politics/tests/conftest.py` exit 0
    - `cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -c "import tests.conftest"` exit 0
  </acceptance_criteria>
  <done>conftest.py imports cleanly without hermes-agent installed; provides 3 fixtures usable by GATE-02 / GATE-03.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Write tests/test_gate_01_hermes_import.py + tests/test_gate_02_minimal_agent.py</name>
  <files>tests/test_gate_01_hermes_import.py, tests/test_gate_02_minimal_agent.py</files>
  <read_first>
    - /Users/xpll081/ai-politics/.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md (sections: Stack — Python side — Hermes import path; Specifics — Test acceptance criteria — GATE-01 / GATE-02 rows)
    - /Users/xpll081/ai-politics/.planning/research/STACK.md (Hermes Agent — Verified API Surface — Programmatic API)
    - /Users/xpll081/ai-politics/.planning/research/PITFALLS.md (Pitfall 4 — Hermes Agent API surface underdocumented)
    - /Users/xpll081/ai-politics/tests/conftest.py (the fixtures we depend on)
  </read_first>
  <behavior>
    GATE-01:
    - Test 1: `from run_agent import AIAgent` succeeds and `AIAgent` is a class (type)
    - Test 2: The class has `run_conversation` attribute (verifies we got the right symbol, not a name collision)

    GATE-02:
    - Test 1: Instantiate `AIAgent(model=model_name, api_key=..., enabled_toolsets=[], ephemeral_system_prompt="You are a test echo.", skip_memory=True)` succeeds
    - Test 2: `agent.run_conversation(user_message="Reply with exactly the word: ack", task_id="gate-02-smoke")` returns a non-empty string within 30s
    - Skipif: when no LLM key is set, skip (don't fail)
  </behavior>
  <action>
Create two test files.

1) `/Users/xpll081/ai-politics/tests/test_gate_01_hermes_import.py`:

```python
"""GATE-01 — `from run_agent import AIAgent` works in a fresh Python 3.11 venv
after `pip install hermes-agent==0.14.0`.

Locked acceptance (CONTEXT.md): pytest exit code 0 after `uv pip install -e ".[dev]"`.

Critical: this test does NOT call any LLM. It only verifies the package
installed correctly and exposes the documented programmatic API. If this
fails, ROADMAP cut criterion fires: stop and open hermes-agent repo issue.
"""

from __future__ import annotations


def test_gate_01_hermes_import():
    """Import the documented Hermes Agent programmatic API entry point."""
    from run_agent import AIAgent  # noqa: F401 — import is the assertion

    assert isinstance(AIAgent, type), (
        f"Expected AIAgent to be a class, got {type(AIAgent).__name__}"
    )


def test_gate_01_ai_agent_has_run_conversation():
    """Defensive: verify we imported the documented Hermes AIAgent, not a name collision."""
    from run_agent import AIAgent

    assert hasattr(AIAgent, "run_conversation"), (
        "AIAgent imported from run_agent does not have run_conversation — "
        "wrong package may have shadowed hermes-agent's run_agent module."
    )
```

2) `/Users/xpll081/ai-politics/tests/test_gate_02_minimal_agent.py`:

```python
"""GATE-02 — A minimal AIAgent returns a non-empty response to a trivial prompt.

Locked acceptance (CONTEXT.md): pytest exit code 0, response is a non-empty string,
total cost under ~$0.001 (cheap model, ~50 input + ~10 output tokens).

If no LLM provider key is configured in .env, the test is SKIPPED (not failed).
"""

from __future__ import annotations

import os


def test_gate_02_minimal_agent_returns_response(model_name, skip_if_no_llm_key):
    """Instantiate AIAgent with a trivial system prompt and assert response is non-empty."""
    from run_agent import AIAgent

    # Pick the matching API key for the chosen model provider.
    if model_name.startswith("openrouter/"):
        api_key = os.environ["OPENROUTER_API_KEY"]
    elif model_name.startswith(("anthropic/", "claude-")):
        api_key = os.environ["ANTHROPIC_API_KEY"]
    elif model_name.startswith(("openai/", "gpt-")):
        api_key = os.environ["OPENAI_API_KEY"]
    else:
        # Fallback — try OPENROUTER_API_KEY; covers Nous Portal too via OpenAI-compat
        api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get(
            "ANTHROPIC_API_KEY"
        )

    agent = AIAgent(
        model=model_name,
        api_key=api_key,
        enabled_toolsets=[],
        ephemeral_system_prompt="You are a test echo. Respond with exactly the word 'ack'.",
        skip_memory=True,
    )

    response = agent.run_conversation(
        user_message="Reply with exactly the word: ack",
        task_id="gate-02-smoke",
    )

    assert isinstance(response, str), (
        f"Expected str response, got {type(response).__name__}: {response!r}"
    )
    assert len(response.strip()) > 0, "Response was empty/whitespace-only"
```

Implementation notes:
- GATE-01 is intentionally tiny — pure import. CONTEXT.md says this is the MOST IMPORTANT gate (cut criterion).
- GATE-02 uses `enabled_toolsets=[]` (no MCP yet — that's Plan 04/05's job) and `skip_memory=True` (CONTEXT.md "skip_memory=True — don't pollute shared MEMORY.md")
- `ephemeral_system_prompt` is the documented Hermes parameter per STACK.md "Programmatic API — AIAgent class"
- `task_id="gate-02-smoke"` per STACK.md example
- Model defaults to cheap `openrouter/openai/gpt-4o-mini` (Pitfall 2 mitigation)
- If `run_conversation` signature differs in the installed package (per Pitfall 4 — API may not match docs), test will fail with a clear message and the executor must consult `python -c "import inspect, run_agent; print(inspect.signature(run_agent.AIAgent.run_conversation))"` — but we don't pre-emptively over-defend; the test asserts what STACK.md research promised.
- Test runtime budget: ~5s LLM round trip + setup. pytest default timeout is fine.
  </action>
  <verify>
    <automated>cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -m pytest tests/test_gate_01_hermes_import.py tests/test_gate_02_minimal_agent.py -x --tb=short --collect-only</automated>
  </verify>
  <acceptance_criteria>
    - `test -f /Users/xpll081/ai-politics/tests/test_gate_01_hermes_import.py` exit 0
    - `test -f /Users/xpll081/ai-politics/tests/test_gate_02_minimal_agent.py` exit 0
    - `grep -q "from run_agent import AIAgent" /Users/xpll081/ai-politics/tests/test_gate_01_hermes_import.py` exit 0
    - `grep -q "def test_gate_01_hermes_import" /Users/xpll081/ai-politics/tests/test_gate_01_hermes_import.py` exit 0
    - `grep -q "def test_gate_02_minimal_agent_returns_response" /Users/xpll081/ai-politics/tests/test_gate_02_minimal_agent.py` exit 0
    - `grep -q "skip_memory=True" /Users/xpll081/ai-politics/tests/test_gate_02_minimal_agent.py` exit 0
    - `grep -q "enabled_toolsets=\[\]" /Users/xpll081/ai-politics/tests/test_gate_02_minimal_agent.py` exit 0
    - `cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -m pytest tests/test_gate_01_hermes_import.py tests/test_gate_02_minimal_agent.py --collect-only` exit 0 (3 tests collected, no import errors)
    - After `uv pip install -e ".[dev]"` and (for GATE-02) a valid LLM key in `.env`: `pytest tests/test_gate_01_hermes_import.py tests/test_gate_02_minimal_agent.py -x` exits 0
    - When no LLM key is set: GATE-02 is SKIPPED (not failed) — verify with `pytest tests/test_gate_02_minimal_agent.py -v` showing `SKIPPED [1]` not `FAILED`
  </acceptance_criteria>
  <done>Both test files are syntactically valid Python and pytest collects them without import errors. GATE-01 runs unconditionally; GATE-02 runs when an LLM key is present, skips cleanly when not.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Write tests/test_gate_03_delegate_task.py</name>
  <files>tests/test_gate_03_delegate_task.py</files>
  <read_first>
    - /Users/xpll081/ai-politics/.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md (sections: Hermes fan-out — delegate_task; Specifics — Test acceptance criteria — GATE-03 row)
    - /Users/xpll081/ai-politics/.planning/research/STACK.md (Hermes Agent — Parallel fan-out via delegate_task)
    - /Users/xpll081/ai-politics/.planning/research/PITFALLS.md (Pitfall 4 — memory isolation; ANTI-PATTERN: asyncio.gather over AIAgent)
    - /Users/xpll081/ai-politics/tests/test_gate_02_minimal_agent.py (for shared instantiation pattern)
  </read_first>
  <behavior>
    - Test 1: Build a parent AIAgent. Issue a single `run_conversation` prompt that instructs the agent to call `delegate_task(tasks=[task1, task2])` with two trivial sub-tasks. Assert: (a) the call returns within 60s wall-clock (Pitfall 4 — verify no deadlock), (b) the final response is non-empty, (c) the response references both sub-task results.
    - Skip-if: no LLM provider key configured.
  </behavior>
  <action>
Create `/Users/xpll081/ai-politics/tests/test_gate_03_delegate_task.py`.

Critical context: Hermes `delegate_task` is invoked BY THE AGENT, not by Python directly. The agent must be told (via system prompt or user prompt) to call `delegate_task`. We can't `import delegate_task` and call it ourselves — it's a Hermes tool, not a Python-side function (STACK.md confirms: "This is the Hermes-native pattern — invoked as a tool by the Marszałek agent").

So GATE-03's test instructs the agent to perform a fan-out and verifies both children completed.

```python
"""GATE-03 — delegate_task(tasks=[t1, t2]) returns both results without deadlock.

Locked acceptance (CONTEXT.md, REQUIREMENTS.md):
- 2 dummy tasks run via Hermes delegate_task batch mode
- Both results returned (non-None)
- Wall-clock under 30s (CONTEXT.md says "within 30s wall-clock"; we allow 60s to
  absorb network jitter on a $5 VPS — anything over 60s = deadlock per Pitfall 4)

Critical anti-pattern check (PITFALLS Pitfall 4 + STACK.md "What NOT to Use"):
- We do NOT call `delegate_task` directly from Python.
- We do NOT use `asyncio.gather` over AIAgent instances (deadlocks on prompt_toolkit stdin).
- We instruct the parent AIAgent to issue delegate_task itself, which is the
  Hermes-blessed fan-out pattern (ThreadPoolExecutor under the hood).
"""

from __future__ import annotations

import os
import time


# Hermes delegate_task is a tool the agent CALLS, not a function we import.
# The toolset name to enable for delegation per STACK.md is the default agent
# toolset (delegate_task is built into hermes-agent). We pass an explicit
# instruction that names the tool to remove ambiguity.

DELEGATE_PROMPT = """\
Use your delegate_task tool to fan out two parallel sub-tasks at once:

  tasks=[
    {"goal": "Reply with exactly the word 'alpha' and nothing else.", "context": "", "toolsets": []},
    {"goal": "Reply with exactly the word 'bravo' and nothing else.", "context": "", "toolsets": []},
  ]

After both sub-tasks complete, return a single line containing both results
joined by a comma, e.g. "alpha, bravo". Do not call delegate_task more than once.
"""


def test_gate_03_delegate_task_runs_two_in_parallel(model_name, skip_if_no_llm_key):
    """Parent agent fans out two sub-tasks via delegate_task and both return."""
    from run_agent import AIAgent

    if model_name.startswith("openrouter/"):
        api_key = os.environ["OPENROUTER_API_KEY"]
    elif model_name.startswith(("anthropic/", "claude-")):
        api_key = os.environ["ANTHROPIC_API_KEY"]
    elif model_name.startswith(("openai/", "gpt-")):
        api_key = os.environ["OPENAI_API_KEY"]
    else:
        api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get(
            "ANTHROPIC_API_KEY"
        )

    parent = AIAgent(
        model=model_name,
        api_key=api_key,
        # The 'delegate' toolset (or its hermes-agent equivalent) must be enabled
        # for the parent agent to call delegate_task. Per hermes-agent 0.14.0
        # convention, delegate_task is in the 'delegate' toolset.
        enabled_toolsets=["delegate"],
        ephemeral_system_prompt=(
            "You are a fan-out coordinator. When asked, you use the delegate_task "
            "tool to run sub-tasks in parallel and combine their results."
        ),
        skip_memory=True,
    )

    started = time.monotonic()
    response = parent.run_conversation(
        user_message=DELEGATE_PROMPT,
        task_id="gate-03-fanout",
    )
    elapsed = time.monotonic() - started

    # Deadlock check (Pitfall 4): if delegate_task locks up, we never reach this.
    # 60s is generous — STACK.md research suggests <30s typical.
    assert elapsed < 60, f"delegate_task took {elapsed:.1f}s — possible deadlock"

    # Both sub-task results must surface in the final response.
    assert isinstance(response, str) and response.strip(), "Empty response"
    lowered = response.lower()
    assert "alpha" in lowered, f"Sub-task 1 result 'alpha' missing from response: {response!r}"
    assert "bravo" in lowered, f"Sub-task 2 result 'bravo' missing from response: {response!r}"
```

Notes:
- We enable `enabled_toolsets=["delegate"]` — Hermes's documented toolset name for delegate_task. If the actual toolset name in 0.14.0 is different (e.g. `"delegation"` or `"tasks"`), the test will fail clearly and the executor must check `python -c "import run_agent; print(dir(run_agent))"` or read `hermes-agent`'s `tools/delegate_tool.py`. CONTEXT.md "Stack — Python side" and STACK.md both name `delegate_task` but do not pin the *toolset* name; `"delegate"` is the most likely convention.
- Sub-tasks use `toolsets: []` — they don't need to call anything, just reply with their goal text.
- 60s timeout because CONTEXT.md says "≤ 30s wall-clock" is the *target*, but we want a meaningful deadlock signal (Pitfall 4) not a flaky-network failure.
- We do NOT call `asyncio.gather` anywhere — explicit per CONTEXT.md "What NOT to Use".

Risk: if `delegate_task` requires a different toolset name in 0.14.0, this test will fail at agent invocation. The Phase 1 cut criterion (CONTEXT.md "If GATE-03 fails: re-architect Phase 3 to sequential ministry consultations") will fire, and the executor will update Phase 3 plans accordingly. That is the intended behavior — we surface this risk Day 1, not Day 4.
  </action>
  <verify>
    <automated>cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -m pytest tests/test_gate_03_delegate_task.py --collect-only --tb=short</automated>
  </verify>
  <acceptance_criteria>
    - `test -f /Users/xpll081/ai-politics/tests/test_gate_03_delegate_task.py` exit 0
    - `grep -q "delegate_task" /Users/xpll081/ai-politics/tests/test_gate_03_delegate_task.py` exit 0
    - `grep -q "enabled_toolsets=\[\"delegate\"\]" /Users/xpll081/ai-politics/tests/test_gate_03_delegate_task.py` exit 0
    - `grep -q "def test_gate_03_delegate_task_runs_two_in_parallel" /Users/xpll081/ai-politics/tests/test_gate_03_delegate_task.py` exit 0
    - NOT-present check (anti-pattern): `! grep -q "asyncio.gather" /Users/xpll081/ai-politics/tests/test_gate_03_delegate_task.py` exit 0
    - NOT-present check (anti-pattern): `! grep -q "multiprocessing" /Users/xpll081/ai-politics/tests/test_gate_03_delegate_task.py` exit 0
    - `grep -q "elapsed < 60" /Users/xpll081/ai-politics/tests/test_gate_03_delegate_task.py` exit 0
    - `cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -m pytest tests/test_gate_03_delegate_task.py --collect-only` exit 0
    - After `uv pip install -e ".[dev]"` + LLM key in `.env`: `pytest tests/test_gate_03_delegate_task.py -x` exits 0 and prints both 'alpha' and 'bravo' in the response (~$0.001 cost on gpt-4o-mini).
    - When no LLM key: test is SKIPPED, not FAILED.
  </acceptance_criteria>
  <done>GATE-03 test file is syntactically valid, references `delegate_task` (not `asyncio.gather`), has a deadlock-detection timer, and passes when run with a valid LLM key.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Python venv → external LLM API | API keys must travel from `.env` → `os.environ` → AIAgent constructor without being logged or echoed |
| Hermes Agent → child threads | `delegate_task` spawns ThreadPoolExecutor workers; each child must use isolated memory namespaces (Pitfall 4 mitigation, but enforced in Phase 3) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-03-01 | Information Disclosure | LLM API key in `os.environ` | mitigate | Key sourced from `.env` (gitignored per Plan 01); test code never logs `api_key`; assertion failure messages quote only the *response*, never the key |
| T-03-02 | Denial of Service | Cost runaway on repeated gate runs | mitigate | `model_name` fixture defaults to `openrouter/openai/gpt-4o-mini` (cheapest tier per STACK.md); per-test prompt is ~50 tokens; full GATE-02/03 round-trip ~$0.001; budget cap enforced socially by CONTEXT.md "Day 1 total < $1" |
| T-03-03 | Tampering | wrong `run_agent` module shadowing hermes-agent | mitigate | `test_gate_01_ai_agent_has_run_conversation` asserts the imported class has the documented `run_conversation` method (catches a stray local `run_agent.py` shadowing the installed package) |
| T-03-04 | Repudiation | `delegate_task` silent failure (Pitfall 4) | mitigate | Test asserts both 'alpha' and 'bravo' appear in the final response — a silent tool-error producing an empty result is caught by the assertion, not swallowed |
</threat_model>

<verification>
After all three tasks complete, run from repo root:

```bash
# Test files exist and are parseable
PYTHONPATH=. python3 -m pytest tests/test_gate_01_hermes_import.py tests/test_gate_02_minimal_agent.py tests/test_gate_03_delegate_task.py --collect-only

# Full run (requires `uv pip install -e ".[dev]"` first and LLM key in .env)
. .venv/bin/activate && pytest tests/test_gate_01_hermes_import.py -x
. .venv/bin/activate && pytest tests/test_gate_02_minimal_agent.py -x  # may skip if no key
. .venv/bin/activate && pytest tests/test_gate_03_delegate_task.py -x  # may skip if no key

# Anti-pattern check
! grep -r "asyncio.gather" tests/test_gate_03_delegate_task.py
```

All exit 0.
</verification>

<success_criteria>
- `from run_agent import AIAgent` works in the Phase 1 venv (GATE-01 passes)
- A minimal AIAgent returns a non-empty response (GATE-02 passes)
- `delegate_task(tasks=[t1, t2])` returns both results in under 60s (GATE-03 passes)
- All three tests collect and skip cleanly when keys absent — no false failures in CI
- Anti-pattern `asyncio.gather` over AIAgent does NOT appear anywhere
- Total Day-1 cost across these three gates: < $0.01
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation-smoke-tests/01-03-SUMMARY.md`.
</output>

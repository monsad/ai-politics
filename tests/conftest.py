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
    """Cheap default model for GATE-02/03. Override via GATE_MODEL env var.

    Auto-detects: prefers ANTHROPIC_API_KEY → claude-haiku-4-5 (native), else openrouter.
    """
    if "GATE_MODEL" in os.environ:
        return os.environ["GATE_MODEL"]
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude-haiku-4-5-20251001"
    return "openrouter/openai/gpt-4o-mini"


@pytest.fixture
def llm_base_url() -> str | None:
    """Base URL override — None means hermes uses its default routing."""
    return None


@pytest.fixture
def llm_provider() -> str | None:
    """Explicit provider name for hermes AIAgent.

    Setting provider="anthropic" makes hermes use the native Anthropic SDK.
    Only set when ANTHROPIC_API_KEY is a real standalone key (present in .env),
    not the Claude Code session token injected into the system environment.
    """
    model = os.environ.get("GATE_MODEL", "")
    if not model and os.environ.get("ANTHROPIC_API_KEY") and "ANTHROPIC_API_KEY" in _dot_env_keys():
        return "anthropic"
    return None


def _dot_env_keys() -> set[str]:
    """Return the set of keys explicitly defined in the project .env file."""
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return set()
    keys: set[str] = set()
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            keys.add(line.split("=", 1)[0].strip())
    return keys


def _has_any_llm_key() -> bool:
    """Return True only when a standalone LLM key (not a CC session token) is available.

    ANTHROPIC_API_KEY injected by Claude Code is a session token — valid only inside
    the CC SDK, not for direct API calls. We trust it only when it is also explicitly
    set in the project .env file, i.e., the user provisioned it as a real key.
    """
    dot_env = _dot_env_keys()
    # Keys that are safe to use regardless of origin
    for k in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "NOUS_PORTAL_TOKEN"):
        if os.environ.get(k):
            return True
    # ANTHROPIC_API_KEY: only trust when the user explicitly placed it in .env
    if os.environ.get("ANTHROPIC_API_KEY") and "ANTHROPIC_API_KEY" in dot_env:
        return True
    return False


@pytest.fixture
def skip_if_no_llm_key():
    """Skip the test if no usable LLM provider key is configured.

    Use as a fixture argument; the fixture itself triggers the skip.
    """
    if not _has_any_llm_key():
        pytest.skip(
            "No standalone LLM key found. Add one to .env:\n"
            "  ANTHROPIC_API_KEY=sk-ant-...   (real key, not the CC session token)\n"
            "  OPENROUTER_API_KEY=sk-or-v1-...\n"
            "  OPENAI_API_KEY=sk-...\n"
        )

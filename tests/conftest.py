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

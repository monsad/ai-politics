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

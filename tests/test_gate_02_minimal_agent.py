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

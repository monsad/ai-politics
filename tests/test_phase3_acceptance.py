"""Phase 3 acceptance tests — Wave 0 stubs, later plans flesh out."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_entry_point():
    """CLI-05: `parliament` command resolves in PATH."""
    assert shutil.which("parliament") is not None, (
        "Run `pip install -e .` after fixing pyproject.toml entry point."
    )


def test_disclaimer_constant():
    """ETHICS-01 (partial): DISCLAIMER constant defined and starts with the warning glyph."""
    from parliament.cli import DISCLAIMER
    assert DISCLAIMER.startswith("⚠️"), DISCLAIMER
    assert "EDUCATIONAL SIMULATION" in DISCLAIMER


def test_db_schema(tmp_path):
    """INFRA-05: tables sessions, utterances, votes, bill_drafts exist; WAL mode set."""
    pytest.skip("Plan 02: parliament/db.py implementation")


def test_token_budget_wired():
    """INFRA-06: session.run_session accounts response chars against TokenBudget."""
    pytest.skip("Plan 04: session.py token budget wiring")


def test_agent_factory_cmd():
    """INFRA-04: build_hermes_cmd returns expected argv for marszalek-sejmu."""
    pytest.skip("Plan 03: agent_factory.py implementation")


def test_citation_validator_smoke():
    """ORCH-09: validate_citations returns dict with required keys on empty input."""
    pytest.skip("Plan 03: citation_validator.py implementation")


def test_reasoning_blocks_parsed():
    """ORCH-08: parse_phases detects [MARSZAŁEK REASONING] marker."""
    pytest.skip("Plan 04: session.parse_phases implementation")


def test_markdown_export(tmp_path):
    """CLI-03 + EXPORT-01: --export markdown writes file with all sections + disclaimers."""
    pytest.skip("Plan 04: cli.py export wiring")


def test_sse_endpoint_smoke():
    """INFRA-04 (api): GET /stream/{session_id} returns 200 with text/event-stream content type."""
    pytest.skip("Plan 05: api.py SSE endpoint")


@pytest.mark.slow
def test_full_simulation_4day_work_week():
    """CLI-01 + ORCH-02..07: end-to-end on '4-day work week' ≤ 5 min, vote table present."""
    pytest.skip("Plan 05: end-to-end acceptance (slow, requires Hermes subprocess)")


@pytest.mark.slow
def test_full_simulation_oze():
    """CLI-01: end-to-end on 'OZE expansion'."""
    pytest.skip("Plan 05: end-to-end acceptance")


@pytest.mark.slow
def test_full_simulation_tax():
    """CLI-01: end-to-end on 'tax simplification'."""
    pytest.skip("Plan 05: end-to-end acceptance")


@pytest.mark.slow
def test_minister_isolation_finanse():
    """CLI-02: --minister finanse returns structured 4-section output < 60 s."""
    pytest.skip("Plan 04: --minister isolation mode")

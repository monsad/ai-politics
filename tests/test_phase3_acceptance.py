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
    """INFRA-05: tables exist; WAL mode set; helpers round-trip data."""
    from parliament import db as pdb

    db_path = tmp_path / "test.db"
    pdb.init_db(db_path)

    import sqlite3
    con = sqlite3.connect(str(db_path))
    try:
        mode = con.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal", mode

        tables = {row[0] for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        assert {"sessions", "utterances", "votes", "bill_drafts"}.issubset(tables), tables
    finally:
        con.close()

    pdb.insert_session(db_path, "sess-1", "4-day work week")
    pdb.insert_utterance(db_path, "sess-1", 1, "MARSZAŁEK", "classification", "Topic accepted.", ["n1", "n2"])
    pdb.insert_vote(db_path, "sess-1", "KO", "FOR", 157)
    pdb.insert_bill_draft(db_path, "sess-1", "Draft 1", "# Article 1\n...")
    pdb.update_session(db_path, "sess-1", status="complete", vote_result="PASSED", exit_code=0, raw_output="...")

    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute("SELECT status, vote_result, exit_code, finished_at FROM sessions WHERE id=?", ("sess-1",)).fetchone()
        assert row[0] == "complete"
        assert row[1] == "PASSED"
        assert row[2] == 0
        assert row[3] is not None
        utt = con.execute("SELECT speaker, node_ids FROM utterances WHERE session_id=?", ("sess-1",)).fetchone()
        assert utt[0] == "MARSZAŁEK"
        import json
        assert json.loads(utt[1]) == ["n1", "n2"]
    finally:
        con.close()


def test_token_budget_wired():
    """INFRA-06: session.run_session accounts response chars against TokenBudget."""
    pytest.skip("Plan 04: session.py token budget wiring")


def test_agent_factory_cmd(monkeypatch):
    """INFRA-04: build_hermes_cmd returns verified argv; env carries flags."""
    from parliament.agent_factory import build_hermes_cmd, build_hermes_env

    cmd = build_hermes_cmd("marszalek-sejmu", "4-day work week")
    assert cmd == [
        "hermes", "chat",
        "-s", "marszalek-sejmu",
        "-q", "4-day work week",
        "-Q", "--accept-hooks", "--yolo",
    ]

    cmd2 = build_hermes_cmd("ministry-finansow", "ile kosztuje 800+", tier="ministry")
    assert cmd2[3] == "ministry-finansow"
    assert cmd2[5] == "ile kosztuje 800+"

    # Topic injection: the topic is one argv element regardless of shell chars
    cmd3 = build_hermes_cmd("marszalek-sejmu", "tax; rm -rf /")
    assert cmd3[5] == "tax; rm -rf /"
    assert "shell" not in " ".join(cmd3).lower()

    env = build_hermes_env("orchestrator")
    assert env["HERMES_YOLO_MODE"] == "1"
    assert env["HERMES_ACCEPT_HOOKS"] == "1"

    # Tier model override
    monkeypatch.setenv("PARLIAMENT_MODEL_MINISTRY", "hermes-3-8b")
    env2 = build_hermes_env("ministry")
    assert env2.get("HERMES_MODEL") == "hermes-3-8b"

    import pytest as _pytest
    with _pytest.raises(ValueError):
        build_hermes_cmd("marszalek-sejmu", "x", tier="invalid")  # type: ignore[arg-type]


def test_citation_validator_smoke(monkeypatch):
    """ORCH-09 support: extract_node_ids parses both citation styles;
    validate_citations returns the contract dict shape with no API key."""
    from parliament.citation_validator import extract_node_ids, validate_citations
    import asyncio

    sample = (
        "Konstytucja Art. 32 (orig. PL: \"Wszyscy są wobec prawa równi\" — konstytucja.pdf p.5)\n"
        "Per node_id: abc123 the right to dignity applies.\n"
        "See also kodeks-pracy.pdf p.12-15 on labor rights.\n"
        "Repeated reference: node_id: abc123 — should not duplicate.\n"
    )
    tokens = extract_node_ids(sample)
    # Expect three unique tokens: konstytucja.pdf#p5, abc123, kodeks-pracy.pdf#p12-15
    assert "abc123" in tokens
    assert "konstytucja.pdf#p5" in tokens
    assert "kodeks-pracy.pdf#p12-15" in tokens
    assert len(tokens) == 3  # de-duped

    # Without API key, validate returns the contract shape + error
    monkeypatch.delenv("PAGEINDEX_API_KEY", raising=False)
    result = asyncio.run(validate_citations(tokens))
    assert set(result.keys()) >= {"total", "resolved", "unresolvable"}
    assert result["total"] == 3
    assert result["resolved"] == 0
    assert len(result["unresolvable"]) == 3
    assert result.get("error") == "PAGEINDEX_API_KEY missing"

    # Empty input → empty result
    empty = asyncio.run(validate_citations([]))
    assert empty == {"total": 0, "resolved": 0, "unresolvable": []} or (
        empty["total"] == 0 and empty["resolved"] == 0 and empty["unresolvable"] == []
    )


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

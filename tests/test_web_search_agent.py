"""Tests for web-search toolset wiring in agent_factory and web-research skill validity.

Non-slow tests are pure argv/YAML assertions — no network, no subprocess.
Slow tests (marked @pytest.mark.slow) spawn hermes and require a live web connection.
Run default suite with: pytest tests/test_web_search_agent.py -m "not slow"
"""
from __future__ import annotations

import os

import pytest
import yaml

from parliament.agent_factory import build_hermes_cmd


# ---------------------------------------------------------------------------
# build_hermes_cmd — toolsets parameter
# ---------------------------------------------------------------------------


def test_build_hermes_cmd_no_toolsets_unchanged():
    """Omitting toolsets returns the same argv as before (backward compatible)."""
    cmd = build_hermes_cmd("ministry-finansow", "query text")
    assert cmd == [
        "hermes", "chat", "-s", "ministry-finansow", "-q", "query text",
        "-Q", "--accept-hooks", "--yolo",
    ]
    assert "-t" not in cmd


def test_build_hermes_cmd_toolsets_none_unchanged():
    """Passing toolsets=None is equivalent to omitting it."""
    cmd = build_hermes_cmd("ministry-finansow", "query", toolsets=None)
    assert "-t" not in cmd


def test_build_hermes_cmd_single_toolset():
    """toolsets=['web'] appends -t web to the argv."""
    cmd = build_hermes_cmd("web-research", "Polish minimum wage 2026", toolsets=["web"])
    assert "-t" in cmd
    t_index = cmd.index("-t")
    assert cmd[t_index + 1] == "web"


def test_build_hermes_cmd_multiple_toolsets_comma_joined():
    """Multiple toolsets are joined as a comma-separated value for -t."""
    cmd = build_hermes_cmd("web-research", "query", toolsets=["web", "search"])
    t_index = cmd.index("-t")
    assert cmd[t_index + 1] == "web,search"


def test_build_hermes_cmd_toolsets_empty_list_unchanged():
    """An empty toolsets list is treated as no toolsets (no -t flag)."""
    cmd = build_hermes_cmd("ministry-finansow", "query", toolsets=[])
    assert "-t" not in cmd


def test_build_hermes_cmd_invalid_toolset_empty_string():
    """An empty string in toolsets raises ValueError."""
    with pytest.raises(ValueError, match="toolset"):
        build_hermes_cmd("ministry-finansow", "query", toolsets=[""])


def test_build_hermes_cmd_invalid_toolset_whitespace():
    """A toolset id containing whitespace raises ValueError."""
    with pytest.raises(ValueError, match="toolset"):
        build_hermes_cmd("ministry-finansow", "query", toolsets=["web search"])


def test_build_hermes_cmd_toolsets_preserves_base_flags():
    """Base flags (-Q, --accept-hooks, --yolo) are still present when toolsets given."""
    cmd = build_hermes_cmd("web-research", "query", toolsets=["web"])
    assert "-Q" in cmd
    assert "--accept-hooks" in cmd
    assert "--yolo" in cmd


# ---------------------------------------------------------------------------
# web-research SKILL.md — frontmatter validity
# ---------------------------------------------------------------------------

_SKILL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "skills", "web-research", "SKILL.md"
)


def _parse_skill_frontmatter(path: str) -> dict:
    """Extract and parse the YAML frontmatter block from a SKILL.md file."""
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    if not content.startswith("---"):
        raise ValueError("SKILL.md does not start with YAML frontmatter")
    parts = content.split("---", 2)
    # parts[0] = '', parts[1] = frontmatter yaml, parts[2] = body
    return yaml.safe_load(parts[1])


def test_skill_frontmatter_name():
    """web-research SKILL.md has name == 'web-research'."""
    fm = _parse_skill_frontmatter(_SKILL_PATH)
    assert fm["name"] == "web-research"


def test_skill_frontmatter_license():
    """web-research SKILL.md declares MIT license."""
    fm = _parse_skill_frontmatter(_SKILL_PATH)
    assert fm["license"] == "MIT"


def test_skill_frontmatter_model_tier():
    """web-research SKILL.md specifies a model_tier."""
    fm = _parse_skill_frontmatter(_SKILL_PATH)
    assert "model_tier" in fm.get("metadata", {})


def test_skill_body_references_web_search():
    """SKILL.md body instructs the agent to call web_search."""
    with open(_SKILL_PATH, encoding="utf-8") as fh:
        content = fh.read()
    assert "web_search" in content


def test_skill_body_has_output_constraints():
    """SKILL.md contains an Output Constraints section."""
    with open(_SKILL_PATH, encoding="utf-8") as fh:
        content = fh.read()
    assert "Output Constraints" in content


# ---------------------------------------------------------------------------
# Slow tests (live subprocess — skipped by default)
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_web_research_agent_live():
    """SLOW: Spawns hermes and performs a live web search. Requires hermes on PATH."""
    import subprocess

    cmd = build_hermes_cmd(
        "web-research",
        "Polish minimum wage 2026",
        toolsets=["web"],
    )
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    # Basic sanity: response should contain a URL pattern
    assert "http" in result.stdout.lower()

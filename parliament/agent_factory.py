"""INFRA-04: build Hermes subprocess command for any skill folder.

The CLI surface (Plan 04 session.py) ALWAYS uses this factory — never
constructs the argv list inline. This makes the Hermes invocation
pattern auditable and testable in one place.
"""
from __future__ import annotations

import os
from typing import Literal

ModelTier = Literal["orchestrator", "ministry", "party"]

_TIER_ENV_VAR = {
    "orchestrator": "PARLIAMENT_MODEL_ORCHESTRATOR",
    "ministry": "PARLIAMENT_MODEL_MINISTRY",
    "party": "PARLIAMENT_MODEL_PARTY",
}

_HERMES_BASE_FLAGS = ("-Q", "--accept-hooks", "--yolo")

def build_hermes_cmd(
    skill: str,
    query: str,
    *,
    tier: ModelTier = "orchestrator",
    toolsets: list[str] | None = None,
) -> list[str]:
    """Return the argv list for `subprocess.Popen(cmd, shell=False)`.

    Verified invocation (research 03-RESEARCH.md Pattern 1):
        hermes chat -s <skill> -q <query> -Q --accept-hooks --yolo

    Optional toolsets attach Hermes built-in toolsets via the -t flag:
        hermes chat -s <skill> -q <query> -t web -Q --accept-hooks --yolo

    Args:
        skill: Skill directory name (lowercase-hyphen, no path separators).
        query: The question/prompt to pass to the agent.
        tier: Model tier — controls which PARLIAMENT_MODEL_* env var is used.
        toolsets: Optional list of Hermes toolset ids to attach (e.g. ["web"]).
            Multiple ids are joined as comma-separated: ["web","search"] -> "-t web,search".
            None or empty list: no -t flag is added (backward compatible).
    """
    if tier not in _TIER_ENV_VAR:
        raise ValueError(f"Unknown model tier: {tier!r}. Allowed: {list(_TIER_ENV_VAR)}")
    if not skill or "/" in skill or skill != skill.strip():
        raise ValueError(f"Invalid skill id: {skill!r}")

    cmd: list[str] = ["hermes", "chat", "-s", skill, "-q", query]

    if toolsets:
        for ts in toolsets:
            if not ts or any(c in ts for c in (" ", "\t", "\n", "/")):
                raise ValueError(
                    f"Invalid toolset id: {ts!r}. Must be non-empty with no whitespace or '/'."
                )
        cmd += ["-t", ",".join(toolsets)]

    cmd += list(_HERMES_BASE_FLAGS)
    return cmd

def build_hermes_env(tier: ModelTier = "orchestrator") -> dict[str, str]:
    """Return the env dict for the subprocess.

    - Always sets HERMES_YOLO_MODE=1 and HERMES_ACCEPT_HOOKS=1 (suppress prompts).
    - If PARLIAMENT_MODEL_<TIER> is set in the parent env, propagates it as HERMES_MODEL.
    """
    if tier not in _TIER_ENV_VAR:
        raise ValueError(f"Unknown model tier: {tier!r}")
    env = {
        **os.environ,
        "HERMES_YOLO_MODE": "1",
        "HERMES_ACCEPT_HOOKS": "1",
    }
    tier_model = os.environ.get(_TIER_ENV_VAR[tier])
    if tier_model:
        env["HERMES_MODEL"] = tier_model
    return env

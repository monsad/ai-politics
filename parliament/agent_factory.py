"""INFRA-04: build hermes subprocess command from a skill folder. Wave 1 Plan 03."""
from __future__ import annotations
from typing import Literal

ModelTier = Literal["orchestrator", "ministry", "party"]

def build_hermes_cmd(skill: str, query: str, *, tier: ModelTier = "orchestrator") -> list[str]:
    """Return argv list for subprocess.Popen. Implemented in Plan 03."""
    raise NotImplementedError("Implemented in Phase 3 Plan 03")

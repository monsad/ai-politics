"""Typer CLI entry point for the Virtual Parliament. Wave 2 wires full logic."""
from __future__ import annotations
import typer

DISCLAIMER = (
    "⚠️  EDUCATIONAL SIMULATION — This is not a political forecast, "
    "endorsement, or prediction of real parliamentary outcomes."
)

app = typer.Typer(add_completion=False, help="Virtual Parliament CLI")

@app.callback(invoke_without_command=True)
def _placeholder() -> None:  # pragma: no cover — replaced in Wave 2
    """Stub. Replaced by full command in Wave 2 Plan 04."""
    raise NotImplementedError("CLI command implemented in Phase 3 Plan 04")

"""Typer CLI entry point for the Virtual Parliament (Phase 3).

The app uses a single @app.command() so `parliament "<topic>"` dispatches
directly without a subcommand name. An @app.callback() is intentionally
omitted to avoid click group positional-argument parsing limitations — the
callback extension point is documented here for future multi-command use.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from parliament.session import (
    DISCLAIMER, run_session, run_minister_isolation, render_markdown, PARTY_SEATS,
)

app = typer.Typer(add_completion=False, help="Virtual Parliament — Polish Sejm simulation.")


def _db_path() -> Path:
    return Path(os.environ.get("PARLIAMENT_DB_PATH", "sessions.db"))


# NOTE: @app.callback() is intentionally not registered here.
# Adding @app.callback() to a single-command typer app creates a click Group,
# which makes positional arguments on the callback fail at parse time.
# This is a known click/typer architectural constraint (groups cannot have
# positional ARGUMENT parameters). The @app.callback pattern is reserved for
# when subcommands (e.g. `parliament session`, `parliament export`) are added.

@app.command()
def main(
    topic: str = typer.Argument(..., help="Bill topic to debate (or question if --minister)."),
    minister: Optional[str] = typer.Option(
        None, "--minister", "-m",
        help="Run a single ministry in isolation (e.g. --minister finanse).",
    ),
    export: Optional[str] = typer.Option(
        None, "--export",
        help="Export format. Currently supports: markdown.",
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Output file path for --export.",
    ),
) -> None:
    """Run a Virtual Parliament simulation on TOPIC."""
    console = Console()
    console.print(DISCLAIMER)
    console.print()

    if minister:
        result = run_minister_isolation(minister, topic, db_path=_db_path(), console=console)
        console.print(result.stdout)
    else:
        result = run_session(topic, db_path=_db_path(), console=console)
        console.print(result.stdout)
        # Print vote tally summary
        console.print()
        console.print("## Vote Tally")
        console.print("| Party | Vote | Seats |")
        console.print("|-------|------|-------|")
        for party, seats in PARTY_SEATS.items():
            v = result.votes.get(party, "—")
            console.print(f"| {party} | {v} | {seats} |")
        console.print(f"\n**Result:** {result.vote_result or 'N/A'}")

    if export == "markdown":
        md = render_markdown(result, topic)
        out_path = output or Path(f"parliament-{result.session_id or 'session'}.md")
        out_path.write_text(md, encoding="utf-8")
        console.print(f"\nExported to {out_path}")
    elif export is not None:
        raise typer.BadParameter(f"Unsupported export format: {export}. Use 'markdown'.")

    console.print()
    console.print(DISCLAIMER)

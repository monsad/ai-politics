"""Subprocess Hermes launcher + transcript parser + SQLite writer (Phase 3 core)."""
from __future__ import annotations

import os
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner

from parliament.agent_factory import build_hermes_cmd, build_hermes_env
from parliament.db import (
    DEFAULT_DB_PATH, init_db,
    insert_session, update_session,
    insert_utterance, insert_vote, insert_bill_draft,
)
from parliament.guards import TokenBudget, TokenBudgetExceeded


PARTY_SEATS = {"CR": 157, "NC": 194, "AC": 65, "Liberty Front": 18, "SD": 26}

PHASE_MARKERS = [
    ("[MARSZAŁEK REASONING]", "marszalek_reasoning"),
    ("## Ministry Analysis", "ministry_analysis"),
    ("## Party Debate — First Reading", "first_reading"),
    ("## Party Debate — Second Reading", "second_reading"),
    ("## Vote", "voting"),
    ("## Draft Bill", "bill_drafting"),
]

DOMAIN_TO_SKILL = {
    "finanse": "ministry-finansow",
    "finansow": "ministry-finansow",
    "zdrowia": "ministry-zdrowia",
    "edukacji": "ministry-edukacji",
    "edukacja": "ministry-edukacji",
    "sprawiedliwosci": "ministry-sprawiedliwosci",
    "klimatu": "ministry-klimatu-i-srodowiska",
    "energii": "ministry-energii",
    "infrastruktury": "ministry-infrastruktury",
    "obrony": "ministry-obrony-narodowej",
    "spraw-zagranicznych": "ministry-spraw-zagranicznych",
    "spraw-wewnetrznych": "ministry-spraw-wewnetrznych-i-administracji",
    "cyfryzacji": "ministry-cyfryzacji",
    "rolnictwa": "ministry-rolnictwa",
    "rodziny": "ministry-rodziny-pracy-i-polityki-spolecznej",
    "kultury": "ministry-kultury-i-dziedzictwa-narodowego",
    "nauki": "ministry-nauki-i-szkolnictwa-wyzszego",
    "aktywow": "ministry-aktywow-panstwowych",
    "funduszy": "ministry-funduszy-i-polityki-regionalnej",
    "rozwoju": "ministry-rozwoju-i-technologii",
    "sportu": "ministry-sportu-i-turystyki",
}

DISCLAIMER = (
    "⚠️  EDUCATIONAL SIMULATION — This is not a political forecast, "
    "endorsement, or prediction of real parliamentary outcomes."
)


@dataclass
class SessionResult:
    session_id: Optional[str]
    stdout: str
    stderr: str
    returncode: int
    vote_result: Optional[str] = None
    votes: dict = field(default_factory=dict)
    phases: list = field(default_factory=list)
    bill_draft: Optional[str] = None
    estimated_tokens: int = 0


# ------------------------------------------------------------------ parsing

def extract_hermes_session_id(stderr: str) -> Optional[str]:
    """Extract the session_id emitted by Hermes to stderr: `\nsession_id: <id>`."""
    m = re.search(r"session_id:\s*(\S+)", stderr)
    return m.group(1) if m else None


def parse_phases(text: str) -> list[dict]:
    """Segment the Hermes stdout blob into phase sections by marker offset."""
    sections: list[dict] = []
    for marker, phase_id in PHASE_MARKERS:
        idx = 0
        while (idx := text.find(marker, idx)) != -1:
            sections.append({"phase": phase_id, "marker": marker, "offset": idx})
            idx += len(marker)
    sections.sort(key=lambda x: x["offset"])
    # attach content slice = from this offset to the next section's offset
    for i, sec in enumerate(sections):
        end = sections[i + 1]["offset"] if i + 1 < len(sections) else len(text)
        sec["content"] = text[sec["offset"]:end]
    return sections


_VOTE_LINE = re.compile(
    r"^\|\s*(CR|NC|AC|Liberty Front|SD)\s*\|\s*(FOR|AGAINST|ABSTAIN)\s*\|",
    re.MULTILINE,
)


def parse_vote_table(text: str) -> tuple[dict[str, str], Optional[str]]:
    """Parse the markdown vote table, compute weighted seat tally → PASSED | REJECTED."""
    votes: dict[str, str] = {}
    for m in _VOTE_LINE.finditer(text):
        votes[m.group(1)] = m.group(2)
    if not votes:
        return votes, None
    total_for = sum(PARTY_SEATS[p] for p, v in votes.items() if v == "FOR")
    total_against = sum(PARTY_SEATS[p] for p, v in votes.items() if v == "AGAINST")
    result = "PASSED" if total_for > total_against else "REJECTED"
    return votes, result


def parse_bill_draft(text: str) -> Optional[str]:
    """Extract the bill draft section between `## Draft Bill` and closing disclaimer."""
    marker = "## Draft Bill"
    idx = text.find(marker)
    if idx == -1:
        return None
    # End at trailing disclaimer or end of text
    tail = text[idx + len(marker):]
    end_idx = tail.find("⚠️")
    body = tail[:end_idx] if end_idx != -1 else tail
    body = body.strip()
    return body or None


# ------------------------------------------------------------------ subprocess

def _spawn(cmd: list[str], env: dict[str, str], timeout: int) -> tuple[str, str, int]:
    """Launch subprocess, capture stdout+stderr in background threads."""
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        shell=False,  # SECURITY: never True; cmd is argv list from build_hermes_cmd
        env=env,
    )
    stdout_buf: list[str] = []
    stderr_buf: list[str] = []
    t_out = threading.Thread(target=lambda: stdout_buf.append(proc.stdout.read()), daemon=True)
    t_err = threading.Thread(target=lambda: stderr_buf.append(proc.stderr.read()), daemon=True)
    t_out.start()
    t_err.start()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    t_out.join(timeout=5)
    t_err.join(timeout=5)
    return "".join(stdout_buf), "".join(stderr_buf), proc.returncode or 0


def _phase_label_for_elapsed(elapsed: float) -> str:
    """Return a human-readable spinner label based on elapsed seconds."""
    if elapsed < 20:
        return "Classifying topic, selecting ministries..."
    if elapsed < 80:
        return "Consulting ministries (parallel via delegate_task)..."
    if elapsed < 180:
        return "Party debate — first reading..."
    if elapsed < 240:
        return "Party debate — second reading..."
    if elapsed < 280:
        return "Voting..."
    return "Drafting bill..."


def _run_with_spinner(
    cmd: list[str], env: dict[str, str], timeout: int,
    console: Optional[Console] = None,
) -> tuple[str, str, int]:
    """Run subprocess in a background thread, show rich.live spinner in main thread."""
    console = console or Console()
    result: dict = {}

    def _worker():
        result["out"], result["err"], result["rc"] = _spawn(cmd, env, timeout)

    worker = threading.Thread(target=_worker, daemon=True)
    start = time.monotonic()
    worker.start()
    with Live(
        Panel(Spinner("dots", text=_phase_label_for_elapsed(0)), title="Parliament"),
        console=console,
        refresh_per_second=4,
        transient=True,
    ) as live:
        while worker.is_alive():
            elapsed = time.monotonic() - start
            live.update(Panel(Spinner("dots", text=_phase_label_for_elapsed(elapsed)), title="Parliament"))
            time.sleep(0.25)
        worker.join(timeout=5)
    return result["out"], result["err"], result["rc"]


# ------------------------------------------------------------------ persistence

def _persist(db_path: Path | str, topic: str, sr: SessionResult) -> None:
    """Write all session data to SQLite after subprocess completes."""
    if sr.session_id is None:
        return
    init_db(db_path)
    insert_session(db_path, sr.session_id, topic)
    for seq, phase in enumerate(sr.phases, start=1):
        insert_utterance(
            db_path, sr.session_id, seq,
            speaker=phase["phase"].upper(),
            phase=phase["phase"],
            content=phase["content"][:32000],
            node_ids=[],
        )
    for party, vote in sr.votes.items():
        insert_vote(db_path, sr.session_id, party, vote, PARTY_SEATS[party])
    if sr.bill_draft:
        insert_bill_draft(db_path, sr.session_id, title=topic, content=sr.bill_draft)
    update_session(
        db_path, sr.session_id,
        status="complete" if sr.returncode == 0 else "error",
        vote_result=sr.vote_result,
        raw_output=sr.stdout,
        exit_code=sr.returncode,
    )


# ------------------------------------------------------------------ public API

def run_session(
    topic: str, *,
    db_path: Path | str | None = None,
    budget: TokenBudget | None = None,
    console: Optional[Console] = None,
) -> SessionResult:
    """Run a full parliament session via subprocess Hermes (marszalek-sejmu skill)."""
    cmd = build_hermes_cmd("marszalek-sejmu", topic, tier="orchestrator")
    env = build_hermes_env("orchestrator")
    stdout, stderr, rc = _run_with_spinner(cmd, env, timeout=360, console=console)

    sid = extract_hermes_session_id(stderr)
    phases = parse_phases(stdout)
    votes, vote_result = parse_vote_table(stdout)
    bill = parse_bill_draft(stdout)
    est_tokens = max(1, len(stdout) // 4)

    budget = budget or TokenBudget(int(os.environ.get("PARLIAMENT_TOKEN_CAP", "200000")))
    try:
        budget.add(est_tokens)
    except TokenBudgetExceeded:
        pass  # budget tracking is reporting-only here; session already ran

    result = SessionResult(
        session_id=sid, stdout=stdout, stderr=stderr, returncode=rc,
        vote_result=vote_result, votes=votes, phases=phases,
        bill_draft=bill, estimated_tokens=est_tokens,
    )
    if db_path is not None:
        _persist(db_path, topic, result)
    return result


def run_minister_isolation(
    domain: str, question: str, *,
    db_path: Path | str | None = None,
    budget: TokenBudget | None = None,
    console: Optional[Console] = None,
) -> SessionResult:
    """Run a single ministry skill in isolation via subprocess Hermes."""
    skill = DOMAIN_TO_SKILL.get(domain)
    if skill is None:
        raise ValueError(f"Unknown ministry domain: {domain!r}. Known: {sorted(DOMAIN_TO_SKILL)}")
    cmd = build_hermes_cmd(skill, question, tier="ministry")
    env = build_hermes_env("ministry")
    stdout, stderr, rc = _run_with_spinner(cmd, env, timeout=120, console=console)
    sid = extract_hermes_session_id(stderr)
    est_tokens = max(1, len(stdout) // 4)
    budget = budget or TokenBudget(int(os.environ.get("PARLIAMENT_TOKEN_CAP", "200000")))
    try:
        budget.add(est_tokens)
    except TokenBudgetExceeded:
        pass
    result = SessionResult(
        session_id=sid, stdout=stdout, stderr=stderr, returncode=rc,
        estimated_tokens=est_tokens,
    )
    if db_path is not None and sid:
        init_db(db_path)
        insert_session(db_path, sid, f"--minister {domain}: {question}")
        insert_utterance(db_path, sid, 1, speaker=skill.upper(), phase="ministry_analysis", content=stdout[:32000])
        update_session(db_path, sid, status="complete" if rc == 0 else "error", raw_output=stdout, exit_code=rc)
    return result


# ------------------------------------------------------------------ markdown export

def render_markdown(result: SessionResult, topic: str) -> str:
    """Render a full markdown export: disclaimer + transcript + vote tally + bill draft."""
    from datetime import datetime, timezone
    lines = [
        DISCLAIMER,
        "",
        f"# Virtual Parliament Session — {topic}",
        "",
        f"- **Session ID:** `{result.session_id or 'unknown'}`",
        f"- **Timestamp:** {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- **Vote result:** {result.vote_result or 'N/A'}",
        f"- **Estimated tokens:** {result.estimated_tokens}",
        "",
        "## Transcript",
        "",
        result.stdout.strip(),
        "",
        "## Vote Tally",
        "",
        "| Party | Vote | Seats |",
        "|-------|------|-------|",
    ]
    for party, seats in PARTY_SEATS.items():
        v = result.votes.get(party, "—")
        lines.append(f"| {party} | {v} | {seats} |")
    lines.extend(["", "## Draft Bill", "", result.bill_draft or "_No draft bill produced._", "", DISCLAIMER, ""])
    return "\n".join(lines)

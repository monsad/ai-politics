# Phase 3: Orchestrator & CLI — Research

**Researched:** 2026-05-27
**Domain:** Python subprocess orchestration, typer CLI, rich Live display, SQLite WAL, FastAPI SSE
**Confidence:** HIGH (all critical findings verified against live code/binaries)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01: CLI invocation pattern — subprocess Hermes**
- `parliament "<topic>"` is a Python typer CLI that launches Hermes as a subprocess
- Subprocess: `hermes chat -s marszalek-sejmu -q "<topic>" -Q`
- Hermes handles skill loading, MCP tool wiring, and ThreadPoolExecutor fan-out internally
- CLI entry point: `parliament = "parliament.cli:app"` in `pyproject.toml`

**D-02: Progress display — rich Live panel parsing Hermes stdout**
- CLI reads Hermes subprocess stdout line-by-line
- Phase markers from marszalek-sejmu SKILL.md update a `rich.live.Live` panel
- Simultaneously accumulate full stdout into buffer for SQLite write + markdown export

### Claude's Discretion (planner decides)
- SQLite schema detail — exact column set, line-by-line vs blob for utterances
- Citation validator timing — post-session is sufficient for Phase 3
- FastAPI SSE scope — single `GET /stream/{session_id}` emitting accumulated events from SQLite
- `--minister` isolation mode — subprocess Hermes with the ministry skill directly, or via marszalek
- Token budget wiring — proxy from output length, or parse hermes stderr if available

### Deferred Ideas (OUT OF SCOPE)
- PDF export (STR-02)
- Web UI reasoning side-panel (STR-03)
- Full SQLite query API — Phase 3 only needs write side + one SSE read endpoint
- Multi-session concurrency
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-04 | `agent_factory.py` creates AIAgent from any `skills/<id>/` folder with model-tier config | Hermes chat -s flag loads skill; subprocess pattern confirmed |
| INFRA-05 | SQLite schema: sessions, utterances, votes, bill_drafts tables with WAL mode | aiosqlite 0.20+ available; WAL mode = PRAGMA journal_mode=WAL |
| INFRA-06 | Token-budget kill switch wired into every LLM call path | TokenBudget stub in parliament/guards.py; proxy via output char count in subprocess mode |
| ORCH-01 | One marszalek-sejmu skill is the only agent allowed to call delegate_task | SKILL.md confirmed; subprocess pattern enforces this |
| ORCH-02 | Ministry selection: Marszałek classifies topic, picks 2–3 ministries, deterministic | Topic→ministry table in SKILL.md; classification via LLM prompt |
| ORCH-03 | Ministry consultation via delegate_task, 3 parallel, ≤30s wall-clock | Hermes ThreadPoolExecutor fan-out; confirmed in GATE-03 smoke test |
| ORCH-04 | First reading: 5 parties speak once, sequentially, each cites ≥1 PageIndex node | Defined in marszalek SKILL.md Session Phases |
| ORCH-05 | Second reading: parties may amend; ≥1 cross-reference per turn | Defined in marszalek SKILL.md Session Phases |
| ORCH-06 | Vote tally: FOR/AGAINST/ABSTAIN weighted by seat count, markdown table | Vote formula in SKILL.md; parse from response text |
| ORCH-07 | Draft bill using bill-draft-template.md after vote | Template confirmed at skills/marszalek-sejmu/assets/bill-draft-template.md |
| ORCH-08 | [MARSZAŁEK REASONING] blocks appear at every routing/selection decision | Confirmed in SKILL.md protocol; CLI parses these markers |
| ORCH-09 | Vote-direction sanity guardrail; re-deliberation on incoherent outcomes | Coherence guardrail section in SKILL.md |
| CLI-01 | `parliament "<topic>"` runs full session ≤5 min | hermes chat -Q subprocess; timing depends on model choice |
| CLI-02 | `parliament --minister <domain> "<question>"` runs single ministry in isolation | subprocess hermes chat -s ministry-<id> -q "<question>" -Q |
| CLI-03 | `parliament ... --export markdown <file>` writes transcript to disk | Buffer accumulated stdout + write with header |
| CLI-04 | rich progress bar shows phase labels with parallelism count | rich.live.Live + rich.panel.Panel + rich.progress.Progress |
| CLI-05 | First run from clean clone: `pip install -e . && parliament "test"` succeeds ≤2 min | Entry point must be registered as `parliament` not `hermes-parliament` |
| EXPORT-01 | Markdown transcript with session header, utterances, vote table, draft bill section | Post-processing accumulated stdout |
| ETHICS-01 | Educational disclaimer at top and bottom of every CLI output surface | Print before launching subprocess, parse disclaimer from response |
</phase_requirements>

---

## Summary

Phase 3 wires the existing agent skills and infrastructure into a single `parliament "<topic>"` command. The architecture is a Python typer CLI (`parliament/cli.py`) that launches Hermes as a subprocess, reads its output, writes to SQLite, and exposes a FastAPI SSE endpoint for Phase 4 consumption.

**Critical architectural correction:** The CONTEXT.md D-02 description of "reading Hermes stdout line-by-line in real time" is based on an incorrect assumption about Hermes output streaming. Hermes in `-Q` (quiet) mode buffers all output and emits a single blob when the agent run completes. There is no incremental stdout. The correct display strategy is: show a `rich` spinner with a static phase label while Hermes runs (indeterminate), then parse phase markers from the completed response for the final transcript display.

The subprocess invocation is `hermes chat -s marszalek-sejmu -q "<topic>" -Q`. The `-Q` flag produces: final response text → stdout, `\nsession_id: <id>` → stderr. The `--accept-hooks` flag must be set (or `HERMES_ACCEPT_HOOKS=1` env var) to prevent interactive prompts hanging the subprocess.

**Primary recommendation:** Use `hermes chat -s <skill> -q "<prompt>" -Q --accept-hooks` as the subprocess command. Wrap with `threading.Thread` reading stdout into a buffer, show a `rich.live.Live` spinner in the main thread, parse buffer on completion.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| typer | 0.25.1 (pinned in pyproject.toml) | Python CLI framework | Already pinned; decorator-based, type-hinted |
| rich | 14.3.3 (installed) | Terminal UI: Live panels, spinners, tables | Already installed; used for progress display |
| aiosqlite | ≥0.20 (pinned in pyproject.toml) | Async SQLite for session storage | Already pinned; used by FastAPI SSE endpoint |
| fastapi | 0.128.8 (installed) | Async web framework for SSE endpoint | Already installed; required by INFRA-05 |
| uvicorn | 0.40.0 (installed) | ASGI server for FastAPI | Already installed; `uvicorn parliament.api:app` |
| sse-starlette | 3.0.2 (installed) | `EventSourceResponse` for SSE | Installed; cleaner SSE than raw `StreamingResponse` |

[VERIFIED: pip show commands on local environment, 2026-05-27]

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| subprocess (stdlib) | Python 3.11 | Launch hermes as subprocess | `asyncio.create_subprocess_exec` or `subprocess.Popen` |
| threading (stdlib) | Python 3.11 | Background stdout reader thread | Reading subprocess stdout while main thread shows spinner |
| sqlite3 (stdlib) | Python 3.11 | Synchronous SQLite for synchronous path | Schema creation; WAL PRAGMA setup |
| asyncio (stdlib) | Python 3.11 | Async coordinator for FastAPI | SSE generator pattern |

### Entry Point Correction
**CRITICAL:** `pyproject.toml` currently registers `hermes-parliament = "parliament.cli:app"`. The locked CLI surface is `parliament "<topic>"`. Phase 3 Wave 0 must fix this:

```toml
[project.scripts]
parliament = "parliament.cli:app"
```

[VERIFIED: grep on /Users/xpll081/ai-politics/pyproject.toml]

### Installation
```bash
# All dependencies already in pyproject.toml
pip install -e ".[dev]"
# sse-starlette must be added to pyproject.toml (already installed but not in deps)
```

---

## Architecture Patterns

### Recommended Project Structure
```
parliament/
├── cli.py          # typer app: parliament "<topic>", --minister, --export
├── session.py      # subprocess launcher, stdout reader, phase marker parser
├── db.py           # SQLite schema init, WAL mode, aiosqlite helpers
├── api.py          # FastAPI app: GET /stream/{session_id} SSE endpoint
├── citation_validator.py  # post-session node_id verification
├── guards.py       # existing TokenBudget (wire in Phase 3)
├── doc_registry.py # existing domain filter (used by citation_validator)
└── second_brain/
    └── pageindex_client.py  # existing async MCP client (used by citation_validator)
```

### Pattern 1: Hermes Subprocess Invocation (VERIFIED)

The confirmed working command for loading a skill and running a single query is:

```python
# Source: verified against /Users/xpll081/.pyenv/versions/3.11.9/lib/python3.11/site-packages/cli.py lines 14072-14133
cmd = [
    "hermes", "chat",
    "-s", "marszalek-sejmu",     # --skills: preloads SKILL.md into system prompt
    "-q", topic,                  # --query: non-interactive single query
    "-Q",                         # --quiet: stdout=response only, stderr=session_id
    "--accept-hooks",             # suppress interactive approval prompts
    "--yolo",                     # bypass dangerous command approval (needed for subagents)
]
env = {**os.environ, "HERMES_YOLO_MODE": "1", "HERMES_ACCEPT_HOOKS": "1"}
```

Output contract (VERIFIED):
- `stdout`: Final response text only (no banner, no spinner, no tool previews)
- `stderr`: `\nsession_id: <id>` at the very end — parseable for SQLite linkage
- Exit code: 0 on success, 1 on failure

**No incremental stdout streaming.** All output arrives as one blob when hermes finishes.

### Pattern 2: Subprocess Launcher with rich Live Spinner

```python
# Source: [ASSUMED] — standard Python threading + rich pattern
import subprocess
import threading
from rich.live import Live
from rich.spinner import Spinner
from rich.panel import Panel

def run_session(topic: str) -> dict:
    """Launch hermes subprocess, show spinner, return parsed session dict."""
    cmd = ["hermes", "chat", "-s", "marszalek-sejmu", "-q", topic, "-Q", "--accept-hooks"]
    result = {"stdout": "", "stderr": "", "returncode": None}
    
    with Live(Panel(Spinner("dots", text="Consulting ministries..."), title="Parliament"), 
              refresh_per_second=4) as live:
        proc = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "HERMES_YOLO_MODE": "1", "HERMES_ACCEPT_HOOKS": "1"},
        )
        
        def _read_stdout():
            result["stdout"] = proc.stdout.read()
        
        def _read_stderr():
            result["stderr"] = proc.stderr.read()
        
        t_out = threading.Thread(target=_read_stdout, daemon=True)
        t_err = threading.Thread(target=_read_stderr, daemon=True)
        t_out.start()
        t_err.start()
        
        # Update spinner label based on estimated elapsed time
        # (Hermes does not stream; we can't parse real-time markers)
        while proc.poll() is None:
            elapsed = time.monotonic() - start
            label = _estimate_phase_label(elapsed)
            live.update(Panel(Spinner("dots", text=label)))
            time.sleep(0.25)
        
        t_out.join(); t_err.join()
    
    result["returncode"] = proc.returncode
    return result
```

**Thread-safety note:** `rich.live.Live.update()` acquires an internal lock and is safe to call from any thread. [VERIFIED: rich 14.3.3 source inspection]

### Pattern 3: Phase Marker Parsing (Post-Completion)

Since Hermes does not stream, phase markers are parsed from the completed response:

```python
# Source: [ASSUMED] — regex pattern against SKILL.md section headers
PHASE_MARKERS = {
    "[MARSZAŁEK REASONING]": "topic_classification",
    "## Ministry Analysis": "ministry_analysis",
    "## Party Debate — First Reading": "first_reading",
    "## Party Debate — Second Reading": "second_reading",
    "## Vote": "voting",
    "## Draft Bill": "bill_drafting",
}

def parse_phases(response_text: str) -> list[dict]:
    """Extract phase sections from marszalek-sejmu output."""
    sections = []
    for marker, phase_id in PHASE_MARKERS.items():
        if marker in response_text:
            idx = response_text.index(marker)
            sections.append({"phase": phase_id, "offset": idx})
    return sorted(sections, key=lambda x: x["offset"])
```

### Pattern 4: SQLite Schema with WAL Mode

```python
# Source: [ASSUMED] — standard SQLite/aiosqlite pattern; WAL is a single PRAGMA
SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,           -- hermes session_id from stderr
    topic       TEXT NOT NULL,
    started_at  TEXT NOT NULL,              -- ISO-8601
    finished_at TEXT,
    status      TEXT DEFAULT 'running',     -- running | complete | error
    raw_output  TEXT,                       -- full hermes stdout blob
    vote_result TEXT,                       -- PASSED | REJECTED
    exit_code   INTEGER
);

CREATE TABLE IF NOT EXISTS utterances (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(id),
    seq         INTEGER NOT NULL,           -- ordering within session
    speaker     TEXT NOT NULL,              -- e.g. "KO", "MINISTRY_FINANSOW", "MARSZAŁEK"
    phase       TEXT NOT NULL,              -- ministry_analysis | first_reading | etc.
    content     TEXT NOT NULL,
    node_ids    TEXT,                       -- JSON array of cited node_ids
    UNIQUE(session_id, seq)
);

CREATE TABLE IF NOT EXISTS votes (
    session_id  TEXT NOT NULL REFERENCES sessions(id),
    party       TEXT NOT NULL,              -- KO | PiS | TD | Konfederacja | Lewica
    vote        TEXT NOT NULL,              -- FOR | AGAINST | ABSTAIN
    seats       INTEGER NOT NULL,
    PRIMARY KEY (session_id, party)
);

CREATE TABLE IF NOT EXISTS bill_drafts (
    session_id  TEXT PRIMARY KEY REFERENCES sessions(id),
    title       TEXT,
    content     TEXT NOT NULL,             -- full bill draft markdown
    created_at  TEXT NOT NULL
);
"""
```

WAL mode enables concurrent reads while a single writer is active — required for Phase 4 SSE reading while CLI is writing. [VERIFIED: SQLite WAL documentation; single PRAGMA call]

### Pattern 5: FastAPI SSE Endpoint

```python
# Source: sse-starlette 3.0.2 EventSourceResponse pattern [ASSUMED — training data + version verified]
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
import aiosqlite, json, asyncio

app = FastAPI()

@app.get("/stream/{session_id}")
async def stream_session(session_id: str):
    async def event_generator():
        async with aiosqlite.connect("sessions.db") as db:
            # Emit existing utterances first
            async with db.execute(
                "SELECT seq, speaker, phase, content FROM utterances "
                "WHERE session_id=? ORDER BY seq", [session_id]
            ) as cur:
                async for row in cur:
                    yield {
                        "event": "utterance",
                        "data": json.dumps({
                            "seq": row[0], "speaker": row[1],
                            "phase": row[2], "content": row[3]
                        })
                    }
            # Emit session status
            async with db.execute(
                "SELECT status, vote_result FROM sessions WHERE id=?", [session_id]
            ) as cur:
                row = await cur.fetchone()
                if row:
                    yield {"event": "status", "data": json.dumps({"status": row[0], "vote": row[1]})}
    
    return EventSourceResponse(event_generator())
```

### Pattern 6: Ministry Isolation Mode (CLI-02)

```python
# --minister flag: subprocess hermes with the ministry skill directly
# Source: [ASSUMED] — same pattern as main session
cmd = [
    "hermes", "chat",
    "-s", f"ministry-{domain}",    # e.g. ministry-finansow
    "-q", question,
    "-Q", "--accept-hooks",
]
```

The ministry skill's output format (4 sections: legal/budget/risks/recommendation) is already defined in MIN-02. No Marszałek routing required.

### Pattern 7: Token Budget Wiring (INFRA-06)

Hermes in subprocess mode does not expose token usage to the parent process. Two options:

1. **Character-count proxy**: 1 token ≈ 4 chars. `estimated_tokens = len(response_text) // 4`. Call `budget.add(estimated_tokens)` after subprocess completes.
2. **stderr session_id**: Parse hermes `session_id` from stderr, then query `~/.hermes/state.db` (Hermes SQLite session store) for actual usage. [ASSUMED — hermes internal DB schema may differ]

**Recommendation:** Use character-count proxy for Phase 3. It is deterministic, requires no internal hermes API knowledge, and is sufficient for the "kill switch" purpose.

```python
# Source: parliament/guards.py interface (existing)
from parliament.guards import TokenBudget, TokenBudgetExceeded

budget = TokenBudget(max_tokens=int(os.getenv("PARLIAMENT_TOKEN_CAP", "200000")))

def account_for_response(response_text: str) -> None:
    estimated = max(1, len(response_text) // 4)
    budget.add(estimated)  # raises TokenBudgetExceeded if cap exceeded
```

### Anti-Patterns to Avoid

- **`asyncio.gather` over AIAgent instances**: Documented deadlock in CLAUDE.md. Hermes handles parallelism internally via ThreadPoolExecutor.
- **`hermes -z <prompt>` without `--skills`**: The `run_oneshot()` function (called by `-z`) does NOT accept a `--skills` argument at the Python level — the top-level parser parses `--skills` but `run_oneshot` signature has no `skills` parameter. Skills would not be loaded. [VERIFIED: hermes_cli/main.py lines 12355-12365, oneshot.py lines 124-128]
- **Assuming Hermes streams stdout incrementally**: In `-Q` mode, `stream_delta_callback` is explicitly set to `None`. All output arrives as one blob at process exit. [VERIFIED: cli.py lines 14099-14102]
- **Registering entry point as `hermes-parliament`**: Current `pyproject.toml` uses `hermes-parliament`. The CLI surface requirement is `parliament "<topic>"`. Must fix to `parliament = "parliament.cli:app"`.
- **Storing utterances as line-by-line from subprocess**: Hermes outputs structured markdown, not one-utterance-per-line. Parse sections after full response arrives.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE event stream | Custom `StreamingResponse` with manual `text/event-stream` formatting | `sse_starlette.sse.EventSourceResponse` | Handles reconnect, event ID, proper content-type, buffering |
| CLI argument parsing | `argparse` / `click` | `typer` (already pinned) | Type-hinted, auto-docs, callback-based |
| subprocess stdout streaming | Custom pipe reader | `subprocess.Popen` + `threading.Thread` + `proc.stdout.read()` | Standard; `communicate()` buffers OK for Hermes single-blob output |
| SQLite concurrent access | Connection pooling | WAL mode + single writer, multiple readers via `aiosqlite` | WAL is SQLite's built-in solution; no extra library |
| Markdown export | Custom renderer | String formatting from accumulated response | The response IS markdown; just add a header section |
| Token estimation | Complex tokenizer | `len(text) // 4` character proxy | Sufficient for kill-switch semantics; no extra dependency |

---

## Common Pitfalls

### Pitfall 1: Hermes Subprocess Hangs Waiting for TTY Input
**What goes wrong:** Hermes prompts user to approve a shell hook or dangerous command. Since the subprocess has no TTY, it hangs indefinitely.
**Why it happens:** Some tools in Hermes require approval. Without `--accept-hooks` and `--yolo`, Hermes tries to write to the terminal.
**How to avoid:** Always pass `--accept-hooks` and `--yolo` in the subprocess command, and set `HERMES_YOLO_MODE=1` and `HERMES_ACCEPT_HOOKS=1` in the subprocess env.
**Warning signs:** Subprocess does not terminate after expected timeout; `proc.poll()` returns `None` indefinitely.

### Pitfall 2: Skills Not Loaded in `-z` Oneshot Mode
**What goes wrong:** `hermes -z "<topic>" --skills marszalek-sejmu` does NOT load the marszalek skill.
**Why it happens:** `run_oneshot()` function signature has no `skills` parameter. The `--skills` argument is parsed by top-level argparse but never forwarded to `run_oneshot()`. [VERIFIED: hermes_cli/main.py lines 12355-12365]
**How to avoid:** Use `hermes chat -s marszalek-sejmu -q "<topic>" -Q` (chat subcommand) — this is the correct path for skill-preloaded single queries.
**Warning signs:** Response lacks `[MARSZAŁEK REASONING]` blocks; ministry consultation does not happen.

### Pitfall 3: Entry Point Name Mismatch
**What goes wrong:** `parliament "4-day work week"` fails with "command not found".
**Why it happens:** `pyproject.toml` currently registers `hermes-parliament`, not `parliament`.
**How to avoid:** Change `[project.scripts]` to `parliament = "parliament.cli:app"` and run `pip install -e .` to update the entrypoint.
**Warning signs:** `which parliament` returns nothing; `which hermes-parliament` returns a path.

### Pitfall 4: Session ID Not Captured for SQLite Linkage
**What goes wrong:** Cannot link hermes session to Parliament SQLite session.
**Why it happens:** Hermes writes `\nsession_id: <id>` to **stderr**, not stdout. If stderr is not captured, the ID is lost.
**How to avoid:** Set `stderr=subprocess.PIPE` in `subprocess.Popen`; after run, parse `\nsession_id: ` from stderr.
**Warning signs:** session_id column in SQLite is always NULL.

### Pitfall 5: aiosqlite Not Available / pyproject.toml Missing sse-starlette
**What goes wrong:** `import aiosqlite` fails; `from sse_starlette.sse import EventSourceResponse` fails.
**Why it happens:** `aiosqlite` was pinned with `>=0.20` but the current environment may not have it installed (it's not in the installed env per `pip show aiosqlite` returning "not installed"). `sse-starlette` is installed but not in `pyproject.toml` dependencies.
**How to avoid:** Wave 0 must install both. Add `sse-starlette>=3.0` to `pyproject.toml` dependencies.
**Warning signs:** ImportError on `api.py` or `db.py` at startup.

### Pitfall 6: Hermes stdout Assumed to Stream Incrementally
**What goes wrong:** Code tries to read and parse hermes stdout line-by-line during execution. Nothing arrives until process exits, so the rich Live panel never updates.
**Why it happens:** In `-Q` mode, Hermes redirects stdout to devnull during agent execution and writes the full response only at the end. `stream_delta_callback = None` is explicitly set.
**How to avoid:** Use a background `threading.Thread` to call `proc.stdout.read()` (blocking). Show an indeterminate spinner in the main thread. Parse phase markers from the completed response.
**Warning signs:** Progress display shows nothing until hermes exits, then jumps directly to "complete".

### Pitfall 7: SQLite WAL Mode Not Initialized Before Concurrent Access
**What goes wrong:** Phase 4 SSE reader and CLI writer deadlock or produce "database is locked" errors.
**Why it happens:** SQLite default journal mode is DELETE (not WAL). WAL must be set before first concurrent read/write.
**How to avoid:** Run `PRAGMA journal_mode=WAL;` in the schema initialization step, before any session rows are created.
**Warning signs:** `sqlite3.OperationalError: database is locked` in FastAPI endpoint.

---

## Code Examples

### Subprocess Invocation (Full Pattern)
```python
# Source: verified against hermes_cli/main.py + cli.py + oneshot.py internals [VERIFIED]
import os, subprocess, threading, time

DISCLAIMER = (
    "⚠️  EDUCATIONAL SIMULATION — This is not a political forecast, "
    "endorsement, or prediction of real parliamentary outcomes.\n"
)

def _run_hermes(skill: str, prompt: str, timeout: int = 360) -> tuple[str, str, int]:
    """
    Launch hermes chat subprocess with skill preloaded.
    Returns (stdout, stderr, returncode).
    
    stdout = full hermes response (response text only, no banner)
    stderr = "\nsession_id: <hermes_session_id>"
    """
    cmd = [
        "hermes", "chat",
        "-s", skill,
        "-q", prompt,
        "-Q",               # quiet: stdout=response, stderr=session_id
        "--accept-hooks",   # suppress hook approval prompts
        "--yolo",           # suppress dangerous command approval
    ]
    env = {
        **os.environ,
        "HERMES_YOLO_MODE": "1",
        "HERMES_ACCEPT_HOOKS": "1",
    }
    
    stdout_buf, stderr_buf = [], []
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=env,
    )
    
    def _read(pipe, buf):
        buf.append(pipe.read())
    
    t_out = threading.Thread(target=_read, args=(proc.stdout, stdout_buf), daemon=True)
    t_err = threading.Thread(target=_read, args=(proc.stderr, stderr_buf), daemon=True)
    t_out.start(); t_err.start()
    
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
    
    t_out.join(timeout=5); t_err.join(timeout=5)
    return "".join(stdout_buf), "".join(stderr_buf), proc.returncode or 0
```

### SQLite Initialization (Synchronous, called once at startup)
```python
# Source: [ASSUMED] — standard sqlite3 + aiosqlite pattern
import sqlite3

def init_db(db_path: str) -> None:
    """Create schema and enable WAL mode. Idempotent."""
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_SQL)  # SCHEMA_SQL defined in Pattern 4 above
    con.commit()
    con.close()
```

### Session ID Extraction from Stderr
```python
# Source: verified against cli.py line 14129 which prints "\nsession_id: {cli.session_id}" to stderr
import re

def extract_hermes_session_id(stderr: str) -> str | None:
    m = re.search(r"session_id:\s*(\S+)", stderr)
    return m.group(1) if m else None
```

### Typer CLI Skeleton
```python
# Source: [ASSUMED] — typer 0.25.1 pattern
import typer
from typing import Optional

app = typer.Typer()

@app.command()
def main(
    topic: str = typer.Argument(..., help="Bill topic to debate"),
    minister: Optional[str] = typer.Option(None, "--minister", help="Run a single ministry in isolation"),
    export: Optional[str] = typer.Option(None, "--export", help="Export format: markdown"),
    output: Optional[str] = typer.Argument(None, help="Output file path for --export"),
):
    """Virtual Parliament — Run a Polish parliamentary simulation."""
    typer.echo(DISCLAIMER)
    if minister:
        _run_minister_isolation(minister, topic)
    else:
        _run_full_session(topic, export=export, output_path=output)
```

### Vote Table Parsing
```python
# Source: [ASSUMED] — regex against SKILL.md vote table format
import re

PARTIES = {"KO": 157, "PiS": 194, "TD": 65, "Konfederacja": 18, "Lewica": 26}

def parse_vote_table(response_text: str) -> dict[str, str]:
    """Extract party votes from marszalek-sejmu vote table markdown."""
    votes = {}
    # Matches: | KO | FOR | 157 |
    pattern = re.compile(
        r"^\|\s*(KO|PiS|TD|Konfederacja|Lewica)\s*\|\s*(FOR|AGAINST|ABSTAIN)\s*\|",
        re.MULTILINE,
    )
    for m in pattern.finditer(response_text):
        votes[m.group(1)] = m.group(2)
    return votes
```

---

## Runtime State Inventory

Phase 3 is a greenfield implementation phase (new files: cli.py, session.py, db.py, api.py, citation_validator.py). No rename or migration work.

**Stored data:** None yet — sessions.db created fresh by Phase 3. [VERIFIED: no sessions/ directory exists]
**Live service config:** None new in Phase 3. PageIndex Cloud and Hermes config established in Phases 1–2.
**OS-registered state:** None. CLI is installed via `pip install -e .` entry point, not OS registration.
**Secrets/env vars:** `PARLIAMENT_TOKEN_CAP` — new optional env var for token budget cap (default: 200000). `PARLIAMENT_DB_PATH` — new optional env var for SQLite path (default: `./sessions.db`).
**Build artifacts:** `parliament.egg-info/` will be stale if `pyproject.toml` scripts section changes. Run `pip install -e .` after changing entry point name.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| hermes CLI | CLI-01 (subprocess) | ✓ | 0.14.0 (at /Users/xpll081/.pyenv/shims/hermes) | None — core dep |
| typer | CLI skeleton | ✓ (0.23.0 installed, 0.25.1 pinned) | 0.23.0 / 0.25.1 | Minor version; install pinned version |
| rich | Progress display | ✓ | 14.3.3 | None — core dep |
| fastapi | API endpoint | ✓ | 0.128.8 | None — core dep |
| uvicorn | ASGI server | ✓ | 0.40.0 | None — core dep |
| sse-starlette | SSE response | ✓ | 3.0.2 | Raw StreamingResponse (more code) |
| aiosqlite | Async SQLite | NOT INSTALLED | — | Use sqlite3 synchronously (Phase 3 is single-session) |
| sqlite3 | Schema init | ✓ (stdlib) | Python 3.11 built-in | N/A |

**Missing dependencies with no fallback:**
- `aiosqlite` is required by INFRA-05 and SSE pattern. Must be installed.

**Missing dependencies with fallback:**
- `sse-starlette` is installed but not in `pyproject.toml`. Add it. Fallback: raw `StreamingResponse`.

**Action items for Wave 0:**
1. Add `sse-starlette>=3.0` to `pyproject.toml` dependencies
2. Add `aiosqlite>=0.20` is already in `pyproject.toml` — run `pip install -e .` to actually install it
3. Fix entry point: `parliament = "parliament.cli:app"` (not `hermes-parliament`)
4. Run `pip install -e .` to refresh entry point registration

[VERIFIED: pip show commands on local environment, 2026-05-27]

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 + pytest-asyncio 0.24.0 |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` with `asyncio_mode = "auto"` |
| Quick run command | `pytest tests/test_phase3_acceptance.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| INFRA-05 | SQLite schema creates tables with WAL | unit | `pytest tests/test_phase3_acceptance.py::test_db_schema -x` | ❌ Wave 0 |
| INFRA-06 | TokenBudget wired: raises on cap exceeded | unit | `pytest tests/test_token_budget.py -x` | ✅ (existing) |
| CLI-01 | Full session completes ≤5 min, vote present | integration | `pytest tests/test_phase3_acceptance.py::test_full_session -x --timeout=360` | ❌ Wave 0 |
| CLI-02 | `--minister finanse` returns structured output <60s | integration | `pytest tests/test_phase3_acceptance.py::test_minister_isolation -x` | ❌ Wave 0 |
| CLI-03 | `--export markdown` writes readable file | integration | `pytest tests/test_phase3_acceptance.py::test_markdown_export -x` | ❌ Wave 0 |
| CLI-04 | Rich progress labels appear (captured via subprocess) | smoke | `pytest tests/test_phase3_acceptance.py::test_cli_smoke -x` | ❌ Wave 0 |
| CLI-05 | Entry point `parliament` resolves | unit | `pytest tests/test_phase3_acceptance.py::test_entry_point -x` | ❌ Wave 0 |
| ORCH-08 | `[MARSZAŁEK REASONING]` blocks in transcript | integration | `pytest tests/test_phase3_acceptance.py::test_reasoning_blocks -x` | ❌ Wave 0 |
| ORCH-09 | Citation validator reports 0 unresolvable | integration | `pytest tests/test_phase3_acceptance.py::test_citation_validator -x` | ❌ Wave 0 |
| ETHICS-01 | Disclaimer at top and bottom of every output | unit | `pytest tests/test_phase3_acceptance.py::test_disclaimer -x` | ❌ Wave 0 |
| EXPORT-01 | Markdown export has all required sections | unit | `pytest tests/test_phase3_acceptance.py::test_export_sections -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_token_budget.py tests/test_phase3_acceptance.py -x -q -k "not test_full_session and not test_minister_isolation"` (fast unit tests only)
- **Per wave merge:** `pytest tests/test_phase3_acceptance.py -x -q` (all Phase 3 acceptance tests)
- **Phase gate:** `pytest tests/ -q` (full suite green before `/gsd-verify-work`)

### Wave 0 Gaps
- [ ] `tests/test_phase3_acceptance.py` — covers all Phase 3 REQ-IDs above
- [ ] `parliament/cli.py` — typer app skeleton (even empty functions) needed for import tests
- [ ] `parliament/db.py` — schema creation needed for db unit tests
- [ ] Install: `pip install -e .` after pyproject.toml entry point fix

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | CLI tool, no auth layer |
| V3 Session Management | No | Sessions are local SQLite, no web auth |
| V4 Access Control | No | Single-user local tool |
| V5 Input Validation | Yes | Sanitize topic/ministry args before subprocess shell construction |
| V6 Cryptography | No | No secrets in Phase 3 code |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Shell injection via topic string | Tampering | Use `subprocess.Popen(cmd_list, shell=False)` — never `shell=True`; `cmd` is always a list. |
| Path traversal in `--export <file>` | Tampering | Validate output path is writable and within expected directory |
| SQLite injection in session queries | Tampering | Use parameterized queries with `?` placeholders throughout `db.py` |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Character-count proxy (len//4) is sufficient for token budget | Pattern 7 | Budget may be significantly over/underestimated; could abort sessions early or allow runaway spend |
| A2 | `hermes chat -s <skill> -q <prompt> -Q --accept-hooks --yolo` does not require TTY and works in subprocess | Pattern 1 | Subprocess may hang or produce different output format; would need to use `hermes -z` path instead (but skills won't load there) |
| A3 | Estimated phase labels (time-based) are an acceptable substitute for real-time phase streaming for Phase 3 | Pattern 2 | Jury may penalize poor UX on progress display; real-time markers might be achievable via a different approach |
| A4 | `sse-starlette 3.0.2` `EventSourceResponse` accepts an async generator directly | Pattern 5 | API may differ from 2.x; verify against 3.0.2 docs |
| A5 | Hermes `--yolo` in subprocess does not cause unintended side effects (file writes, shell commands) in the marszalek-sejmu skill | Pattern 1 | Marszalek skill may try to write files; `--yolo` bypasses approval. Accept this risk for contest context. |

---

## Open Questions

1. **Real-time streaming vs post-completion display**
   - What we know: Hermes `-Q` mode does not stream; all output arrives at process exit
   - What's unclear: Whether a time-based phase label (e.g., "Consulting ministries" at 0–30s, "Party debate" at 30–120s) is acceptable UX for the demo vs no live updates
   - Recommendation: Use time-based spinner labels for Phase 3; acceptable for contest jury

2. **Ministry isolation skill path**
   - What we know: `hermes chat -s ministry-finansow -q "<question>" -Q` is the candidate command
   - What's unclear: Whether ministry skills produce structured 4-section output without the Marszałek wrapper (they should per MIN-02, but untested in isolation)
   - Recommendation: Test one ministry in isolation as Wave 0 task; adjust prompt if output format differs

3. **`aiosqlite` not installed**
   - What we know: It's in `pyproject.toml` but `pip show aiosqlite` returns "not installed" — the project hasn't been installed in the active venv
   - What's unclear: Whether the Phase 1/2 tests ran in a different venv
   - Recommendation: Wave 0 task: `pip install -e ".[dev]"` from the project root to ensure full install

---

## Sources

### Primary (HIGH confidence)
- `/Users/xpll081/.pyenv/versions/3.11.9/lib/python3.11/site-packages/hermes_cli/main.py` — lines 12353-12365 (oneshot path + skills not passed to run_oneshot), lines 14072-14133 (quiet chat path, session_id to stderr)
- `/Users/xpll081/.pyenv/versions/3.11.9/lib/python3.11/site-packages/hermes_cli/oneshot.py` — lines 124-128 (run_oneshot signature, no skills param), lines 175-199 (stdout capture, single blob output)
- `/Users/xpll081/.pyenv/versions/3.11.9/lib/python3.11/site-packages/cli.py` — lines 14099-14103 (quiet mode disables streaming callbacks)
- `hermes --help` + `hermes chat --help` — confirmed `-s/--skills`, `-q/--query`, `-Q/--quiet`, `--accept-hooks`, `--yolo` flags
- `/Users/xpll081/ai-politics/pyproject.toml` — entry point name, installed dependencies
- `/Users/xpll081/ai-politics/parliament/guards.py` — TokenBudget interface (Phase 3 wires this)
- `/Users/xpll081/ai-politics/skills/marszalek-sejmu/SKILL.md` — phase markers, session output format
- `pip show fastapi uvicorn sse-starlette rich typer` — installed versions

### Secondary (MEDIUM confidence)
- sse-starlette 3.0.2 installed; `EventSourceResponse` import confirmed working locally
- Rich `Live.__init__` signature verified via Python help(); thread safety via lock inspection

### Tertiary (LOW confidence)
- Assumptions A1–A5 in Assumptions Log: subprocess behavior, time-based phase labels, aiosqlite availability, EventSourceResponse 3.x API

---

## Metadata

**Confidence breakdown:**
- Hermes CLI flags: HIGH — verified by reading source and running `--help`
- Hermes output streaming behavior: HIGH — verified by reading oneshot.py and cli.py source
- Standard stack versions: HIGH — verified by pip show
- Architecture patterns: MEDIUM — subprocess + threading pattern is standard Python; exact behavior under contest conditions is assumed
- Pitfalls: HIGH — grounded in source code inspection, not speculation

**Research date:** 2026-05-27
**Valid until:** 2026-05-31 (contest deadline — no updates needed)

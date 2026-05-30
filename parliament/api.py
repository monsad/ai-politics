"""FastAPI app: health, session lifecycle, SSE transcript stream, optional static UI."""
from __future__ import annotations

import asyncio
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from parliament import db as pdb

app = FastAPI(title="Virtual Parliament API")

_cors_origins = os.environ.get("PARLIAMENT_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _db_path() -> Path:
    return Path(os.environ.get("PARLIAMENT_DB_PATH", "sessions.db"))

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _new_session_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{secrets.token_hex(3)}"

class CreateSessionRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)

class CreateSessionResponse(BaseModel):
    session_id: str

@app.on_event("startup")
async def _ensure_schema() -> None:
    pdb.init_db(_db_path())

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/last-error")
def last_error() -> dict:
    """Return the most recent failed session's raw_output for debugging."""
    import sqlite3
    con = sqlite3.connect(str(_db_path()))
    try:
        row = con.execute(
            "SELECT id, topic, status, raw_output FROM sessions "
            "WHERE raw_output IS NOT NULL AND raw_output != '' "
            "ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
    finally:
        con.close()
    if not row:
        return {"error": "no session with raw_output yet"}
    return {
        "id": row[0], "topic": row[1], "status": row[2],
        "raw_output": (row[3] or "")[:3000],
    }

@app.get("/diag")
def diag() -> dict:
    """Container introspection: hermes binary, config, env, quick smoke call."""
    import shutil
    import subprocess as sp
    out: dict = {}
    hermes_bin = shutil.which("hermes")
    out["hermes_path"] = hermes_bin or "NOT FOUND"
    try:
        v = sp.run([hermes_bin or "hermes", "--version"], capture_output=True, text=True, timeout=10)
        out["hermes_version"] = (v.stdout + v.stderr).strip()[:300]
    except Exception as e:  # noqa: BLE001
        out["hermes_version"] = f"ERR: {e!r}"
    out["home_hermes_exists"] = Path("/root/.hermes").exists()
    cfg = Path("/root/.hermes/config.yaml")
    out["config_yaml"] = cfg.read_text()[:500] if cfg.exists() else "MISSING"
    envf = Path("/root/.hermes/.env")
    out["env_file_exists"] = envf.exists()
    out["env_file_keys"] = sorted([line.split("=")[0] for line in envf.read_text().splitlines() if "=" in line]) if envf.exists() else []
    out["env_OPENROUTER_KEY_present"] = bool(os.environ.get("OPENROUTER_API_KEY"))
    out["env_PARLIAMENT_MODEL_ORCHESTRATOR"] = os.environ.get("PARLIAMENT_MODEL_ORCHESTRATOR", "UNSET")
    try:
        out["marszalek_skill_app"] = Path("/app/skills/marszalek-sejmu/SKILL.md").exists()
        out["marszalek_skill_home"] = Path("/root/.hermes/skills/marszalek-sejmu/SKILL.md").exists()
        home_skills = Path("/root/.hermes/skills")
        out["home_skills_list"] = sorted([p.name for p in home_skills.iterdir()])[:8] if home_skills.exists() else []
    except Exception as e:  # noqa: BLE001
        out["skills_err"] = repr(e)
    try:
        r = sp.run(
            ["hermes", "chat", "-q", "say hi in one word", "-Q", "--accept-hooks", "--yolo"],
            capture_output=True, text=True, timeout=25,
        )
        out["hermes_smoke_returncode"] = r.returncode
        out["hermes_smoke_stdout"] = r.stdout[-500:] if r.stdout else ""
        out["hermes_smoke_stderr"] = r.stderr[-500:] if r.stderr else ""
    except sp.TimeoutExpired:
        out["hermes_smoke_returncode"] = "TIMEOUT"
    except Exception as e:  # noqa: BLE001
        out["hermes_smoke_returncode"] = f"ERR: {e!r}"
    return out

def _run_parliament_session(session_id: str, topic: str, db_path: Path) -> None:
    """Run Hermes, then re-parse stdout into per-speaker utterances written incrementally.

    The Hermes subprocess does not stream — `run_session` returns only after the full
    debate has completed. We compensate by parsing the stdout via `transcript_parser`
    (splitting party debates into one utterance per speaker), then inserting them into
    the DB with a small delay between each so the polling SSE stream picks them up
    incrementally and the UI feels live.
    """
    import json
    import sqlite3
    import time

    from parliament.session import run_session
    from parliament.transcript_parser import parse_transcript

    try:
        result = run_session(topic, db_path=db_path)
    except Exception as exc:  # noqa: BLE001
        pdb.update_session(
            db_path, session_id,
            status="error",
            raw_output=f"backend error: {exc!r}",
            finished_at=_now_iso(),
        )
        return

    real_id = result.session_id
    con = sqlite3.connect(str(db_path))
    try:
        if real_id and real_id != session_id:
            con.execute("PRAGMA foreign_keys=OFF")
            con.execute("DELETE FROM utterances WHERE session_id=?", (real_id,))
            con.execute("UPDATE votes SET session_id=? WHERE session_id=?", (session_id, real_id))
            con.execute(
                "UPDATE bill_drafts SET session_id=? WHERE session_id=?",
                (session_id, real_id),
            )
            con.execute("DELETE FROM sessions WHERE id=?", (real_id,))
        con.execute("DELETE FROM utterances WHERE session_id=?", (session_id,))
        con.commit()
    finally:
        con.close()

    utterances = parse_transcript(result.stdout)
    pace_seconds = float(os.environ.get("PARLIAMENT_STREAM_PACE_S", "1.2"))

    for seq, u in enumerate(utterances, start=1):
        try:
            pdb.insert_utterance(
                db_path, session_id, seq,
                speaker=u["speaker"],
                phase=u["phase"],
                content=u["content"][:32000],
                node_ids=u.get("node_ids", []),
            )
        except Exception:  # noqa: BLE001
            pass
        time.sleep(pace_seconds)

    pdb.update_session(
        db_path, session_id,
        status="complete" if result.returncode == 0 else "error",
        vote_result=result.vote_result,
        raw_output=result.stdout,
        exit_code=result.returncode,
        finished_at=_now_iso(),
    )

def _replay_cached_session(session_id: str, topic: str, db_path: Path) -> None:
    """Replay a previously-successful Hermes session as a streaming demo.

    Picks the most recent `status='complete'` session from the DB (any topic), runs
    its raw_output through the new transcript_parser, then inserts utterances under
    `session_id` with the same pacing as a live run. This is the contest-demo fallback
    that works even when the LLM is unreachable or out of credits.
    """
    import sqlite3
    import time

    from parliament.transcript_parser import parse_transcript

    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute(
            "SELECT raw_output, vote_result FROM sessions "
            "WHERE status='complete' AND raw_output IS NOT NULL "
            "AND raw_output LIKE '%is amended to read%' "
            "ORDER BY length(raw_output) DESC LIMIT 1"
        ).fetchone()
        if not row:
            row = con.execute(
                "SELECT raw_output, vote_result FROM sessions "
                "WHERE status='complete' AND raw_output IS NOT NULL "
                "AND length(raw_output) > 5000 "
                "ORDER BY length(raw_output) DESC LIMIT 1"
            ).fetchone()
    finally:
        con.close()

    if not row:
        fixture_path = Path(__file__).resolve().parent.parent / "deploy" / "fixtures" / "demo-session.json"
        if fixture_path.exists():
            try:
                with open(fixture_path, encoding="utf-8") as f:
                    data = json.load(f)
                row = (data.get("raw_output"), data.get("vote_result"))
            except Exception:  # noqa: BLE001
                row = None
        if not row:
            pdb.update_session(
                db_path, session_id,
                status="error",
                raw_output="No cached session available for replay.",
                finished_at=_now_iso(),
            )
            return

    raw_stdout, cached_vote = row[0], row[1]
    utterances = parse_transcript(raw_stdout)
    pace = float(os.environ.get("PARLIAMENT_REPLAY_PACE_S", "1.5"))

    for seq, u in enumerate(utterances, start=1):
        try:
            pdb.insert_utterance(
                db_path, session_id, seq,
                speaker=u["speaker"],
                phase=u["phase"],
                content=u["content"][:32000],
                node_ids=u.get("node_ids", []),
            )
        except Exception:  # noqa: BLE001
            pass
        time.sleep(pace)

    pdb.update_session(
        db_path, session_id,
        status="complete",
        vote_result=cached_vote or "PASSED",
        raw_output=raw_stdout,
        exit_code=0,
        finished_at=_now_iso(),
    )

@app.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    req: CreateSessionRequest, background: BackgroundTasks
) -> CreateSessionResponse:
    """Create a placeholder session row, spawn the Hermes run in the background."""
    db_path = _db_path()
    pdb.init_db(db_path)
    placeholder_id = _new_session_id()
    pdb.insert_session(db_path, placeholder_id, req.topic)
    background.add_task(_run_parliament_session, placeholder_id, req.topic, db_path)
    return CreateSessionResponse(session_id=placeholder_id)

@app.post("/sessions/demo", response_model=CreateSessionResponse)
async def create_demo_session(
    req: CreateSessionRequest, background: BackgroundTasks
) -> CreateSessionResponse:
    """Instant demo replay — uses the most recent cached successful transcript.

    Streams in ~25s with full per-speaker pacing and avatars. Use this when LLM is
    out of credits or you want a deterministic demo.
    """
    db_path = _db_path()
    pdb.init_db(db_path)
    placeholder_id = _new_session_id()
    pdb.insert_session(db_path, placeholder_id, f"[DEMO] {req.topic}")
    background.add_task(_replay_cached_session, placeholder_id, req.topic, db_path)
    return CreateSessionResponse(session_id=placeholder_id)

@app.get("/stream/{session_id}")
async def stream_session(session_id: str):
    """Live SSE stream of utterances + status. Polls DB until status is terminal."""

    async def event_generator():
        db_path = _db_path()
        if not db_path.exists():
            yield {
                "event": "not_found",
                "data": json.dumps({"session_id": session_id, "reason": "no db"}),
            }
            return

        last_seq = 0
        terminal_emitted = False
        poll_interval = 0.5
        max_wait_no_session = 30.0
        elapsed_no_session = 0.0

        while not terminal_emitted:
            async with aiosqlite.connect(str(db_path)) as conn:
                async with conn.execute(
                    "SELECT id, status, vote_result FROM sessions WHERE id = ?",
                    (session_id,),
                ) as cur:
                    row = await cur.fetchone()

                if row is None:
                    if elapsed_no_session > max_wait_no_session:
                        yield {
                            "event": "not_found",
                            "data": json.dumps({"session_id": session_id}),
                        }
                        return
                    elapsed_no_session += poll_interval
                    await asyncio.sleep(poll_interval)
                    continue

                real_id, status, vote_result = row[0], row[1], row[2]

                async with conn.execute(
                    "SELECT seq, speaker, phase, content, node_ids "
                    "FROM utterances WHERE session_id = ? AND seq > ? ORDER BY seq",
                    (real_id, last_seq),
                ) as cur:
                    async for u in cur:
                        last_seq = u[0]
                        yield {
                            "event": "utterance",
                            "data": json.dumps(
                                {
                                    "seq": u[0],
                                    "speaker": u[1],
                                    "phase": u[2],
                                    "content": u[3],
                                    "node_ids": json.loads(u[4]) if u[4] else [],
                                }
                            ),
                        }

                if status in {"complete", "error"}:
                    yield {
                        "event": "status",
                        "data": json.dumps({"status": status, "vote_result": vote_result}),
                    }
                    terminal_emitted = True
                    return

            await asyncio.sleep(poll_interval)

    return EventSourceResponse(event_generator())

_STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "out"
if _STATIC_DIR.exists():
    app.mount("/app", StaticFiles(directory=_STATIC_DIR, html=True), name="ui")

    @app.get("/")
    def _root_redirect():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/app/")

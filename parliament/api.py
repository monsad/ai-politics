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


def _run_parliament_session(session_id: str, topic: str, db_path: Path) -> None:
    """Run Hermes in a worker thread, then migrate utterances/votes to the placeholder id.

    `run_session` extracts a Hermes-generated session_id from stderr and writes a new
    row under that id. We migrate everything to `session_id` (the placeholder the
    frontend is already subscribed to) so the SSE connection sees the data.
    """
    import sqlite3

    from parliament.session import run_session

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
    if real_id is None or real_id == session_id:
        pdb.update_session(
            db_path, session_id,
            status="complete" if result.returncode == 0 else "error",
            vote_result=result.vote_result,
            raw_output=result.stdout,
            exit_code=result.returncode,
            finished_at=_now_iso(),
        )
        return

    con = sqlite3.connect(str(db_path))
    try:
        con.execute("PRAGMA foreign_keys=OFF")
        con.execute(
            "UPDATE utterances SET session_id=? WHERE session_id=?",
            (session_id, real_id),
        )
        con.execute(
            "UPDATE votes SET session_id=? WHERE session_id=?",
            (session_id, real_id),
        )
        con.execute(
            "UPDATE bill_drafts SET session_id=? WHERE session_id=?",
            (session_id, real_id),
        )
        con.execute("DELETE FROM sessions WHERE id=?", (real_id,))
        con.commit()
    finally:
        con.close()

    pdb.update_session(
        db_path, session_id,
        status="complete" if result.returncode == 0 else "error",
        vote_result=result.vote_result,
        raw_output=result.stdout,
        exit_code=result.returncode,
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
    # The Hermes subprocess will emit its own session_id; the placeholder ensures the
    # SSE client has something to connect to immediately. session.py reads the same
    # db_path and writes utterances/status under the real session id, so we expose
    # both here: the frontend polls /stream/{placeholder_id} as well as listens for
    # status events that include the real id.
    background.add_task(_run_parliament_session, placeholder_id, req.topic, db_path)
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
        max_wait_no_session = 30.0  # seconds to wait for placeholder→real-id transition
        elapsed_no_session = 0.0

        while not terminal_emitted:
            async with aiosqlite.connect(str(db_path)) as conn:
                # Find session row — try direct id first, then most recent matching topic
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


# Static UI mount — single-host deploy serves Next.js export under /app.
# API routes (`/health`, `/sessions`, `/stream`) stay at root so the frontend can use
# absolute paths without rewriting fetch URLs.
_STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "out"
if _STATIC_DIR.exists():
    app.mount("/app", StaticFiles(directory=_STATIC_DIR, html=True), name="ui")

    @app.get("/")
    def _root_redirect():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/app/")

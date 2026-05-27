"""FastAPI app: health + SSE stream endpoint for session transcripts."""
from __future__ import annotations

import json
import os
from pathlib import Path

import aiosqlite
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="Virtual Parliament API")


def _db_path() -> Path:
    return Path(os.environ.get("PARLIAMENT_DB_PATH", "sessions.db"))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/stream/{session_id}")
async def stream_session(session_id: str):
    async def event_generator():
        db_path = _db_path()
        if not db_path.exists():
            yield {"event": "not_found", "data": json.dumps({"session_id": session_id, "reason": "no db"})}
            return
        async with aiosqlite.connect(str(db_path)) as db:
            async with db.execute(
                "SELECT id FROM sessions WHERE id = ?", (session_id,)
            ) as cur:
                row = await cur.fetchone()
            if row is None:
                yield {"event": "not_found", "data": json.dumps({"session_id": session_id})}
                return

            async with db.execute(
                "SELECT seq, speaker, phase, content, node_ids "
                "FROM utterances WHERE session_id = ? ORDER BY seq",
                (session_id,),
            ) as cur:
                async for row in cur:
                    yield {
                        "event": "utterance",
                        "data": json.dumps({
                            "seq": row[0],
                            "speaker": row[1],
                            "phase": row[2],
                            "content": row[3],
                            "node_ids": json.loads(row[4]) if row[4] else [],
                        }),
                    }

            async with db.execute(
                "SELECT status, vote_result FROM sessions WHERE id = ?", (session_id,)
            ) as cur:
                s = await cur.fetchone()
                if s:
                    yield {"event": "status", "data": json.dumps({"status": s[0], "vote_result": s[1]})}

    return EventSourceResponse(event_generator())

"""FastAPI SSE endpoint for session streaming. Wave 3 Plan 05 fills this in."""
from __future__ import annotations
from fastapi import FastAPI

app = FastAPI(title="Virtual Parliament API")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

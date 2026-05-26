# Virtual Parliament

> Multi-agent simulation of the Polish Sejm. Five party agents debate user-submitted bills, consulting nineteen ministry experts and a Second Brain (PageIndex) holding the Polish Constitution and ~50 statutes. Every argument cites a real Polish legal document.

**Contest entry:** [Hermes Agent Challenge](https://dev.to/devteam/join-the-hermes-agent-challenge-1000-in-prizes-13cd) (deadline 2026-05-31 23:59 PDT).
**License:** MIT.

## Quickstart

```bash
git clone <repo-url>
cd ai-politics
cp .env.example .env   # then edit .env and add PAGEINDEX_API_KEY
make setup             # uv venv + pip install + npm install + skills install + pre-commit
make smoke             # run all 7 day-1 gate tests
```

## Status

Phase 1 — Foundation & Smoke Tests (Day 1 of 5). De-risking Hermes Agent 0.14.0 + PageIndex Cloud before agent skill writing begins in Phase 2.

## Stack

- Python 3.11 (exact) + uv + hermes-agent==0.14.0
- PageIndex Cloud (free tier, MCP server `pageindex-mcp@1.6.3`)
- Node.js >=20.8.1 for `skills-ref@0.1.5` validation
- Future: Next.js 16.2.6 (Phase 4), FastAPI + SSE (Phase 3)

Full stack rationale: see `CLAUDE.md` "Recommended Stack" table.

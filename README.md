# Virtual Parliament

> Multi-agent simulation of the Polish Sejm. Five party agents debate user-submitted bills, consulting nineteen ministry experts and a Second Brain (PageIndex) holding the Polish Constitution and ~50 statutes. Every argument cites a real Polish legal document.

**Contest entry:** [Hermes Agent Challenge](https://dev.to/devteam/join-the-hermes-agent-challenge-1000-in-prizes-13cd) — *Build With Hermes Agent* (deadline 2026-05-31 23:59 PDT).
**License:** MIT.

> ⚠️ **EDUCATIONAL SIMULATION** — not a political forecast, endorsement, or prediction of real parliamentary outcomes. No real Members of Parliament are named. A disclaimer is emitted on every run.

🌐 **Live demo:** <https://web-production-53027.up.railway.app/>
📝 **DEV.to submission:** see [`SUBMISSION.md`](SUBMISSION.md)

## What it does

Type a bill topic → get a full, source-cited parliamentary simulation in ≤ 5 minutes:

1. **Classification & routing** — a Marszałek (Speaker) orchestrator agent classifies the topic and picks the relevant ministries.
2. **Ministry consultation** — 2–3 of the 19 ministry-expert agents are consulted **in parallel** (via Hermes `delegate_task`), each citing real statutes.
3. **Party debate** — five party agents (CR, NC, AC, Liberty Front, SD) argue from their real ideology across a first and second reading.
4. **Vote** — FOR/AGAINST/ABSTAIN weighted by real seat counts (460 total; >230 passes).
5. **Bill drafting** — if it passes (or is close), the chamber drafts an amended statute.

Every argument cites a node in the **Second Brain** — 50 Polish legal documents indexed in PageIndex (Constitution + Criminal/Civil/Labour codes + ~46 statutes) — and citations are traceable back to the source.

## Quickstart

```bash
git clone https://github.com/monsad/ai-politics
cd ai-politics
cp .env.example .env   # then edit .env and add PAGEINDEX_API_KEY
make setup             # uv venv + pip install + npm install + skills install + pre-commit

# CLI
parliament "four-day work week"
parliament "flat income tax" --export markdown -o session.md
parliament "renewable energy" --minister energii      # one ministry in isolation

# Web chamber (Next.js + FastAPI SSE)
uvicorn parliament.api:app --reload      # backend
cd web && npm run dev                    # frontend at http://localhost:3000
```

`make smoke` runs the 7 foundation gate tests (Hermes import, minimal agent, `delegate_task`, PageIndex search + diacritics + concurrency, skill validation).

## Architecture

```
Marszałek (orchestrator skill) ── delegate_task(parallel) ──► 19 ministry skills ──► PageIndex (legal RAG)
        │                                                                                  ▲
        ├─ first + second reading ──► 5 party skills (CR/NC/AC/Liberty Front/SD) ──────┘ (cite sources)
        ├─ seat-weighted vote (460 seats)
        └─ bill drafting

parliament/  CLI (typer) + FastAPI SSE + subprocess Hermes launcher + SQLite persistence + citation validator
skills/      25 Hermes Agent Skills (Anthropic skill spec) — orchestrator + 5 parties + 19 ministries + web-research
web/         Next.js 16 broadcast-style chamber, fed by the same SSE stream
data/        50-document legal corpus manifest + Constitution PDF
```

## Stack

- **Agents:** hermes-agent `0.14.0` — every participant is a Hermes skill; orchestrator fans out via `delegate_task`.
- **Skill format:** Anthropic Agent Skills spec (validated with `skills-ref@0.1.5`).
- **RAG:** PageIndex Cloud (vectorless, MCP-native) — chosen for citation traceability over chunked vector search.
- **Runtime:** Python 3.11 + uv, `typer` CLI, FastAPI + SSE, SQLite.
- **Web:** Next.js 16 (App Router) over the same SSE pipeline.
- **Models:** tiered via `litellm` (cheaper ministries, stronger orchestrator/parties) — runnable on a ~$5/month VPS.

Full stack rationale: see `CLAUDE.md` "Recommended Stack" table.

## Contest submission

The DEV.to write-up (What I Built · Demo · Code · Tech Stack · How I Used Hermes Agent) lives at
[`docs/devto-submission.md`](docs/devto-submission.md). Tags: `hermesagentchallenge`, `devchallenge`, `agents`.

## Ethics

Educational use only. No real politicians are modeled, no hate speech is produced, and a disclaimer is
emitted at the start and end of every session. Party positions are stylized from public party programmes,
not statements by named individuals.

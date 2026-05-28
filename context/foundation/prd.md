---
project: "Virtual Parliament — Deploy & Frontend"
version: 1
status: draft
created: 2026-05-27
context_type: brownfield
product_type: web-app
target_scale:
  users: small
  qps: low
  data_volume: small
timeline_budget:
  delivery_weeks: 1
  hard_deadline: "2026-05-31"
  after_hours_only: true
---

## Current System Overview

Virtual Parliament is a multi-agent simulation of the Polish Sejm. The system accepts a bill topic, routes it through a Marszałek orchestrator that delegates to 19 ministry-expert agents and 5 party agents, produces a debate transcript, and returns a PASSED/REJECTED vote result.

- **Architecture:** Python monolith — CLI entry point, orchestrator, agent skills, FastAPI SSE layer, SQLite storage
- **Tech stack:** Python 3.11, Hermes Agent 0.14.0, FastAPI, sse-starlette, typer, aiosqlite, SQLite
- **Current user base:** No users — project has never been deployed publicly
- **Core functionality:** `parliament "<topic>"` CLI → Marszałek orchestrates ministry consultations via `delegate_task` → party agents debate → vote aggregated → result written to SQLite

## Problem Statement & Motivation

The project exists as working code on a local machine but has no public URL. Without a deployment, there is no demo, no jury evaluation, and no contest submission. The Hermes Agent Challenge deadline is 2026-05-31 23:59 PDT — four days away. The current workaround (running locally and screen-sharing) is not a contest-valid submission; it produces no shareable artifact.

## User & Persona

**Jury — Hermes Agent Challenge.** Evaluates the project through a browser and/or a ≤ 3-minute demo video. Needs: (1) a public HTTPS URL reachable from outside the submitter's network, (2) a UI that shows the simulation in action without any local setup, (3) a working demonstration path: enter a bill topic → receive a cited parliamentary debate with a vote result.

## Success Criteria

### Primary
- A user opens the public HTTPS URL, enters a bill topic, and sees a live-streaming debate transcript appear utterance by utterance, followed by a vote table with a PASSED or REJECTED result.

### Secondary
- Party colours are visible in the transcript (KO=blue, PiS=red, etc.).
- A disclaimer `⚠️ EDUCATIONAL SIMULATION` appears at the top and bottom of the page.

### Guardrails
- Hermes Agent skills (marszałek, ministries, parties) execute correctly on the server — they must not be broken by the deployment change.
- API keys (`OPENROUTER_API_KEY`, `PAGEINDEX_API_KEY`) do not appear in the repository or in application logs.
- The application is reachable at the public URL before 2026-05-31 23:59 PDT.

## User Stories

### US-01: Full parliamentary simulation via browser

**Given** a user opens the public HTTPS URL in a browser,
**When** they enter a bill topic and click "Uruchom" (Run),
**Then** they see debate utterances appear one by one with party colours, and after the simulation completes they see a vote table with PASSED or REJECTED.

## Scope of Change

- [new] Next.js UI with a bill-topic form, live SSE transcript stream with party-colour coding, and a vote-result table
- [new] PaaS deployment configuration (Dockerfile or railway.toml/fly.toml) with environment-variable injection for API keys
- [new] CORS headers on the FastAPI layer enabling cross-origin requests from the Next.js domain
- [preserved] `parliament` CLI (typer) — must continue to run locally and on the server without modification
- [preserved] `/stream/{session_id}` and `/health` SSE contract — event format and field names unchanged
- [preserved] SQLite schema (sessions, utterances, votes, bill_drafts) — no migrations
- [preserved] `skills/` directory (marszalek-sejmu, ministerstwa, partie) — out of scope for this change

## Constraints & Compatibility

- `parliament` CLI and Hermes subprocess launcher must run without code changes on the PaaS server (Python 3.11 + venv correctly provisioned).
- `/stream/{session_id}` event format (event name, JSON fields) is a frozen contract — the Next.js client depends on it.
- SQLite schema is unchanged — no migration scripts, no schema alterations.
- API keys are supplied exclusively through environment variables on the PaaS platform — never hardcoded, never committed.

## Business Logic Changes

No domain logic change. This is an infrastructure and presentation change. The existing domain rule — accept a bill topic, route through Marszałek to ministry experts and party agents, aggregate votes, return PASSED/REJECTED — is implemented in the CLI and skills and is not modified by this change.

## Access Control Changes

No access control changes — current model preserved. Public open access by design (contest demo, not a multi-user product). API keys remain server-side environment variables only.

## Non-Goals

- **No auth / user accounts** — open access is intentional for the contest demo; login is out of scope.
- **No multiple concurrent sessions or queue** — one simulation at a time is sufficient for demo purposes.
- **No database migration** — the SQLite schema is frozen; no schema changes in this change.

## Open Questions

No open questions. All required decisions were resolved during the shape session (2026-05-27). Quality check status: accepted.

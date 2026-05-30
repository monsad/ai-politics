---
title: Virtual Parliament — a Polish Sejm simulation built on 25 Hermes Agent skills
published: false
tags: hermesagentchallenge, devchallenge, agents
---

*This is a submission for the [Hermes Agent Challenge](https://dev.to/challenges/hermes-agent-2026-05-15)*

## What I Built

**Virtual Parliament** is a multi-agent simulation of the Polish Sejm (Parliament). Type in a draft bill topic — *"flat income tax"*, *"four-day work week"*, *"renewable energy expansion"* — and watch a full legislative session unfold in your browser in 2–3 minutes:

1. A **Marszałek (Speaker) AI orchestrator** reads the topic, classifies it, and selects the relevant ministries.
2. **Ministry experts** (19 of them — Finance, Labour & Social Policy, Climate, Energy, Justice, Foreign Affairs, …) return structured analyses with legal, fiscal, and risk findings.
3. **Five party agents** (KO, PiS, TD, Konfederacja, Lewica) hold a first reading using the ministry findings, then a second reading with rebuttals.
4. The Marszałek tallies votes by seat count (460 total) and produces a **draft bill** with explicit "Article X §Y *is amended to read…*" diffs against current Polish law.

Every argument cites a real legal source — articles of the Constitution, Labour Code, Personal Income Tax Act, etc. — retrieved via PageIndex RAG. The frontend then surfaces a side-by-side **"Current law vs proposed change"** panel so a non-lawyer can read what the AI is actually proposing to change in the statute book.

**Why I built it.** Public discussions about new laws in Poland (and most countries) rarely show the diff: people argue about whether a tax should be flat or progressive, never about *which specific paragraph* of *which act* gets rewritten and how. I wanted a tool that turns a sentence into a draft amendment with traceable legal citations — partly an educational toy, partly a way to stress-test what multi-agent debate plus retrieval can do for civic literacy.

## Demo

🎥 **Video walkthrough**: <https://www.loom.com/share/92cdac7da31c471088a4e569b0cfe1ed>
🔗 **Live deployment**: <https://web-production-53027.up.railway.app/>

Click **▶ Open session** for a fresh AI-generated debate (~2–3 min), or **⚡ Demo** for an instant replay of a cached transcript (~25 s, useful when you just want to see the UI).

**Screens**
- Stage panel with current speaker (Marszałek 🎯, ministries 💰🏥⚡, parties in their colours)
- AI thought process panel — the Marszałek's chain-of-thought between phases
- Live vote tally — bar segmented FOR / ABSTAIN / AGAINST, with party-by-party breakdown
- Society impact — heuristic estimate of support across six demographic groups (youth, middle class, rural, retirees, entrepreneurs, wage workers)
- Social-media reactions — one tweet per party in their characteristic narrative tone
- **Current law vs proposed change** — for each amended article, the existing wording on the left, the AI's proposed new wording on the right

## Code

📦 **Repository**: <https://github.com/monsad/ai-politics> (MIT-licensed)

Key folders:
- `parliament/` — Python orchestrator (FastAPI, subprocess launcher, citation validator, transcript parser)
- `skills/` — 25 Hermes Agent skills following the [Anthropic Agent Skills](https://agentskills.io/specification) spec
  - `marszalek-sejmu/` — the orchestrator skill (delegates to ministries via `delegate_task`)
  - `ministry-finansow/`, `ministry-zdrowia/`, … — 19 ministry experts (validated by `skills-ref`)
  - `party-ko/`, `party-pis/`, `party-td/`, `party-konfederacja/`, `party-lewica/` — 5 party agents with their actual political profiles
- `web/` — Next.js 16 (App Router) static export, deployed alongside FastAPI on a single Railway service
- `deploy/` — Dockerfile, entrypoint, Hermes config and demo fixtures shipped with the image

### My Tech Stack

| Layer | Tech | Notes |
| --- | --- | --- |
| Agent framework | **Hermes Agent 0.14.0** | the heart of the project — `pip install hermes-agent==0.14.0`, Python 3.11 |
| Skills spec | **Agent Skills** spec, validated by `skills-ref@0.1.5` | YAML frontmatter + markdown; lowercase-hyphen names |
| RAG | **PageIndex Cloud** via MCP | vectorless retrieval over the Polish Constitution + ~50 statutes; every node ID is a real legal reference |
| Model gateway | **OpenRouter** | `google/gemini-3.1-flash-lite` for orchestrator + ministries + parties (fast, ~$0.05 per session) |
| Orchestrator | **Python + FastAPI + uvicorn** | subprocess launcher around `hermes chat -s <skill>` |
| Storage | **SQLite via aiosqlite** | sessions, utterances, votes, bill_drafts |
| CLI | **typer 0.25.1** | `parliament "<topic>"` |
| Frontend | **Next.js 16.2.6 + Tailwind CSS** | static export, served by FastAPI on `/app/`; SSE consumer for live transcripts |
| Streaming | **sse-starlette** | `/stream/{session_id}` polls SQLite and pushes per-speaker `utterance` events |
| Deploy | **Railway** (Dockerfile builder) | one container, public HTTPS, env-var driven config |

## How I Used Hermes Agent

Hermes Agent is the load-bearing piece — without it the project simply doesn't work the way I want.

**1. Skills as first-class units of expertise.** Every actor in the simulation is a skill in `skills/<id>/SKILL.md`: 1 Marszałek, 19 ministries, 5 parties. Each one has a tight system prompt and toolsets declared in YAML frontmatter. The Marszałek skill, for instance, knows about the bill drafting template (`assets/bill-draft-template.md`) and the ministry-selection table; the party skills know each party's actual seats (KO=157, PiS=194, TD=65, Konfederacja=18, Lewica=26 — totalling 460) and characteristic policy positions. This kept the prompts maintainable: I never have one giant master prompt; I have 25 small ones.

**2. `delegate_task` for parallel ministry consultation.** When the Marszałek classifies a topic, it calls `delegate_task(tasks=[...])` with 2–3 ministry assignments at once. Hermes' batch mode spawns parallel `AIAgent` children via a `ThreadPoolExecutor`, and the Marszałek receives the consolidated findings back. This is the documented Hermes fan-out pattern and it's exactly the shape my problem needs — ministries are independent of each other; I should not be wiring up asyncio gathers manually around `AIAgent` instances (which is documented as a foot-gun because subagents run on threads, not coroutines).

**3. Subprocess invocation as the integration surface.** Hermes is a CLI/TUI framework first; the cleanest way to embed it in a web app is `subprocess.Popen(["hermes", "chat", "-s", skill, "-q", topic, "-Q", "--accept-hooks", "--yolo"])`. My `parliament/session.py` is essentially that subprocess launcher plus a stdout parser. Once a session completes I re-parse the stdout into per-speaker utterances via `parliament/transcript_parser.py` and stream them to the frontend with deliberate pacing so the UI feels live.

**4. MCP tools for retrieval.** PageIndex Cloud exposes a `tree_search` / `fetch_node` API via MCP. Each skill that needs to cite Polish law (the Marszałek, all ministries, all parties) declares `toolsets: ["pageindex-rag"]` and gets retrieval for free — no client code in my repo. The orchestrator then runs every emitted `[node:…]` reference through a `citation_validator` that asserts the citation actually resolves, before letting the session pass.

**5. Hermes config + skills baked into the Docker image.** For the Railway deployment, I copy `deploy/hermes-config.yaml` to `/root/.hermes/config.yaml` and `skills/*` to `/root/.hermes/skills/`, then an entrypoint script materializes `OPENROUTER_API_KEY` into `~/.hermes/.env` from the platform-provided env var. With `disabled_toolsets: [browser, computer-use, voice, terminal-modal]` in the config, Hermes starts in ~2 s instead of hanging on a missing chromium install — a non-obvious gotcha I only found via a `/diag` endpoint.

### What this combination unlocks

The reason I leaned into Hermes (rather than rolling a custom LangGraph/LlamaIndex agent loop) is the **operational ergonomics**: spawning a parallel fan-out, passing context, hooking up MCP tools, and getting reasonable behavior out of a 24-call legislative chain are *the kind of things Hermes already does well*. I spent my time on the simulation design and the diff-extraction UX, not on writing a delegation framework. That's the right division of labour for a 5-day contest project.

---

🇵🇱 Built in Warsaw. MIT-licensed. Educational simulation only — no real MPs are represented.

⚠️ The vote results, party positions, and draft amendments are AI-generated content. Do not treat them as legal advice or political forecasts.

---
title: I Built a 25-Agent Polish Parliament That Drafts Bills With Real Legal Citations
published: false
tags: hermesagentchallenge, devchallenge, agents
---

*This is a submission for the [Hermes Agent Challenge](https://dev.to/challenges/hermes-agent-2026-05-15)*

> **TL;DR** — Type a one-line bill topic. Twenty-five Hermes agents (1 Speaker, 19 ministries, 5 parties) run a full Polish legislative session in 2 minutes. Vote tally, social impact, party tweets — and a side-by-side **"current law vs proposed amendment"** with every clause cited to a real statute. Built on `delegate_task` for parallel ministry consultation.

![Virtual Parliament — live chamber view with the four-day work week bill passing 248:212, AI thought process panel, vote tally and ministry analyses](https://raw.githubusercontent.com/monsad/ai-politics/main/docs/screenshots/chamber-overview.png)

🌐 **Live:** <https://web-production-53027.up.railway.app/>
🎥 **Walkthrough:** <https://www.loom.com/share/92cdac7da31c471088a4e569b0cfe1ed>
📦 **Repo:** <https://github.com/monsad/ai-politics> (MIT)

---

## What I Built

Watch a politician debate a new tax law on TV. They argue whether it's fair, whether it'll work, whether the other side is lying. **Nobody ever shows you the diff** — *which paragraph of which statute* actually changes, and from what to what. The conversation is theatre on top of an invisible legal document.

So I built the theatre AND the legal document.

**Virtual Parliament** is a multi-agent simulation of the Polish Sejm. You type something like *"four-day work week"* or *"flat income tax"*, and 25 Hermes agents run a full legislative session:

1. **🎯 Marszałek (Speaker) — the orchestrator.** Classifies the topic. Picks 2–3 ministries via `delegate_task` *in parallel*. Reads their findings. Routes the bill to a party debate.
2. **🏛️ 19 ministry experts** — Finance, Climate, Labour & Social Policy, Justice, … Each returns a structured analysis: *legal finding · budget impact · top 3 risks · recommendation*. Every claim cites a real statute via PageIndex RAG.
3. **🗳️ 5 party agents** — CR, NC, AC, Liberty Front, SD. Each one carries the real party's seat count (157, 194, 65, 18, 26 — totalling 460), policy positions and rhetorical style. First reading. Second reading with rebuttals.
4. **📊 Vote** — weighted by seats. >230 passes.
5. **📜 Draft bill** — produced with explicit *"Article 129 §1 of the Labour Code **is amended to read**…"* diffs against current law.

The frontend surfaces the diff as a **Current law vs proposed change** panel. Left column: what's in force today, quoted from the statute. Right column: what the AI just proposed. A non-lawyer can finally see the actual edit.

This is the part of legislation that's normally invisible. **The whole point is to make it visible.**

---

## Demo

🎥 **Video walkthrough (~2 min):** <https://www.loom.com/share/92cdac7da31c471088a4e569b0cfe1ed>

🌐 **Live URL:** <https://web-production-53027.up.railway.app/>

Two buttons:
- **▶ Open session** — fresh AI-generated debate, ~2–3 minutes. Costs ~$0.04 in `google/gemini-3.1-flash-lite` calls.
- **⚡ Demo** — instant replay of a cached transcript, ~25 s. Useful when you just want to see the UI without burning credits.

Try **"four-day work week"** (Demo) — it's the demo fixture I ship in the Docker image. SD and Liberty Front vote on opposite sides (pro-labour vs free-market), which is the political-coherence check I built into the acceptance tests.

**Local one-command run:**
```bash
git clone https://github.com/monsad/ai-politics && cd ai-politics && make setup && parliament "four-day work week"
```

---

## Code

📦 **Repo:** <https://github.com/monsad/ai-politics> (MIT)

```
skills/                         # 25 Hermes Agent skills, validated by skills-ref
  marszalek-sejmu/              # the orchestrator — owns the bill-drafting template
  ministry-finansow/            # 19 ministry experts (Finance, Health, Climate, ...)
  ...
  party-cr/                     # 5 party agents (CR, NC, AC, Liberty Front, SD)
parliament/
  session.py                    # subprocess launcher around `hermes chat -s <skill>`
  transcript_parser.py          # splits orchestrator stdout into per-speaker utterances
  citation_validator.py         # every [node:...] must resolve back to a real statute
  api.py                        # FastAPI: POST /sessions, polling SSE /stream/{id}
  cli.py                        # `parliament "<topic>"` (typer)
web/                            # Next.js 16 static export, served by FastAPI
deploy/                         # Dockerfile entrypoint + Hermes config + demo fixture
```

### My Tech Stack

| Layer | Tech | Notes |
|---|---|---|
| **Agent framework** | **hermes-agent 0.14.0** | the load-bearing piece — `pip install hermes-agent==0.14.0` |
| **Skills spec** | Anthropic Agent Skills + `skills-ref@0.1.5` | 25 skills, lowercase-hyphen, validated in CI |
| **RAG** | **PageIndex Cloud** via MCP | vectorless retrieval over Polish Constitution + ~50 statutes; every citation traces to a real document |
| **Models** | `google/gemini-3.1-flash-lite` via OpenRouter | ~$0.04 per full session, fast enough for live demo |
| **Orchestrator** | Python 3.11 + FastAPI + uvicorn | subprocess launcher around `hermes chat` |
| **Stream** | sse-starlette + polling SQLite | per-speaker utterances pushed as `event: utterance` |
| **Frontend** | Next.js 16 (App Router, static export) + Tailwind | served from `/app/*` by the same FastAPI |
| **Deploy** | Railway (single Docker container) | public HTTPS, ~$5/month |

---

## How I Used Hermes Agent

There's one Hermes property the whole project is built on:

> **`delegate_task` lets a parent skill fan out to N child skills in parallel as a single tool call.**

Without that, this project isn't tractable. With it, the entire 25-agent pipeline is **24 LLM calls in a tight DAG**, runs in 2 minutes, and the orchestrator never has to manage thread pools or async gathers itself.

Here's the shape:

```
                  ┌─────────────────────────────┐
                  │  marszalek-sejmu (skill)    │
                  │  Topic → ministry selection │
                  └──────────────┬──────────────┘
                                 │ delegate_task(tasks=[...])  ← Hermes batch mode
                ┌────────────────┼────────────────┐
                ▼                ▼                ▼
       ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
       │ ministry-      │ │ ministry-      │ │ ministry-      │
       │ finansow       │ │ klimatu        │ │ rodziny-pracy  │
       └────────┬───────┘ └────────┬───────┘ └────────┬───────┘
                │  PageIndex RAG   │   (cite real statutes)
                └────────┬─────────┴─────────┬───────┘
                         ▼                   ▼
                  Synthesized findings → Marszałek
                         │
                         ▼   5 × party debate, ×2 readings
                  ┌──────────────┐
                  │ CR  NC  AC  │
                  │ LF  SD       │
                  └──────┬───────┘
                         ▼
                  Seat-weighted vote → Draft bill
```

### Why `delegate_task` was the right primitive

- **Ministries are independent.** Finance doesn't need to know what Climate said before doing its own analysis. They both run on the same input bill topic, return findings, get merged by the orchestrator. Classic embarrassingly parallel.
- **Hermes already handles the thread pool.** Batch mode uses `ThreadPoolExecutor` to spawn `AIAgent` children. I don't have to mix asyncio with hermes-agent's threaded subagents — a known foot-gun if you roll your own.
- **Context isolation is free.** Each ministry gets its own skill prompt with its own toolsets (`pageindex-rag`). The Marszałek doesn't pollute their context.
- **Approval and audit are centralized.** When PageIndex is called from a ministry, it goes through Hermes' tool registry. I get the audit trail for free.

### The other Hermes pieces that mattered

1. **Skills as the unit of expertise.** Every agent is one `SKILL.md`. The Marszałek has the bill-drafting template (`assets/bill-draft-template.md`). The parties have their actual policy positions. None of this fits in one big system prompt — but as 25 separate skills, it's maintainable. I can rewrite SD's economic stance without touching Liberty Front.

2. **MCP toolsets for retrieval.** Every skill that cites Polish law declares `toolsets: ["pageindex-rag"]` and gets retrieval for free. Zero Python integration code. The PageIndex MCP server is one config-yaml entry.

3. **Subprocess as the integration surface.** Hermes is a CLI first. The cleanest way to embed it in FastAPI is `subprocess.Popen(["hermes", "chat", "-s", skill, "-q", topic, "-Q", "--accept-hooks", "--yolo"])`. My `session.py` is essentially that subprocess launcher plus a stdout parser that splits the result into per-speaker utterances for SSE streaming.

4. **Bake-time config for the container.** For Railway, the Dockerfile copies `hermes-config.yaml` to `/root/.hermes/config.yaml` and `skills/*` to `/root/.hermes/skills/`. An entrypoint script materializes `OPENROUTER_API_KEY` into `~/.hermes/.env` at boot. Crucially: **`disabled_toolsets: [browser, computer-use, voice, terminal-modal]`** — otherwise Hermes hangs at startup looking for a Chromium binary that isn't in `python:3.11-slim`. I only found that via a `/diag` endpoint I added to introspect the running container.

### What this combination unlocks

If I had to write the parallel fan-out + tool registry + skill loader by hand, I'd still be debugging deadlocks instead of arguing with my own bill drafts.

Hermes let me spend my time on **the simulation design** (how does a Marszałek pick ministries? what does each party's house style sound like? how do you parse "Article 129 §1 is amended to read…" out of free-form markdown?) and **the legal-diff UX** (the Current law vs proposed change panel) — not on the orchestration framework.

That's the right division of labour for a 5-day contest project, and frankly for most agent projects.

---

## What surprised me

- **Hermes models matter less than you'd think.** Most of the quality comes from the skill prompts. Swapping `gemini-flash-lite` ↔ `llama-3.3-70b` changes vocabulary, barely changes the structure of the debate.
- **The frontend is where civic value lives.** The pipeline produces a 40 KB markdown blob. Useless to a non-lawyer. The UI panel showing *"`Czas pracy nie może przekraczać 8 godzin na dobę i przeciętnie 40 godzin…`"* on the left and the proposed *"…32 godzin w przeciętnie czterodniowym…"* on the right is what makes this a tool instead of a transcript.
- **Free OpenRouter tiers are rate-limited into uselessness during contest week.** Plan for $5 of paid model credit, or bake a demo fixture into the image. I shipped both.

---

🇵🇱 Built in Warsaw. MIT-licensed. Educational simulation only — no real Members of Parliament are represented, no hate speech is produced, and a disclaimer is emitted at the top and bottom of every session.

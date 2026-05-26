# Phase 2: Agent Skills & Corpus — Context

**Gathered:** 2026-05-26
**Status:** Ready for planning
**Source:** User discussion (discuss-phase workflow)

<domain>
## Phase Boundary

Days 2–3 of the contest (2026-05-27 to 2026-05-28). This phase delivers all the *content* of the parliament simulation:

- 25 SKILL.md files (5 parties + 19 ministries + 1 Marszałek)
- Full curated corpus ingested into PageIndex Cloud (~50 docs)
- `doc_registry.py` with agent_id→doc_id mapping AND filtering function
- LLM-pair ethics review documented for all party profiles
- Every skill passes `npx skills-ref@0.1.5 validate`

Phase 2 explicitly does NOT deliver:

- Orchestrator state machine / CLI wiring (Phase 3)
- `agent_factory.py` (Phase 3)
- SQLite session schema or token-budget enforcement (Phase 3)
- Next.js web UI (Phase 4)
- Corpus beyond ~50 docs

</domain>

<decisions>
## Implementation Decisions

### Corpus — document selection (BRAIN-03, BRAIN-04)

**Locked:** 4 core docs + ~46 additional = ~50 total, ≤ 1000 pages (PageIndex Cloud free tier).

Core docs already ingested (Phase 1): Konstytucja RP.
Additional core docs to ingest first: Kodeks Karny (KK), Kodeks Cywilny (KC), Kodeks Pracy (KP).

**~46 additional docs by domain grouping (researcher/planner fills in specific ISAP URLs):**

| Domain | Target docs | Representative examples |
|--------|-------------|------------------------|
| Labor / social | 5 | Ustawa o minimalnym wynagrodzeniu, ustawa o urlopach rodzicielskich, ustawa o zasiłkach, ustawa o związkach zawodowych |
| Finance / tax | 6 | Ustawa o PIT, ustawa o CIT, ustawa o VAT, ustawa budżetowa (most recent), ustawa o podatku od nieruchomości, ustawa Ordynacja podatkowa |
| Health | 4 | Ustawa o świadczeniach opieki zdrowotnej finansowanych ze środków publicznych, ustawa Prawo farmaceutyczne, ustawa o ochronie zdrowia psychicznego, ustawa o zawodach lekarza |
| Justice / civil procedure | 3 | Kodeks postępowania cywilnego (KPC), Kodeks postępowania karnego (KPK), ustawa o Trybunale Konstytucyjnym |
| Climate / energy | 5 | Ustawa o odnawialnych źródłach energii (OZE), Prawo energetyczne, ustawa o efektywności energetycznej, ustawa o elektromobilności, EU Fit for 55 PL implementation act |
| Education | 3 | Ustawa Prawo oświatowe, ustawa Prawo o szkolnictwie wyższym i nauce, ustawa o systemie oświaty |
| Agriculture | 3 | Ustawa o kształtowaniu ustroju rolnego, ustawa o ubezpieczeniu społecznym rolników (KRUS), ustawa o ochronie gruntów rolnych |
| Defense / Foreign | 2 | Ustawa o obronie Ojczyzny, ustawa o cudzoziemcach |
| Digital / cyber | 3 | Ustawa o krajowym systemie cyberbezpieczeństwa, ustawa o ochronie danych osobowych (RODO implementacja PL), ustawa Prawo telekomunikacyjne |
| Infrastructure / transport | 3 | Ustawa Prawo budowlane, ustawa o transporcie drogowym, ustawa o publicznym transporcie zbiorowym |
| Other ministries | 9 | Culture: ustawa o organizowaniu i prowadzeniu działalności kulturalnej; Sport: ustawa o sporcie; Science: ustawa o Polskiej Akademii Nauk; Regional Funds: ustawa o zasadach prowadzenia polityki rozwoju; State Assets: ustawa o zasadach zarządzania mieniem państwowym; Family programs: ustawa o pomocy społecznej; Interior: ustawa o Policji, ustawa o straży granicznej; Sportu i Turystyki: ustawa o usługach turystycznych |

**Page budget discipline:** Researcher must verify page counts before ingest. If total exceeds 1000 pages, cut from "Other ministries" first, then from larger domain docs (use excerpts/chapters for KPC, KPK if needed).

**Ingest order:** Core 4 docs first (BRAIN-03 acceptance). Then by domain priority: Finance/Tax → Labor → Health → Climate → Justice → Education → remaining.

**Seeding tool:** `scripts/seed_pageindex_konstytucja.py` pattern — extend or replicate for batch ingest. Each doc needs: doc_id stored in doc_registry.py.

---

### Party SKILL.md depth (PARTY-01..05, SKILL-01..03)

**Decision: Full profiles** — ~800–1200 words per party SKILL.md.

Each party SKILL.md must contain:

1. **Identity** — party name, year founded, coalition/bloc, current leader reference (no real names of current MPs — use role title only, e.g., "party leader")
2. **Ideology** — core political values, position on left-right spectrum, key positions on economic vs social policy
3. **Electorate notes** — who votes for this party, what they care about, regional distribution
4. **Rhetorical style** — language register, preferred argument types (emotional/statistical/historical), typical phrases
5. **Sample positions on 5–8 canonical topics** — "4-day work week", "OZE expansion", "tax simplification", "immigration", "EU relations", "education reform", "healthcare privatization", "flat tax" — each 2–3 sentences
6. **Red lines** — what this party would never support and why (drives politically coherent vote outcomes in Phase 3)
7. **Output constraints** — mandatory section in every SKILL.md: "Never name real MPs. Never use slurs. Never advocate violence."

**Rationale:** Full profiles are the most important investment for demo quality — the ideological differentiation between parties is the core value proposition of the simulation.

**Frontmatter requirements (PARTY-02):**
```yaml
---
name: party-ko
description: Koalicja Obywatelska party agent for the Virtual Parliament simulation.
license: MIT
metadata:
  type: party
  ideology: liberal-center
  seats: 157
  model_tier: party
---
```

Seat counts: KO=157, PiS=194, TD=65, Konfederacja=18, Lewica=26.

---

### Ministry SKILL.md structure (MIN-01..04, SKILL-03)

**Shared template:** `skills/_template-ministry/SKILL.md` — all 19 ministries derive from it. The template defines structure; each ministry fills in domain-specific content.

Template sections:
1. **Identity** — ministry name, mandate summary, model tier (ministry → cheaper model)
2. **Expertise scope** — which domains this ministry covers (informs doc_registry filtering)
3. **Output format** (mandatory, locked by MIN-02):
   ```
   1. Legal analysis (with PageIndex citations)
   2. Budget impact
   3. Risks
   4. Technical recommendation
   ```
4. **Stateless expert stance** — "You have data, not opinions. Provide analysis, not advocacy."
5. **Output constraints** — same as parties: no real names, no hate speech

**Ministry frontmatter:**
```yaml
---
name: ministry-finansow
description: Ministry of Finance expert agent providing legal and fiscal analysis.
license: MIT
metadata:
  type: ministry
  domain: finance
  model_tier: ministry
---
```

**Wave structure for Phase 2 execution (cut plan):**

- **Wave 1 (Day 2 priority):** 7 core ministries — finansow, zdrowia, edukacji, sprawiedliwosci, klimatu-i-srodowiska, infrastruktury, spraw-zagranicznych
- **Wave 2 (Day 3 if time permits):** Remaining 12 — obrony-narodowej, rozwoju-i-technologii, rolnictwa, rodziny-pracy-i-polityki-spolecznej, cyfryzacji, kultury-i-dziedzictwa-narodowego, nauki-i-szkolnictwa-wyzszego, energii, spraw-wewnetrznych-i-administracji, aktywow-panstwowych, funduszy-i-polityki-regionalnej, sportu-i-turystyki
- **Cut trigger:** If Day 3 EOD arrives with Wave 2 incomplete, ship Wave 1 (7 ministries). Do not start Phase 3 with partial Wave 2 ministry stubs.

Wave 2 ministries get a shorter SKILL.md (~400 words, minimal but valid) if time is tight; Wave 1 ministries get full profiles.

---

### Ethics review process (PARTY-03)

**Decision: LLM-only pair review** — two separate LLM prompts with opposing political frames.

Process:
1. After writing each party SKILL.md, run two review prompts:
   - Reviewer A: "You are a progressive political analyst. Review this party profile for caricature, strawmanning, or missing nuance."
   - Reviewer B: "You are a conservative political analyst. Review this party profile for caricature, strawmanning, or missing nuance."
2. Document both review outputs in `skills/<party-id>/REVIEW.md`
3. Apply flagged corrections to the SKILL.md before committing

**This satisfies PARTY-03** in a 5-day solo project context. The REVIEW.md files serve as the audit trail for the contest jury.

---

### doc_registry.py scope (BRAIN-05)

**Decision: Registry data + filtering function.**

`parliament/doc_registry.py` delivers:
1. A dict mapping `agent_id → {"domain": str, "doc_ids": list[str], "categories": list[str]}`
2. A `get_filter(agent_id: str) -> dict` function returning the metadata filter to inject into `search_documents` calls
3. A `list_agents() -> list[str]` helper for test assertions

The filtering mechanism is: pass `folder_id` or a metadata query param to `search_documents` to restrict results to documents tagged for that ministry's domain. Exact PageIndex filter API should be confirmed by researcher (check `pageindex-mcp` tool schema for `search_documents` args).

**Why Phase 2 (not Phase 3):** The doc_registry is data, not orchestration logic. Writing it in Phase 2 alongside the skills means the ministry scope is defined while content is fresh. Phase 3 just calls `get_filter(agent_id)` — no discovery work needed.

---

### Marszałek skill (ORCH-01)

**Included in Phase 2** — the Marszałek SKILL.md is one of the 25 skills. It defines:
- Identity as orchestrator/speaker of the Sejm
- Permission to call `delegate_task` (the only agent with this permission)
- Ministry selection decision logic (conceptual — actual implementation is Phase 3)
- Output format for session documents

Marszałek frontmatter:
```yaml
---
name: marszalek-sejmu
description: Marszałek Sejmu orchestrator — manages ministry consultations, party debate, and vote tallying.
license: MIT
metadata:
  type: orchestrator
  model_tier: orchestrator
---
```

---

### Skills validation (SKILL-01)

All 25 skills must pass `npx skills-ref@0.1.5 validate skills/<id>` before Phase 2 is marked complete. CI hook is already wired (Phase 1). The validation gate is the acceptance criterion, not a post-phase check.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents (planner, executor) MUST read these before planning or implementing.**

### Project planning artifacts
- `.planning/ROADMAP.md` — Phase 2 section with cut criteria
- `.planning/REQUIREMENTS.md` — SKILL-01..03, PARTY-01..05, MIN-01..04, BRAIN-03..05, ETHICS-02..04, LANG-01..03
- `.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md` — Phase 1 locked decisions (stack, Python 3.11, PageIndex Cloud, doc seeding pattern)
- `./CLAUDE.md` — Recommended Stack table, What NOT to Use table

### Existing codebase assets (reuse in Phase 2)
- `parliament/second_brain/pageindex_client.py` — MCP client for PageIndex; search_documents, get_page_content, browse_documents
- `scripts/seed_pageindex_konstytucja.py` — REST API seeding pattern; replicate for batch ingest
- `skills/party-ko/SKILL.md` — existing stub (overwrite with full profile in Phase 2)
- `parliament/guards.py` — TokenBudget interface (do not modify in Phase 2)
- `data/konstytucja.pdf` — already downloaded; other PDFs need ISAP URLs

### External references
- `https://agentskills.io/specification` — SKILL.md frontmatter schema (name, description required; metadata optional)
- `https://isap.sejm.gov.pl` — Polish legal document source for PDF downloads
- `https://github.com/mmtmr/pageindex-rag` — the RAG skill already installed globally
- `pageindex-mcp` tool schema — check `search_documents` args for metadata filter params

</canonical_refs>

<specifics>
## Specific Implementation Notes

### Recommended execution order for Phase 2 plans

1. **Plan 02-01: Core corpus ingest** — KK, KC, KP + first batch of domain docs. Validates ingest pipeline before writing skills.
2. **Plan 02-02: Ministry template + Wave 1 ministries** — `_template-ministry` + 7 Wave 1 ministries + `doc_registry.py`.
3. **Plan 02-03: Party skills** — All 5 party SKILL.md files + LLM-pair ethics review + REVIEW.md files.
4. **Plan 02-04: Wave 2 ministries** — Remaining 12 ministry SKILL.md files (minimal if time-constrained).
5. **Plan 02-05: Marszałek skill + full validation** — `marszalek-sejmu/SKILL.md` + `skills-ref validate` all 25 + Phase 2 acceptance test.

### Corpus page budget math

Target: ≤ 1000 pages total including Konstytucja (~110 pages already used).
Remaining budget: ~890 pages for ~46 docs.
Average: ~19 pages/doc — achievable for most Polish statute excerpts.
If any single doc exceeds 50 pages, use the `pages` param to ingest key chapters only (e.g., KPC general provisions + Title VII, not all 1300 articles).

### Ministry name→skill-id mapping

| Ministry | skill-id |
|----------|---------|
| Finansów | ministry-finansow |
| Zdrowia | ministry-zdrowia |
| Edukacji | ministry-edukacji |
| Sprawiedliwości | ministry-sprawiedliwosci |
| Obrony Narodowej | ministry-obrony-narodowej |
| Spraw Zagranicznych | ministry-spraw-zagranicznych |
| Klimatu i Środowiska | ministry-klimatu-i-srodowiska |
| Infrastruktury | ministry-infrastruktury |
| Rozwoju i Technologii | ministry-rozwoju-i-technologii |
| Rolnictwa | ministry-rolnictwa |
| Rodziny, Pracy i Polityki Społecznej | ministry-rodziny-pracy-i-polityki-spolecznej |
| Cyfryzacji | ministry-cyfryzacji |
| Kultury i Dziedzictwa Narodowego | ministry-kultury-i-dziedzictwa-narodowego |
| Nauki i Szkolnictwa Wyższego | ministry-nauki-i-szkolnictwa-wyzszego |
| Energii | ministry-energii |
| Spraw Wewnętrznych i Administracji | ministry-spraw-wewnetrznych-i-administracji |
| Aktywów Państwowych | ministry-aktywow-panstwowych |
| Funduszy i Polityki Regionalnej | ministry-funduszy-i-polityki-regionalnej |
| Sportu i Turystyki | ministry-sportu-i-turystyki |

### Gate-style acceptance criteria for Phase 2

| Criterion | Test |
|-----------|------|
| All 25 skills validate | `npx skills-ref@0.1.5 validate skills/` exits 0 |
| Party divergence | Run "4-day work week" prompt through party-ko and party-konfederacja in isolation → visibly opposing positions, ≥1 PageIndex node_id per response |
| Ministry filtering | `pytest tests/test_brain_05_doc_registry.py` — asserts Finance doesn't return health docs |
| Corpus ingested | `browse_documents(folder_id="root")` returns ≥ 4 docs; `search_documents("konstytucja")` and `search_documents("kodeks karny")` each return results |
| Ethics review trail | `ls skills/party-*/REVIEW.md` returns 5 files |

</specifics>

<deferred>
## Deferred Ideas

- **Full 1300-article KPC/KPK ingest** — page budget won't allow it; ingest key chapters/excerpts only
- **Per-ministry test for all 19** — Phase 2 tests only the registry data structure; full per-ministry validation is Phase 3 integration test
- **STR-01 party long-term memory** — deferred to Phase 3/4 stretch; not in Phase 2 scope
- **Marszałek orchestration logic** — SKILL.md only in Phase 2; state machine and `delegate_task` wiring is Phase 3
- **GATE-06 re-run** — party-ko stub already passes; Phase 2 overwrites it with full profile but doesn't re-run the gate explicitly (skills-ref validate covers it)

</deferred>

---

*Phase: 02-agent-skills-corpus*
*Context gathered: 2026-05-26 via gsd-discuss-phase*

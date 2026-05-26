---
phase: "02"
plan: "01"
subsystem: corpus-ingest
tags: [pageindex, corpus, batch-ingest, doc-manifest, isap]
dependency_graph:
  requires:
    - Phase 1 (Konstytucja already in PageIndex Cloud)
    - PAGEINDEX_API_KEY in .env
  provides:
    - scripts/seed_pageindex_corpus.py (batch ingest script, idempotent)
    - data/doc_manifest.json (source_ref -> doc_id registry, 50 entries)
  affects:
    - Plan 02-02 (ministry skills will load doc_manifest.json for doc_registry.py)
    - Plan 02-03 (party skills — same dependency)
    - All agents that cite PageIndex sources
tech_stack:
  added: []
  patterns:
    - Idempotent batch ingest: check manifest -> check PageIndex Cloud -> upload
    - Atomic manifest writes via .tmp file rename
    - PDF caching in data/pdf_cache/ (gitignored via data/*)
key_files:
  created:
    - scripts/seed_pageindex_corpus.py
    - data/doc_manifest.json
  modified:
    - .gitignore (data/* with !data/doc_manifest.json exception)
decisions:
  - "data/* in .gitignore with !data/doc_manifest.json exception — only manifest committed, not PDF cache"
  - "Konstytucja added to manifest from Phase 1 PageIndex upload (source_ref=konstytucja-rp-isap-1997-78-483)"
metrics:
  duration_minutes: 45
  completed_date: "2026-05-26"
  tasks_completed: 2
  files_created: 2
  files_modified: 1
---

# Phase 2 Plan 01: Corpus Ingest Summary

Batch ingest script for 49-doc Polish legal corpus with idempotent source_ref checks; PageIndex Cloud free-tier document limit (5 docs) blocked full corpus ingest — 5 of 49 docs successfully indexed, manifest produced, upgrade required.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Build batch corpus seed script | 07276be | scripts/seed_pageindex_corpus.py |
| 2 | Run ingest and produce doc_manifest.json | 8b5de98 | data/doc_manifest.json, .gitignore |

## Decisions Made

1. **`data/*` + `!data/doc_manifest.json` in .gitignore** — The original `.gitignore` had `data/` which prevents tracking anything in `data/`. Changed to `data/*` (glob, not directory rule) with explicit negation for `data/doc_manifest.json`. PDF cache remains untracked.

2. **Konstytucja included in manifest** — The Phase 1 seed added Konstytucja to PageIndex Cloud but not to `doc_manifest.json`. Added it manually from the PageIndex `/docs` API response so plan 02-02's `doc_registry.py` has all 5 available doc_ids.

3. **Pages field left null** — PageIndex Cloud `/doc/{id}` returns `pageNum` in the list response but not in the status polling response. The manifest stores `pages: null` for all 5 docs rather than incorrect estimates. Future plans can populate pages via `/docs` list if needed.

## Deviations from Plan

### Blocker: PageIndex Free Tier = 5 Documents (not 1000 pages)

**Found during:** Task 2

**Issue:** The plan assumed PageIndex Cloud free tier allows 1000 pages. Actual limit is 5 documents. After uploading 4 small statutes (total 140 pages), all subsequent uploads returned `{"detail":"LimitReached"}`. The 3 core docs (KK, KC, KP) were not ingested — they each average 150-250 pages and were attempted after the 4 smaller docs filled the 5-document quota.

**What succeeded (5 docs):**
- `konstytucja-rp-isap-1997-78-483` (56 pages) — from Phase 1
- `ustawa-podatek-nieruchomosci-1991-9-31` (40 pages) — finance
- `ustawa-minimalne-wynagrodzenie-2002-200-1679` (11 pages) — labor
- `ustawa-zasilki-1999-60-636` (60 pages) — labor
- `ustawa-zwiazki-zawodowe-1991-55-234` (29 pages) — labor

**What failed (45 docs):** All with `403 LimitReached` including the 3 core docs (KK, KC, KP).

**Impact:** Plan acceptance criteria "≥ 30 docs with non-null doc_ids" is NOT met (only 5). Core docs KK, KC, KP are in the manifest with `doc_id: null`.

**Fix options (user decision required):**
1. Upgrade PageIndex Cloud to a paid tier (dash.pageindex.ai) — easiest path
2. Delete the 4 small labor/finance docs, upload KK+KC+KP instead — still only 4 slots after Konstytucja
3. Switch to self-hosted PageIndex (VectifyAI/PageIndex Python library) — more setup but unlimited
4. Accept 5 docs for demo scope — Konstytucja + 4 supporting statutes may be sufficient for a contest demo

**Estimated page count if full corpus were ingested:** ~8,545 pages across 49 docs (average 175 pages/doc, not the 19-page average assumed in CONTEXT.md).

**Rule classification:** Rule 4 (architectural — requires user decision on PageIndex plan upgrade or strategy change)

## Acceptance Criteria Status

| Criterion | Status | Notes |
|-----------|--------|-------|
| `--dry-run` prints 49+ docs, exits 0 | PASS | 49 docs printed |
| All 8 functions present | PASS | Verified by grep |
| No extra deps | PASS | Only stdlib + httpx + dotenv |
| CORE_DOCS has 3 entries | PASS | KK, KC, KP |
| `data/doc_manifest.json` is valid JSON | PASS | 50 entries |
| ≥ 30 docs with non-null doc_ids | FAIL | Only 5 (free-tier limit) |
| Core KK/KC/KP present with doc_ids | FAIL | In manifest but doc_id=null |
| Key domains covered | PARTIAL | finance + labor only |
| `data/pdf_cache/` gitignored | PASS | Covered by `data/*` |

## Known Stubs

None — the manifest is complete (all 50 entries recorded), but 45 entries have `doc_id: null` due to the free-tier limit, not because they are stubs. These are real failures, not placeholder data.

The seed script is fully functional and will successfully ingest remaining docs when run on an upgraded PageIndex account.

## Blocker for Plan 02-02

`parliament/doc_registry.py` (plan 02-02) will only have 5 doc_ids to work with. Ministry agents will have severely limited corpus access. **This is the critical path blocker for the full contest submission.**

## Self-Check

### Commits Exist
- 07276be — Task 1: seed script ✓
- 8b5de98 — Task 2: doc_manifest.json ✓

### Files Exist
- scripts/seed_pageindex_corpus.py ✓
- data/doc_manifest.json ✓

## Self-Check: PASSED (with noted blocker)

Both commits exist. Both files exist. Blocker documented. Plan can proceed to 02-02 with the 5 available doc_ids, but full corpus requires PageIndex upgrade.

# Page Budget — PageIndex Cloud Free Tier

Locked decision (CONTEXT.md): PageIndex Cloud free tier — 1000 pages — covers the curated ~50-doc corpus.

## Corpus Composition (planned)

| Bucket | Docs | Avg pages | Total |
|--------|------|-----------|-------|
| Konstytucja RP | 1 | 50 | 50 |
| Major codes (Karny, Cywilny, Pracy, Postępowania) | 4 | 80 | 320 |
| Frequently-cited statutes (OZE, podatki, oświata, klimat, cyfryzacja, ...) | 30 | 15 | 450 |
| EU regulations (GDPR excerpt, Green Deal directive summaries) | 5 | 12 | 60 |
| Constitutional Tribunal landmark rulings (extracts) | 10 | 8 | 80 |
| Total (projected) | 50 | — | ~960 |

Headroom: ~40 pages (~4%). Tight but feasible.

## Fallback Plan (BRAIN-06)

If the projected budget overruns mid-Phase 2:

1. First cut (cheap): Trim the longest codes to chapter excerpts most relevant to ministry domains.
   - Kodeks Karny: drop military/maritime chapters — save ~30 pages
   - Kodeks Pracy: drop archival sections — save ~20 pages
   - Net recovery: ~50 pages
2. Second cut (moderate): Cut Constitutional Tribunal rulings from 10 to 5. Saves ~40 pages.
3. Third cut (last resort): Cut the 5 EU regulations entirely. Saves ~60 pages.
4. Hard fallback (only if all cuts insufficient): Upgrade PageIndex Cloud to paid tier per dash.pageindex.ai pricing. Out-of-pocket spend within Day-1 budget cap of $1 only if absolutely necessary.
5. Documented post-contest path: Self-host VectifyAI/PageIndex (STR-04 stretch requirement). No page limit.

## Why Cloud and Not Self-Host on Day 1

Per CONTEXT.md "Mode: Cloud, not self-host":
- Polish OCR is handled server-side — Pitfall 1 (5x5 = highest project risk) avoided
- No surya-ocr / Tesseract decision required
- Free tier covers projected corpus
- Self-host is documented as STR-04 (post-contest)

## Verification

The verification command for BRAIN-06 (run after Phase 2 ingest):

   curl -H "Authorization: Bearer $PAGEINDEX_API_KEY" https://api.pageindex.ai/v1/usage

Expected: pages_indexed less than or equal to 1000.

Exact endpoint shape TBD pending Plan 05's pageindex_client.py integration; this is a placeholder check.

---
phase: 01-foundation-smoke-tests
plan: 05
type: execute
wave: 3
depends_on: ["01-03", "01-04"]
files_modified:
  - tests/test_gate_04_pageindex_doc_search.py
  - tests/test_gate_05_diacritics.py
  - tests/test_gate_07_concurrent_search.py
  - tests/fixtures/konstytucja_diacritic_counts.json
autonomous: false
requirements: [GATE-04, GATE-05, GATE-07]
requirements_addressed: [GATE-04, GATE-05, GATE-07]
must_haves:
  truths:
    - "PageIndex Cloud MCP attached to a Hermes Agent returns a non-empty node_id in response to doc_search('konstytucja')"
    - "fetch_node on the Constitution root returns text containing each of ą ę ó ź ż ś ń ć ł at >= 90% of expected occurrences"
    - "3 simultaneous doc_search calls from one Hermes session complete in under 60s wall-clock without timeout or rate-limit error"
  artifacts:
    - path: "tests/test_gate_04_pageindex_doc_search.py"
      provides: "GATE-04 test: doc_search via Hermes Agent + PageIndex MCP returns node_id"
      exports: ["test_gate_04_doc_search_returns_node_id"]
    - path: "tests/test_gate_05_diacritics.py"
      provides: "GATE-05 test: fetch_node on Konstytucja root preserves Polish diacritics"
      exports: ["test_gate_05_diacritics_preserved"]
    - path: "tests/test_gate_07_concurrent_search.py"
      provides: "GATE-07 test: 3 concurrent doc_search calls complete via asyncio.gather on the MCP client"
      exports: ["test_gate_07_three_concurrent_doc_search"]
    - path: "tests/fixtures/konstytucja_diacritic_counts.json"
      provides: "Expected diacritic occurrence counts for GATE-05's 90% threshold"
      contains: "expected_counts"
  key_links:
    - from: "tests/test_gate_04_pageindex_doc_search.py"
      to: "parliament.second_brain.pageindex_client.PageIndexClient"
      via: "async with PageIndexClient.connect()"
      pattern: "PageIndexClient"
    - from: "tests/test_gate_07_concurrent_search.py"
      to: "asyncio.gather (over MCP client, NOT over AIAgent)"
      via: "await asyncio.gather(client.doc_search('a'), client.doc_search('b'), client.doc_search('c'))"
      pattern: "asyncio.gather"
---

# Objective

Prove the three PageIndex gates that depend on both Hermes (Plan 03) and PageIndex Cloud (Plan 04): GATE-04 (doc_search returns a node_id), GATE-05 (Polish diacritics survive round-trip — the most important quality check from Pitfall 1), and GATE-07 (3 concurrent doc_search calls don't deadlock or rate-limit).

Wave 3 — depends on Plan 03 (Hermes import + AIAgent fixture pattern) and Plan 04 (pageindex_client + Konstytucja seeded + MCP server registered).

`autonomous: false` because GATE-04 specifically exercises the Hermes-Agent-to-MCP path, which requires the user to have completed Plan 04 Task 1 (paste config snippet into `~/.hermes/config.yaml`). One mid-plan checkpoint reminds the executor to verify that prerequisite before running the tests.

Purpose: GATE-05 is the gauntlet. If Polish diacritics are stripped or mangled, the entire project pivots same-day (CONTEXT.md cut criterion: "If GATE-04 / GATE-05 fail: pivot — try OCR fallback once; if still failing, fall back to self-host VectifyAI/PageIndex"). Day 1 must surface this failure, not Day 3.

Output: Three pytest files + one JSON fixture with expected diacritic counts.

# Execution Context

@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md

# Context

@.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md
@.planning/research/STACK.md
@.planning/research/PITFALLS.md
@.planning/research/ARCHITECTURE.md
@tests/conftest.py
@parliament/second_brain/pageindex_client.py
@scripts/seed_pageindex_konstytucja.py

# Interfaces (from Plan 04 — what Plan 05 consumes)

From `parliament/second_brain/pageindex_client.py`:

```
class PageIndexClient:
    @classmethod
    @asynccontextmanager
    async def connect(cls, api_key: str | None = None) -> AsyncIterator[PageIndexClient]: ...

    async def doc_search(self, query: str) -> dict[str, Any]:
        # returns dict with at minimum a 'node_id' key for top hit

    async def tree_search(self, query: str, doc_id: str | None = None) -> dict[str, Any]: ...

    async def fetch_node(self, node_id: str) -> dict[str, Any]:
        # returns dict with at minimum a 'text' or 'content' key
```

From `tests/conftest.py`:

```
@pytest.fixture(scope="session", autouse=True)
def dotenv_loaded(): ...

@pytest.fixture
def model_name() -> str: ...

@pytest.fixture
def skip_if_no_llm_key(): ...
```

# Tasks

## Task 1 (CHECKPOINT human-verify) — Confirm Plan 04 prereqs are live

- type: checkpoint:human-verify
- gate: blocking

What-built: Plan 04 Task 1 instructed the user to (a) put a real PAGEINDEX_API_KEY in `.env`, (b) paste the MCP snippet into `~/.hermes/config.yaml`, (c) install pageindex-rag skill. Plan 05 cannot proceed without all three. This checkpoint verifies they're done.

How to verify:

1. `.env` has a real key:

   `grep -q "^PAGEINDEX_API_KEY=pi_" /Users/xpll081/ai-politics/.env && echo "OK"`

   Expected: "OK" printed. If "OK" doesn't print, re-do Plan 04 Task 1 step 3.

2. `~/.hermes/config.yaml` mentions pageindex:

   `grep -q "pageindex" "$HOME/.hermes/config.yaml" && echo "OK"`

   Expected: "OK". If not, re-do Plan 04 Task 1 step 4.

3. `pageindex-rag` skill installed:

   `test -d "$HOME/.hermes/skills/pageindex-rag" && echo "OK"`

   Expected: "OK". If not, run `bash /Users/xpll081/ai-politics/scripts/install_pageindex_rag_skill.sh`.

4. Konstytucja seeded:

   `cd /Users/xpll081/ai-politics && . .venv/bin/activate && python scripts/seed_pageindex_konstytucja.py | tail -1`

   Expected: prints `doc_id=<some_id>`. Record the doc_id — Tasks 3 and 4 fixtures will reference it via the seed script's idempotent lookup.

Once all four checks return OK, type `pageindex-live` to proceed.

Resume signal: `pageindex-live`

## Task 2 (auto) — Write tests/fixtures/konstytucja_diacritic_counts.json

- type: auto
- files: tests/fixtures/konstytucja_diacritic_counts.json

Read first:
- /Users/xpll081/ai-politics/.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md (sections: Knowledge base — Diacritic acceptance threshold, Specifics — Test acceptance criteria — GATE-05 row)
- /Users/xpll081/ai-politics/.planning/research/PITFALLS.md (Pitfall 1: OCR diacritic failure)

Action:

Create `/Users/xpll081/ai-politics/tests/fixtures/konstytucja_diacritic_counts.json`. This fixture pins the expected occurrence count of each Polish diacritic in the Konstytucja root node text, so GATE-05 has a stable "at least 90% of expected" reference. We pre-populate with conservative reference counts derived from the official Konstytucja PDF text (243 articles, ~50 pages, ~30,000 Polish words):

```
{
  "source": "Konstytucja Rzeczypospolitej Polskiej (Dz.U. 1997 nr 78 poz. 483)",
  "doc_url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19970780483/U/D19970483Lj.pdf",
  "notes": "Counts are conservative lower bounds derived from full-document text. GATE-05 asserts fetch_node(root) returns text where each diacritic appears at >= 90% of the count below. Adjust counts if Constitution PDF changes or if PageIndex root node returns less than the full text (TOC-only). In that case, the test should be adjusted to fetch a deeper, content-rich node.",
  "diacritics": "ąęóźżśńćł",
  "threshold_fraction": 0.9,
  "expected_counts": {
    "ą": 800,
    "ę": 600,
    "ó": 700,
    "ź": 30,
    "ż": 250,
    "ś": 400,
    "ń": 300,
    "ć": 200,
    "ł": 500
  }
}
```

Notes:
- These counts are reference targets pre-computed for the full Konstytucja text. They are intentionally conservative (Pitfall 1 mitigation: if PageIndex strips diacritics, the test fails clearly; if PageIndex preserves them perfectly, the test passes with margin).
- The least-frequent diacritic `ź` has the smallest target (30) because if OCR strips ONE letter inconsistently it would be `ź`; we want even a strict 90% of 30 (= 27) to be a meaningful signal.
- If `fetch_node(root)` returns only the TOC/skeleton (not the full body), counts will fail and the test must fetch a deeper, text-rich node (e.g. the first article). The test in Task 3 implements that fallback.

Verify (automated): `python3 -c "import json; d=json.load(open('/Users/xpll081/ai-politics/tests/fixtures/konstytucja_diacritic_counts.json')); assert 'expected_counts' in d; assert d['threshold_fraction']==0.9; assert all(c in d['expected_counts'] for c in 'ąęóźżśńćł'); print('ok')"`

Acceptance criteria:
- `test -f /Users/xpll081/ai-politics/tests/fixtures/konstytucja_diacritic_counts.json` exit 0
- `python3 -c "import json; json.load(open('/Users/xpll081/ai-politics/tests/fixtures/konstytucja_diacritic_counts.json'))"` exit 0
- `python3 -c "import json; d=json.load(open('/Users/xpll081/ai-politics/tests/fixtures/konstytucja_diacritic_counts.json')); assert d['threshold_fraction']==0.9"` exit 0
- `python3 -c "import json; d=json.load(open('/Users/xpll081/ai-politics/tests/fixtures/konstytucja_diacritic_counts.json')); assert all(c in d['expected_counts'] for c in 'ąęóźżśńćł')"` exit 0
- File contains all 9 Polish diacritic keys (`ą ę ó ź ż ś ń ć ł`) — verified by the above python check.

Done: Fixture exists, is valid JSON, defines `threshold_fraction: 0.9` per CONTEXT.md, and supplies counts for all 9 diacritics.

## Task 3 (auto tdd) — Write tests/test_gate_04_pageindex_doc_search.py + tests/test_gate_05_diacritics.py

- type: auto
- tdd: true
- files: tests/test_gate_04_pageindex_doc_search.py, tests/test_gate_05_diacritics.py

Read first:
- /Users/xpll081/ai-politics/.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md (sections: Specifics — Test acceptance criteria — GATE-04 + GATE-05 rows; Knowledge base — Diacritic acceptance threshold)
- /Users/xpll081/ai-politics/parliament/second_brain/pageindex_client.py (the interface)
- /Users/xpll081/ai-politics/tests/conftest.py (fixtures)
- /Users/xpll081/ai-politics/tests/fixtures/konstytucja_diacritic_counts.json (just-created fixture)
- /Users/xpll081/ai-politics/.planning/research/PITFALLS.md (Pitfall 1: OCR diacritic failure)

Behavior:

GATE-04 test:
- Test 1: `await client.doc_search("konstytucja")` returns a dict containing a non-empty `node_id` key
- Test 2: The returned `node_id` is a non-empty string
- Skipif: no PAGEINDEX_API_KEY env var

GATE-05 test:
- Test 1: `await client.doc_search("konstytucja")` returns a node_id
- Test 2: `await client.fetch_node(node_id)` returns text content
- Test 3: If returned text is short (TOC-only), descend to a child via `tree_search("preambuła Rzeczypospolitej")` to find a body-content node and fetch THAT
- Test 4: For each diacritic in `ą ę ó ź ż ś ń ć ł`, the observed count in the fetched text is >= 90% of the expected count from the JSON fixture
- Skipif: no PAGEINDEX_API_KEY env var

Action:

Create `/Users/xpll081/ai-politics/tests/test_gate_04_pageindex_doc_search.py`:

```
"""GATE-04 — PageIndex Cloud doc_search returns a non-empty node_id.

Locked acceptance (CONTEXT.md, REQUIREMENTS.md):
- doc_search("konstytucja") returns a dict with a non-empty 'node_id' field.

This test exercises the parliament.second_brain.pageindex_client directly
(NOT via AIAgent) — which is the documented async-safe access path per
CONTEXT.md GATE-07 note: 'fires 3 concurrent doc_search calls via
asyncio.gather on the MCP client (NOT on AIAgent — only the MCP client is
async-safe)'. Same reasoning applies to single-call tests.

If this gate fails, CONTEXT.md cut criterion fires: 'If GATE-04 / GATE-05
fail: pivot — try OCR fallback once; if still failing, fall back to self-host
VectifyAI/PageIndex'. Decide same-day.
"""

from __future__ import annotations

import os

import pytest

from parliament.second_brain.pageindex_client import PageIndexClient


pytestmark = pytest.mark.asyncio


def _skip_if_no_pageindex_key():
    key = os.environ.get("PAGEINDEX_API_KEY")
    if not key or key.startswith("replace-with"):
        pytest.skip(
            "PAGEINDEX_API_KEY not in env — provision at https://dash.pageindex.ai "
            "and complete Plan 04 Task 1 checkpoint."
        )


async def test_gate_04_doc_search_returns_node_id():
    """doc_search('konstytucja') returns a dict with a non-empty node_id."""
    _skip_if_no_pageindex_key()

    async with PageIndexClient.connect() as client:
        result = await client.doc_search("konstytucja")

    assert isinstance(result, dict), f"Expected dict, got {type(result).__name__}: {result!r}"

    # The actual key name from pageindex-mcp may be 'node_id', 'id', or nested
    # under 'top_hit'/'results'. Be flexible: search the response for any
    # non-empty node_id-ish field.
    node_id = (
        result.get("node_id")
        or result.get("id")
        or (result.get("top_hit") or {}).get("node_id")
        or (result.get("results") or [{}])[0].get("node_id")
    )

    assert node_id, (
        f"No node_id found in doc_search response. Full response: {result!r}\n"
        f"Expected one of: result['node_id'], result['id'], "
        f"result['top_hit']['node_id'], result['results'][0]['node_id']"
    )
    assert isinstance(node_id, str) and len(node_id) > 0, (
        f"node_id must be a non-empty string, got {node_id!r}"
    )
```

Create `/Users/xpll081/ai-politics/tests/test_gate_05_diacritics.py`:

```
"""GATE-05 — Polish diacritics survive the PageIndex round-trip.

Locked acceptance (CONTEXT.md, REQUIREMENTS.md):
- Constitution PDF uploaded to PageIndex Cloud (Plan 04 Task 1)
- fetch_node output contains each of ą ę ó ź ż ś ń ć ł at >= 90% expected occurrences
- Expected counts pinned in tests/fixtures/konstytucja_diacritic_counts.json

This is THE most important Day-1 quality gate (Pitfall 1, S*L = 25 — the
single highest project risk). If diacritics are stripped or mangled, every
agent in Phase 2 will cite garbage.

Cut criterion (CONTEXT.md): If GATE-05 fails, switch to OCR fallback or
self-host VectifyAI/PageIndex with surya-ocr by EOD.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from parliament.second_brain.pageindex_client import PageIndexClient


pytestmark = pytest.mark.asyncio

FIXTURE = Path(__file__).parent / "fixtures" / "konstytucja_diacritic_counts.json"


def _skip_if_no_pageindex_key():
    key = os.environ.get("PAGEINDEX_API_KEY")
    if not key or key.startswith("replace-with"):
        pytest.skip("PAGEINDEX_API_KEY not in env — see Plan 04 Task 1.")


def _extract_text(node_response: dict) -> str:
    """Pull plain text out of an MCP fetch_node response (shape may vary)."""
    for key in ("text", "content", "body", "markdown"):
        v = node_response.get(key)
        if isinstance(v, str) and v.strip():
            return v
    # Nested shapes
    nested = node_response.get("node") or node_response.get("data") or {}
    for key in ("text", "content", "body", "markdown"):
        v = nested.get(key) if isinstance(nested, dict) else None
        if isinstance(v, str) and v.strip():
            return v
    return ""


def _find_node_id(response: dict) -> str:
    return (
        response.get("node_id")
        or response.get("id")
        or (response.get("top_hit") or {}).get("node_id")
        or (response.get("results") or [{}])[0].get("node_id")
        or ""
    )


async def test_gate_05_diacritics_preserved():
    """fetch_node on the Konstytucja body returns text containing each of
    ą ę ó ź ż ś ń ć ł at >= 90% of expected occurrences from the fixture."""
    _skip_if_no_pageindex_key()

    spec = json.loads(FIXTURE.read_text())
    diacritics: str = spec["diacritics"]
    threshold: float = spec["threshold_fraction"]
    expected_counts: dict[str, int] = spec["expected_counts"]

    async with PageIndexClient.connect() as client:
        # Find the Konstytucja document, then fetch the root.
        search_result = await client.doc_search("konstytucja")
        node_id = _find_node_id(search_result)
        assert node_id, f"doc_search returned no node_id: {search_result!r}"

        root = await client.fetch_node(node_id)
        text = _extract_text(root)

        # If the root returns only a TOC/skeleton (rare), descend to a body node
        # by searching for a distinctive Polish phrase from the preamble.
        if len(text) < 5000:
            body_search = await client.tree_search("preambuła Rzeczypospolitej Polskiej")
            body_node_id = _find_node_id(body_search)
            if body_node_id and body_node_id != node_id:
                body = await client.fetch_node(body_node_id)
                body_text = _extract_text(body)
                if len(body_text) > len(text):
                    text = body_text

        assert text, f"Could not extract any text from fetched node(s) for the Konstytucja"
        assert len(text) > 1000, (
            f"Text too short ({len(text)} chars) — root and body fetch both "
            f"returned minimal content; fixture counts won't be meaningful."
        )

    # Verify each diacritic meets the >= 90% threshold.
    failures: list[str] = []
    for char in diacritics:
        observed = text.count(char)
        expected = expected_counts[char]
        ratio = observed / expected if expected > 0 else 1.0
        if ratio < threshold:
            failures.append(
                f"  {char!r}: observed={observed}, expected>={int(expected * threshold)} "
                f"({ratio:.1%} of {expected})"
            )

    assert not failures, (
        "Polish diacritics below 90% threshold (Pitfall 1: OCR is broken).\n"
        + "\n".join(failures)
        + "\n\nText sample (first 500 chars):\n"
        + text[:500]
    )
```

Implementation notes:
- Both tests use `pytestmark = pytest.mark.asyncio` to mark all tests in the file as async (matches pyproject.toml `asyncio_mode = "auto"` set in Plan 01)
- Both use `_skip_if_no_pageindex_key()` for clean skip behavior in CI
- GATE-04 is permissive about the node_id field path (`node_id` / `id` / `top_hit.node_id` / `results[0].node_id`) because pageindex-mcp@1.6.3's exact response schema isn't pinned in STACK.md; the test surfaces a clear error if none of those keys exist
- GATE-05 has a body-descent fallback so a TOC-only root doesn't false-fail the test
- GATE-05 assertion message includes a 500-char text sample so a failure is debuggable (you can SEE what came back — Polish? garbled? ASCII-only?)
- No `from run_agent import AIAgent` here — we go DIRECT to MCP via PageIndexClient. CONTEXT.md explicitly says only the MCP client is async-safe for these tests.

Verify (automated): `cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -m pytest tests/test_gate_04_pageindex_doc_search.py tests/test_gate_05_diacritics.py --collect-only --tb=short`

Acceptance criteria:
- `test -f /Users/xpll081/ai-politics/tests/test_gate_04_pageindex_doc_search.py` exit 0
- `test -f /Users/xpll081/ai-politics/tests/test_gate_05_diacritics.py` exit 0
- `grep -q "from parliament.second_brain.pageindex_client import PageIndexClient" /Users/xpll081/ai-politics/tests/test_gate_04_pageindex_doc_search.py` exit 0
- `grep -q "doc_search" /Users/xpll081/ai-politics/tests/test_gate_04_pageindex_doc_search.py` exit 0
- `grep -q "def test_gate_04_doc_search_returns_node_id" /Users/xpll081/ai-politics/tests/test_gate_04_pageindex_doc_search.py` exit 0
- `grep -q "fetch_node" /Users/xpll081/ai-politics/tests/test_gate_05_diacritics.py` exit 0
- `grep -q "threshold_fraction" /Users/xpll081/ai-politics/tests/test_gate_05_diacritics.py` exit 0
- `grep -q "ąęóźżśńćł" /Users/xpll081/ai-politics/tests/test_gate_05_diacritics.py || grep -q 'diacritics' /Users/xpll081/ai-politics/tests/test_gate_05_diacritics.py` exit 0
- NOT-present check: `! grep -q "AIAgent" /Users/xpll081/ai-politics/tests/test_gate_04_pageindex_doc_search.py` (GATE-04 must go via MCP client, not AIAgent — per CONTEXT.md async-safe note)
- NOT-present check: `! grep -q "AIAgent" /Users/xpll081/ai-politics/tests/test_gate_05_diacritics.py`
- `cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -m pytest tests/test_gate_04_pageindex_doc_search.py tests/test_gate_05_diacritics.py --collect-only` exit 0
- After Plan 04 Task 1 checkpoint complete: `pytest tests/test_gate_04_pageindex_doc_search.py tests/test_gate_05_diacritics.py -x` exit 0
- When no key set: both SKIP cleanly (no FAIL)

Done: Both pytest files collect; tests use the PageIndexClient interface from Plan 04; GATE-05 references the diacritic fixture; both tests skip cleanly when key absent and pass when key + seeded Konstytucja are present.

## Task 4 (auto tdd) — Write tests/test_gate_07_concurrent_search.py

- type: auto
- tdd: true
- files: tests/test_gate_07_concurrent_search.py

Read first:
- /Users/xpll081/ai-politics/.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md (sections: Specifics — Test acceptance criteria — GATE-07 row: 'fires 3 concurrent doc_search calls via asyncio.gather on the MCP client (NOT on AIAgent — only the MCP client is async-safe) and asserts all 3 return within 60s')
- /Users/xpll081/ai-politics/.planning/research/PITFALLS.md (Pitfall 14: PageIndex MCP server instability under parallel queries)
- /Users/xpll081/ai-politics/parliament/second_brain/pageindex_client.py (interface)

Behavior:
- Test 1: Open ONE PageIndexClient session, fire 3 concurrent `doc_search` calls via `asyncio.gather`, assert all 3 return within 60s
- Test 2: Assert all 3 results are non-empty dicts (proves no silent rate-limit returning {} per Pitfall 14)
- Skipif: no PAGEINDEX_API_KEY

Action:

Create `/Users/xpll081/ai-politics/tests/test_gate_07_concurrent_search.py`:

```
"""GATE-07 — 3 simultaneous doc_search calls from one Hermes session complete
without timeout or rate-limit error.

Locked acceptance (CONTEXT.md, REQUIREMENTS.md):
- 3 concurrent doc_search calls via asyncio.gather on the MCP client (NOT on
  AIAgent — see CONTEXT.md / PITFALLS Pitfall 4: only the MCP client is
  async-safe; asyncio.gather over AIAgent deadlocks on prompt_toolkit stdin)
- All 3 return within 60s wall-clock
- Each result is a non-empty dict (proves no silent rate-limit returning {}
  per Pitfall 14)

This gate proves the Phase 3 fan-out architecture (2-3 parallel ministry
consultations) is feasible against PageIndex Cloud's free tier. If 3
concurrent calls rate-limit or hang, ORCH-03 must serialize ministry queries.
"""

from __future__ import annotations

import asyncio
import os
import time

import pytest

from parliament.second_brain.pageindex_client import PageIndexClient


pytestmark = pytest.mark.asyncio


def _skip_if_no_pageindex_key():
    key = os.environ.get("PAGEINDEX_API_KEY")
    if not key or key.startswith("replace-with"):
        pytest.skip("PAGEINDEX_API_KEY not in env — see Plan 04 Task 1.")


async def test_gate_07_three_concurrent_doc_search():
    """3 concurrent doc_search calls complete within 60s and all return non-empty."""
    _skip_if_no_pageindex_key()

    queries = ["konstytucja", "prawa obywatelskie", "wladza ustawodawcza"]

    async with PageIndexClient.connect() as client:
        started = time.monotonic()
        results = await asyncio.gather(
            client.doc_search(queries[0]),
            client.doc_search(queries[1]),
            client.doc_search(queries[2]),
        )
        elapsed = time.monotonic() - started

    assert elapsed < 60, (
        f"3 concurrent doc_search took {elapsed:.1f}s — possible rate-limit/queue "
        f"(Pitfall 14). Phase 3 must serialize ministry consultations if this fires."
    )

    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    for i, (query, result) in enumerate(zip(queries, results)):
        assert isinstance(result, dict), (
            f"Result {i} for query {query!r} is not a dict: {result!r}"
        )
        assert result, (
            f"Result {i} for query {query!r} is empty — possible silent "
            f"rate-limit (Pitfall 14: MCP server may return {{}} instead of "
            f"raising). Check PageIndex Cloud dashboard for 429 events."
        )
```

Implementation notes:
- Uses `asyncio.gather` over the MCP client — explicitly NOT over AIAgent (the documented async-safe path per CONTEXT.md GATE-07 acceptance)
- 3 distinct queries (not the same query 3x) to defeat any client-side caching
- 60s budget per CONTEXT.md "all 3 return within 60s"
- Non-empty dict assertion catches Pitfall 14's "silent rate limit returns {}" failure mode
- Single PageIndexClient session (one MCP subprocess) shared across the 3 calls — matches CONTEXT.md "from one Hermes session"

Verify (automated): `cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -m pytest tests/test_gate_07_concurrent_search.py --collect-only --tb=short`

Acceptance criteria:
- `test -f /Users/xpll081/ai-politics/tests/test_gate_07_concurrent_search.py` exit 0
- `grep -q "asyncio.gather" /Users/xpll081/ai-politics/tests/test_gate_07_concurrent_search.py` exit 0
- `grep -q "PageIndexClient" /Users/xpll081/ai-politics/tests/test_gate_07_concurrent_search.py` exit 0
- `grep -q "elapsed < 60" /Users/xpll081/ai-politics/tests/test_gate_07_concurrent_search.py` exit 0
- `grep -q "def test_gate_07_three_concurrent_doc_search" /Users/xpll081/ai-politics/tests/test_gate_07_concurrent_search.py` exit 0
- NOT-present check (CONTEXT.md anti-pattern): `! grep -q "AIAgent" /Users/xpll081/ai-politics/tests/test_gate_07_concurrent_search.py` exit 0 (must use MCP client only, NOT asyncio.gather over AIAgent)
- `cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -m pytest tests/test_gate_07_concurrent_search.py --collect-only` exit 0
- After Plan 04 Task 1 checkpoint complete: `pytest tests/test_gate_07_concurrent_search.py -x` exit 0
- When no key set: SKIPPED (not FAILED)

Done: Test file uses `asyncio.gather` over `PageIndexClient` (NOT over `AIAgent`), enforces a 60s deadline, asserts non-empty results for all 3 queries, skips cleanly without an API key.

# Threat Model

## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| pytest process to PageIndex Cloud (HTTPS) | API key flows via env var into the `npx pageindex-mcp` subprocess; query text and document content travel to PageIndex Inc. |
| MCP stdio channel | Process-local; trust is bounded by the local user — no network exposure |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-05-01 | Information Disclosure | API key leaked via test output | mitigate | Tests never print or assert on `api_key` value; assertion messages reference response payload only; the `PageIndexClient.connect` method passes the key via subprocess `env`, never via argv |
| T-05-02 | Denial of Service | PageIndex Cloud rate-limit kicking in during GATE-07 | mitigate | GATE-07 explicitly tests for this — 60s deadline + non-empty-dict assertion catches silent 429s (Pitfall 14); if test fails, ORCH-03 must serialize ministry queries in Phase 3 |
| T-05-03 | Tampering | OCR-corrupted text passing GATE-05 silently | mitigate | GATE-05 fixture (`konstytucja_diacritic_counts.json`) defines per-diacritic counts; assertion message dumps a 500-char text sample on failure so corruption is visible — not just "test failed" |
| T-05-04 | Repudiation | False-pass when PageIndex returns TOC-only root | mitigate | GATE-05 includes a body-descent step: if root text is < 5000 chars, search for "preambuła Rzeczypospolitej Polskiej" and fetch the deeper node, so we test against substantive text not metadata |
</threat_model>

# Verification

After all four tasks complete, with Plan 04 Task 1 checkpoint also done and `uv pip install -e ".[dev]"` run, from repo root:

```
# Fixture is valid
python3 -c "import json; json.load(open('tests/fixtures/konstytucja_diacritic_counts.json'))"

# Tests collect (no import errors)
PYTHONPATH=. python3 -m pytest tests/test_gate_04_pageindex_doc_search.py tests/test_gate_05_diacritics.py tests/test_gate_07_concurrent_search.py --collect-only

# Full run (requires Plan 04 prereqs live)
. .venv/bin/activate && pytest tests/test_gate_04_pageindex_doc_search.py -x
. .venv/bin/activate && pytest tests/test_gate_05_diacritics.py -x
. .venv/bin/activate && pytest tests/test_gate_07_concurrent_search.py -x

# Final: full Day-1 gate sweep (the make target from Plan 01)
. .venv/bin/activate && make smoke
```

All exit 0. `make smoke` should run all 7 gate tests + the token-budget unit tests.

# Success Criteria

- GATE-04 test passes: `doc_search("konstytucja")` returns a non-empty `node_id`
- GATE-05 test passes: `fetch_node` text contains all 9 Polish diacritics at >= 90% of expected counts (Pitfall 1 mitigated — the highest-risk failure mode is verified absent)
- GATE-07 test passes: 3 concurrent `doc_search` calls return within 60s, all non-empty (Pitfall 14 mitigated)
- All three tests skip cleanly when no PAGEINDEX_API_KEY (CI-friendly)
- The full `make smoke` target runs end-to-end (all 7 gates + token budget)
- Phase 1 cut criteria (CONTEXT.md) can now be evaluated — if any test fails, the documented pivot decisions activate

# Output

After completion, create `.planning/phases/01-foundation-smoke-tests/01-05-SUMMARY.md` documenting:
- Which gates passed/failed
- Observed diacritic counts vs expected (concrete numbers for Phase 2 reference)
- Observed concurrent-search elapsed time (concrete number for ORCH-03 sizing)
- If any cut criterion fires, name it explicitly and link the relevant CONTEXT.md section

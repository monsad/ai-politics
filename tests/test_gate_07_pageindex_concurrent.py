"""GATE-07: Three concurrent PageIndex searches complete without deadlock.

Acceptance criteria (CONTEXT.md):
  Given Konstytucja is indexed,
  When we fire 3 concurrent search_documents calls via asyncio.gather,
  Then all 3 complete within 60 seconds with non-empty results.

asyncio.gather over the MCP client is safe (unlike asyncio.gather over AIAgent
instances which deadlocks — see CONTEXT.md PITFALLS Pitfall 4).

Skipped automatically when PAGEINDEX_API_KEY is not set.
"""

from __future__ import annotations

import asyncio
import os

import pytest

from parliament.second_brain.pageindex_client import PageIndexClient


pytestmark = pytest.mark.asyncio

QUERIES = ["konstytucja", "konstytucja", "konstytucja"]
TIMEOUT_SECONDS = 60


@pytest.fixture
def skip_if_no_pageindex_key():
    if not os.environ.get("PAGEINDEX_API_KEY"):
        pytest.skip("PAGEINDEX_API_KEY not set — skip PageIndex live gate tests")


@pytest.mark.asyncio
async def test_gate_07_concurrent_search(skip_if_no_pageindex_key):
    """GATE-07: 3 concurrent search_documents calls all return results."""
    async with PageIndexClient.connect() as client:
        results = await asyncio.wait_for(
            asyncio.gather(
                client.search_documents(QUERIES[0]),
                client.search_documents(QUERIES[1]),
                client.search_documents(QUERIES[2]),
            ),
            timeout=TIMEOUT_SECONDS,
        )

    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    for i, (query, result) in enumerate(zip(QUERIES, results)):
        assert isinstance(result, dict), (
            f"GATE-07 FAIL: result[{i}] (query={query!r}) is not a dict: {result!r}"
        )
        # Must have some content — either a list of docs or a text field
        has_content = bool(
            result.get("documents")
            or result.get("files")
            or result.get("results")
            or result.get("items")
            or result.get("text")
            or result.get("raw")
        )
        assert has_content, (
            f"GATE-07 FAIL: result[{i}] (query={query!r}) is empty: {result!r}"
        )

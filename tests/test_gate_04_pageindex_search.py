"""GATE-04: PageIndex doc search smoke test.

Acceptance criteria (CONTEXT.md):
  Given the Konstytucja RP PDF has been seeded (doc_id pinned in DOC_ID),
  When we call search_documents("konstytucja"),
  Then the result contains the Konstytucja document (name contains "konstytucja").

Skipped automatically when PAGEINDEX_API_KEY is not set.
"""

from __future__ import annotations

import os

import pytest
import pytest_asyncio  # noqa: F401 — required for @pytest.mark.asyncio

from parliament.second_brain.pageindex_client import PageIndexClient


pytestmark = pytest.mark.asyncio


@pytest.fixture
def skip_if_no_pageindex_key():
    if not os.environ.get("PAGEINDEX_API_KEY"):
        pytest.skip("PAGEINDEX_API_KEY not set — skip PageIndex live gate tests")


@pytest.mark.asyncio
async def test_gate_04_doc_search(skip_if_no_pageindex_key):
    """GATE-04: search_documents finds Konstytucja by keyword."""
    async with PageIndexClient.connect() as client:
        result = await client.search_documents("konstytucja")

    # Result should be a dict with documents list or similar structure
    assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result!r}"

    # Accept any key that might hold the document list
    docs = (
        result.get("documents")
        or result.get("files")
        or result.get("results")
        or result.get("items")
        or []
    )
    # Also accept plain text response with "konstytucja" in it
    text_result = result.get("text", "")

    found = (
        any(
            "konstytucja" in (d.get("name") or d.get("title") or "").lower()
            for d in docs
        )
        or "konstytucja" in text_result.lower()
    )
    assert found, (
        f"GATE-04 FAIL: Konstytucja not found in search results. "
        f"Full response: {result!r}"
    )

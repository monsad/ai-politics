"""GATE-05: PageIndex returns Polish diacritics correctly.

Acceptance criteria (CONTEXT.md):
  Given Konstytucja is indexed,
  When we fetch page content from the first few pages,
  Then the response contains Polish diacritic characters (ą ę ó ś ź ż ć ń ł).

Skipped automatically when PAGEINDEX_API_KEY is not set.
"""

from __future__ import annotations

import os

import pytest

from parliament.second_brain.pageindex_client import PageIndexClient


pytestmark = pytest.mark.asyncio

POLISH_DIACRITICS = set("ąęóśźżćńłĄĘÓŚŹŻĆŃŁ")
KONSTYTUCJA_DOC_NAME = "konstytucja.pdf"


@pytest.fixture
def skip_if_no_pageindex_key():
    if not os.environ.get("PAGEINDEX_API_KEY"):
        pytest.skip("PAGEINDEX_API_KEY not set — skip PageIndex live gate tests")


def _extract_text(result: dict) -> str:
    """Pull all text out of an MCP result regardless of schema variant."""
    import json

    text = result.get("text") or ""
    if isinstance(text, str) and text:
        return text
    # Some responses nest content inside pages/items
    for key in ("pages", "content", "items", "results"):
        items = result.get(key) or []
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    text += item.get("text") or item.get("content") or ""
    if not text:
        text = json.dumps(result)
    return text


@pytest.mark.asyncio
async def test_gate_05_diacritics(skip_if_no_pageindex_key):
    """GATE-05: page content from Konstytucja contains Polish diacritics."""
    async with PageIndexClient.connect() as client:
        # First browse to get exact doc name
        browse = await client.browse_documents()
        docs = browse.get("documents") or browse.get("files") or browse.get("items") or []
        doc_name = KONSTYTUCJA_DOC_NAME
        for d in docs:
            name = d.get("name") or d.get("title") or ""
            if "konstytucja" in name.lower():
                doc_name = name
                break

        result = await client.get_page_content(doc_name=doc_name, pages="1-3")

    text = _extract_text(result)
    found_diacritics = POLISH_DIACRITICS & set(text)
    assert found_diacritics, (
        f"GATE-05 FAIL: No Polish diacritics found in page content. "
        f"Expected any of {sorted(POLISH_DIACRITICS)}, "
        f"got text snippet: {text[:300]!r}"
    )

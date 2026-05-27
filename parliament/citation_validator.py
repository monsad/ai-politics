"""ORCH-09 support: verify every cited node_id resolves against PageIndex.

Called by E2E acceptance tests post-session (Plan 05). Operates on the raw
transcript blob produced by the marszalek-sejmu subprocess.
"""
from __future__ import annotations

import os
import re
from typing import Iterable

# Pattern 1: bare node_id token
_RE_NODE_ID = re.compile(r"node_id[:=]\s*([A-Za-z0-9_\-./#]+)")
# Pattern 2: (orig. PL: "..." — doc_name.pdf p.5)  or  ... doc_name.pdf p.5)
# Capture group 1 = doc_name (without .pdf), group 2 = page or page range
_RE_DOC_PAGE = re.compile(
    r"([A-Za-z0-9_\-]+)\.pdf\s*(?:p\.|page\s+)(\d+(?:-\d+)?)",
    re.IGNORECASE,
)


def extract_node_ids(transcript_text: str) -> list[str]:
    """Scan transcript and return unique citation tokens in first-seen order.

    Returned tokens take one of two shapes:
      - "<bare_token>"           from `node_id: <bare_token>`
      - "<doc_name>.pdf#p<N>"    from `<doc_name>.pdf p.<N>` style references
    """
    seen: dict[str, None] = {}
    for m in _RE_NODE_ID.finditer(transcript_text):
        seen.setdefault(m.group(1), None)
    for m in _RE_DOC_PAGE.finditer(transcript_text):
        token = f"{m.group(1)}.pdf#p{m.group(2)}"
        seen.setdefault(token, None)
    return list(seen.keys())


def _split_token(token: str) -> tuple[str, str | None]:
    """Return (doc_name, pages_or_None)."""
    if "#p" in token:
        doc, pages = token.split("#p", 1)
        return doc + ".pdf", pages
    if token.endswith(".pdf"):
        return token, None
    # bare node id without doc name — treat as opaque, no page lookup
    return token, None


async def validate_citations(node_ids: Iterable[str]) -> dict:
    """Resolve each citation token via PageIndex MCP.

    Returns:
        {
          "total": int,
          "resolved": int,
          "unresolvable": list[str],
          "error": str | absent,
        }
    """
    tokens = list(dict.fromkeys(node_ids))  # de-dupe, preserve order
    total = len(tokens)

    api_key = os.environ.get("PAGEINDEX_API_KEY", "")
    if not api_key or api_key.startswith("replace-with"):
        return {
            "total": total,
            "resolved": 0,
            "unresolvable": list(tokens),
            "error": "PAGEINDEX_API_KEY missing",
        }

    if total == 0:
        return {"total": 0, "resolved": 0, "unresolvable": []}

    from parliament.second_brain.pageindex_client import PageIndexClient

    unresolvable: list[str] = []
    resolved = 0
    async with PageIndexClient.connect() as client:
        for token in tokens:
            doc_name, pages = _split_token(token)
            try:
                if pages is not None:
                    result = await client.get_page_content(doc_name=doc_name, pages=pages)
                else:
                    result = await client.get_document(doc_name=doc_name)
                # Treat empty result as unresolvable
                if not result or (isinstance(result, dict) and not any(result.values())):
                    unresolvable.append(token)
                else:
                    resolved += 1
            except Exception:  # noqa: BLE001 — any failure = unresolvable
                unresolvable.append(token)
    return {"total": total, "resolved": resolved, "unresolvable": unresolvable}

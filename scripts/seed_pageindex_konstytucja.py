#!/usr/bin/env python3
"""Seed PageIndex Cloud with the Konstytucja RP PDF for GATE-04 / GATE-05 smoke tests.

Responsibilities (CONTEXT.md "PageIndex Cloud seed script — concrete responsibilities"):
1. Read PAGEINDEX_API_KEY from .env (or environment).
2. Download Konstytucja RP PDF from ISAP (URL pinned below).
3. POST to PageIndex Cloud ingest endpoint.
4. Poll status until indexing completes.
5. Print the resulting doc_id.
6. Idempotent: if a doc with the same source URL already exists, return its doc_id.

This script does NOT use hermes-agent. It uses httpx directly because seeding
happens before any Hermes Agent runs (chicken-and-egg with MCP setup).

API: https://api.pageindex.ai (FastAPI, OpenAPI spec at /openapi.json)
  - POST /doc       multipart/form-data, required field: file
  - GET  /doc/{id}  status polling
  - GET  /docs      list all documents

Usage:
    python scripts/seed_pageindex_konstytucja.py

Output: prints `doc_id=<the_id>` on the last line of stdout for downstream test
fixtures to capture.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv


REPO_ROOT = Path(__file__).parent.parent
KONSTYTUCJA_PDF_URL = (
    "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19970780483/U/D19970483Lj.pdf"
)
LOCAL_PDF_CACHE = REPO_ROOT / "data" / "konstytucja.pdf"
PAGEINDEX_BASE_URL = os.environ.get(
    "PAGEINDEX_BASE_URL", "https://api.pageindex.ai"
)
# Stored as JSON string in the metadata field so we can find the doc on re-runs.
SOURCE_REF = "konstytucja-rp-isap-1997-78-483"
DOC_TITLE = "Konstytucja Rzeczypospolitej Polskiej"


def fetch_pdf(client: httpx.Client) -> Path:
    """Download the Konstytucja PDF to LOCAL_PDF_CACHE if not present."""
    LOCAL_PDF_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if LOCAL_PDF_CACHE.exists() and LOCAL_PDF_CACHE.stat().st_size > 50_000:
        print(f"[seed] PDF already cached at {LOCAL_PDF_CACHE}")
        return LOCAL_PDF_CACHE
    print(f"[seed] Downloading Konstytucja from {KONSTYTUCJA_PDF_URL}")
    r = client.get(KONSTYTUCJA_PDF_URL, follow_redirects=True, timeout=60.0)
    r.raise_for_status()
    LOCAL_PDF_CACHE.write_bytes(r.content)
    print(f"[seed] Wrote {len(r.content)} bytes to {LOCAL_PDF_CACHE}")
    return LOCAL_PDF_CACHE


def find_existing_doc(client: httpx.Client, api_key: str) -> str | None:
    """Return existing doc_id if Konstytucja was already ingested (checks title)."""
    try:
        r = client.get(
            f"{PAGEINDEX_BASE_URL}/docs",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        r.raise_for_status()
        docs = r.json().get("documents", [])
        for doc in docs:
            # Match by title or source_ref stored in metadata
            title = doc.get("title") or doc.get("name") or ""
            meta = doc.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            if DOC_TITLE in title or meta.get("source_ref") == SOURCE_REF:
                doc_id = doc.get("id") or doc.get("doc_id")
                print(f"[seed] Found existing doc_id={doc_id} (title={title!r})")
                return doc_id
    except Exception as e:
        print(f"[seed] WARN — could not check for existing doc: {e}")
    return None


def upload_pdf(client: httpx.Client, api_key: str, pdf_path: Path) -> str:
    """Upload PDF to PageIndex Cloud via POST /doc; return doc_id."""
    print(f"[seed] Uploading {pdf_path.name} to {PAGEINDEX_BASE_URL}/doc")
    with pdf_path.open("rb") as f:
        files = {"file": (pdf_path.name, f, "application/pdf")}
        data = {
            "metadata": json.dumps({"source_ref": SOURCE_REF, "title": DOC_TITLE}),
            "if_ocr": "true",
        }
        r = client.post(
            f"{PAGEINDEX_BASE_URL}/doc",
            headers={"Authorization": f"Bearer {api_key}"},
            files=files,
            data=data,
            timeout=300.0,
        )
    r.raise_for_status()
    payload = r.json()
    doc_id = (
        payload.get("id")
        or payload.get("doc_id")
        or payload.get("document_id")
    )
    if not doc_id:
        raise RuntimeError(f"PageIndex upload returned no doc_id: {payload!r}")
    print(f"[seed] Uploaded — doc_id={doc_id}")
    return doc_id


def wait_for_indexing(client: httpx.Client, api_key: str, doc_id: str) -> None:
    """Poll GET /doc/{doc_id} until status is ready/indexed/completed."""
    print(f"[seed] Waiting for indexing of doc_id={doc_id}")
    deadline = time.monotonic() + 600  # 10 minute hard cap
    while time.monotonic() < deadline:
        r = client.get(
            f"{PAGEINDEX_BASE_URL}/doc/{doc_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        r.raise_for_status()
        payload = r.json()
        doc_status = payload.get("status") or payload.get("state") or "unknown"
        print(f"[seed]   status={doc_status}")
        if doc_status in ("ready", "indexed", "completed", "done", "success"):
            print("[seed] Indexing complete.")
            return
        if doc_status in ("failed", "error"):
            raise RuntimeError(f"PageIndex ingest failed: {payload!r}")
        time.sleep(5)
    raise TimeoutError("PageIndex did not finish indexing within 10 minutes")


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.environ.get("PAGEINDEX_API_KEY")
    if not api_key or api_key.startswith("replace-with"):
        print(
            "[seed] ERROR: PAGEINDEX_API_KEY is not set in .env. "
            "Provision it at https://dash.pageindex.ai first.",
            file=sys.stderr,
        )
        return 2

    with httpx.Client() as client:
        existing = find_existing_doc(client, api_key)
        if existing:
            print(f"doc_id={existing}")
            return 0
        pdf = fetch_pdf(client)
        doc_id = upload_pdf(client, api_key, pdf)
        wait_for_indexing(client, api_key, doc_id)
        print(f"doc_id={doc_id}")
        return 0


if __name__ == "__main__":
    sys.exit(main())

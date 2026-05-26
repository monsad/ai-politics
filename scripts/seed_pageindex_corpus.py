#!/usr/bin/env python3
"""
Batch seed PageIndex Cloud with the full ~50-doc corpus.
Extends scripts/seed_pageindex_konstytucja.py pattern for batch ingest.

Usage:
    python scripts/seed_pageindex_corpus.py [--dry-run] [--domain DOMAIN]

    --dry-run: Print URLs and source_refs, do not upload
    --domain DOMAIN: Only ingest docs for a specific domain

Output: Updates data/doc_manifest.json with {source_ref: {doc_id, title, domain, pages}}
Exit codes: 0=success, 1=partial failure (some docs failed), 2=config error
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv


REPO_ROOT = Path(__file__).parent.parent
PAGEINDEX_BASE_URL = os.environ.get("PAGEINDEX_BASE_URL", "https://api.pageindex.ai")
MANIFEST_PATH = REPO_ROOT / "data" / "doc_manifest.json"
PDF_CACHE_DIR = REPO_ROOT / "data" / "pdf_cache"
PAGE_BUDGET_WARN = 950  # warn before hitting 1000 limit

CORE_DOCS = [
    {
        "source_ref": "kodeks-karny-1997-88-553",
        "title": "Kodeks karny",
        "domain": "justice",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19970880553/U/D19970553Lj.pdf",
    },
    {
        "source_ref": "kodeks-cywilny-1964-16-93",
        "title": "Kodeks cywilny",
        "domain": "justice",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640160093/U/D19640093Lj.pdf",
    },
    {
        "source_ref": "kodeks-pracy-1974-24-141",
        "title": "Kodeks pracy",
        "domain": "labor",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19740240141/U/D19740141Lj.pdf",
    },
]

DOMAIN_DOCS = [
    # Finance/Tax (6 docs)
    {
        "source_ref": "ustawa-pit-1991-80-350",
        "title": "Ustawa o podatku dochodowym od osób fizycznych (PIT)",
        "domain": "finance",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19910800350/U/D19910350Lj.pdf",
    },
    {
        "source_ref": "ustawa-cit-1992-21-86",
        "title": "Ustawa o podatku dochodowym od osób prawnych (CIT)",
        "domain": "finance",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19920210086/U/D19920086Lj.pdf",
    },
    {
        "source_ref": "ustawa-vat-2004-54-535",
        "title": "Ustawa o podatku od towarów i usług (VAT)",
        "domain": "finance",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20040540535/U/D20040535Lj.pdf",
    },
    {
        "source_ref": "ordynacja-podatkowa-1997-137-926",
        "title": "Ordynacja podatkowa",
        "domain": "finance",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19971370926/U/D19970926Lj.pdf",
    },
    {
        "source_ref": "ustawa-podatek-nieruchomosci-1991-9-31",
        "title": "Ustawa o podatkach i opłatach lokalnych",
        "domain": "finance",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19910090031/U/D19910031Lj.pdf",
    },
    {
        "source_ref": "ustawa-rachunkowosc-1994-121-591",
        "title": "Ustawa o rachunkowości",
        "domain": "finance",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19941210591/U/D19940591Lj.pdf",
    },
    # Labor/Social (5 docs)
    {
        "source_ref": "ustawa-minimalne-wynagrodzenie-2002-200-1679",
        "title": "Ustawa o minimalnym wynagrodzeniu za pracę",
        "domain": "labor",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20022001679/U/D20021679Lj.pdf",
    },
    {
        "source_ref": "ustawa-urlopy-rodzicielskie-2013-675",
        "title": "Ustawa o zmianie ustawy — Kodeks pracy (urlopy rodzicielskie)",
        "domain": "labor",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20130000675/U/D20130675Lj.pdf",
    },
    {
        "source_ref": "ustawa-zasilki-1999-60-636",
        "title": "Ustawa o świadczeniach pieniężnych z ubezpieczenia społecznego",
        "domain": "labor",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19990600636/U/D19990636Lj.pdf",
    },
    {
        "source_ref": "ustawa-zwiazki-zawodowe-1991-55-234",
        "title": "Ustawa o związkach zawodowych",
        "domain": "labor",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19910550234/U/D19910234Lj.pdf",
    },
    {
        "source_ref": "ustawa-pomoc-spoleczna-2004-64-593",
        "title": "Ustawa o pomocy społecznej",
        "domain": "labor",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20040640593/U/D20040593Lj.pdf",
    },
    # Health (4 docs)
    {
        "source_ref": "ustawa-swiadczenia-zdrowotne-2004-210-2135",
        "title": "Ustawa o świadczeniach opieki zdrowotnej finansowanych ze środków publicznych",
        "domain": "health",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20042102135/U/D20042135Lj.pdf",
    },
    {
        "source_ref": "prawo-farmaceutyczne-2001-126-1381",
        "title": "Prawo farmaceutyczne",
        "domain": "health",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20011261381/U/D20011381Lj.pdf",
    },
    {
        "source_ref": "ustawa-ochrona-zdrowia-psychicznego-1994-111-535",
        "title": "Ustawa o ochronie zdrowia psychicznego",
        "domain": "health",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19941110535/U/D19940535Lj.pdf",
    },
    {
        "source_ref": "ustawa-zawody-lekarza-1996-28-152",
        "title": "Ustawa o zawodach lekarza i lekarza dentysty",
        "domain": "health",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19960280152/U/D19960152Lj.pdf",
    },
    # Climate/Energy (5 docs)
    {
        "source_ref": "ustawa-oze-2015-478",
        "title": "Ustawa o odnawialnych źródłach energii",
        "domain": "climate",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20150000478/U/D20150478Lj.pdf",
    },
    {
        "source_ref": "prawo-energetyczne-1997-54-348",
        "title": "Prawo energetyczne",
        "domain": "climate",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19970540348/U/D19970348Lj.pdf",
    },
    {
        "source_ref": "ustawa-efektywnosc-energetyczna-2016-831",
        "title": "Ustawa o efektywności energetycznej",
        "domain": "climate",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20160000831/U/D20160831Lj.pdf",
    },
    {
        "source_ref": "ustawa-elektromobilnosc-2018-317",
        "title": "Ustawa o elektromobilności i paliwach alternatywnych",
        "domain": "climate",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20180000317/U/D20180317Lj.pdf",
    },
    {
        "source_ref": "ustawa-emisje-co2-2015-1223",
        "title": "Ustawa o systemie handlu uprawnieniami do emisji gazów cieplarnianych",
        "domain": "climate",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20150001223/U/D20151223Lj.pdf",
    },
    # Justice/Procedure (3 docs — use excerpt mode for KPC/KPK if > 50 pages)
    {
        "source_ref": "kpc-1964-43-296",
        "title": "Kodeks postępowania cywilnego",
        "domain": "justice",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640430296/U/D19640296Lj.pdf",
        "pages_hint": "Use pages param if > 80 pages — ingest Część pierwsza (art. 1–505) only",
    },
    {
        "source_ref": "kpk-1997-89-555",
        "title": "Kodeks postępowania karnego",
        "domain": "justice",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19970890555/U/D19970555Lj.pdf",
        "pages_hint": "Use pages param if > 80 pages — ingest Dział I-VI only",
    },
    {
        "source_ref": "ustawa-tk-2015-1064",
        "title": "Ustawa o Trybunale Konstytucyjnym",
        "domain": "justice",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20150001064/U/D20151064Lj.pdf",
    },
    # Education (3 docs)
    {
        "source_ref": "prawo-oswiatowe-2017-59",
        "title": "Prawo oświatowe",
        "domain": "education",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20170000059/U/D20170059Lj.pdf",
    },
    {
        "source_ref": "prawo-szkolnictwo-wyzsze-2018-1668",
        "title": "Ustawa Prawo o szkolnictwie wyższym i nauce",
        "domain": "education",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20180001668/U/D20181668Lj.pdf",
    },
    {
        "source_ref": "ustawa-system-oswiaty-1991-95-425",
        "title": "Ustawa o systemie oświaty",
        "domain": "education",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19910950425/U/D19910425Lj.pdf",
    },
    # Agriculture (3 docs)
    {
        "source_ref": "ustawa-ustroj-rolny-2003-64-592",
        "title": "Ustawa o kształtowaniu ustroju rolnego",
        "domain": "agriculture",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20030640592/U/D20030592Lj.pdf",
    },
    {
        "source_ref": "ustawa-krus-1990-71-422",
        "title": "Ustawa o ubezpieczeniu społecznym rolników",
        "domain": "agriculture",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19900710422/U/D19900422Lj.pdf",
    },
    {
        "source_ref": "ustawa-grunty-rolne-1995-16-78",
        "title": "Ustawa o ochronie gruntów rolnych i leśnych",
        "domain": "agriculture",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19950160078/U/D19950078Lj.pdf",
    },
    # Defense/Foreign (2 docs)
    {
        "source_ref": "ustawa-obrona-ojczyzny-2022-2305",
        "title": "Ustawa o obronie Ojczyzny",
        "domain": "defense",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20220002305/U/D20222305Lj.pdf",
    },
    {
        "source_ref": "ustawa-cudzoziemcy-2013-1650",
        "title": "Ustawa o cudzoziemcach",
        "domain": "foreign",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20130001650/U/D20131650Lj.pdf",
    },
    # Digital/Cyber (3 docs)
    {
        "source_ref": "ustawa-cyberbezpieczenstwo-2018-1560",
        "title": "Ustawa o krajowym systemie cyberbezpieczeństwa",
        "domain": "digital",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20180001560/U/D20181560Lj.pdf",
    },
    {
        "source_ref": "ustawa-ochrona-danych-2018-1000",
        "title": "Ustawa o ochronie danych osobowych (RODO implementacja PL)",
        "domain": "digital",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20180001000/U/D20181000Lj.pdf",
    },
    {
        "source_ref": "prawo-telekomunikacyjne-2004-171-1800",
        "title": "Prawo telekomunikacyjne",
        "domain": "digital",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20041711800/U/D20041800Lj.pdf",
    },
    # Infrastructure/Transport (3 docs)
    {
        "source_ref": "prawo-budowlane-1994-89-414",
        "title": "Prawo budowlane",
        "domain": "infrastructure",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19940890414/U/D19940414Lj.pdf",
    },
    {
        "source_ref": "ustawa-transport-drogowy-2001-125-1371",
        "title": "Ustawa o transporcie drogowym",
        "domain": "infrastructure",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20011251371/U/D20011371Lj.pdf",
    },
    {
        "source_ref": "ustawa-transport-zbiorowy-2010-106-1191",
        "title": "Ustawa o publicznym transporcie zbiorowym",
        "domain": "infrastructure",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20101061191/U/D20101191Lj.pdf",
    },
    # Other ministries (9 docs)
    {
        "source_ref": "ustawa-dzialalnosc-kulturalna-1991-114-493",
        "title": "Ustawa o organizowaniu i prowadzeniu działalności kulturalnej",
        "domain": "culture",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19911140493/U/D19910493Lj.pdf",
    },
    {
        "source_ref": "ustawa-sport-2010-127-857",
        "title": "Ustawa o sporcie",
        "domain": "sport",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20101270857/U/D20100857Lj.pdf",
    },
    {
        "source_ref": "ustawa-pan-1960-54-271",
        "title": "Ustawa o Polskiej Akademii Nauk",
        "domain": "science",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19600540271/U/D19600271Lj.pdf",
    },
    {
        "source_ref": "ustawa-polityka-rozwoju-2006-227-1658",
        "title": "Ustawa o zasadach prowadzenia polityki rozwoju",
        "domain": "regional",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20062271658/U/D20061658Lj.pdf",
    },
    {
        "source_ref": "ustawa-mienie-panstwowe-2016-154",
        "title": "Ustawa o zasadach zarządzania mieniem państwowym",
        "domain": "stateassets",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20160000154/U/D20160154Lj.pdf",
    },
    {
        "source_ref": "ustawa-policja-1990-30-179",
        "title": "Ustawa o Policji",
        "domain": "interior",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19900300179/U/D19900179Lj.pdf",
    },
    {
        "source_ref": "ustawa-straz-graniczna-1990-78-462",
        "title": "Ustawa o Straży Granicznej",
        "domain": "interior",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19900780462/U/D19900462Lj.pdf",
    },
    {
        "source_ref": "ustawa-usligi-turystyczne-1997-133-884",
        "title": "Ustawa o usługach turystycznych",
        "domain": "sport",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19971330884/U/D19970884Lj.pdf",
    },
    {
        "source_ref": "ustawa-zamowienia-publiczne-2019-2019",
        "title": "Ustawa Prawo zamówień publicznych",
        "domain": "stateassets",
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20192019/U/D20192019Lj.pdf",
    },
]


def load_manifest(path: Path) -> dict:
    """Load existing doc_manifest.json; return empty dict if not found."""
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[corpus] WARN — could not load manifest at {path}: {e}")
    return {}


def save_manifest(path: Path, manifest: dict) -> None:
    """Write manifest atomically via a .tmp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def find_existing_doc(client: httpx.Client, api_key: str, source_ref: str) -> Optional[str]:
    """Return existing doc_id if a document with this source_ref was already ingested."""
    try:
        r = client.get(
            f"{PAGEINDEX_BASE_URL}/docs",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        r.raise_for_status()
        docs = r.json().get("documents", [])
        for doc in docs:
            meta = doc.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            if meta.get("source_ref") == source_ref:
                doc_id = doc.get("id") or doc.get("doc_id")
                print(f"[corpus] Found existing doc source_ref={source_ref!r} doc_id={doc_id}")
                return doc_id
    except Exception as e:
        print(f"[corpus] WARN — could not check existing docs: {e}")
    return None


def fetch_pdf(client: httpx.Client, doc_entry: dict, cache_dir: Path) -> Path:
    """Download PDF to cache_dir/{source_ref}.pdf if not already cached."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    source_ref = doc_entry["source_ref"]
    pdf_path = cache_dir / f"{source_ref}.pdf"
    if pdf_path.exists() and pdf_path.stat().st_size > 10_000:
        print(f"[corpus] PDF cached: {pdf_path.name}")
        return pdf_path
    url = doc_entry["url"]
    print(f"[corpus] Downloading {source_ref} from {url}")
    r = client.get(url, follow_redirects=True, timeout=120.0)
    r.raise_for_status()
    pdf_path.write_bytes(r.content)
    print(f"[corpus] Wrote {len(r.content):,} bytes to {pdf_path.name}")
    return pdf_path


def upload_pdf(client: httpx.Client, api_key: str, pdf_path: Path, doc_entry: dict) -> str:
    """POST /doc multipart/form-data; return doc_id."""
    source_ref = doc_entry["source_ref"]
    title = doc_entry["title"]
    domain = doc_entry["domain"]
    print(f"[corpus] Uploading {source_ref!r} to {PAGEINDEX_BASE_URL}/doc")
    with pdf_path.open("rb") as f:
        files = {"file": (pdf_path.name, f, "application/pdf")}
        data = {
            "metadata": json.dumps({
                "source_ref": source_ref,
                "title": title,
                "domain": domain,
            }),
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
    print(f"[corpus] Uploaded {source_ref!r} — doc_id={doc_id}")
    return doc_id


def wait_for_indexing(
    client: httpx.Client, api_key: str, doc_id: str, timeout: int = 600
) -> None:
    """Poll GET /doc/{doc_id} until indexing completes or times out."""
    print(f"[corpus] Waiting for indexing of doc_id={doc_id}")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r = client.get(
            f"{PAGEINDEX_BASE_URL}/doc/{doc_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        r.raise_for_status()
        payload = r.json()
        doc_status = payload.get("status") or payload.get("state") or "unknown"
        pages = payload.get("pages") or payload.get("page_count") or payload.get("num_pages")
        print(f"[corpus]   status={doc_status}" + (f" pages={pages}" if pages else ""))
        if doc_status in ("ready", "indexed", "completed", "done", "success"):
            print("[corpus] Indexing complete.")
            return
        if doc_status in ("failed", "error"):
            raise RuntimeError(f"PageIndex ingest failed: {payload!r}")
        time.sleep(5)
    raise TimeoutError(f"PageIndex did not finish indexing doc_id={doc_id} within {timeout}s")


def ingest_doc(
    client: httpx.Client,
    api_key: str,
    doc_entry: dict,
    manifest: dict,
    cache_dir: Path,
) -> str:
    """
    Idempotent: ingest a single document.
    Checks manifest first, then PageIndex Cloud, then uploads.
    Returns the doc_id.
    """
    source_ref = doc_entry["source_ref"]

    # Check manifest for already-ingested doc
    if source_ref in manifest and manifest[source_ref].get("doc_id"):
        print(f"[corpus] Already in manifest: source_ref={source_ref!r} doc_id={manifest[source_ref]['doc_id']}")
        return manifest[source_ref]["doc_id"]

    # Check PageIndex Cloud for existing doc
    existing = find_existing_doc(client, api_key, source_ref)
    if existing:
        manifest[source_ref] = {
            "doc_id": existing,
            "title": doc_entry["title"],
            "domain": doc_entry["domain"],
            "pages": manifest.get(source_ref, {}).get("pages"),
        }
        return existing

    # Download and upload
    pdf_path = fetch_pdf(client, doc_entry, cache_dir)
    doc_id = upload_pdf(client, api_key, pdf_path, doc_entry)
    wait_for_indexing(client, api_key, doc_id)

    # Try to get page count from status response
    try:
        r = client.get(
            f"{PAGEINDEX_BASE_URL}/doc/{doc_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        payload = r.json()
        pages = (
            payload.get("pages")
            or payload.get("page_count")
            or payload.get("num_pages")
        )
    except Exception:
        pages = None

    manifest[source_ref] = {
        "doc_id": doc_id,
        "title": doc_entry["title"],
        "domain": doc_entry["domain"],
        "pages": pages,
    }
    return doc_id


def _count_estimated_pages(manifest: dict) -> int:
    """Sum up page counts from manifest (use 20 as default if unknown)."""
    total = 0
    for entry in manifest.values():
        if entry.get("doc_id"):  # only count successfully ingested
            pages = entry.get("pages")
            total += int(pages) if pages else 20  # assume 20 pages if unknown
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch seed PageIndex Cloud corpus")
    parser.add_argument("--dry-run", action="store_true", help="Print URLs without uploading")
    parser.add_argument("--domain", help="Only ingest docs for this domain")
    args = parser.parse_args()

    # Load API key
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.environ.get("PAGEINDEX_API_KEY")

    # Build the full doc list
    all_docs = CORE_DOCS + DOMAIN_DOCS

    # Filter by domain if requested
    if args.domain:
        all_docs = [d for d in all_docs if d["domain"] == args.domain]
        print(f"[corpus] Filtered to domain={args.domain!r}: {len(all_docs)} docs")

    if args.dry_run:
        print(f"[corpus] DRY RUN — {len(all_docs)} documents would be ingested:")
        for doc in all_docs:
            print(f"  source_ref={doc['source_ref']!r} domain={doc['domain']!r} title={doc['title']!r}")
            print(f"    url={doc['url']}")
        print(f"[corpus] Total: {len(all_docs)} docs")
        return 0

    if not api_key or api_key.startswith("replace-with"):
        print(
            "[corpus] ERROR: PAGEINDEX_API_KEY is not set in .env. "
            "Provision it at https://dash.pageindex.ai first.",
            file=sys.stderr,
        )
        return 2

    manifest = load_manifest(MANIFEST_PATH)
    success_count = 0
    failure_count = 0
    failures: list[tuple[str, str]] = []

    with httpx.Client() as client:
        for i, doc_entry in enumerate(all_docs, 1):
            source_ref = doc_entry["source_ref"]
            print(f"\n[corpus] [{i}/{len(all_docs)}] Processing {source_ref!r}")

            # Page budget check
            estimated_pages = _count_estimated_pages(manifest)
            print(f"[corpus] Running page estimate: ~{estimated_pages} pages used so far")
            if estimated_pages >= PAGE_BUDGET_WARN:
                print(
                    f"[corpus] WARNING: Estimated page count ({estimated_pages}) approaching "
                    f"1000-page limit. Press Enter to continue or Ctrl+C to stop."
                )
                try:
                    input()
                except (EOFError, KeyboardInterrupt):
                    print("[corpus] Stopped by user.")
                    break

            try:
                doc_id = ingest_doc(client, api_key, doc_entry, manifest, PDF_CACHE_DIR)
                success_count += 1
                print(f"[corpus] OK: {source_ref!r} → doc_id={doc_id}")
            except Exception as e:
                failure_count += 1
                failures.append((source_ref, str(e)))
                print(f"[corpus] FAILED: {source_ref!r} — {e}", file=sys.stderr)
                # Record failure in manifest
                manifest[source_ref] = {
                    "doc_id": None,
                    "title": doc_entry.get("title", ""),
                    "domain": doc_entry.get("domain", ""),
                    "pages": None,
                    "error": str(e),
                }

            # Save manifest after each doc (incremental progress)
            save_manifest(MANIFEST_PATH, manifest)

    # Final summary
    print(f"\n[corpus] === SUMMARY ===")
    print(f"[corpus] Success: {success_count}/{len(all_docs)} docs")
    if failures:
        print(f"[corpus] Failures ({failure_count}):")
        for ref, err in failures:
            print(f"  - {ref}: {err}")
    print(f"[corpus] Manifest written to: {MANIFEST_PATH}")

    total_pages_est = _count_estimated_pages(manifest)
    print(f"[corpus] Estimated total pages in PageIndex: ~{total_pages_est}")

    return 1 if failure_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

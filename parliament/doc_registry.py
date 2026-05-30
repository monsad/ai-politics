"""
BRAIN-05: Agent-to-document registry and metadata filter builder.

Maps agent_id → {domain, doc_ids, categories} so each ministry's
doc_search calls only return documents relevant to its domain.

Phase 2 populates this with ~50 doc corpus.
Phase 3 calls get_filter(agent_id) to inject into search_documents.
"""
from __future__ import annotations

import json
from pathlib import Path

_MANIFEST_PATH = Path(__file__).parent.parent / "data" / "doc_manifest.json"

def _load_manifest() -> dict:
    """Load data/doc_manifest.json if it exists, else return empty dict."""
    if _MANIFEST_PATH.exists():
        return json.loads(_MANIFEST_PATH.read_text())
    return {}

_MANIFEST = _load_manifest()

def _doc_ids_for_domain(domain: str) -> list[str]:
    """Extract doc_ids from manifest for a given domain."""
    return [
        v["doc_id"]
        for v in _MANIFEST.values()
        if v.get("domain") == domain and v.get("doc_id")
    ]

REGISTRY: dict[str, dict] = {
    "ministry-finansow": {
        "domain": "finance",
        "doc_ids": _doc_ids_for_domain("finance"),
        "categories": ["tax", "budget", "fiscal_policy", "banking"],
    },
    "ministry-zdrowia": {
        "domain": "health",
        "doc_ids": _doc_ids_for_domain("health"),
        "categories": ["healthcare", "pharmaceutical", "mental_health", "medical_professions"],
    },
    "ministry-edukacji": {
        "domain": "education",
        "doc_ids": _doc_ids_for_domain("education") + _doc_ids_for_domain("science"),
        "categories": ["primary_education", "higher_education", "school_system"],
    },
    "ministry-sprawiedliwosci": {
        "domain": "justice",
        "doc_ids": _doc_ids_for_domain("justice"),
        "categories": ["criminal_law", "civil_law", "court_procedure", "constitutional"],
    },
    "ministry-klimatu-i-srodowiska": {
        "domain": "climate",
        "doc_ids": _doc_ids_for_domain("climate"),
        "categories": ["renewable_energy", "emissions", "electromobility", "energy_efficiency"],
    },
    "ministry-infrastruktury": {
        "domain": "infrastructure",
        "doc_ids": _doc_ids_for_domain("infrastructure"),
        "categories": ["transport", "construction", "public_transit", "roads"],
    },
    "ministry-spraw-zagranicznych": {
        "domain": "foreign",
        "doc_ids": _doc_ids_for_domain("foreign"),
        "categories": ["immigration", "international_law", "eu_relations", "diplomacy"],
    },
    "ministry-obrony-narodowej": {
        "domain": "defense",
        "doc_ids": _doc_ids_for_domain("defense"),
        "categories": ["military", "national_security", "defense_procurement"],
    },
    "ministry-rolnictwa": {
        "domain": "agriculture",
        "doc_ids": _doc_ids_for_domain("agriculture"),
        "categories": ["agricultural_land", "farmers_insurance", "rural_policy"],
    },
    "ministry-rodziny-pracy-i-polityki-spolecznej": {
        "domain": "labor",
        "doc_ids": _doc_ids_for_domain("labor"),
        "categories": ["labor_law", "social_benefits", "minimum_wage", "trade_unions"],
    },
    "ministry-cyfryzacji": {
        "domain": "digital",
        "doc_ids": _doc_ids_for_domain("digital"),
        "categories": ["cybersecurity", "data_protection", "telecommunications", "digital_services"],
    },
    "ministry-kultury-i-dziedzictwa-narodowego": {
        "domain": "culture",
        "doc_ids": _doc_ids_for_domain("culture"),
        "categories": ["cultural_activity", "heritage", "arts_funding"],
    },
    "ministry-nauki-i-szkolnictwa-wyzszego": {
        "domain": "science",
        "doc_ids": _doc_ids_for_domain("science"),
        "categories": ["higher_education", "research", "academic_institutions"],
    },
    "ministry-energii": {
        "domain": "climate",
        "doc_ids": _doc_ids_for_domain("climate"),
        "categories": ["energy_market", "grid_regulation", "energy_security"],
    },
    "ministry-spraw-wewnetrznych-i-administracji": {
        "domain": "interior",
        "doc_ids": _doc_ids_for_domain("interior"),
        "categories": ["police", "border_guard", "public_order", "civil_registration"],
    },
    "ministry-aktywow-panstwowych": {
        "domain": "stateassets",
        "doc_ids": _doc_ids_for_domain("stateassets"),
        "categories": ["state_property", "public_procurement", "soe_governance"],
    },
    "ministry-funduszy-i-polityki-regionalnej": {
        "domain": "regional",
        "doc_ids": _doc_ids_for_domain("regional"),
        "categories": ["eu_funds", "regional_policy", "cohesion_policy"],
    },
    "ministry-rozwoju-i-technologii": {
        "domain": "digital",
        "doc_ids": _doc_ids_for_domain("digital"),
        "categories": ["economic_development", "innovation", "technology_policy"],
    },
    "ministry-sportu-i-turystyki": {
        "domain": "sport",
        "doc_ids": _doc_ids_for_domain("sport"),
        "categories": ["sports_law", "tourism", "physical_education"],
    },
}

def get_filter(agent_id: str) -> dict:
    """
    Return a metadata filter dict for injection into PageIndex search_documents.

    The filter restricts search results to documents tagged with the agent's domain,
    preventing cross-domain citation contamination (MIN-03).

    Args:
        agent_id: e.g. "ministry-finansow"

    Returns:
        dict — e.g. {"domain": "finance"}

    Raises:
        KeyError: if agent_id not in REGISTRY
    """
    if agent_id not in REGISTRY:
        raise KeyError(
            f"Agent '{agent_id}' not found in doc_registry. "
            f"Known agents: {sorted(REGISTRY.keys())}"
        )
    entry = REGISTRY[agent_id]
    return {"domain": entry["domain"]}

def list_agents() -> list[str]:
    """Return sorted list of all agent_ids registered in REGISTRY."""
    return sorted(REGISTRY.keys())

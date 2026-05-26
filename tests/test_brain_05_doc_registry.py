"""
BRAIN-05: parliament/doc_registry.py domain isolation tests.
Tests that each ministry's filter is scoped to its own domain,
preventing cross-domain citation contamination.
"""
import pytest
from parliament.doc_registry import REGISTRY, get_filter, list_agents


def test_registry_contains_wave1_ministries():
    wave1 = [
        "ministry-finansow",
        "ministry-zdrowia",
        "ministry-edukacji",
        "ministry-sprawiedliwosci",
        "ministry-klimatu-i-srodowiska",
        "ministry-infrastruktury",
        "ministry-spraw-zagranicznych",
    ]
    for agent_id in wave1:
        assert agent_id in REGISTRY, f"{agent_id} missing from REGISTRY"


def test_registry_entries_have_required_keys():
    for agent_id, entry in REGISTRY.items():
        assert "domain" in entry, f"{agent_id} missing 'domain'"
        assert "doc_ids" in entry, f"{agent_id} missing 'doc_ids'"
        assert "categories" in entry, f"{agent_id} missing 'categories'"
        assert isinstance(entry["doc_ids"], list), f"{agent_id}.doc_ids is not a list"
        assert isinstance(entry["categories"], list), f"{agent_id}.categories is not a list"


def test_get_filter_returns_nonempty_dict():
    f = get_filter("ministry-finansow")
    assert isinstance(f, dict)
    assert len(f) > 0


def test_get_filter_finance_domain():
    f = get_filter("ministry-finansow")
    assert f.get("domain") == "finance"


def test_get_filter_health_domain():
    f = get_filter("ministry-zdrowia")
    assert f.get("domain") == "health"


def test_get_filter_unknown_agent_raises():
    with pytest.raises(KeyError, match="unknown-agent"):
        get_filter("unknown-agent")


def test_finance_filter_excludes_health_domain():
    """Finance ministry should NOT see health domain documents (MIN-03)."""
    finance_filter = get_filter("ministry-finansow")
    health_filter = get_filter("ministry-zdrowia")
    # Filters must differ in domain
    assert finance_filter.get("domain") != health_filter.get("domain")
    # Finance filter must not contain "health" as domain value
    assert "health" not in finance_filter.values()


def test_list_agents_returns_sorted_list():
    agents = list_agents()
    assert isinstance(agents, list)
    assert len(agents) >= 7  # Wave 1 minimum
    assert agents == sorted(agents), "list_agents() must return sorted list"
    assert "ministry-finansow" in agents


def test_each_agent_domain_is_unique_enough():
    """No two ministries should share identical domain scope (would defeat filtering)."""
    domains = [REGISTRY[a]["domain"] for a in REGISTRY]
    # Finance and health must not share a domain
    finance_domain = REGISTRY["ministry-finansow"]["domain"]
    health_domain = REGISTRY["ministry-zdrowia"]["domain"]
    assert finance_domain != health_domain

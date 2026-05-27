"""
Phase 2 acceptance tests — gate before Phase 3 begins.

Corresponds to ROADMAP.md Phase 2 success criteria:
1. npx skills-ref@0.1.5 validate skills/ exits 0 for all 25 folders
2. party-cr and party-lf profiles contain visibly opposing positions
   on "4-day work week" and "flat tax" (text-level check — no LLM call needed)
3. doc_registry.py domain isolation — Finance does not return Health docs
4. Corpus ingested — data/doc_manifest.json has >= 5 docs with non-null doc_id
   (Note: free-tier limit reached at 5 docs; upgrade account to reach 50.
   See 02-01-SUMMARY.md for blocker details.)
5. Ethics review files exist for all 5 parties and contain required structure
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SKILLS_DIR = REPO_ROOT / "skills"


# ─────────────────────────────────────────────────────────────────────────────
# Criterion 1: All 25 skills pass skills-ref validate
# ─────────────────────────────────────────────────────────────────────────────

EXPECTED_SKILLS = [
    "party-cr", "party-nc", "party-ac", "party-lf", "party-sd",
    "marszalek-sejmu",
    "ministry-finansow", "ministry-zdrowia", "ministry-edukacji",
    "ministry-sprawiedliwosci", "ministry-klimatu-i-srodowiska",
    "ministry-infrastruktury", "ministry-spraw-zagranicznych",
    "ministry-obrony-narodowej", "ministry-rozwoju-i-technologii",
    "ministry-rolnictwa", "ministry-rodziny-pracy-i-polityki-spolecznej",
    "ministry-cyfryzacji", "ministry-kultury-i-dziedzictwa-narodowego",
    "ministry-nauki-i-szkolnictwa-wyzszego", "ministry-energii",
    "ministry-spraw-wewnetrznych-i-administracji", "ministry-aktywow-panstwowych",
    "ministry-funduszy-i-polityki-regionalnej", "ministry-sportu-i-turystyki",
]


def test_all_25_skill_directories_exist():
    """All 25 expected skill directories must exist."""
    for skill_id in EXPECTED_SKILLS:
        skill_dir = SKILLS_DIR / skill_id
        assert skill_dir.is_dir(), f"Missing skill directory: {skill_dir}"
        assert (skill_dir / "SKILL.md").exists(), f"Missing SKILL.md in: {skill_dir}"


def test_all_25_skills_pass_skills_ref_validate():
    """npx skills-ref@0.1.5 validate <skill_dir> exits 0 for each of the 25 skill folders."""
    failures = []
    for skill_id in EXPECTED_SKILLS:
        skill_dir = SKILLS_DIR / skill_id
        result = subprocess.run(
            ["npm", "exec", "--yes", "--", "skills-ref@0.1.5", "validate", str(skill_dir)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        if result.returncode != 0:
            failures.append(f"{skill_id}: {result.stdout.strip()} {result.stderr.strip()}")
    assert not failures, "skills-ref validate failed for:\n" + "\n".join(failures)


def test_all_skills_have_output_constraints():
    """Every SKILL.md must contain an ## Output Constraints section."""
    for skill_id in EXPECTED_SKILLS:
        skill_file = SKILLS_DIR / skill_id / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        assert "## Output Constraints" in content, (
            f"{skill_id}/SKILL.md missing '## Output Constraints' section"
        )
        assert "NEVER name real" in content, (
            f"{skill_id}/SKILL.md missing 'NEVER name real' guardrail"
        )


def test_marszalek_has_delegate_task_authority():
    """Marszałek SKILL.md must declare delegate_task authority."""
    marszalek = (SKILLS_DIR / "marszalek-sejmu" / "SKILL.md").read_text(encoding="utf-8")
    assert "delegate_task" in marszalek, "marszalek-sejmu SKILL.md missing delegate_task reference"
    assert "ONLY agent" in marszalek or "ONLY" in marszalek, (
        "marszalek-sejmu SKILL.md should declare sole delegate_task authority"
    )
    assert "EDUCATIONAL SIMULATION" in marszalek, (
        "marszalek-sejmu SKILL.md missing mandatory educational disclaimer"
    )
    assert "MARSZAŁEK REASONING" in marszalek, (
        "marszalek-sejmu SKILL.md missing [MARSZAŁEK REASONING] protocol"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Criterion 2: Party divergence (text-level — no LLM call)
# ─────────────────────────────────────────────────────────────────────────────

def test_party_divergence_profile_ko_vs_konfederacja():
    """
    CR and Liberty Front must have visibly opposing positions on flat tax.
    Verified by text-level check — no LLM call needed.
    """
    ko = (SKILLS_DIR / "party-cr" / "SKILL.md").read_text(encoding="utf-8").lower()
    konfederacja = (SKILLS_DIR / "party-lf" / "SKILL.md").read_text(encoding="utf-8").lower()

    # Both must mention flat tax
    assert "flat tax" in ko, "party-cr SKILL.md missing 'flat tax' position"
    assert "flat tax" in konfederacja, "party-lf SKILL.md missing 'flat tax' position"

    # CR opposes flat tax
    ko_flat_idx = ko.find("flat tax")
    ko_context = ko[ko_flat_idx:ko_flat_idx + 300]
    ko_opposes = any(w in ko_context for w in ["oppos", "against", "reject", "regress"])
    assert ko_opposes, f"party-cr flat tax section should contain oppositional language. Got: {ko_context!r}"

    # Liberty Front supports flat tax
    konf_flat_idx = konfederacja.find("flat tax")
    konf_context = konfederacja[konf_flat_idx:konf_flat_idx + 300]
    konf_supports = any(w in konf_context for w in ["support", "flagship", "advocate", "15%", "flat rate", "universal flat"])
    assert konf_supports, (
        f"party-lf flat tax section should contain support language. Got: {konf_context!r}"
    )


def test_all_party_skills_cover_canonical_topics():
    """All 5 party SKILL.md files must address all 8 canonical topics."""
    canonical_topics = [
        "4-day work week", "oze", "tax simplification", "immigration",
        "eu relations", "education reform", "healthcare", "flat tax",
    ]
    party_ids = ["party-cr", "party-nc", "party-ac", "party-lf", "party-sd"]
    for party_id in party_ids:
        content = (SKILLS_DIR / party_id / "SKILL.md").read_text(encoding="utf-8").lower()
        for topic in canonical_topics:
            assert topic in content, (
                f"{party_id}/SKILL.md missing canonical topic: '{topic}'"
            )


# ─────────────────────────────────────────────────────────────────────────────
# Criterion 3: doc_registry domain isolation
# ─────────────────────────────────────────────────────────────────────────────

def test_doc_registry_domain_isolation():
    """Finance filter must not contain health domain docs (MIN-03)."""
    sys.path.insert(0, str(REPO_ROOT))
    from parliament.doc_registry import get_filter, REGISTRY

    finance_filter = get_filter("ministry-finansow")
    health_filter = get_filter("ministry-zdrowia")

    assert finance_filter.get("domain") == "finance", (
        f"ministry-finansow filter domain wrong: {finance_filter}"
    )
    assert health_filter.get("domain") == "health", (
        f"ministry-zdrowia filter domain wrong: {health_filter}"
    )
    assert finance_filter != health_filter, (
        "Finance and Health filters must not be identical"
    )
    assert "health" not in finance_filter.values(), (
        "Finance filter must not contain 'health' domain value"
    )


def test_doc_registry_covers_all_19_ministries():
    """REGISTRY must contain all 19 ministry agent_ids."""
    sys.path.insert(0, str(REPO_ROOT))
    from parliament.doc_registry import REGISTRY, list_agents

    all_ministry_ids = [
        "ministry-finansow", "ministry-zdrowia", "ministry-edukacji",
        "ministry-sprawiedliwosci", "ministry-klimatu-i-srodowiska",
        "ministry-infrastruktury", "ministry-spraw-zagranicznych",
        "ministry-obrony-narodowej", "ministry-rozwoju-i-technologii",
        "ministry-rolnictwa", "ministry-rodziny-pracy-i-polityki-spolecznej",
        "ministry-cyfryzacji", "ministry-kultury-i-dziedzictwa-narodowego",
        "ministry-nauki-i-szkolnictwa-wyzszego", "ministry-energii",
        "ministry-spraw-wewnetrznych-i-administracji", "ministry-aktywow-panstwowych",
        "ministry-funduszy-i-polityki-regionalnej", "ministry-sportu-i-turystyki",
    ]
    agents = list_agents()
    for ministry_id in all_ministry_ids:
        assert ministry_id in agents, f"{ministry_id} missing from doc_registry.py REGISTRY"


# ─────────────────────────────────────────────────────────────────────────────
# Criterion 4: Corpus ingested (doc_manifest.json)
# Note: PageIndex Cloud free tier = 5 documents. Accepted for demo scope.
# See 02-01-SUMMARY.md for details. Upgrade account to reach full 50-doc corpus.
# ─────────────────────────────────────────────────────────────────────────────

def test_doc_manifest_exists_and_has_ingested_docs():
    """
    data/doc_manifest.json must exist with at least 5 docs having doc_ids.
    (Free-tier limit: 5 docs. Upgrade PageIndex account for full corpus.)
    """
    manifest_path = REPO_ROOT / "data" / "doc_manifest.json"
    assert manifest_path.exists(), (
        "data/doc_manifest.json does not exist — run scripts/seed_pageindex_corpus.py"
    )

    manifest = json.loads(manifest_path.read_text())
    assert len(manifest) >= 30, f"Manifest should have >= 30 doc entries, got {len(manifest)}"

    total_with_ids = sum(1 for v in manifest.values() if v.get("doc_id"))
    # Free tier: 5 docs. Full corpus requires paid account.
    assert total_with_ids >= 5, (
        f"Expected >= 5 docs with doc_id (free tier minimum), got {total_with_ids}. "
        "Run scripts/seed_pageindex_corpus.py to ingest."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Criterion 5: Ethics review files for all 5 parties
# ─────────────────────────────────────────────────────────────────────────────

def test_ethics_review_files_exist_for_all_parties():
    """All 5 parties must have REVIEW.md files with required sections."""
    party_ids = ["party-cr", "party-nc", "party-ac", "party-lf", "party-sd"]
    for party_id in party_ids:
        review_file = SKILLS_DIR / party_id / "REVIEW.md"
        assert review_file.exists(), f"Missing REVIEW.md: {review_file}"
        content = review_file.read_text(encoding="utf-8")
        assert "## Reviewer A" in content, f"{party_id}/REVIEW.md missing '## Reviewer A' section"
        assert "## Reviewer B" in content, f"{party_id}/REVIEW.md missing '## Reviewer B' section"
        assert "## Verdict" in content, f"{party_id}/REVIEW.md missing '## Verdict' section"
        assert "## Corrections Applied" in content, (
            f"{party_id}/REVIEW.md missing '## Corrections Applied' section"
        )


def test_no_real_mp_names_in_party_skills():
    """
    Spot-check that no party SKILL.md contains obvious real politician names
    outside the Output Constraints section.
    """
    known_names = [
        "tusk", "morawiecki", "kaczyński", "biedroń",
        "hołownia", "kosiniak", "bosak", "mentzen",
    ]
    party_ids = ["party-cr", "party-nc", "party-ac", "party-lf", "party-sd"]
    for party_id in party_ids:
        content = (SKILLS_DIR / party_id / "SKILL.md").read_text(encoding="utf-8").lower()
        constraints_idx = content.find("## output constraints")
        for name in known_names:
            name_idx = content.find(name)
            if name_idx != -1:
                # Only acceptable if inside Output Constraints section
                assert constraints_idx != -1 and name_idx >= constraints_idx, (
                    f"{party_id}/SKILL.md contains real politician name '{name}' "
                    f"outside Output Constraints section (at char {name_idx})"
                )

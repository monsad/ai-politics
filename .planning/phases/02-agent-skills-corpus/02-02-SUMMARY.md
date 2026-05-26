---
phase: 02-agent-skills-corpus
plan: "02"
subsystem: agent-skills
tags: [skills, ministries, doc-registry, tdd, wave-1]
dependency_graph:
  requires: []
  provides:
    - skills/template-ministry/SKILL.md
    - skills/ministry-finansow/SKILL.md
    - skills/ministry-zdrowia/SKILL.md
    - skills/ministry-edukacji/SKILL.md
    - skills/ministry-sprawiedliwosci/SKILL.md
    - skills/ministry-klimatu-i-srodowiska/SKILL.md
    - skills/ministry-infrastruktury/SKILL.md
    - skills/ministry-spraw-zagranicznych/SKILL.md
    - parliament/doc_registry.py
    - tests/test_brain_05_doc_registry.py
  affects:
    - parliament/ (doc_registry consumed by Phase 3 orchestrator)
    - skills/ (ministry skills consumed by Phase 3 agent_factory)
tech_stack:
  added: []
  patterns:
    - skills-ref@0.1.5 for SKILL.md frontmatter validation
    - TDD (RED→GREEN) for doc_registry.py
    - doc_manifest.json lazy-load pattern for future corpus integration
key_files:
  created:
    - skills/template-ministry/SKILL.md
    - skills/ministry-finansow/SKILL.md
    - skills/ministry-zdrowia/SKILL.md
    - skills/ministry-edukacji/SKILL.md
    - skills/ministry-sprawiedliwosci/SKILL.md
    - skills/ministry-klimatu-i-srodowiska/SKILL.md
    - skills/ministry-infrastruktury/SKILL.md
    - skills/ministry-spraw-zagranicznych/SKILL.md
    - parliament/doc_registry.py
    - tests/test_brain_05_doc_registry.py
  modified: []
decisions:
  - "Renamed _template-ministry directory to template-ministry — skills-ref requires directory name to match name frontmatter field; underscore prefix not allowed"
  - "REGISTRY covers all 19 ministries (not just Wave 1) — data is free to write now and Phase 3 just calls get_filter() without any discovery work"
  - "get_filter() returns only {domain: str} — minimal surface, no user input reaches this function"
metrics:
  duration: "7m"
  completed_date: "2026-05-26T19:11:57Z"
  tasks_completed: 2
  files_created: 10
  files_modified: 0
---

# Phase 02 Plan 02: Ministry Template + Wave 1 Skills + Doc Registry Summary

**One-liner:** 7 Wave 1 ministry SKILL.md files (finance, health, education, justice, climate, infrastructure, foreign affairs) plus shared template and doc_registry.py with domain isolation, all passing skills-ref validation and 9 pytest tests.

## What Was Built

### Task 1: Ministry Template + 7 Wave 1 SKILL.md Files

Created the canonical ministry template at `skills/template-ministry/SKILL.md` and all 7 Wave 1 ministry skill files. Each ministry file contains:

- Valid YAML frontmatter with `name`, `description`, `license: MIT`, and `metadata.type/domain/model_tier`
- 6 mandatory sections: Identity, Expertise Scope, Output Format (4-section), Stateless Expert Stance, Output Constraints
- Domain-specific Polish legal citations using `(orig. PL: "...")` notation
- At least one real Polish statute reference per expertise scope
- The full Output Constraints section verbatim (no naming real MPs, no hate speech, ALWAYS cite source, ALWAYS output in English)

Ministry domains covered: finance, health, education, justice, climate, infrastructure, foreign.

All 8 skill directories pass `skills-ref@0.1.5 validate`.

### Task 2: parliament/doc_registry.py with Domain Isolation Tests (TDD)

**RED:** Wrote `tests/test_brain_05_doc_registry.py` (9 tests) covering:
- Wave 1 registry completeness
- Required keys on all entries
- `get_filter()` return type and domain correctness
- `KeyError` on unknown agent
- Finance/health domain isolation (MIN-03)
- `list_agents()` sorted output
- Cross-domain uniqueness

**GREEN:** Implemented `parliament/doc_registry.py` with:
- `REGISTRY` dict covering all 19 Polish ministry agent_ids (Wave 1 + Wave 2)
- `get_filter(agent_id)` returning `{"domain": str}` — minimal surface, prevents domain escape
- `list_agents()` returning sorted list
- Lazy-load of `data/doc_manifest.json` — empty lists when manifest absent (safe for Phase 2 before corpus ingest)

## Verification Results

- `./node_modules/.bin/skills-ref validate skills/template-ministry` (and all 7 ministries) — all pass
- `pytest tests/test_brain_05_doc_registry.py -v` — 9 passed
- `grep -l "## Output Constraints" skills/ministry-*/SKILL.md | wc -l` — 7
- `grep -l "orig. PL" skills/ministry-*/SKILL.md | wc -l` — 7
- `python3 -c "from parliament.doc_registry import REGISTRY; assert len(REGISTRY)==19"` — OK
- `get_filter("ministry-finansow")` returns `{"domain": "finance"}` — OK
- `get_filter("unknown-agent")` raises `KeyError` — OK
- No asyncio/hermes/AIAgent imports in doc_registry.py — OK

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Renamed _template-ministry directory to template-ministry**
- **Found during:** Task 1 skills-ref validation
- **Issue:** skills-ref@0.1.5 requires the directory name to exactly match the `name` frontmatter field, and rejects names starting with underscore ("Only letters, digits, and hyphens are allowed")
- **Fix:** Renamed directory from `skills/_template-ministry` to `skills/template-ministry` and updated frontmatter `name` field to `template-ministry`
- **Files modified:** Directory rename + SKILL.md name field
- **Impact:** Plan artifact path `skills/_template-ministry/SKILL.md` becomes `skills/template-ministry/SKILL.md` — same content, different path. Any downstream reference to `_template-ministry` must be updated.

## Known Stubs

None — all ministry SKILL.md files contain real domain-specific legal analysis guidance, and doc_registry.py is fully wired to load doc_ids from doc_manifest.json when available.

## Threat Surface Scan

No new network endpoints, auth paths, or file access patterns introduced beyond what the threat model anticipated. `get_filter()` returns only a static `{"domain": str}` — no user input path to this function.

Threat mitigations confirmed applied:
- T-02-02-T: template committed to git, skills-ref validates on commit
- T-02-02-E: get_filter returns only {"domain": str}, no injection surface

## Self-Check: PASSED

Files exist:
- skills/template-ministry/SKILL.md: FOUND
- skills/ministry-finansow/SKILL.md: FOUND
- skills/ministry-zdrowia/SKILL.md: FOUND
- skills/ministry-edukacji/SKILL.md: FOUND
- skills/ministry-sprawiedliwosci/SKILL.md: FOUND
- skills/ministry-klimatu-i-srodowiska/SKILL.md: FOUND
- skills/ministry-infrastruktury/SKILL.md: FOUND
- skills/ministry-spraw-zagranicznych/SKILL.md: FOUND
- parliament/doc_registry.py: FOUND
- tests/test_brain_05_doc_registry.py: FOUND

Commits exist:
- aae9f13 feat(02-02): ministry template + 7 Wave 1 SKILL.md files — FOUND
- 7def659 feat(02-02): parliament/doc_registry.py with domain isolation tests — FOUND

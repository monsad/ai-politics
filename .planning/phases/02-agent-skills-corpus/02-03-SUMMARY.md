---
plan: 02-03
phase: 02-agent-skills-corpus
status: complete
completed: 2026-05-27
---

# Plan 02-03: Party Agent Profiles — Summary

## What Was Built

**Task 1:** 5 party SKILL.md files with full ideological profiles (850–1100 words each):
- `skills/party-ko/SKILL.md` — KO, liberal-center, 157 seats
- `skills/party-pis/SKILL.md` — PiS, national-conservative, 194 seats
- `skills/party-td/SKILL.md` — TD, centrist-agrarian, 65 seats
- `skills/party-konfederacja/SKILL.md` — Konfederacja, libertarian-nationalist, 18 seats
- `skills/party-lewica/SKILL.md` — Lewica, left-progressive, 26 seats

All 5 cover all 8 canonical debate topics; all include mandatory Output Constraints; all pass `npx skills-ref@0.1.5 validate`.

**Task 2:** 5 REVIEW.md ethics review files documenting dual-perspective (progressive + conservative) LLM-pair review:
- Konfederacja: immigration language reviewed, nationality/ethnicity distinction added
- PiS: "liberal elites" framing noted as rhetorical device, not factual descriptor
- Lewica: education section corrected from "remove" to "make optional" for religious instruction
- KO: rural voter note added; "restorer of norms" qualified as self-characterization
- TD: flat tax agricultural context clarified; cultural war avoidance noted

All 5 REVIEW.md files: Reviewer A + Reviewer B sections, Corrections Applied table, Verdict.

## Key Files Created

- `skills/party-*/SKILL.md` (5 files) — full party profiles
- `skills/party-*/REVIEW.md` (5 files) — ethics review audit trail

## Commits

- `e8a34b5` — feat(02-03): write 5 party SKILL.md files with full ideological profiles
- `13fe271` — feat(02-03): LLM-pair ethics review + REVIEW.md for all 5 party agents

## Verification

- All 5 party SKILL.md: valid per skills-ref@0.1.5
- Seats correct: KO=157, PiS=194, TD=65, Konfederacja=18, Lewica=26
- KO vs Konfederacja flat tax divergence: confirmed
- No real MP names in any profile
- All 8 canonical topics covered by all 5 parties
- 5 REVIEW.md files with dual-reviewer structure and corrections documented

## Self-Check: PASSED

All must-haves from plan frontmatter satisfied.

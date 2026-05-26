---
phase: 01-foundation-smoke-tests
plan: 02
type: execute
wave: 1
depends_on: []
files_modified:
  - skills/party-ko/SKILL.md
  - .pre-commit-config.yaml
  - .github/workflows/ci.yml
  - tests/test_gate_06_skills_ref.py
autonomous: true
requirements: [INFRA-03, GATE-06]
requirements_addressed: [INFRA-03, GATE-06]
must_haves:
  truths:
    - "npx skills-ref@0.1.5 validate skills/party-ko exits 0 on minimal SKILL.md"
    - "pre-commit hook runs skills-ref validate on every commit"
    - "CI workflow runs skills-ref validate + the token-budget test on every push"
  artifacts:
    - path: "skills/party-ko/SKILL.md"
      provides: "Minimal valid SKILL.md template (placeholder for Phase 2)"
      contains: "name: party-ko"
    - path: ".pre-commit-config.yaml"
      provides: "Pre-commit hook running skills-ref validate"
      contains: "skills-ref"
    - path: ".github/workflows/ci.yml"
      provides: "GitHub Actions CI running skills-ref + pytest"
      contains: "skills-ref"
    - path: "tests/test_gate_06_skills_ref.py"
      provides: "Gate-06 test that asserts skills-ref validate exits 0"
      exports: ["test_gate_06_skills_ref_validates_party_ko"]
  key_links:
    - from: "tests/test_gate_06_skills_ref.py"
      to: "skills/party-ko/SKILL.md"
      via: "subprocess.run(['npx', 'skills-ref@0.1.5', 'validate', 'skills/party-ko'])"
      pattern: "skills-ref"
    - from: ".pre-commit-config.yaml"
      to: "skills/"
      via: "local hook running npx skills-ref validate"
      pattern: "skills-ref"
---

<objective>
Wire `skills-ref@0.1.5` validation into both pre-commit (INFRA-03) and a passing pytest test (GATE-06). Wave 1 — no Python deps required at runtime; the test shells out to `npx`. Can run in parallel with Plan 01.

Purpose: Block any future commit that introduces an invalid SKILL.md (frontmatter mistake, ASCII violation, missing required field). The minimal `party-ko` skill exists ONLY as the validator's smoke target — Phase 2 (PARTY-01) replaces its body with real ideology.
Output: One minimal SKILL.md, a pre-commit config, a GitHub Actions CI workflow, and a pytest test that asserts the validator exits 0.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md
@.planning/REQUIREMENTS.md
@.planning/research/STACK.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Write minimal valid SKILL.md for party-ko</name>
  <files>skills/party-ko/SKILL.md</files>
  <read_first>
    - /Users/xpll081/ai-politics/.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md (sections: Agent Skills format, Specifics — Concrete frontmatter for the smoke-test SKILL.md)
    - /Users/xpll081/ai-politics/.planning/research/STACK.md (Agent Skills Specification — Verified Fields)
  </read_first>
  <action>
Create `/Users/xpll081/ai-politics/skills/party-ko/SKILL.md` with the exact content from CONTEXT.md "Specifics — Concrete frontmatter for the smoke-test SKILL.md":

```markdown
---
name: party-ko
description: Minimal placeholder skill used to validate skills-ref tooling. Real content lands in Phase 2.
license: MIT
metadata:
  type: party
  ideology: liberal-center
  seats: 157
---

# Koalicja Obywatelska — placeholder for GATE-06

This file exists only to prove `skills-ref validate` exits 0 on a minimal
frontmatter. Phase 2 replaces the body wholesale.
```

Important format rules (from CONTEXT.md "Agent Skills format" + STACK.md "Agent Skills Specification — Verified Fields"):
- `name` field MUST be lowercase, hyphens only, no underscores, ASCII only — `party-ko` matches
- `description` MUST be 1–1024 chars, non-empty — the sentence above is ~95 chars
- Frontmatter delimited by `---` on its own lines
- `metadata` is a free-form key-value map per the spec — `seats: 157` is allowed
- YAML indentation uses 2 spaces (NOT tabs — a tab anywhere breaks `skills-ref` per Pitfall 5)
- Description is on a single line (no folded scalar continuation) to avoid the indentation gotcha from Pitfall 5

Do NOT use Polish diacritics in any frontmatter value (only ASCII per locked decision). Body text below the second `---` may contain anything.
  </action>
  <verify>
    <automated>cd /Users/xpll081/ai-politics && npx --yes skills-ref@0.1.5 validate skills/party-ko</automated>
  </verify>
  <acceptance_criteria>
    - `test -f /Users/xpll081/ai-politics/skills/party-ko/SKILL.md` exit 0
    - `head -1 /Users/xpll081/ai-politics/skills/party-ko/SKILL.md` outputs exactly `---`
    - `grep -q "^name: party-ko$" /Users/xpll081/ai-politics/skills/party-ko/SKILL.md` exit 0
    - `grep -q "^description: " /Users/xpll081/ai-politics/skills/party-ko/SKILL.md` exit 0
    - `grep -q "^license: MIT$" /Users/xpll081/ai-politics/skills/party-ko/SKILL.md` exit 0
    - `grep -q "  seats: 157" /Users/xpll081/ai-politics/skills/party-ko/SKILL.md` exit 0
    - NOT-present check: `! grep -P "^\t" /Users/xpll081/ai-politics/skills/party-ko/SKILL.md` (no leading tabs anywhere)
    - NOT-present check (ASCII frontmatter): `python3 -c "import sys; lines=open('/Users/xpll081/ai-politics/skills/party-ko/SKILL.md').read().split('---',2); assert all(ord(c)<128 for c in lines[1]), 'non-ASCII in frontmatter'"` exit 0
    - `cd /Users/xpll081/ai-politics && npx --yes skills-ref@0.1.5 validate skills/party-ko` exit 0
  </acceptance_criteria>
  <done>SKILL.md exists with the verbatim frontmatter from CONTEXT.md, contains zero tab characters, frontmatter is pure ASCII, and `npx skills-ref@0.1.5 validate skills/party-ko` returns exit code 0.</done>
</task>

<task type="auto">
  <name>Task 2: Write .pre-commit-config.yaml + .github/workflows/ci.yml</name>
  <files>.pre-commit-config.yaml, .github/workflows/ci.yml</files>
  <read_first>
    - /Users/xpll081/ai-politics/.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md (sections: Stack — Node side, Claude's Discretion — pre-commit framework + CI provider)
    - /Users/xpll081/ai-politics/skills/party-ko/SKILL.md (the target the hooks validate)
  </read_first>
  <action>
Create two files.

1) `/Users/xpll081/ai-politics/.pre-commit-config.yaml` — use `pre-commit` framework (Claude's discretion per CONTEXT.md). Hook is `local` because `skills-ref` is an npm package, not a pre-commit repo. Verbatim:

```yaml
repos:
  - repo: local
    hooks:
      - id: skills-ref-validate
        name: skills-ref validate
        description: Validate Agent Skills SKILL.md frontmatter against agentskills.io spec
        entry: npx --yes skills-ref@0.1.5 validate skills/
        language: system
        pass_filenames: false
        files: ^skills/.*SKILL\.md$
        always_run: false

      - id: ruff-check
        name: ruff check
        entry: ruff check .
        language: system
        types: [python]
        pass_filenames: false

      - id: ruff-format-check
        name: ruff format --check
        entry: ruff format --check .
        language: system
        types: [python]
        pass_filenames: false
```

Notes:
- `entry: npx --yes skills-ref@0.1.5 validate skills/` validates the WHOLE skills directory (not just the changed file) because INFRA-03 says "commit fails if any skill is invalid" — full-directory check is correct
- `files: ^skills/.*SKILL\.md$` makes the hook only fire when a SKILL.md changed (efficiency)
- `pass_filenames: false` — we want `validate skills/`, not `validate <changed-file>`
- ruff hooks use the system-installed `ruff` (from pyproject.toml dev deps) — no need for pre-commit's bundled mirror

2) `/Users/xpll081/ai-politics/.github/workflows/ci.yml` — GitHub Actions per CONTEXT.md "Claude's Discretion" recommendation. Verbatim:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate-skills:
    name: Validate Agent Skills
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20.18.0'
      - name: Run skills-ref validate
        run: npx --yes skills-ref@0.1.5 validate skills/

  pytest:
    name: Python unit tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install uv
        run: pip install uv
      - name: Install project
        run: |
          uv venv .venv --python 3.11
          . .venv/bin/activate
          uv pip install -e ".[dev]"
      - name: Run TokenBudget unit tests
        run: |
          . .venv/bin/activate
          pytest tests/test_token_budget.py -x
      - name: Run skills-ref gate-06 test
        run: |
          . .venv/bin/activate
          pytest tests/test_gate_06_skills_ref.py -x

  ruff:
    name: Lint (ruff)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ruff==0.8.4
      - run: ruff check .
      - run: ruff format --check .
```

Notes:
- Node 20.18.0 (LTS, satisfies `pageindex-mcp@1.6.3`'s `>=20.8.1` requirement from STACK.md "Version Compatibility")
- Python 3.11 explicit (locked decision from CONTEXT.md)
- CI runs ONLY the cheap unit tests (token budget + gate-06). The expensive gate tests (GATE-01..05, 07) hit real Hermes/PageIndex and would require API keys in CI — we keep those local for now. Phase 3+ can add a secrets-gated workflow.
- `validate-skills` job is the INFRA-03 acceptance lever — if any skill is invalid, CI fails and the PR can't merge.

Also create the `.github/` and `.github/workflows/` directories implicitly via the file write.
  </action>
  <verify>
    <automated>test -f /Users/xpll081/ai-politics/.pre-commit-config.yaml && test -f /Users/xpll081/ai-politics/.github/workflows/ci.yml && python3 -c "import yaml; yaml.safe_load(open('/Users/xpll081/ai-politics/.pre-commit-config.yaml')); yaml.safe_load(open('/Users/xpll081/ai-politics/.github/workflows/ci.yml')); print('ok')"</automated>
  </verify>
  <acceptance_criteria>
    - `test -f /Users/xpll081/ai-politics/.pre-commit-config.yaml` exit 0
    - `test -f /Users/xpll081/ai-politics/.github/workflows/ci.yml` exit 0
    - `python3 -c "import yaml; yaml.safe_load(open('/Users/xpll081/ai-politics/.pre-commit-config.yaml'))"` exit 0 (valid YAML)
    - `python3 -c "import yaml; yaml.safe_load(open('/Users/xpll081/ai-politics/.github/workflows/ci.yml'))"` exit 0
    - `grep -q "skills-ref@0.1.5 validate skills/" /Users/xpll081/ai-politics/.pre-commit-config.yaml` exit 0
    - `grep -q "id: skills-ref-validate" /Users/xpll081/ai-politics/.pre-commit-config.yaml` exit 0
    - `grep -q "skills-ref@0.1.5 validate skills/" /Users/xpll081/ai-politics/.github/workflows/ci.yml` exit 0
    - `grep -q "python-version: '3.11'" /Users/xpll081/ai-politics/.github/workflows/ci.yml` exit 0
    - `grep -q "node-version: '20.18.0'" /Users/xpll081/ai-politics/.github/workflows/ci.yml || grep -q 'node-version: "20.18.0"' /Users/xpll081/ai-politics/.github/workflows/ci.yml` exit 0
    - `grep -q "pytest tests/test_token_budget.py" /Users/xpll081/ai-politics/.github/workflows/ci.yml` exit 0
    - `grep -q "pytest tests/test_gate_06_skills_ref.py" /Users/xpll081/ai-politics/.github/workflows/ci.yml` exit 0
  </acceptance_criteria>
  <done>Both YAML files are valid, contain the skills-ref invocation pinned to 0.1.5, and CI references Python 3.11 + Node 20.18.0.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Write tests/test_gate_06_skills_ref.py (the GATE-06 pytest)</name>
  <files>tests/test_gate_06_skills_ref.py</files>
  <read_first>
    - /Users/xpll081/ai-politics/.planning/phases/01-foundation-smoke-tests/01-CONTEXT.md (section: Specifics — Test acceptance criteria — GATE-06 row)
    - /Users/xpll081/ai-politics/skills/party-ko/SKILL.md (the target of validation)
  </read_first>
  <behavior>
    - Test 1: `subprocess.run(["npx", "--yes", "skills-ref@0.1.5", "validate", "skills/party-ko"])` from repo root returns returncode 0
    - Test 2: A skill folder with deliberately broken frontmatter (e.g. missing `name`) makes the same command return non-zero (proves the validator actually catches errors, not just accepts everything)
    - Skipif: if `npx` is not on PATH, skip with a clear message (so the test isn't a false-fail on a machine without Node yet)
  </behavior>
  <action>
Create `/Users/xpll081/ai-politics/tests/test_gate_06_skills_ref.py`:

```python
"""GATE-06 — skills-ref validates the minimal party-ko SKILL.md.

Locked acceptance: `npx skills-ref@0.1.5 validate skills/party-ko` exits 0.
Also asserts the validator rejects a deliberately broken skill — so a future
typo can't silently be considered valid.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
PARTY_KO_PATH = REPO_ROOT / "skills" / "party-ko"

requires_npx = pytest.mark.skipif(
    shutil.which("npx") is None,
    reason="npx not on PATH — install Node.js >=20.8.1 to run GATE-06",
)


@requires_npx
def test_gate_06_skills_ref_validates_party_ko():
    """Locked acceptance: skills-ref@0.1.5 validate skills/party-ko exits 0."""
    assert PARTY_KO_PATH.is_dir(), f"Missing skill folder: {PARTY_KO_PATH}"
    assert (PARTY_KO_PATH / "SKILL.md").is_file(), "Missing SKILL.md"

    result = subprocess.run(
        ["npx", "--yes", "skills-ref@0.1.5", "validate", "skills/party-ko"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"skills-ref validate failed (exit {result.returncode})\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


@requires_npx
def test_gate_06_skills_ref_rejects_broken_skill(tmp_path: Path):
    """Sanity: the validator actually catches bad frontmatter, not just rubber-stamps.

    Creates a temporary skills dir with a SKILL.md that is missing `name` and
    asserts skills-ref exits non-zero.
    """
    broken_skills_dir = tmp_path / "skills" / "broken-skill"
    broken_skills_dir.mkdir(parents=True)
    (broken_skills_dir / "SKILL.md").write_text(
        "---\n"
        "description: missing required name field\n"
        "---\n"
        "# broken\n"
    )

    result = subprocess.run(
        ["npx", "--yes", "skills-ref@0.1.5", "validate", "skills/broken-skill"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode != 0, (
        "Expected non-zero exit for missing `name` field, got 0.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
```

Implementation notes:
- Uses `subprocess.run` not asyncio — `skills-ref` is a CLI, sync is fine
- `cwd=REPO_ROOT` ensures the validator finds `skills/party-ko` regardless of where pytest was invoked
- `--yes` to `npx` avoids the interactive "Need to install" prompt that hangs CI
- `timeout=180` matches CONTEXT.md MCP timeout convention and gives `npx` time to download `skills-ref` on first run
- `requires_npx` skip-marker is cleaner than failing if Node isn't installed yet — Plan 03 doesn't need npx and shouldn't be blocked by it
- The second test creates a *broken* skill in `tmp_path` so it doesn't pollute the real `skills/` directory and won't be picked up by pre-commit
  </action>
  <verify>
    <automated>cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -m pytest tests/test_gate_06_skills_ref.py -x --tb=short</automated>
  </verify>
  <acceptance_criteria>
    - `test -f /Users/xpll081/ai-politics/tests/test_gate_06_skills_ref.py` exit 0
    - `grep -q "skills-ref@0.1.5" /Users/xpll081/ai-politics/tests/test_gate_06_skills_ref.py` exit 0
    - `grep -q "test_gate_06_skills_ref_validates_party_ko" /Users/xpll081/ai-politics/tests/test_gate_06_skills_ref.py` exit 0
    - `grep -q "test_gate_06_skills_ref_rejects_broken_skill" /Users/xpll081/ai-politics/tests/test_gate_06_skills_ref.py` exit 0
    - `cd /Users/xpll081/ai-politics && PYTHONPATH=. python3 -m pytest tests/test_gate_06_skills_ref.py -x` exits 0 (assuming `npx` on PATH — if not, both tests skip with a clear reason, which is also acceptable since they will run in CI where Node IS installed)
    - When run in CI (Node 20.18.0 present), `pytest tests/test_gate_06_skills_ref.py -x` returns exit code 0 with both tests collected and passing.
  </acceptance_criteria>
  <done>The pytest file imports cleanly; both tests pass locally when `npx` is available (or both skip cleanly when it isn't); the broken-skill negative test proves the validator isn't a no-op.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| developer commit → `main` branch | Pre-commit hook intercepts invalid SKILL.md before it lands; CI catches anything that slipped past pre-commit (e.g. `--no-verify`) |
| `skills-ref@0.1.5` (npm package) → repo | Trusted dependency pinned to exact version; transitive packages execute on `npx` install |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-01 | Tampering | `skills-ref` validator bypass | mitigate | Pre-commit + CI both run the same `skills-ref@0.1.5 validate skills/` invocation; a developer who skips pre-commit (`--no-verify`) will be caught by the CI `validate-skills` job before merge |
| T-02-02 | Tampering | malicious skill content executing on `npx skills add` (Phase 2) | accept | Out of scope for this plan; `skills add` runs in Plan 03 (Hermes install) and is documented in CLAUDE.md as a trusted Vercel Labs CLI |
| T-02-03 | Denial of Service | `npx skills-ref@0.1.5` re-downloads on every commit | accept | npm cache makes this fast after first run; pinned version means cache hit is reliable |
| T-02-04 | Spoofing | typo-squatted `skills-ref` package | mitigate | Pinned to exact version `0.1.5` and exact name; STACK.md verified live 2026-05-26 that this is the canonical Vercel Labs package |
</threat_model>

<verification>
After all three tasks complete, run from repo root:

```bash
# Minimal skill exists and is well-formed
test -f skills/party-ko/SKILL.md
! grep -P "^\t" skills/party-ko/SKILL.md  # no tabs

# Validator passes on the real skill
npx --yes skills-ref@0.1.5 validate skills/party-ko

# YAML files are syntactically valid
python3 -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml'))"
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"

# Pytest GATE-06 passes
PYTHONPATH=. python3 -m pytest tests/test_gate_06_skills_ref.py -x
```

All commands exit 0.
</verification>

<success_criteria>
- `skills/party-ko/SKILL.md` exists with valid frontmatter (GATE-06 target)
- `npx skills-ref@0.1.5 validate skills/party-ko` returns exit 0 (GATE-06)
- `.pre-commit-config.yaml` runs `skills-ref validate skills/` on commit (INFRA-03)
- `.github/workflows/ci.yml` runs `skills-ref validate skills/` + pytest on push (INFRA-03)
- `tests/test_gate_06_skills_ref.py` passes and includes a negative test proving the validator catches real errors
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation-smoke-tests/01-02-SUMMARY.md`.
</output>

#!/usr/bin/env bash
# BRAIN-02 — install mmtmr/pageindex-rag external skill globally via skills CLI.
# Idempotent: re-running is safe (skills CLI handles "already installed" gracefully).

set -euo pipefail

echo "[BRAIN-02] Installing mmtmr/pageindex-rag globally (npx skills add -g -y)..."
npx --yes skills@1.5.7 add mmtmr/pageindex-rag -g -y

# Verify the skill landed in ~/.hermes/skills/ (locked path per CONTEXT.md).
SKILL_DIR="${HOME}/.hermes/skills/pageindex-rag"
if [ -d "${SKILL_DIR}" ]; then
  echo "[BRAIN-02] OK — skill installed at ${SKILL_DIR}"
else
  echo "[BRAIN-02] WARN — skill not found at expected path ${SKILL_DIR}"
  echo "[BRAIN-02] Check: ls ~/.hermes/skills/ to find actual install location"
  exit 1
fi

echo "[BRAIN-02] Done."

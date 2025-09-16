#!/usr/bin/env bash
set -euo pipefail

# Run Codex audit
cat meta/prompts/audit.json | codex exec \
  -m gpt-5-codex \
  -c model="gpt-5-codex" \
  --sandbox workspace-write

# Verify labs_state.md was written
if test -s meta/output/labs_state.md; then
  echo "labs_state.md generated successfully"
else
  echo "ERROR: labs_state.md not generated"
  exit 1
fi

# Check if AGENTS.md changed
if git diff --quiet AGENTS.md; then
  echo "AGENTS.md unchanged"
else
  echo "AGENTS.md updated"
fi

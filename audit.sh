#!/usr/bin/env bash
set -euo pipefail

cat meta/prompts/audit.json | codex exec \
  -m gpt-5-codex \
  -c model="gpt-5-codex" \
  --sandbox workspace-write

# Verify audit actually wrote output
test -s meta/output/labs_state.md || { echo "ERROR: labs_state.md not generated"; exit 1; }

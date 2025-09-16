#!/usr/bin/env bash
set -euo pipefail

# Run audit.json with gpt-5-codex explicitly
codex exec \
  -m gpt-5-codex \
  -c model="gpt-5-codex" \
  --sandbox workspace-write \
  -a on-failure \
  meta/prompts/audit.json



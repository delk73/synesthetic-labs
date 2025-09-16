#!/usr/bin/env bash
set -euo pipefail

cat meta/prompts/audit.json| codex exec \
  -m gpt-5-codex \
  -c model="gpt-5-codex" \
  --sandbox workspace-write \
  apply
#!/usr/bin/env bash
set -euo pipefail

# Run emit.json with gpt-5-codex explicitly
codex exec -m gpt-5-codex -c model="gpt-5-codex" meta/prompts/emit.json

#!/usr/bin/env bash
set -euo pipefail

echo "[reset] Nuking Codex-emitted source and audit artefacts..."

# Remove emitted code and harness
rm -rf labs
rm -rf tests
rm -f requirements.txt
rm -f Dockerfile docker-compose.yml test.sh

# Remove audit/emit artefacts
rm -rf meta/output
rm -f AGENTS.md

# Clean caches
rm -rf **/__pycache__ .pytest_cache

# Recreate output dir for next audit
mkdir -p meta/output

echo "[reset] Done. Repo reset to canon (meta/prompts + docs/* + README.md)."

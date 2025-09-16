#!/usr/bin/env bash
set -euo pipefail

# Delete all local branches except main
git branch | grep -v "main" | xargs git branch -D || true

# Make sure we’re up to date
git fetch origin main
git checkout main
git pull origin main

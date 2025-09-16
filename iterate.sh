#!/usr/bin/env bash
set -euo pipefail

# 1. Emit the repo
./emit.sh

# 2. Run audit
./audit.sh

# 3. Check audit output for Missing/Divergent
if grep -qE 'Missing|Divergent' meta/output/labs_state.md; then
  echo "⚠️  Issues detected in audit. Re-emitting…"
  exit 1   # or loop back to emit.sh until clean
else
  echo "✅ Audit clean — iteration complete."
fi

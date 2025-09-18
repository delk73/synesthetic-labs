#!/usr/bin/env bash
set -euo pipefail

echo "[labs-e2e] Running generator → critic against live MCP..."

# Fallback defaults: assume MCP is on local Docker network
MCP_HOST="${MCP_HOST:-localhost}"
MCP_PORT="${MCP_PORT:-7000}"
SYN_SCHEMAS_DIR="${SYN_SCHEMAS_DIR:-libs/synesthetic-schemas}"

echo "[labs-e2e] Using MCP_HOST=$MCP_HOST MCP_PORT=$MCP_PORT SYN_SCHEMAS_DIR=$SYN_SCHEMAS_DIR"

# Step 1: Generate a candidate asset
GEN_OUT=$(python -m labs.cli generate "a simple test asset with one circle")
echo "$GEN_OUT" > /tmp/labs_gen.json

# Step 2: Critique the generated asset with MCP validation
set +e
CRIT_OUT=$(python -m labs.cli critique "$(cat /tmp/labs_gen.json)")
CRIT_EXIT=$?
set -e

echo "[labs-e2e] Critic output:"
echo "$CRIT_OUT"

# Step 3: Parse success/failure
if [ $CRIT_EXIT -eq 0 ] && echo "$CRIT_OUT" | grep -q '"ok": true'; then
  echo "[labs-e2e] ✅ End-to-end validation succeeded"
  exit 0
else
  echo "[labs-e2e] ❌ End-to-end validation failed"
  exit 1
fi

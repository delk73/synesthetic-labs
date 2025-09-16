#!/usr/bin/env bash
set -euo pipefail

# Run emit.json with gpt-5-codex explicitly
#!/usr/bin/env bash
set -euo pipefail

codex exec \
  -m gpt-5-codex \
  -c model="gpt-5-codex" \
  --sandbox workspace-write \
  meta/prompts/emit.json




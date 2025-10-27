# Reset Process - Synesthetic Labs v2

## Overview

This document describes the reset process to transition from v0.3.6a (archived) to v2 (minimal schema-driven implementation).

## Context

v0.3.6a failed to achieve MCP validation due to fundamental architectural issues:
- Schema authority confusion (stub files vs MCP)
- Hardcoded template generators
- Premature abstraction layers
- Tests validating against wrong schemas

See `LESSONS_LEARNED.md` for full details.

## Reset Goals

1. **Preserve working infrastructure**: MCP client, Docker, tests that prove connectivity
2. **Remove broken complexity**: Generators, agents, experimental code, normalization layers
3. **Create clean foundation**: Minimal working state ready for schema-driven v2 rebuild

## What We Keep

### ✅ MCP Infrastructure (Proven Working)
- `labs/mcp/` - Complete MCP client implementation
  - `client.py` - Fetches schemas, validates assets
  - `validate.py` - Validation logic
  - `exceptions.py` - Error types
  - Transport implementations (TCP, socket, stdio)
- `mcp/` - MCP server core
- MCP tests: `test_mcp*.py`, `test_socket.py`, `test_tcp.py`

### ✅ Documentation & Archives
- `meta/` - Complete directory
  - `meta/archive/` - v0.3.6a zip archive
  - `meta/prompts/` - Standup and reset scripts
  - `meta/schemas/` - Reference schemas (MCP is still authority)
  - `meta/output/` - Logs and telemetry
- `docs/` - Documentation directory (will be updated for v2)
- `LESSONS_LEARNED.md` - Critical context from v0.3.6a

### ✅ Infrastructure
- Docker files: `Dockerfile`, `docker-compose.yml`
- CI/CD: `.github/workflows/`
- Editor config: `.vscode/`
- Git config: `.gitignore`
- Dependencies: `requirements.txt` (will be trimmed)

## What We Remove

### ❌ Broken Generators
- `labs/generator/` - Entire directory
  - `assembler.py` - Complex orchestration
  - `shader.py`, `tone.py`, `control.py`, `haptic.py` - Hardcoded templates
  - `meta.py` - Template-based metadata
  - `external.py` - Azure/Gemini integration (will rebuild in v2)

**Why**: Generators used hardcoded templates instead of reading from MCP schema. Output structure didn't match MCP requirements.

### ❌ Premature Features
- `labs/agents/` - Critic and generator agents added before core worked
- `labs/experimental/` - Experimental code built on broken foundation
- `labs/experiments/` - Prompt experiments from v0.3.6a
- `labs/lifecycle/` - Patch/normalization system we shouldn't need

**Why**: Features added before proving basic MCP validation. Built on unvalidated assumptions.

### ❌ Cruft Files
- `labs/patches.py` - Normalization band-aids
- `labs/mcp_stub.py` - Stub server (not needed)
- `labs/transport.py` - If redundant with mcp/ implementations
- `labs/mcp_stdio.py` - If redundant with mcp/ implementations

### ❌ v0.3.6a Scripts
- `audit.sh`, `clear.sh`, `e2e.sh`, `nuke.sh`, `test.sh` - Old workflow scripts
- `notes.md` - Development notes from v0.3.6a
- `AGENTS.md` - State report from v0.3.6a (in archive)

### ❌ Non-MCP Tests
All generator/feature tests that validated against wrong schemas:
- `test_generator*.py` - All generator tests
- `test_critic.py` - Critic agent tests
- `test_pipeline.py` - Pipeline tests
- `test_patches.py` - Normalization tests
- `test_prompt_experiment.py` - Experiment tests
- `test_external_generator.py` - External generator tests
- `test_ratings.py`, `test_determinism.py`, `test_cli_logging.py`, etc.

**Keep only**: MCP connectivity/validation tests that prove infrastructure works.

## Step-by-Step Reset Procedure

### Step 1: Verify Archive Exists
```bash
ls -lh meta/archived/archive-v0.3.6a.zip
# Should see ~15MB file
```

**Critical**: Don't proceed if archive is missing. v0.3.6a must be safely stored.

**Note**: Archive only contains `.env.example` files (safe templates), never actual `.env` secrets.

### Step 2: Remove Cruft Directories
```bash
rm -rf labs/agents/
rm -rf labs/experimental/
rm -rf labs/experiments/
rm -rf labs/lifecycle/
rm -rf labs/datasets/
rm -rf labs/generator/
```

### Step 3: Remove Cruft Files
```bash
rm -f labs/cli.py
rm -f labs/patches.py
rm -f labs/mcp_stub.py
rm -f .env labs/.env
rm -f audit.sh clear.sh e2e.sh nuke.sh test.sh
rm -f notes.md AGENTS.md
```

**Note**: `labs/transport.py` and `labs/mcp_stdio.py` are KEPT - they're required by MCP client.

### Step 3b: Update labs/__init__.py
```bash
cat > labs/__init__.py << 'EOF'
"""Synesthetic Labs v2 - Minimal schema-driven generator."""

__version__ = "2.0.0"

__all__ = []
EOF
```

### Step 4: Clean Tests Directory
```bash
cd tests/
# Remove all non-MCP tests
rm -f test_generator*.py test_critic.py test_pipeline.py test_patches.py
rm -f test_prompt_experiment.py test_external_generator.py test_ratings.py
rm -f test_determinism.py test_cli_logging.py test_logging.py test_path_guard.py
cd ..
```

**Verify**: `ls tests/` should show only:
- `conftest.py`
- `test_mcp.py`
- `test_mcp_validator.py`
- `test_mcp_schema_pull.py`
- `test_socket.py`
- `test_tcp.py`

### Step 5: Verify MCP Infrastructure Intact
```bash
ls labs/mcp/
# Should see: client.py, validate.py, exceptions.py, __init__.py, etc.

ls mcp/
# Should see: core.py, __init__.py
```

### Step 6: Verify Documentation Preserved
```bash
ls meta/archived/
# Should see: archive-v0.3.6a.zip

ls meta/prompts/
# Should see: v2standup.json, reset.json

ls docs/
# Should see preserved docs
```

### Step 7: Trim requirements.txt
Edit `requirements.txt` to minimal dependencies:

```txt
# MCP Client
httpx>=0.27.0
jsonschema>=4.23.0
pydantic>=2.8.0

# Environment
python-dotenv>=1.0.1

# Testing
pytest>=8.3.0
pytest-asyncio>=0.24.0
```

**Remove**: Azure SDK, Gemini SDK, Anthropic SDK (will add back in v2 phase 2.1 if needed)

### Step 8: Update README.md
Update the existing `README.md` for v2 (keep the file, update content):

```markdown
# Synesthetic Labs v2

Minimal schema-driven synesthetic asset generator with MCP validation.

## Status

🏗️ **Under reconstruction** - v0.3.6a archived, building minimal v2

## Architecture

- **MCP Client**: Proven working infrastructure (preserved from v0.3.6a)
- **Schema Authority**: MCP is single source of truth
- **Generation**: Schema-driven (not template-based)

## Setup

See `meta/prompts/v2standup.json` for rebuild process.

## Documentation

- `LESSONS_LEARNED.md` - Context from v0.3.6a failures
- `docs/reset_process.md` - This reset procedure
- `meta/prompts/v2standup.json` - Step-by-step v2 rebuild guide

## Archive

v0.3.6a archived in `meta/archived/archive-v0.3.6a.zip`

**Note**: Archive contains only `.env.example` files (safe templates), never actual secrets.

## Next Steps

1. Read `LESSONS_LEARNED.md` for context
2. Follow `meta/prompts/v2standup.json` to build v2
3. Prove minimal generator passes MCP validation
4. Extend incrementally
```

### Step 9: Verify MCP Tests Pass
```bash
pytest tests/test_mcp.py -v
pytest tests/test_mcp_validator.py -v
pytest tests/test_mcp_schema_pull.py -v
```

**Expected**: All MCP tests should pass, proving infrastructure works after cleanup.

If tests fail, something essential was deleted - check what's missing.

### Step 10: Commit Reset State
```bash
git add -A
git commit -m "Reset to minimal foundation - MCP infrastructure only

- Preserved: labs/mcp/, mcp/, meta/, docs/, Docker infrastructure
- Removed: labs/generator/, labs/agents/, labs/experimental/, etc.
- v0.3.6a archived in meta/archive/
- Ready for v2 rebuild following meta/prompts/v2standup.json"

git push
```

## Post-Reset State

After reset, the repo has:

### ✅ Working Infrastructure
- MCP client fully functional (`labs/mcp/`)
- MCP tests passing (prove connectivity)
- Docker deployment infrastructure
- v0.3.6a safely archived (`meta/archive/`)
- Complete documentation (LESSONS_LEARNED.md, v2standup.json, reset.json)

### ❌ Removed Complexity
- Hardcoded template generators deleted
- Critic/generator agents deleted
- Experimental modules deleted
- Patch/normalization layers deleted
- Non-MCP tests deleted
- v0.3.6a cruft scripts deleted

### 🚀 Ready For
v2 rebuild following `meta/prompts/v2standup.json`:
1. Create schema-driven generator
2. Write validation test
3. TDD loop until MCP validation passes
4. Extend incrementally

## Validation Checklist

Before proceeding to v2 rebuild, verify:

- [ ] Archive exists: `meta/archived/archive-v0.3.6a.zip` (~15MB)
- [ ] No secrets in repo: `git ls-files | grep -E '^\\.env$'` returns nothing
- [ ] Transport files kept: `labs/transport.py` and `labs/mcp_stdio.py` exist
- [ ] MCP client intact: `labs/mcp/client.py` exists
- [ ] MCP tests pass: `pytest tests/test_mcp.py -v` succeeds
- [ ] Generator code removed: `labs/generator/` doesn't exist
- [ ] Clean git status: `git status` shows working tree clean (after commit)
- [ ] Prompts preserved: `meta/prompts/v2standup.json` and `reset.json` exist
- [ ] Documentation updated: `README.md` describes v2 approach
- [ ] Requirements trimmed: No Azure/Gemini SDKs in `requirements.txt`

## Next Steps

After reset validation passes:

1. **Read context**: `LESSONS_LEARNED.md` - Understand what went wrong in v0.3.6a
2. **Follow standup**: `meta/prompts/v2standup.json` - Step-by-step v2 rebuild
3. **TDD approach**: Write test first, then make it pass
4. **Prove core**: Get `test_validation.py` passing with MCP strict validation
5. **Extend carefully**: Add features one at a time, validating at each step

## Key Principles for v2

1. **MCP is authority** - Never cache schemas to disk as "reference"
2. **Schema-driven** - Read structure from MCP, don't hardcode templates
3. **Test-first** - Prove MCP validation before adding features
4. **Minimal core** - Single generator, single test, then extend
5. **No normalization** - Generators output correct structure initially

## Emergency Recovery

If reset goes wrong, recover from archive:

```bash
# Extract v0.3.6a archive
cd /tmp
unzip /path/to/synesthetic-labs/meta/archived/archive-v0.3.6a.zip -d v0.3.6a-recovery

# Or restore from git history
git log --oneline  # Find commit before reset
git checkout <commit-hash>
```

The archive preserves the complete v0.3.6a state for reference or recovery.

---

**Reset Status**: Ready to execute
**Next Action**: Follow Step 1 - Verify Archive Exists
**Success Criteria**: MCP tests pass after cleanup, ready for v2 rebuild

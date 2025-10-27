# Pre-Reset Cleanup Plan - Review & Confirm

## 📋 Quick Reference

**What gets DELETED**: 6 directories + 20+ files (generators, agents, experimental, scripts, wrong tests)  
**What gets KEPT UNTOUCHED**: `labs/mcp/`, `mcp/`, MCP tests, transport files, docs  
**What gets REWRITTEN**: 4 files only (`labs/__init__.py`, `requirements.txt`, `README.md`, CI test command)  
**What gets FORBIDDEN**: Adding schema files, modifying MCP infrastructure, adding code  

---

## ⚠️ CRITICAL RULES (Read First)

**UNTOUCHABLE INFRASTRUCTURE** - Do NOT modify:
- ✅ `labs/mcp/` - Entire directory stays as-is (working MCP client)
- ✅ `mcp/` - Entire directory stays as-is (protocol core)
- ✅ `tests/test_mcp*.py`, `test_labs_mcp_modes.py`, `test_socket.py`, `test_tcp.py` - Keep unmodified
- ✅ `labs/transport.py`, `labs/mcp_stdio.py` - Required dependencies
- ✅ `labs/logging.py`, `labs/core.py` - Shared utilities
- ✅ `docs/`, `meta/prompts/` - Documentation stays as-is

**FORBIDDEN ACTIONS**:
- ❌ Do NOT add schema files to `meta/schemas/` - MCP is schema authority
- ❌ Do NOT modify any file in `labs/mcp/` or `mcp/`
- ❌ Do NOT modify MCP test files
- ❌ Do NOT add code - only delete or rewrite specified files

**ALLOWED ACTIONS**:
- ✅ DELETE directories/files listed in DELETE section
- ✅ REWRITE (complete replacement) of 4 files: `labs/__init__.py`, `requirements.txt`, `README.md`, CI test command
- ✅ That's it - nothing else

---

## Purpose
Document exactly what will be removed in first cleanup pass. Review before executing.

---

## Files to DELETE (First Pass)

### Directories - High Confidence Removals
```bash
# These are clearly v0.3.6a cruft
labs/agents/                    # Premature - critic/generator agents
labs/experimental/              # Untested experimental code
labs/experiments/               # Prompt experiments
labs/lifecycle/                 # Patch/normalization we shouldn't need
labs/datasets/                  # Empty/unused
labs/generator/                 # Hardcoded template generators
```

**Rationale**: All built on broken foundation, none pass MCP validation

**CRITICAL**: Do NOT modify `labs/mcp/` directory at all - keep it completely untouched

### Root Scripts - v0.3.6a Workflow
```bash
audit.sh                        # v0.3.6a audit script
clear.sh                        # v0.3.6a cleanup
e2e.sh                          # v0.3.6a end-to-end tests
nuke.sh                         # v0.3.6a nuke script
test.sh                         # v0.3.6a test runner
```

**Rationale**: v0.3.6a-specific workflow, will use pytest directly

### Root Files - Documentation/Notes
```bash
notes.md                        # Development notes
AGENTS.md                       # v0.3.6a state report (in archive)
```

**Rationale**: Historical context, already in archive

### Labs Root Files - v0.3.6a Specific
```bash
labs/cli.py                     # Imports deleted modules (agents, generator, patches)
labs/patches.py                 # Normalization band-aids
labs/mcp_stub.py                # Stub server (not needed)
```

**Rationale**: Heavy dependencies on code we're deleting

### Test Files - Wrong Validation Source
```bash
tests/test_generator.py
tests/test_generator_assembler.py
tests/test_generator_components.py
tests/test_generator_e2e.py
tests/test_generator_schema.py
tests/test_external_generator.py
tests/test_critic.py
tests/test_pipeline.py
tests/test_patches.py
tests/test_prompt_experiment.py
tests/test_ratings.py
tests/test_determinism.py
tests/test_cli_logging.py
tests/test_logging.py
tests/test_path_guard.py
```

**Rationale**: Validated against stub schemas, not MCP

---

## Files to KEEP (First Pass)

### MCP Infrastructure (Core)
```bash
labs/mcp/                       # ✅ KEEP - Entire directory UNTOUCHED
  __init__.py
  __main__.py
  client.py                     # ✅ DO NOT MODIFY - Working as-is
  validate.py                   # ✅ DO NOT MODIFY
  exceptions.py                 # ✅ DO NOT MODIFY
  tcp_client.py                 # ✅ DO NOT MODIFY
  socket_main.py                # ✅ DO NOT MODIFY

labs/transport.py               # ✅ KEEP - Required by mcp/
labs/mcp_stdio.py               # ✅ KEEP - Required by mcp/client.py
```

**Rationale**: Working MCP infrastructure we confirmed is solid

**CRITICAL**: `labs/mcp/` is proven working infrastructure - any modifications risk breaking it

### Shared Infrastructure
```bash
labs/logging.py                 # ✅ KEEP - Structured logging pattern
labs/core.py                    # ✅ KEEP - Generic path utilities
labs/__init__.py                # ✅ KEEP - Will update to minimal
labs/.env.example               # ✅ KEEP - Configuration template
```

**Rationale**: Generic utilities, no v0.3.6a coupling

### MCP Server
```bash
mcp/__init__.py                 # ✅ KEEP - UNTOUCHED
mcp/core.py                     # ✅ KEEP - UNTOUCHED
```

**Rationale**: Protocol core infrastructure

**CRITICAL**: Do not modify these files

### Tests - MCP Only
```bash
tests/conftest.py               # ✅ KEEP - Pytest config
tests/test_mcp.py               # ✅ KEEP - UNTOUCHED - MCP client tests
tests/test_mcp_validator.py     # ✅ KEEP - UNTOUCHED - Validation tests
tests/test_mcp_schema_pull.py   # ✅ KEEP - UNTOUCHED - Schema fetching tests
tests/test_labs_mcp_modes.py    # ✅ KEEP - UNTOUCHED - Inline resolution tests
tests/test_socket.py            # ✅ KEEP - UNTOUCHED - Socket transport tests
tests/test_tcp.py               # ✅ KEEP - UNTOUCHED - TCP transport tests
```

**Rationale**: Prove MCP infrastructure works

**CRITICAL**: Do not modify these test files - they verify working infrastructure

### Documentation
```bash
docs/                           # ✅ KEEP - Entire directory UNTOUCHED
meta/                           # ✅ KEEP - Entire directory UNTOUCHED
  archived/archive-v0.3.6a.zip  # Archive is safe
  prompts/                      # Standup templates
  schemas/                      # ⚠️ REFERENCE ONLY - MCP is authority, do not add files here
    0.7.3/                      # Empty directory (no .json files)
    0.7.4/                      # Empty directory (no .json files)
  output/                       # Logs
```

**Rationale**: Documentation and context preservation

**CRITICAL**: 
- Do NOT add schema files to `meta/schemas/` - MCP is the only schema authority
- Schema directories exist but are EMPTY (no .json files) and must stay that way
- Do NOT modify existing files in docs/ or meta/prompts/
- Logs in meta/output/ can accumulate but don't modify structure

### Root Infrastructure
```bash
.gitignore                      # ✅ KEEP
.github/workflows/ci.yml        # ✅ KEEP - Generic CI
.vscode/settings.json           # ✅ KEEP - Editor config
Dockerfile                      # ✅ KEEP - Container infrastructure
docker-compose.yml              # ✅ KEEP - Container orchestration
requirements.txt                # ✅ KEEP - Will trim dependencies
README.md                       # ✅ KEEP - Will update for v2
LESSONS_LEARNED.md              # ✅ KEEP - Critical context
.env.example                    # ✅ KEEP - Environment template
```

**Rationale**: Infrastructure and documentation

---

## Files to UPDATE (First Pass)

### `labs/__init__.py`
**Current**:
```python
from .agents.generator import GeneratorAgent
from .agents.critic import CriticAgent
```

**Update to**:
```python
"""Synesthetic Labs v2 - Minimal schema-driven generator."""

__version__ = "2.0.0"

__all__ = []
```

**Rationale**: Remove deleted module imports, mark as v2

**NOTE**: This is a complete rewrite, not a modification

### `requirements.txt`
**Current**: Has Azure SDK, Gemini SDK, Anthropic SDK, many dependencies

**Update to**: Minimal dependencies only
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

**Rationale**: Remove external generator dependencies until needed in v2

**NOTE**: Complete rewrite of file

### `README.md`
**Update**: Rewrite for v2 architecture (keep file, update content)

**NOTE**: Complete content rewrite - document minimal MCP-only foundation

**Key sections to include**:
- Status: Under reconstruction
- Architecture: MCP client only
- What's preserved: MCP infrastructure
- What's removed: Generators, agents, etc.
- Next steps: Follow CLEANUP_PLAN.md → standup_template.json

### `.github/workflows/ci.yml`
**Current**:
```yaml
- name: Run tests
  run: pytest -q
```

**Update to**:
```yaml
- name: Run tests
  run: pytest tests/test_mcp*.py tests/test_labs_mcp_modes.py tests/test_socket.py tests/test_tcp.py -v
```

**Rationale**: Only run MCP infrastructure tests (deleted tests will fail)

**NOTE**: Modify only the test command line, leave rest of CI config untouched

---

## ⚠️ CRITICAL CONSTRAINTS

### DO NOT MODIFY
- **`labs/mcp/` directory** - Entire directory stays untouched
- **`mcp/` directory** - Entire directory stays untouched  
- **Test files** - `test_mcp*.py`, `test_labs_mcp_modes.py`, `test_socket.py`, `test_tcp.py` stay untouched
- **`labs/transport.py`** - Required by mcp/, keep as-is
- **`labs/mcp_stdio.py`** - Required by mcp/client.py, keep as-is
- **`labs/logging.py`** - Keep as-is
- **`labs/core.py`** - Keep as-is
- **`docs/` directory** - Keep all files as-is
- **`meta/prompts/` directory** - Keep all files as-is
- **Existing schema files** in `meta/schemas/` - Don't add new ones

### DO NOT ADD
- **Schema files to `meta/schemas/`** - MCP is the ONLY schema authority
- **Any new dependencies** to requirements.txt beyond the minimal list
- **Any new code** - this is deletion only

### ONLY DELETE
- Directories listed in DELETE section
- Files listed in DELETE section

### ONLY UPDATE (Complete Rewrites)
- `labs/__init__.py` - Rewrite to minimal v2
- `requirements.txt` - Rewrite to minimal deps
- `README.md` - Rewrite for v2 status
- `.github/workflows/ci.yml` - Update test command only

## Verification Before Execution

### Pre-Flight Checks
- [ ] Archive exists: `ls -lh meta/archived/archive-v0.3.6a.zip` (~15MB)
- [ ] Git status clean or changes committed
- [ ] On branch: `dce-reset-dev`
- [ ] No uncommitted work we care about

### Post-Removal Checks
- [ ] `labs/mcp/` directory intact and unmodified
- [ ] `labs/transport.py` exists and unmodified
- [ ] `labs/mcp_stdio.py` exists and unmodified
- [ ] `mcp/core.py` exists and unmodified
- [ ] MCP tests exist and unmodified: `ls tests/test_mcp*.py`
- [ ] Can run: `pytest tests/test_mcp.py --collect-only` (tests discovered)
- [ ] NO new schema files in `meta/schemas/` beyond what existed

---

## Execution Plan

### Step 1: Verify Archive
```bash
ls -lh meta/archived/archive-v0.3.6a.zip
# Should see ~15MB file
```

### Step 2: Remove Directories
```bash
rm -rf labs/agents/
rm -rf labs/experimental/
rm -rf labs/experiments/
rm -rf labs/lifecycle/
rm -rf labs/datasets/
rm -rf labs/generator/
```

### Step 3: Remove Root Scripts
```bash
rm -f audit.sh clear.sh e2e.sh nuke.sh test.sh
rm -f notes.md AGENTS.md
```

### Step 4: Remove Labs Files
```bash
rm -f labs/cli.py
rm -f labs/patches.py
rm -f labs/mcp_stub.py
```

### Step 5: Remove Test Files
```bash
cd tests/
rm -f test_generator*.py test_critic.py test_pipeline.py test_patches.py
rm -f test_prompt_experiment.py test_external_generator.py test_ratings.py
rm -f test_determinism.py test_cli_logging.py test_logging.py test_path_guard.py
rm -f test_minimal.py
cd ..
```

### Step 6: Update labs/__init__.py
```bash
cat > labs/__init__.py << 'EOF'
"""Synesthetic Labs v2 - Minimal schema-driven generator."""

__version__ = "2.0.0"

__all__ = []
EOF
```

### Step 7: Update CI Config
```bash
cat > .github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run MCP infrastructure tests
        run: pytest tests/test_mcp*.py tests/test_labs_mcp_modes.py tests/test_socket.py tests/test_tcp.py -v
EOF
```

### Step 8: Verify MCP Tests
```bash
pytest tests/test_mcp.py --collect-only
# Should show test collection without errors

# Verify no schema files were added
find meta/schemas -name "*.json" -type f
# Should only show files that existed before cleanup (if any)
```

### Step 9: Git Status Check
```bash
git status
# Review what was deleted
# Verify kept files are untouched
```

---

## Risk Assessment

### Low Risk (Confident Removals)
- ✅ `labs/agents/`, `labs/experimental/`, `labs/experiments/` - Never worked
- ✅ `labs/generator/` - Hardcoded templates, wrong approach
- ✅ Test files for deleted code - Will fail anyway

### Medium Risk (Verify First)
- ⚠️ `labs/cli.py` - CLI has env setup pattern we documented, but imports broken modules
- ⚠️ `labs/patches.py` - Normalization we don't want, but verify nothing else imports it

### No Risk (Keeping Essential)
- ✅ `labs/mcp/` - Verified working, required
- ✅ `labs/transport.py` - Used by mcp/
- ✅ `labs/mcp_stdio.py` - Used by mcp/client.py

---

## Rollback Plan

If something goes wrong:
```bash
# Archive is safe
ls meta/archived/archive-v0.3.6a.zip

# Git history preserved
git log --oneline
git checkout <commit-before-cleanup>

# Or extract from archive
cd /tmp
unzip /path/to/meta/archived/archive-v0.3.6a.zip -d recovery
```

---

## Decisions Confirmed ✅

1. **Remove all of `labs/generator/`** - CONFIRMED
   - Contains: assembler.py, shader.py, tone.py, control.py, haptic.py, meta.py, external.py
   - Rationale: All use hardcoded templates, wrong structure
   - Including: minimal.py (prototype from this session)

2. **Remove `labs/cli.py`** - CONFIRMED
   - Rationale: Imports agents, generator, patches (all deleted)
   - Env setup pattern is documented in LESSONS_LEARNED.md

3. **Remove `test_minimal.py` and `labs/generator/minimal.py`** - CONFIRMED
   - These were prototypes created during this session
   - Not in archive, not needed for v2
   - Fresh start from MCP-driven TDD

4. **Nothing else to preserve** - CONFIRMED
   - KEEP list is complete
   - Ready to execute cleanup

---

## Next Steps After Cleanup

1. Verify MCP tests still pass: `pytest tests/test_mcp.py -v`
2. Document: Update any docs that reference deleted code
3. Ready: Repo is now minimal foundation for v2 standup

---

**Status**: ✅ CONFIRMED - READY TO EXECUTE
**Decisions**: All removals confirmed - complete clean slate for v2
**Next**: Execute cleanup steps 1-9, verify MCP tests

---

## 🔍 Pre-Execution Validation Checklist

Before running cleanup, verify:
- [ ] You understand: `labs/mcp/` stays completely untouched
- [ ] You understand: NO schema files will be added to `meta/schemas/`
- [ ] You understand: Only DELETE and 4 REWRITES - no other modifications
- [ ] Archive verified: `ls -lh meta/archived/archive-v0.3.6a.zip` (~15MB)
- [ ] On correct branch: `git branch` shows `dce-reset-dev`

After execution, verify:
- [ ] `git diff labs/mcp/` shows NO changes
- [ ] `git diff mcp/` shows NO changes
- [ ] `git diff tests/test_mcp.py` shows NO changes
- [ ] `git diff tests/test_labs_mcp_modes.py` shows NO changes
- [ ] `find meta/schemas -name "*.json" -type f` shows NO files (currently empty)
- [ ] `pytest tests/test_mcp*.py tests/test_labs_mcp_modes.py --collect-only` succeeds

If ANY of the above fail, STOP and review what went wrong.

---

## 📊 Final Checklist Summary

**Before Execution**:
- [ ] Understood: `labs/mcp/`, `mcp/`, and MCP tests are completely untouched
- [ ] Understood: `meta/schemas/` stays empty (no .json files added)
- [ ] Understood: Only 6 directories deleted, 20+ files deleted, 4 files rewritten
- [ ] Archive exists and is ~15MB
- [ ] On `dce-reset-dev` branch

**Actions Taken**:
- [ ] Deleted 6 directories: agents, experimental, experiments, lifecycle, datasets, generator
- [ ] Deleted root scripts: audit.sh, clear.sh, e2e.sh, nuke.sh, test.sh
- [ ] Deleted root files: notes.md, AGENTS.md
- [ ] Deleted labs files: cli.py, patches.py, mcp_stub.py
- [ ] Deleted 15 test files (generator/critic/pipeline/etc.)
- [ ] Rewrote `labs/__init__.py` to v2 minimal
- [ ] Rewrote `requirements.txt` to minimal deps
- [ ] Rewrote `README.md` for v2 status
- [ ] Updated CI to run only MCP tests

**Post-Execution Verification**:
- [ ] No changes to `labs/mcp/`, `mcp/`, or MCP test files (git diff)
- [ ] No .json files in `meta/schemas/` (find command)
- [ ] MCP tests collect successfully (pytest --collect-only)
- [ ] Git status shows only expected deletions and 4 rewrites


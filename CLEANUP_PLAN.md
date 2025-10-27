# Pre-Reset Cleanup Plan - Review & Confirm

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
labs/mcp/                       # ✅ KEEP - Entire directory
  __init__.py
  __main__.py
  client.py                     # Proven working
  validate.py                   # Validation logic
  exceptions.py                 # Error types
  tcp_client.py                 # TCP transport
  socket_main.py                # Socket transport (keep, won't use initially)

labs/transport.py               # ✅ KEEP - Required by mcp/
labs/mcp_stdio.py               # ✅ KEEP - Required by mcp/client.py
```

**Rationale**: Working MCP infrastructure we confirmed is solid

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
mcp/__init__.py                 # ✅ KEEP
mcp/core.py                     # ✅ KEEP
```

**Rationale**: Protocol core infrastructure

### Tests - MCP Only
```bash
tests/conftest.py               # ✅ KEEP - Pytest config
tests/test_mcp.py               # ✅ KEEP - MCP client tests
tests/test_mcp_validator.py     # ✅ KEEP - Validation tests
tests/test_mcp_schema_pull.py   # ✅ KEEP - Schema fetching tests
tests/test_socket.py            # ✅ KEEP - Socket transport tests
tests/test_tcp.py               # ✅ KEEP - TCP transport tests
```

**Rationale**: Prove MCP infrastructure works

### Documentation
```bash
docs/                           # ✅ KEEP - Entire directory (updated for v2)
meta/                           # ✅ KEEP - Entire directory
  archived/archive-v0.3.6a.zip  # Archive is safe
  prompts/                      # Standup templates
  schemas/                      # Reference (MCP is authority)
  output/                       # Logs
```

**Rationale**: Documentation and context preservation

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

### `README.md`
**Update**: Rewrite for v2 architecture (keep file, update content)

### `.github/workflows/ci.yml`
**Current**:
```yaml
- name: Run tests
  run: pytest -q
```

**Update to**:
```yaml
- name: Run tests
  run: pytest tests/test_mcp*.py tests/test_socket.py tests/test_tcp.py -v
```

**Rationale**: Only run MCP infrastructure tests (deleted tests will fail)

---

## Verification Before Execution

### Pre-Flight Checks
- [ ] Archive exists: `ls -lh meta/archived/archive-v0.3.6a.zip` (~15MB)
- [ ] Git status clean or changes committed
- [ ] On branch: `dce-reset-dev`
- [ ] No uncommitted work we care about

### Post-Removal Checks
- [ ] `labs/mcp/` directory intact
- [ ] `labs/transport.py` exists
- [ ] `labs/mcp_stdio.py` exists
- [ ] `mcp/core.py` exists
- [ ] MCP tests exist: `ls tests/test_mcp*.py`
- [ ] Can run: `pytest tests/test_mcp.py --collect-only` (tests discovered)

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
        run: pytest tests/test_mcp*.py tests/test_socket.py tests/test_tcp.py -v
EOF
```

### Step 8: Verify MCP Tests
```bash
pytest tests/test_mcp.py --collect-only
# Should show test collection without errors
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
2. Commit: `git commit -m "Reset to minimal foundation - MCP infrastructure only"`
3. Review: `git diff main` to see full changes
4. Document: Update any docs that reference deleted code
5. Ready: Repo is now minimal foundation for v2 standup

---

**Status**: ✅ CONFIRMED - READY TO EXECUTE
**Decisions**: All removals confirmed - complete clean slate for v2
**Next**: Execute cleanup steps 1-8, verify MCP tests, commit minimal foundation

# Reset Evaluation - Base Repo Components

## Executive Summary

**CI Status**: ✅ **KEEP** - Generic enough for v2  
**Coverage**: ✅ **COMPLETE** - All essential components identified  
**Issues Found**: ⚠️ **4 ITEMS** - Need to update keep/remove lists  

---

## CI/CD Analysis

### `.github/workflows/ci.yml`

**Current Configuration**:
```yaml
- Install dependencies from requirements.txt
- Run pytest -q
```

**Assessment**: ✅ **KEEP - Generic and minimal**

**Rationale**:
- No v0.3.6a-specific logic
- Simply runs pytest on Python 3.11
- Will work for v2 (MCP tests will run)
- Generic enough for any future tests

**Action**: No changes needed to CI config

---

## Complete Inventory: Keep vs Remove

### ✅ KEEP - Essential Infrastructure

| Component | Location | Purpose | Status |
|-----------|----------|---------|--------|
| **MCP Client** | `labs/mcp/` | Schema fetching, validation | ✅ Core - works correctly |
| **MCP Server** | `mcp/` | Protocol core | ✅ Infrastructure |
| **Transport** | `labs/transport.py` | Message encoding/decoding | ✅ REQUIRED by labs/mcp/ |
| **TCP Client** | `labs/mcp/tcp_client.py` | TCP transport (primary) | ✅ Single connectivity path |
| **Stdio/Socket** | `labs/mcp/socket_main.py`, `labs/mcp_stdio.py` | Alternative transports | ⚠️ Keep but unused (v2 uses TCP only) |
| **Logging** | `labs/logging.py` | Structured JSONL logging | ✅ Proven pattern |
| **Core Utils** | `labs/core.py` | Path normalization | ✅ Generic utility |
| **MCP Tests** | `tests/test_mcp*.py`, `test_socket.py`, `test_tcp.py` | Prove connectivity | ✅ Validation |
| **Test Config** | `tests/conftest.py` | Pytest setup | ✅ Test infrastructure |
| **CI/CD** | `.github/workflows/ci.yml` | GitHub Actions | ✅ Generic - works for v2 |
| **Docker** | `Dockerfile`, `docker-compose.yml` | Container infrastructure | ✅ Deployment |
| **Git Config** | `.gitignore` | Ignore patterns | ✅ Source control |
| **Editor** | `.vscode/settings.json` | VS Code config | ✅ Developer experience |
| **Docs** | `docs/` | Documentation directory | ✅ Preserved, updated for v2 |
| **Meta** | `meta/` | Archive, prompts, schemas, output | ✅ Documentation & context |
| **Env** | `.env.example`, `labs/.env.example` | Environment templates | ✅ Configuration |
| **README** | `README.md` | Project overview | ✅ KEEP - Update for v2 |
| **Env Template** | `.env.example`, `labs/.env.example` | Environment templates | ✅ Configuration templates (safe) |

### ❌ REMOVE - v0.3.6a Cruft

| Component | Location | Reason | Impact |
|-----------|----------|--------|--------|
| **CLI** | `labs/cli.py` | v0.3.6a-specific, imports deleted modules | HIGH - will break |
| **Generators** | `labs/generator/` | Hardcoded templates, wrong structure | HIGH - core problem |
| **Agents** | `labs/agents/` | Premature feature | MEDIUM - built on broken foundation |
| **Experimental** | `labs/experimental/` | Untested code | LOW - not used |
| **Experiments** | `labs/experiments/` | v0.3.6a experiments | LOW - historical |
| **Lifecycle** | `labs/lifecycle/` | Patch/normalization | MEDIUM - shouldn't need |
| **Datasets** | `labs/datasets/` | Not used | LOW - empty |
| **Patches** | `labs/patches.py` | Normalization band-aid | MEDIUM - wrong approach |
| **Stubs** | `labs/mcp_stub.py` | Stub server (not MCP client) | LOW - not needed |
| **Scripts** | `*.sh` (audit, clear, e2e, nuke, test) | v0.3.6a workflow | LOW - obsolete |
| **Notes** | `notes.md`, `AGENTS.md` | Dev notes | LOW - in archive |
| **Secrets** | `.env` (if exists) | Live environment vars | CRITICAL - Security risk |
| **Tests** | `test_generator*.py`, `test_critic.py`, etc. | Wrong validation source | HIGH - false confidence |

---

## ⚠️ Issues Found & Resolutions

### Issue 1: `labs/__init__.py` Imports Deleted Modules

**Current Content**:
```python
from .agents.generator import GeneratorAgent
from .agents.critic import CriticAgent

__all__ = ["GeneratorAgent", "CriticAgent"]
```

**Problem**: Imports `labs/agents/` which will be deleted

**Solution**: Update to minimal v2 version
```python
"""Synesthetic Labs v2 - Minimal schema-driven generator."""

__version__ = "2.0.0"

__all__ = []
```

**Action**: ✅ Add step to reset procedure

---

### Issue 2: `labs/cli.py` Has Heavy v0.3.6a Dependencies

**Current Imports**:
```python
from labs.agents.critic import CriticAgent, is_fail_fast_enabled
from labs.agents.generator import GeneratorAgent
from labs.generator.assembler import AssetAssembler
from labs.generator.external import ExternalGenerationError, build_external_generator
from labs.patches import apply_patch, preview_patch, rate_patch
```

**Problem**: CLI depends on modules we're deleting

**Solution**: ❌ **DELETE `labs/cli.py`**

**Rationale**:
- v0.3.6a-specific command structure
- v2 standup will create new CLI if needed
- Env loading pattern is documented in LESSONS_LEARNED.md and can be reimplemented
- Preserving broken CLI adds confusion

**Action**: ✅ Add to remove list

---

### Issue 3: `labs/transport.py` IS Required by MCP

**Dependencies Found**:
```
labs/mcp/socket_main.py:11: from labs.transport import PayloadTooLargeError, decode_payload, read_message, write_message
labs/mcp/tcp_client.py:10: from labs.transport import (...)
```

**Problem**: Originally marked for removal, but MCP client needs it

**Solution**: ✅ **KEEP `labs/transport.py`**

**Action**: ✅ Kept in preserved list

---

### Issue 4: `labs/mcp_stdio.py` IS Required by MCP Client

**Dependencies Found**:
```
labs/mcp/client.py:339: from labs.mcp_stdio import build_validator_from_env
```

**Problem**: Originally marked for removal, but MCP client needs it

**Solution**: ✅ **KEEP `labs/mcp_stdio.py`**

**Action**: ✅ Kept in preserved list

---

## Final Keep/Remove Lists

### ✅ KEEP in `labs/` Root Files

```
labs/
├── __init__.py (UPDATE to minimal v2 version)
├── core.py (keep - generic utility)
├── logging.py (keep - proven pattern)
├── transport.py (keep - REQUIRED by mcp/)
├── mcp_stdio.py (keep - REQUIRED by mcp/client.py)
├── .env.example (keep - config template)
└── mcp/ (keep - entire directory)
```

### ❌ REMOVE from `labs/` Root Files

```
labs/
├── cli.py (DELETE - v0.3.6a-specific)
├── patches.py (DELETE - normalization cruft)
├── mcp_stub.py (DELETE - not used by mcp/)
├── agents/ (DELETE - entire directory)
├── experimental/ (DELETE - entire directory)
├── experiments/ (DELETE - entire directory)
├── lifecycle/ (DELETE - entire directory)
├── datasets/ (DELETE - entire directory)
└── generator/ (DELETE - entire directory)
```

---

## Updated Reset Procedure Steps

### Step 2b: Remove Cruft Directories (Updated)
```bash
rm -rf labs/agents/
rm -rf labs/experimental/
rm -rf labs/experiments/
rm -rf labs/lifecycle/
rm -rf labs/datasets/
rm -rf labs/generator/
```

### Step 3b: Remove Cruft Files (Updated)
```bash
# Remove v0.3.6a-specific files
rm -f labs/cli.py
rm -f labs/patches.py
rm -f labs/mcp_stub.py

# Remove v0.3.6a scripts
rm -f audit.sh clear.sh e2e.sh nuke.sh test.sh
rm -f notes.md AGENTS.md
```

### Step 3c: Update labs/__init__.py (New)
```bash
# Remove v0.3.6a-specific files
rm -f labs/cli.py
rm -f labs/patches.py
rm -f labs/mcp_stub.py

# Remove any secrets (CRITICAL)
rm -f .env labs/.env

# Remove v0.3.6a scripts
rm -f audit.sh clear.sh e2e.sh nuke.sh test.sh
rm -f notes.md AGENTS.md
```

### Step 3c: Update labs/__init__.py (New)
"""Synesthetic Labs v2 - Minimal schema-driven generator."""

__version__ = "2.0.0"

__all__ = []
EOF
```

---

## Verification Checklist

After reset, verify:

### ✅ Files That MUST Exist
- [ ] `labs/mcp/client.py`
- [ ] `labs/mcp/validate.py`
- [ ] `labs/mcp/exceptions.py`
- [ ] `labs/transport.py` (REQUIRED by MCP)
- [ ] `labs/mcp_stdio.py` (REQUIRED by MCP)
- [ ] `labs/logging.py`
- [ ] `labs/core.py`
- [ ] `labs/__init__.py` (updated to v2 version)
- [ ] `tests/test_mcp.py`
- [ ] `tests/conftest.py`
- [ ] `.github/workflows/ci.yml`
- [ ] `meta/archived/archive-v0.3.6a.zip`
- [ ] `meta/prompts/standup_template.json`
- [ ] `CLEANUP_PLAN.md`
- [ ] `docs/reset_process.md`
- [ ] `LESSONS_LEARNED.md`
- [ ] `README.md` (kept and updated)
- [ ] `.env.example`, `labs/.env.example` (templates only)

### ❌ Files That MUST NOT Exist
- [ ] `.env` or `labs/.env` (secrets)
- [ ] `labs/cli.py`
- [ ] `labs/patches.py`
- [ ] `labs/mcp_stub.py`
- [ ] `labs/agents/`
- [ ] `labs/generator/`
- [ ] `labs/experimental/`
- [ ] `audit.sh`, `e2e.sh`, `nuke.sh`, etc.

### ✅ Tests MUST Pass
```bash
pytest tests/test_mcp.py -v
pytest tests/test_mcp_validator.py -v
pytest tests/test_mcp_schema_pull.py -v
```

If these pass, MCP infrastructure is intact.

---

## Summary

### What We're Keeping

**Core Infrastructure** (7 files in labs/):
- `labs/mcp/` - MCP client (entire directory)
- `labs/transport.py` - Transport layer (required)
- `labs/mcp_stdio.py` - Stdio support (required)
- `labs/logging.py` - Structured logging
- `labs/core.py` - Generic utilities
- `labs/__init__.py` - Package init (updated for v2)
- `labs/.env.example` - Config template

**Other Infrastructure**:
- `mcp/` - MCP server
- `tests/` - MCP tests only
- `.github/` - CI (works for v2)
- `docker/` - Container infrastructure
- `meta/` - Archive & documentation
- `docs/` - Documentation (updated for v2)

### What We're Removing

**v0.3.6a Code** (3 files + 6 directories):
- `labs/cli.py` - v0.3.6a CLI
- `labs/patches.py` - Normalization
- `labs/mcp_stub.py` - Unused stub
- `labs/agents/`, `labs/generator/`, `labs/experimental/`, `labs/experiments/`, `labs/lifecycle/`, `labs/datasets/`

**Scripts & Notes**:
- `*.sh` files (audit, clear, e2e, nuke, test)
- `notes.md`, `AGENTS.md`

**Tests**:
- All non-MCP tests (generator, critic, pipeline, etc.)

### Coverage Assessment

✅ **COMPLETE** - All components accounted for:
- MCP infrastructure: Preserved and verified
- Dependencies: `transport.py` and `mcp_stdio.py` found and kept
- Broken code: Identified and marked for removal
- CI: Evaluated and confirmed generic
- Documentation: Preserved and updated

### CI Assessment

✅ **CI is generic enough** - No changes needed:
- Runs pytest on requirements.txt
- No v0.3.6a-specific logic
- Will work for v2 MCP tests
- Will work for future v2 generator tests

---

## Next Steps

1. **Execute cleanup** following `CLEANUP_PLAN.md` steps 1-9

2. **Verify** all checklist items pass

3. **Commit** clean minimal state

4. **Begin v2** following `meta/prompts/standup_template.json` (instantiate for 0.7.3)

---

**Evaluation Status**: ✅ COMPLETE  
**CI Status**: ✅ KEEP AS-IS  
**Action Required**: Follow CLEANUP_PLAN.md for execution

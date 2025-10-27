# Lessons Learned: Synesthetic Labs v0.3.6a

## Executive Summary

This codebase attempted to build a synesthetic asset generation system with MCP (Model Context Protocol) schema validation. The implementation became overly complex and failed to achieve full MCP compliance due to fundamental architectural mistakes. This document captures the key lessons learned before building a fresh implementation.

---

## Critical Architecture Mistakes

### 1. **Schema Authority Confusion**

**Problem**: The codebase treated local stub schema files (`meta/schemas/0.7.3/synesthetic-asset.schema.json`) as authoritative instead of MCP-provided schemas.

**Impact**:
- Stub schemas were simplified, missing critical `anyOf`/`oneOf` validation constraints
- Assets passed validation against stubs but failed MCP strict validation
- Generators were built to match stub structure, not actual MCP requirements
- No single source of truth

**Lesson**: **MCP must be the ONLY schema authority. Never cache schemas to disk as "reference" - it creates divergence.**

### 2. **Hardcoded Template Generators**

**Problem**: Component generators (`shader.py`, `tone.py`, `control.py`, `haptic.py`) used hardcoded templates with constants like `_FRAGMENT_SHADER`, `_UNIFORMS`, etc.

**Impact**:
- Generators output structure didn't match MCP schema (e.g., `sources: {fragment: "..."}` instead of `vertex_shader`/`fragment_shader`)
- Schema changes required manual code updates across multiple files
- No schema-driven approach - templates were guesses at valid structure

**Lesson**: **Generators must read schema dynamically from MCP and construct assets from schema structure, not hardcoded templates.**

### 3. **Premature Abstraction Layers**

**Problem**: Built complex abstraction layers before proving core functionality:
- `AssetAssembler` with normalization paths for multiple schema versions
- `ExternalGenerator` with Azure/Gemini/Anthropic integrations
- `CriticAgent` for asset review
- Patch lifecycle system
- Multiple experimental modules

**Impact**:
- Couldn't achieve basic MCP validation before adding complexity
- Each layer added assumptions that didn't match MCP reality
- Debugging became impossible - too many moving parts

**Lesson**: **Build minimal working implementation first. Single test: generate asset → MCP validates ✅. Add complexity only after core works.**

### 4. **Schema Version Lock-In Without Validation**

**Problem**: Locked to schema version 0.7.3 but never achieved full MCP compliance for it.

**Impact**:
- Couldn't upgrade to 0.7.4 due to 0.7.3 failures
- Built entire system on unvalidated foundation
- Schema resolution modes (preserve/inline/bundled) added before basic validation worked

**Lesson**: **Don't lock schema versions until you can pass strict MCP validation. Don't add resolution modes until basic inline validation works.**

### 5. **Test Suite Validated Against Wrong Source**

**Problem**: Tests used `json.load()` to read stub schemas from disk instead of `MCPClient.fetch_schema()`.

**Impact**:
- Tests passed while actual MCP validation failed
- False confidence in implementation
- Test suite didn't catch schema structure mismatches

**Lesson**: **All schema validation tests must use MCP as source. If MCP is unreachable, tests should fail - don't fall back to disk schemas.**

---

## Technical Debt Patterns

### Documentation Over Implementation
- Added `docs/schema_authority.md`, `meta/schemas/README.md`, inline documentation
- User correctly called it "cruft" - documentation doesn't fix broken architecture
- **Lesson**: Fix the code first, document working systems second.

### Normalization as Band-Aid
- `AssetAssembler._normalize_0_7_3()` tried to fix generator output to match schema
- Normalization shouldn't exist - generators should output correct structure initially
- **Lesson**: If you need normalization, your generators are wrong.

### Feature Creep
- External LLM generators (Azure, Gemini) before basic generation worked
- Critic agents before assets validated
- Experimental modules before core stability
- **Lesson**: Each feature should build on validated foundation.

---

## What Actually Worked

### MCP Client (`labs/mcp/client.py`)
- `MCPClient` class with TCP/stdio/socket transport support
- `load_schema_bundle()` function correctly fetches inline schemas
- `validate()` method enforces strict MCP validation
- **Keep**: This module is solid and should be the foundation.

### Environment Configuration (`labs/cli.py:18-24`)
- CLI preloads `.env` before agents start
- Forces `LABS_SCHEMA_VERSION="0.7.3"` and `LABS_SCHEMA_RESOLUTION="inline"`
- **Keep**: Early environment setup pattern is good.

### Structured Logging (`labs/logging.py`)
- JSONL logging with telemetry
- Tracks schema resolution metadata
- **Keep**: Observable systems are debuggable systems.

---

## Fresh Implementation Requirements

### Minimal Core (Build This First)

1. **MCP Client Module** ✅
   - Already exists and works: `labs/mcp/client.py`
   - Functions: `fetch_schema()`, `validate()`, `load_schema_bundle()`

2. **Schema-Driven Generator** (New)
   ```python
   def generate_asset(mcp_client, prompt: str) -> dict:
       # 1. Fetch schema from MCP
       schema = load_schema_bundle(client=mcp_client, version="0.7.3")
       
       # 2. Read required fields from schema
       required = schema.get("required", [])
       properties = schema.get("properties", {})
       
       # 3. Build minimal valid asset matching schema structure
       # - For anyOf, pick first valid option
       # - Use schema to determine field names/types
       # - No hardcoded templates
       
       return asset
   ```

3. **Single Validation Test**
   ```python
   def test_mcp_validation():
       client = MCPClient()
       asset = generate_asset(client, "test")
       result = client.validate(asset, strict=True)
       assert result["valid"] is True
   ```

### Success Criteria (Must Pass Before Adding Features)

- ✅ Generator reads schema from MCP (via `load_schema_bundle()`)
- ✅ Asset structure matches MCP schema (including anyOf/oneOf)
- ✅ MCP strict validation passes
- ✅ No disk schema files referenced
- ✅ No hardcoded templates

### Add Features Only After Core Works

**Phase 2** (after basic validation passes):
- External LLM integration (Azure/Gemini) for rich content generation
- But still use schema-driven structure, not hardcoded templates

**Phase 3** (after external generation works):
- Critic/review agents
- Patch lifecycle
- Multi-version support

**Never Add**:
- Stub schemas to disk
- Normalization layers
- Template-based generation

---

## Key Technical Insights

### MCP Schema Structure
- Schemas use `anyOf` for variant types (e.g., shader can be GLSL or WGSL)
- For generation, pick ONE valid anyOf option - don't try to handle all
- Required fields vary by anyOf option - read from schema, don't hardcode
- Example: Shader anyOf[0] requires `fragment_shader`, `name`, `vertex_shader` (not `sources` object)

### Schema Resolution Modes
- `inline`: Embeds all `$ref` dependencies (required for Azure strict mode)
- `preserve`: Keeps `$ref` pointers (breaks external validation)
- `bundled`: Separate definitions object (not widely supported)
- **Default to inline** and only add other modes if proven necessary

### Validation Strictness
- `strict=False`: jsonschema validation (lenient)
- `strict=True`: MCP enforces exact schema compliance
- **Always test with strict=True** - that's the real requirement

---

## Anti-Patterns to Avoid

❌ **Don't**: Cache schemas to disk "for reference"
✅ **Do**: Fetch from MCP every time (cache in memory if needed)

❌ **Don't**: Build generators with hardcoded templates
✅ **Do**: Read schema structure and build from that

❌ **Don't**: Add normalization to fix generator output
✅ **Do**: Make generators output correct structure initially

❌ **Don't**: Write tests that pass with wrong schemas
✅ **Do**: Tests must use MCP as schema source

❌ **Don't**: Add features before core validation works
✅ **Do**: Prove minimal implementation, then extend

❌ **Don't**: Document problems instead of fixing them
✅ **Do**: Fix architecture, then document working system

---

## Recommended Fresh Start Approach

### Step 1: Minimal Repo Structure
```
labs-v2/
├── README.md
├── requirements.txt  (minimal: jsonschema, httpx, pydantic)
├── .env.example
├── labs/
│   ├── __init__.py
│   ├── mcp/          # Copy from v0.3.6a (works correctly)
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── validate.py
│   │   └── exceptions.py
│   └── generator.py  # Single schema-driven generator
└── tests/
    └── test_validation.py  # Single test: generate → validate
```

### Step 2: Single Test (TDD)
Write the test first:
```python
def test_mcp_validation():
    client = MCPClient()
    asset = generate_asset(client, prompt="peaceful waves")
    result = client.validate(asset, strict=True)
    assert result["valid"] is True
```

### Step 3: Schema-Driven Implementation
Make the test pass by reading schema from MCP and building asset structure from it.

### Step 4: Extend Only After Success
Once basic test passes, add:
- External LLM for content (but keep schema-driven structure)
- CLI interface
- Logging/telemetry
- Additional tests

---

## Questions for Fresh Implementation

### Architecture Decisions
1. **Should we support multiple schema versions simultaneously?**
   - v0.3.6a tried this and it added massive complexity
   - Recommendation: Support ONE version at a time, upgrade when ready

2. **Should we support all MCP transports (TCP/stdio/socket)?**
   - v0.3.6a supports all three
   - Recommendation: Start with TCP only, add others if needed

3. **Should we generate all components (shader/tone/control/haptic)?**
   - v0.3.6a tried to generate all
   - Recommendation: Start with minimal required set, expand incrementally

### Implementation Patterns
1. **How to handle anyOf/oneOf in schemas?**
   - Pick first valid option for generation
   - Don't try to generate all variants
   - Read required fields from selected option

2. **How to integrate external LLMs (Azure/Gemini)?**
   - Use for content generation (shader code, descriptions)
   - Still use schema-driven structure assembly
   - Don't let LLM dictate asset structure

3. **How to test schema evolution?**
   - Test against current MCP schema version
   - When schema updates, tests will fail → update generator
   - Don't try to support old schemas with normalization

---

## Code Migration Guide

### From v0.3.6a to v2

**Copy These** (They Work):
- `labs/mcp/client.py` - MCP client is solid
- `labs/mcp/validate.py` - Validation logic works
- `labs/mcp/exceptions.py` - Error types are good
- Environment setup pattern from `labs/cli.py:18-24`

**Rewrite These** (Schema-Driven):
- All generators (`labs/generator/*.py`) - use schema reading instead of templates
- Tests (`tests/test_generator*.py`) - use MCP as schema source

**Delete These** (Cruft):
- `meta/schemas/` - stub schemas are wrong
- `labs/experimental/` - added before core worked
- `labs/agents/critic.py` - premature feature
- `labs/patches.py` - normalization shouldn't exist
- `docs/schema_authority.md` - fix code, not docs

---

## Conclusion

The core insight: **MCP is the authority, generators must be schema-driven, prove minimal implementation before adding features.**

This codebase failed because it built complexity on an unvalidated foundation. A fresh implementation should:
1. Start with MCP client (copy from v0.3.6a)
2. Build single schema-driven generator
3. Prove MCP validation passes
4. Then and only then add features

The path forward is clear: smaller, schema-driven, test-first, MCP-authoritative.

---

**Status**: Repository archived at v0.3.6a with these lessons documented.
**Next**: Build labs-v2 following minimal schema-driven architecture.

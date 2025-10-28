---
version: v2.0.0
lastReviewed: 2025-10-27
owner: labs-core
status: minimal-foundation
predecessor: v0.3.6a (archived)
---

# Synesthetic Labs — Spec v2.0.0 (MCP-Only Foundation)

> **Reset Philosophy:**  
> Complete rebuild from minimal MCP infrastructure.  
> Schema version **NOT locked** - standup process is version-agnostic via template pattern.  
> No generators, no assemblers, no critics - only proven MCP client infrastructure.  
> Future generators will be built schema-first via TDD standup process.

---

## 1 · Scope (Current State)

**What EXISTS (v2.0.0)**:
- ✅ MCP client (`labs/mcp/`) - TCP transport, inline schema resolution, batch validation
- ✅ Schema fetching (`MCPClient.fetch_schema()`) - Version-agnostic, resolution-aware
- ✅ Validation gateway (`MCPClient.validate()`, `MCPClient.confirm()`) - Strict mode, batch support
- ✅ Transport utilities (`labs/transport.py`, `labs/mcp_stdio.py`) - Connection management
- ✅ Core utilities (`labs/logging.py`, `labs/core.py`) - Structured logging, path helpers

**What DOES NOT EXIST (removed in cleanup)**:
- ❌ No generators (`labs/generator/` deleted)
- ❌ No assemblers (hardcoded templates removed)
- ❌ No agents (`labs/agents/` deleted)
- ❌ No critics (premature abstraction removed)
- ❌ No experimental code (`labs/experimental/` deleted)
- ❌ No CLI (`labs/cli.py` deleted)

**What WILL EXIST (future standup)**:
- ⏳ Version-confined generators (e.g., `labs/v0_7_3/generator.py`)
- ⏳ Schema-driven builders (TDD process, MCP validation first)
- ⏳ Telemetry layer (trace_id, deployment metadata - **local to Labs, NOT in MCP schema**)
- ⏳ Test harnesses (version-specific test suites)  

---

## 2 · Architecture Principles (v2 Forward)

### 2.1 · Schema Version Confinement
- Each schema version gets isolated namespace: `labs/v{VERSION}/`
- Tests mirror structure: `tests/v{VERSION}/`
- Environment configs: `.env.{VERSION}`
- **NO cross-version dependencies** - versions evolve independently

### 2.2 · MCP as Single Source of Truth
- MCP server is **ONLY** schema authority
- Labs **NEVER** adds schema files to `meta/schemas/`
- Schema bundles fetched at runtime via `MCPClient`
- Inline resolution mode required for LLM consumption

### 2.3 · Telemetry Separation
- **MCP schema** = Pure validation contract (asset structure only)
- **Labs telemetry** = Local metadata (`trace_id`, `deployment`, `engine`, `timestamp`)
- Telemetry stored in `meta/output/`, NOT mixed with validated assets
- Translation layer maps validated asset → telemetry-enriched record

### 2.4 · Test-First Development
- Write failing test against MCP validation FIRST
- Implement generator to pass validation
- No code without corresponding test
- CI must pass before merge

---

## 3 · Current Capabilities (v2.0.0)

### 3.1 · MCP Client

```python
from labs.mcp.client import MCPClient

# Fetch schema (version-agnostic)
client = MCPClient(schema_version="0.7.3", resolution="inline")
descriptor = client.fetch_schema("synesthetic-asset", version="0.7.3")
schema_bundle = descriptor["schema"]

# Validate assets
assets = [{"$schema": "...", "name": "test", ...}]
results = client.validate(assets, strict=True)

# Single asset confirmation
result = client.confirm(asset, strict=True)
assert result["ok"]
```

### 3.2 · Available Transports
- **TCP** (primary): `localhost:3000` via `labs.mcp.tcp_client`
- **Stdio** (fallback): Process pipe via `labs.mcp_stdio`

### 3.3 · Schema Resolution Modes

| Mode       | Behavior                  | Labs Usage                        |
| ---------- | ------------------------- | --------------------------------- |
| `inline`   | Embeds all `$ref` deps    | ✅ Required for LLM structured output |
| `preserve` | Keeps `$ref` links        | ❌ LLMs cannot resolve remote refs |
| `bundled`  | Root + refs array         | ⚙️ Future: Offline CI option       |

---

## 4 · Environment (Minimal v2)

**Current v2 Environment Variables**:

| Var | Purpose | Default | Notes |
|-----|----------|---------|-------|
| `LABS_SCHEMA_VERSION` | Target schema version | `"0.7.4"` | Set per standup |
| `LABS_SCHEMA_RESOLUTION` | Resolution mode | `"inline"` | Force inline |
| `LABS_MCP_LOG_PATH` | Telemetry output | `meta/output/labs/mcp.jsonl` | Structured logs |
| `MCP_ENDPOINT` | Transport URI | `tcp://localhost:3000` | Server location |
| `MCP_MAX_BATCH` | Validation batch limit | `50` | Prevent overload |

**Future Environment Variables** (per-version standups):

| Var | Purpose | Example | When Added |
|-----|----------|---------|------------|
| `.env.0_7_3` | 0.7.3-specific config | Schema version, engine settings | During 0.7.3 standup |
| `.env.0_7_4` | 0.7.4-specific config | Schema version, engine settings | During 0.7.4 standup |
| `AZURE_OPENAI_*` | Azure engine config | Endpoint, key, deployment | When Azure generator added |
| `GEMINI_*` | Gemini engine config | API key, project | When Gemini generator added |

---

## 5 · MCP Contract (Schema Authority)

### 5.1 · Schema Retrieval

Labs retrieves authoritative schemas from MCP at runtime. **Never** stores schema files locally.

```python
from labs.mcp.client import MCPClient, load_schema_bundle

# Fetch descriptor (includes metadata + schema bundle)
client = MCPClient(schema_version="0.7.3", resolution="inline")
descriptor = client.fetch_schema("synesthetic-asset", version="0.7.3")

# Extract pure schema bundle for validation/generation
schema_bundle = descriptor["schema"]

# Convenience function
bundle = load_schema_bundle(version="0.7.3")  # Returns descriptor["schema"]
```

### 5.2 · Validation Contract

**MCP validates ONLY the asset structure** - no telemetry fields.

```python
# Create asset (pure schema-compliant structure)
asset = {
    "$schema": "https://schemas.synesthetic-labs.ai/...",
    "name": "example",
    "modality": {"type": "shader", "tags": []},
    "output": {"type": "glsl", "content": "..."},
    "meta_info": {}
}

# Validate via MCP (strict mode)
result = client.confirm(asset, strict=True)
assert result["ok"] is True

# Labs telemetry layer (SEPARATE from validated asset)
telemetry_record = {
    "asset": asset,  # Validated structure
    "trace_id": "uuid",  # Labs-local metadata
    "engine": "azure_openai",  # Labs-local metadata
    "deployment": "gpt-4o-mini",  # Labs-local metadata
    "timestamp": "2025-10-27T...",  # Labs-local metadata
    "validation_result": result  # MCP response
}

# Store telemetry separately
log_jsonl("meta/output/labs/generation.jsonl", telemetry_record)
```

**Key Principle**: MCP schema defines asset structure. Labs telemetry wraps validated assets with operational metadata. **No mixing**.

### 5.3 · Resolution Requirements

| Requirement | Reason |
|-------------|--------|
| **Must use `inline` mode** | LLMs cannot resolve remote `$ref` URIs |
| **Schema bundle unmodified** | Validation equality depends on exact structure |
| **No local schema cache** | MCP is single source of truth |

---

## 6 · Future: Schema-Driven Generation Pattern

**Template for version-specific standup** (e.g., 0.7.3):

### 6.1 · Namespace Structure
```
labs/v0_7_3/
├── __init__.py
├── generator.py      # Core generation logic
├── builders.py       # Schema-driven component builders
├── fixtures.py       # Test fixtures
└── telemetry.py      # Trace/deployment metadata

tests/v0_7_3/
├── __init__.py
├── test_generator.py
├── test_validation.py
└── fixtures/
    └── valid_assets.json

.env.0_7_3            # Version-specific config
```

### 6.2 · Schema-Driven Builder Pattern

```python
# labs/v0_7_3/builders.py
def build_from_schema(subschema: dict, prompt: str) -> dict:
    """
    Generate asset section by reading schema structure.
    NO hardcoded templates - structure derived from subschema.
    """
    data = {}
    
    # Required fields
    for key in subschema.get("required", []):
        prop = subschema["properties"][key]
        
        if "enum" in prop:
            data[key] = prop["enum"][0]  # First enum value
        elif "default" in prop:
            data[key] = prop["default"]
        elif prop.get("type") == "string":
            data[key] = f"Generated {key} for: {prompt}"
        elif prop.get("type") == "array":
            data[key] = []  # Minimal valid array
        elif prop.get("type") == "object":
            data[key] = build_from_schema(prop, prompt)  # Recurse
    
    return data
```

### 6.3 · LLM Integration (Azure Example)

```python
# labs/v0_7_3/generator.py
from labs.mcp.client import load_schema_bundle
from openai import AzureOpenAI

def generate_with_azure(prompt: str, version: str = "0.7.3") -> dict:
    """
    Generate asset via Azure OpenAI structured output.
    Schema bundle injected from MCP - NO local schema files.
    """
    # Fetch live schema from MCP
    schema_bundle = load_schema_bundle(version=version)
    
    # Azure client (from env vars)
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )
    
    # Structured generation with schema constraint
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "Generate synesthetic asset JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": f"SynestheticAsset_{version.replace('.', '_')}",
                "schema": schema_bundle,
                "strict": True
            }
        },
        temperature=0
    )
    
    # Extract generated asset
    asset = json.loads(response.choices[0].message.content)
    return asset
```

### 6.4 · Telemetry Separation

```python
# labs/v0_7_3/telemetry.py
def enrich_with_telemetry(asset: dict, engine: str, deployment: str) -> dict:
    """
    Wrap validated asset with Labs-local metadata.
    Telemetry fields NOT part of MCP validation contract.
    """
    return {
        "asset": asset,  # Pure validated structure
        "trace_id": str(uuid.uuid4()),
        "engine": engine,
        "deployment": deployment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "schema_version": asset.get("$schema", "").split("/")[-2]
    }
```

### 6.5 · Test-First Flow

```python
# tests/v0_7_3/test_generator.py
def test_generated_asset_validates_via_mcp():
    """
    TDD: Write this test FIRST, implement generator to pass.
    """
    from labs.v0_7_3.generator import generate_with_azure
    from labs.mcp.client import MCPClient
    
    # Generate asset
    asset = generate_with_azure("minimal shader", version="0.7.3")
    
    # Validate via MCP (strict mode)
    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    
    # Assert validation passes
    assert result["ok"] is True
    assert result["reason"] == "validation_passed"
```

---

## 7 · Current Test Coverage (v2.0.0)

**Existing Tests** (27 tests, 21 passing):
- ✅ `tests/test_mcp.py` - MCP client validation flows
- ✅ `tests/test_mcp_validator.py` - Schema validation logic
- ✅ `tests/test_mcp_schema_pull.py` - Schema fetching
- ✅ `tests/test_labs_mcp_modes.py` - Resolution mode handling
- ✅ `tests/test_socket.py` - Socket transport
- ✅ `tests/test_tcp.py` - TCP transport

**Test Failures** (6 failures - URL config issues, not structural):
- Schema URL domain mismatches (fixture vs system)
- Pre-existing issues, not cleanup-related

---

## 8 · Standup Process (Future Versions)

### Phase 1: Test Infrastructure
1. Create `tests/v{VERSION}/` namespace
2. Write failing validation test against MCP
3. Create test fixtures (valid/invalid assets)

### Phase 2: Generator Implementation
1. Create `labs/v{VERSION}/` namespace
2. Implement `builders.py` (schema-driven logic)
3. Implement `generator.py` (LLM integration if needed)
4. Run tests - iterate until MCP validation passes

### Phase 3: Telemetry Layer
1. Implement `telemetry.py` (trace_id, deployment, etc.)
2. Write telemetry logs to `meta/output/`
3. Keep telemetry SEPARATE from validated assets

### Phase 4: Integration
1. Version-specific environment config (`.env.{VERSION}`)
2. CI configuration for version-specific tests
3. Documentation update

---

## 9 · Logging (Future)

Telemetry records in `meta/output/labs/v{VERSION}_generation.jsonl`:

```json
{
  "trace_id": "b47a1b5c-4e7a-42ef-9efb-6bfa22f31ed8",
  "timestamp": "2025-10-27T10:15:00Z",
  "schema_version": "0.7.3",
  "engine": "azure_openai",
  "deployment": "gpt-4o-mini",
  "prompt": "red pulsing shader",
  "asset": {
    "$schema": "https://schemas.synesthetic-labs.ai/mcp/0.7.3/synesthetic-asset.schema.json",
    "name": "red_pulse",
    "modality": {"type": "shader", "tags": ["color", "animation"]},
    "output": {"type": "glsl", "content": "..."}
  },
  "validation_result": {
    "ok": true,
    "reason": "validation_passed",
    "errors": []
  }
}
```

**Key**: `asset` field contains pure MCP-validated structure. All other fields are Labs telemetry.

---

## 10 · Exit Criteria (Per-Version Standup)

| Check | Requirement |
|-------|-------------|
| **Schema fetch** | MCP returns inline bundle for target version |
| **Generator output** | Derives structure from schema, NO hardcoded templates |
| **MCP validation** | 100% pass rate in strict mode |
| **Telemetry separation** | No telemetry fields in validated asset structure |
| **Test coverage** | All generator paths tested via MCP validation |
| **CI green** | Version-specific test suite passes |
| **Namespace isolation** | No imports from other version namespaces |

---

## 11 · Summary (v2.0.0)

**Current State**:
- ✅ MCP infrastructure proven and stable
- ✅ v0.3.6a code archived and removed
- ✅ Clean foundation for version-specific standups

**Architecture**:
- **MCP = Schema authority** (runtime fetch, inline resolution)
- **Labs = Generator + telemetry** (wraps validated assets)
- **No mixing** of validation contract and operational metadata

**Next Steps**:
1. Follow `meta/prompts/standup_template.json` for 0.7.3 standup
2. Implement TDD flow: test → generator → validate
3. Keep telemetry separate from MCP schema contract

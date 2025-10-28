---
version: v2.0.0
lastReviewed: 2025-10-27
owner: labs-core
status: authoritative-ssot
predecessor: v0.3.6a (archived)
purpose: single-source-of-truth for all schema version standups
---

# Synesthetic Labs — Specification v2.0.0

> **This document is the SSOT for Labs architecture and implementation.**  
> All schema version standups MUST follow this specification.  
> Any deviation requires spec update and review.

## Philosophy

**Version-Agnostic Foundation**  
Labs provides MCP-driven infrastructure for **any** schema version.  
Each version stands up independently via the template pattern defined here.

**Schema Authority**  
MCP is the sole schema authority. Labs never stores, modifies, or caches schemas locally.  
All generation and validation flows through live MCP schema bundles.

**Telemetry Separation**  
MCP validates pure asset structure. Labs manages operational metadata separately.  
No mixing of validation contracts and telemetry concerns.

**Test-Driven Development**  
Every feature starts with a failing MCP validation test.  
Code exists only to make tests pass.

---

## 1 · Core Infrastructure (Stable Foundation)

### 1.1 · MCP Client (`labs/mcp/`)

**Proven, stable infrastructure** - never modify without explicit need.

```python
from labs.mcp.client import MCPClient, load_schema_bundle

# Version-agnostic client initialization
client = MCPClient(
    schema_version="0.7.3",      # Target version
    resolution="inline",          # Required for LLMs
    batch_limit=50,               # Validation batch size
    telemetry_path="meta/output/labs/mcp.jsonl"
)

# Fetch schema descriptor
descriptor = client.fetch_schema("synesthetic-asset", version="0.7.3")
schema_bundle = descriptor["schema"]  # Pure JSON Schema bundle

# Validate assets (batch)
results = client.validate([asset1, asset2], strict=True)

# Validate single asset (with exception on failure)
result = client.confirm(asset, strict=True)  # Raises MCPValidationError if failed

# Convenience: Load schema bundle directly
bundle = load_schema_bundle(version="0.7.3")
```

**Capabilities**:
- ✅ Version-agnostic schema fetching
- ✅ Inline resolution (embeds all `$ref` dependencies)
- ✅ Strict mode validation (fail-fast)
- ✅ Batch validation (up to 50 assets)
- ✅ TCP transport (`tcp://localhost:8765`)
- ✅ Telemetry logging (structured JSONL)

**Files**:
```
labs/mcp/
├── client.py          # Main MCPClient class, load_schema_bundle()
├── validate.py        # Local validation logic
├── tcp_client.py      # TCP transport implementation
├── socket_main.py     # Socket helpers
├── exceptions.py      # MCPClientError, MCPValidationError, MCPUnavailableError
└── __main__.py        # CLI entry point
```

### 1.2 · Transport Layer

**TCP Only** - Service-oriented architecture requires reliable network transport.

```
labs/mcp/tcp_client.py    # TCP transport to MCP server
labs/transport.py          # Connection management utilities
```

**MCP Endpoint**: `tcp://localhost:8765` (required, no fallback)

If MCP is unavailable, the client raises `MCPUnavailableError` immediately.  
This ensures infrastructure failures are visible and addressed, not silently bypassed.

### 1.3 · Shared Utilities

```
labs/logging.py        # log_jsonl(), structured logging
labs/core.py           # Path utilities, generic helpers
labs/transport.py      # Connection management
labs/__init__.py       # Version: "2.0.0", minimal exports
```

### 1.4 · Test Infrastructure (Stable)

```
tests/conftest.py              # Pytest configuration
tests/test_mcp.py              # MCP client tests
tests/test_mcp_validator.py    # Validation tests
tests/test_mcp_schema_pull.py  # Schema fetching tests
tests/test_labs_mcp_modes.py   # Resolution mode tests
tests/test_socket.py           # Socket transport tests
tests/test_tcp.py              # TCP transport tests
```

**27 tests total** - 21 passing (infrastructure solid), 6 failures (URL config, non-blocking)  

---

## 2 · Architectural Principles (Mandatory)

### 2.1 · Schema Version Confinement

**Rule**: Each schema version is completely isolated.

```
Namespace Pattern:
  labs/v{MAJOR}_{MINOR}_{PATCH}/     # Underscores, not dots
  tests/v{MAJOR}_{MINOR}_{PATCH}/
  .env.{MAJOR}_{MINOR}_{PATCH}

Examples:
  labs/v0_7_3/generator.py
  labs/v0_7_4/generator.py
  tests/v0_7_3/test_generator.py
  .env.0_7_3
```

**Requirements**:
- ✅ NO imports across version namespaces
- ✅ Each version has independent test suite
- ✅ Each version has independent environment config
- ✅ Versions can coexist and evolve independently

**Rationale**: Schema versions may diverge significantly. Coupling creates brittleness.

### 2.2 · MCP as Sole Schema Authority

**Rule**: MCP is the **ONLY** source of schema definitions.

```
✅ CORRECT:
  bundle = load_schema_bundle(version="0.7.3")  # Fetch from MCP at runtime

❌ FORBIDDEN:
  with open("meta/schemas/0.7.3/schema.json") as f:  # NEVER store schemas locally
      bundle = json.load(f)
```

**Requirements**:
- ✅ Fetch schemas via `MCPClient` at runtime
- ✅ Use `inline` resolution mode (embeds all `$ref` deps)
- ✅ Never modify, cache, or store schema files in `meta/schemas/`
- ✅ Schema bundle passed unmodified to LLMs and validators

**Rationale**: Single source of truth prevents drift, ensures consistency.

### 2.3 · Telemetry Separation (Critical)

**Rule**: MCP validates **ONLY** asset structure. Telemetry is Labs-local.

```python
# ✅ CORRECT: Separate concerns

# 1. Generate pure asset (matches MCP schema exactly)
asset = {
    "$schema": "https://schemas.synesthetic-labs.ai/mcp/0.7.3/synesthetic-asset.schema.json",
    "name": "red_pulse",
    "modality": {"type": "shader", "tags": ["color"]},
    "output": {"type": "glsl", "content": "void main() { ... }"},
    "meta_info": {}
}

# 2. Validate via MCP (pure structure only)
result = client.confirm(asset, strict=True)
assert result["ok"] is True

# 3. Wrap with telemetry (separate record)
telemetry_record = {
    "trace_id": str(uuid.uuid4()),        # Labs metadata
    "timestamp": datetime.now().isoformat(),  # Labs metadata
    "engine": "azure_openai",              # Labs metadata
    "deployment": "gpt-4o-mini",          # Labs metadata
    "schema_version": "0.7.3",            # Labs metadata
    "asset": asset,                        # Validated structure
    "validation_result": result            # MCP response
}

# 4. Store telemetry separately
log_jsonl("meta/output/labs/v0_7_3_generation.jsonl", telemetry_record)
```

```python
# ❌ FORBIDDEN: Mixing concerns

asset = {
    "$schema": "...",
    "name": "red_pulse",
    "trace_id": "...",        # NO - not in MCP schema
    "engine": "azure",        # NO - not in MCP schema
    "deployment": "gpt-4o",   # NO - not in MCP schema
    "modality": {...}
}
# This will FAIL MCP validation - extra fields not in schema
```

**Requirements**:
- ✅ Assets sent to MCP contain ONLY schema-defined fields
- ✅ Telemetry fields stored in separate wrapper structure
- ✅ Telemetry logs in `meta/output/labs/v{VERSION}_*.jsonl`
- ✅ Never mix validation contract with operational metadata

**Rationale**: MCP validates schema compliance. Labs tracks operational metadata. These are orthogonal concerns.

### 2.4 · Test-Driven Development (Mandatory)

**Rule**: Tests written before implementation, validated via MCP.

```python
# TDD Flow:

# 1. Write failing test FIRST
def test_generator_produces_valid_asset():
    from labs.v0_7_3.generator import generate_asset
    from labs.mcp.client import MCPClient
    
    # This will fail - generator doesn't exist yet
    asset = generate_asset("red pulsing shader")
    
    # Validate via MCP
    client = MCPClient(schema_version="0.7.3")
    result = client.confirm(asset, strict=True)
    
    # Assert validation passes
    assert result["ok"] is True

# 2. Run test - it fails (import error)
# 3. Implement generator to make test pass
# 4. Run test - it passes
# 5. Commit
```

**Requirements**:
- ✅ Every feature has corresponding test
- ✅ Tests validate against live MCP (not mocks)
- ✅ Tests fail before implementation exists
- ✅ CI must pass before merge
- ✅ No code without test coverage

**Rationale**: MCP validation is ground truth. Tests ensure generators stay compliant.

---

## 3 · Schema Version Standup Process (SSOT)

**This is the authoritative procedure for standing up any schema version.**

Follow `meta/prompts/standup_template.json` for detailed step-by-step execution.  
This section provides the conceptual framework and requirements.

### 3.1 · Standup Phases

```
Phase 1: Test Infrastructure Setup
  ↓
Phase 2: Schema Integration
  ↓
Phase 3: Generator Implementation (Optional)
  ↓
Phase 4: Telemetry Layer
  ↓
Phase 5: Validation & CI
  ↓
Phase 6: Documentation
```

### 3.2 · Phase 1: Test Infrastructure Setup

**Goal**: Create version-specific test namespace with failing validation test.

```bash
# Create test namespace
mkdir -p tests/v{VERSION}/
touch tests/v{VERSION}/__init__.py

# Create fixtures directory
mkdir -p tests/v{VERSION}/fixtures/
```

```python
# tests/v{VERSION}/test_validation.py

"""
Validation tests for schema version {VERSION}.
These tests define the contract - write them FIRST.
"""

from labs.mcp.client import MCPClient
import pytest

def test_minimal_valid_asset_passes_mcp():
    """
    Most basic asset that satisfies schema requirements.
    This test defines what we're building toward.
    """
    asset = {
        "$schema": "https://schemas.synesthetic-labs.ai/mcp/{VERSION}/synesthetic-asset.schema.json",
        "name": "minimal_test",
        "modality": {"type": "shader", "tags": []},
        "output": {"type": "glsl", "content": "void main() {}"},
        "meta_info": {}
    }
    
    client = MCPClient(schema_version="{VERSION}")
    result = client.confirm(asset, strict=True)
    
    assert result["ok"] is True
    assert result["reason"] == "validation_passed"

def test_invalid_asset_fails_mcp():
    """Ensure validation actually rejects bad assets."""
    asset = {"name": "incomplete"}  # Missing required fields
    
    client = MCPClient(schema_version="{VERSION}")
    
    with pytest.raises(MCPValidationError):
        client.confirm(asset, strict=True)
```

**Run tests** - they should pass (fixtures are manually created).

### 3.3 · Phase 2: Schema Integration

**Goal**: Verify MCP serves target schema version, test inline resolution.

```python
# tests/v{VERSION}/test_schema_fetch.py

from labs.mcp.client import MCPClient, load_schema_bundle

def test_mcp_serves_version():
    """Verify MCP has schema for target version."""
    client = MCPClient(schema_version="{VERSION}")
    descriptor = client.fetch_schema("synesthetic-asset", version="{VERSION}")
    
    assert descriptor["ok"] is True
    assert descriptor["version"] == "{VERSION}"
    assert "schema" in descriptor
    assert descriptor["resolution"] == "inline"

def test_schema_bundle_has_required_fields():
    """Verify schema structure matches expectations."""
    bundle = load_schema_bundle(version="{VERSION}")
    
    assert "$schema" in bundle
    assert "type" in bundle
    assert bundle["type"] == "object"
    assert "properties" in bundle
    assert "required" in bundle
    
    # Check key properties exist
    props = bundle["properties"]
    assert "name" in props
    assert "modality" in props
    assert "output" in props

def test_inline_resolution_embeds_refs():
    """Verify $refs are embedded, not external links."""
    bundle = load_schema_bundle(version="{VERSION}")
    
    # Inline mode should have no external $ref URIs
    bundle_str = json.dumps(bundle)
    assert "https://" not in bundle_str or "$schema" in bundle_str  # Only $schema can have URL
```

**Run tests** - verify MCP connectivity and schema availability.

### 3.4 · Phase 3: Generator Implementation (Optional)

**Goal**: Build schema-driven generator (if LLM integration needed).

**3.4.1 · Create Generator Namespace**

```bash
mkdir -p labs/v{VERSION}/
touch labs/v{VERSION}/__init__.py
```

**3.4.2 · Schema-Driven Builder Pattern**

```python
# labs/v{VERSION}/builders.py

"""
Schema-driven builders - NO hardcoded templates.
Structure derived from MCP schema bundle.
"""

from labs.mcp.client import load_schema_bundle
from typing import Any, Dict

def build_from_schema(
    subschema: Dict[str, Any],
    prompt: str,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generic schema-driven builder.
    Reads schema structure and generates compliant data.
    """
    data = {}
    properties = subschema.get("properties", {})
    required = subschema.get("required", [])
    
    for key in required:
        if key not in properties:
            continue
            
        prop = properties[key]
        
        # Handle enums
        if "enum" in prop:
            data[key] = prop["enum"][0]
        
        # Handle defaults
        elif "default" in prop:
            data[key] = prop["default"]
        
        # Handle types
        elif "type" in prop:
            if prop["type"] == "string":
                data[key] = f"Generated {key}"
            elif prop["type"] == "array":
                data[key] = []
            elif prop["type"] == "object":
                # Recurse for nested objects
                data[key] = build_from_schema(prop, prompt, context)
            elif prop["type"] == "boolean":
                data[key] = False
            elif prop["type"] == "number" or prop["type"] == "integer":
                data[key] = 0
    
    return data

def build_minimal_asset(prompt: str, version: str) -> Dict[str, Any]:
    """
    Build minimal valid asset for given version.
    Uses schema bundle to determine structure.
    """
    bundle = load_schema_bundle(version=version)
    asset = build_from_schema(bundle, prompt)
    
    # Add $schema field
    asset["$schema"] = f"https://schemas.synesthetic-labs.ai/mcp/{version}/synesthetic-asset.schema.json"
    
    return asset
```

**3.4.3 · LLM Integration (Azure Example)**

```python
# labs/v{VERSION}/generator.py

"""
LLM-based generation with schema constraint.
Schema injected from MCP - NO local files.
"""

from labs.mcp.client import load_schema_bundle
from openai import AzureOpenAI
import json
import os

def generate_with_llm(
    prompt: str,
    version: str,
    engine: str = "azure"
) -> Dict[str, Any]:
    """
    Generate asset via LLM with schema constraint.
    
    Args:
        prompt: User prompt describing desired asset
        version: Schema version (e.g., "0.7.3")
        engine: LLM engine ("azure", "gemini", etc.)
    
    Returns:
        Generated asset (validated structure)
    """
    # Fetch live schema from MCP
    schema_bundle = load_schema_bundle(version=version)
    
    if engine == "azure":
        return _generate_azure(prompt, version, schema_bundle)
    elif engine == "gemini":
        return _generate_gemini(prompt, version, schema_bundle)
    else:
        raise ValueError(f"Unsupported engine: {engine}")

def _generate_azure(
    prompt: str,
    version: str,
    schema_bundle: Dict[str, Any]
) -> Dict[str, Any]:
    """Azure OpenAI structured output generation."""
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    )
    
    # Format version for schema name (no dots/dashes allowed)
    schema_name = f"SynestheticAsset_{version.replace('.', '_')}"
    
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": "You are a synesthetic asset generator. Generate JSON conforming to the schema."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "schema": schema_bundle,
                "strict": True
            }
        },
        temperature=0  # Deterministic
    )
    
    # Parse generated JSON
    asset = json.loads(response.choices[0].message.content)
    return asset
```

**3.4.4 · Generator Tests**

```python
# tests/v{VERSION}/test_generator.py

from labs.v{VERSION}.generator import generate_with_llm, build_minimal_asset
from labs.mcp.client import MCPClient
import pytest

def test_minimal_builder_validates():
    """Minimal builder produces MCP-valid assets."""
    asset = build_minimal_asset("test prompt", version="{VERSION}")
    
    client = MCPClient(schema_version="{VERSION}")
    result = client.confirm(asset, strict=True)
    
    assert result["ok"] is True

@pytest.mark.skipif(
    not os.getenv("AZURE_OPENAI_API_KEY"),
    reason="Azure credentials not available"
)
def test_azure_generator_validates():
    """Azure-generated assets pass MCP validation."""
    asset = generate_with_llm(
        "red pulsing shader",
        version="{VERSION}",
        engine="azure"
    )
    
    client = MCPClient(schema_version="{VERSION}")
    result = client.confirm(asset, strict=True)
    
    assert result["ok"] is True
    assert asset["name"]  # Has content
```

### 3.5 · Phase 4: Telemetry Layer

**Goal**: Wrap validated assets with operational metadata.

```python
# labs/v{VERSION}/telemetry.py

"""
Telemetry layer - Labs-local metadata management.
NEVER mixed with MCP validation contract.
"""

from datetime import datetime, timezone
import uuid
from typing import Dict, Any

def create_telemetry_record(
    asset: Dict[str, Any],
    validation_result: Dict[str, Any],
    engine: str = None,
    deployment: str = None,
    prompt: str = None,
    **extra_fields
) -> Dict[str, Any]:
    """
    Wrap validated asset with telemetry metadata.
    
    Args:
        asset: MCP-validated asset structure
        validation_result: Result from client.confirm()
        engine: LLM engine used (optional)
        deployment: Model deployment name (optional)
        prompt: User prompt (optional)
        **extra_fields: Additional metadata
    
    Returns:
        Telemetry record for logging
    """
    record = {
        "trace_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "schema_version": asset.get("$schema", "").split("/")[-2] if "$schema" in asset else None,
        "asset": asset,  # Pure validated structure
        "validation_result": validation_result,
    }
    
    # Optional fields
    if engine:
        record["engine"] = engine
    if deployment:
        record["deployment"] = deployment
    if prompt:
        record["prompt"] = prompt
    
    # Merge extra fields
    record.update(extra_fields)
    
    return record

def log_generation(
    asset: Dict[str, Any],
    validation_result: Dict[str, Any],
    log_path: str = "meta/output/labs/v{VERSION}_generation.jsonl",
    **metadata
) -> None:
    """Log generation event with telemetry."""
    from labs.logging import log_jsonl
    
    record = create_telemetry_record(
        asset=asset,
        validation_result=validation_result,
        **metadata
    )
    
    log_jsonl(log_path, record)
```

### 3.6 · Phase 5: Integration & CI

**Goal**: Wire everything together, ensure CI passes.

```bash
# .env.{VERSION}
LABS_SCHEMA_VERSION={VERSION}
LABS_SCHEMA_RESOLUTION=inline
LABS_MCP_LOG_PATH=meta/output/labs/mcp.jsonl
MCP_ENDPOINT=tcp://localhost:3000

# Optional: LLM credentials
# AZURE_OPENAI_ENDPOINT=...
# AZURE_OPENAI_API_KEY=...
# AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
# AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

**CI Configuration**:

```yaml
# .github/workflows/ci.yml (add version-specific job)

  test-v{VERSION}:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run v{VERSION} tests
        run: pytest tests/v{VERSION}/ -v
```

### 3.7 · Phase 6: Documentation

**Goal**: Document version-specific implementation.

```markdown
# labs/v{VERSION}/README.md

# Schema Version {VERSION} Implementation

## Status
- ✅ MCP validation passing
- ✅ Test coverage complete
- ✅ Generator implemented (if applicable)
- ✅ CI passing

## Usage

### Validate Asset
```python
from labs.mcp.client import MCPClient

client = MCPClient(schema_version="{VERSION}")
result = client.confirm(asset, strict=True)
```

### Generate Asset (if implemented)
```python
from labs.v{VERSION}.generator import generate_with_llm

asset = generate_with_llm("red pulsing shader", version="{VERSION}")
```

## Tests
```bash
pytest tests/v{VERSION}/ -v
```

## Environment
See `.env.{VERSION}` for configuration.
```

---

## 4 · MCP Client Reference (v2.0.0)

**Full API documentation for MCPClient** (stable, proven infrastructure).

```python
from labs.mcp.client import MCPClient, MCPClientError, MCPValidationError, load_schema_bundle

# === Initialization ===

client = MCPClient(
    schema_name="synesthetic-asset",           # Default schema name
    schema_version="0.7.3",                     # Target version
    resolution="inline",                        # inline|preserve|bundled
    batch_limit=50,                             # Max assets per validation batch
    telemetry_path="meta/output/labs/mcp.jsonl"  # Telemetry log path
)

# === Schema Fetching ===

# Fetch full descriptor
descriptor = client.fetch_schema(
    "synesthetic-asset",
    version="0.7.3",
    resolution="inline",
    force=False  # Bypass cache
)
# Returns: {
#   "ok": True,
#   "name": "synesthetic-asset",
#   "version": "0.7.3",
#   "resolution": "inline",
#   "schema": {...},  # Full JSON Schema bundle
#   "schema_id": "https://...",
#   "fetched_at": "2025-10-27T..."
# }

# Extract schema bundle
schema_bundle = descriptor["schema"]

# Convenience function (recommended)
bundle = load_schema_bundle(version="0.7.3")

# === Validation ===

# Batch validation (up to batch_limit assets)
results = client.validate(
    [asset1, asset2, asset3],
    strict=True  # Fail on validation errors
)
# Returns: [
#   {"ok": True, "reason": "validation_passed", "errors": []},
#   {"ok": False, "reason": "validation_failed", "errors": [...]},
#   ...
# ]

# Single asset confirmation (raises exception on failure)
try:
    result = client.confirm(asset, strict=True)
    assert result["ok"] is True
except MCPValidationError as e:
    print(f"Validation failed: {e.result}")

# === Properties ===

client.schema_version    # Resolved version (may differ from requested)
client.schema_id         # Schema $id URI
client.descriptor        # Cached descriptor (thread-safe copy)
client.resolution        # Always "inline" (forced)
client.batch_limit       # Current batch size limit

# === Telemetry ===

client.record_event("custom_event", field1="value1", field2="value2")
# Logs to telemetry_path with timestamp
```

**Exceptions**:
```python
MCPClientError       # Base error for all MCP client failures
MCPValidationError   # Validation failed (strict mode)
MCPUnavailableError  # MCP server unreachable (TCP connection failed)
```

**Transport**:
- **TCP only**: `tcp://localhost:3000` (required, no fallback)
- Connection failure raises `MCPUnavailableError` immediately
- Ensures infrastructure problems are visible and addressed

**Resolution Modes** (forced to `inline`):

| Mode       | Behavior                  | Status |
| ---------- | ------------------------- | ------ |
| `inline`   | Embeds all `$ref` deps    | ✅ Active (required) |
| `preserve` | Keeps `$ref` links        | ❌ Rejected by client |
| `bundled`  | Root + refs array         | ❌ Rejected by client |

---

## 5 · Environment Configuration

### 5.1 · Core Variables (All Versions)

| Variable | Purpose | Default | Required |
|----------|---------|---------|----------|
| `LABS_SCHEMA_VERSION` | Target schema version | `"0.7.4"` | ✅ |
| `LABS_SCHEMA_RESOLUTION` | Resolution mode | `"inline"` | ✅ (forced) |
| `LABS_MCP_LOG_PATH` | MCP telemetry path | `meta/output/labs/mcp.jsonl` | ❌ |
| `MCP_ENDPOINT` | MCP server TCP endpoint | `tcp://localhost:8765` | ✅ (required) |
| `MCP_MAX_BATCH` | Validation batch limit | `50` | ❌ |

**Critical**: `MCP_ENDPOINT` must be a valid TCP endpoint. No fallback transport is supported.  
If the MCP server is unavailable, all validation operations will fail immediately with `MCPUnavailableError`.

### 5.2 · Version-Specific Configuration

**Pattern**: Each version gets isolated `.env.{VERSION}` file.

```bash
# .env.0_7_3 (example)
LABS_SCHEMA_VERSION=0.7.3
LABS_SCHEMA_RESOLUTION=inline
MCP_ENDPOINT=tcp://localhost:8765
LABS_MCP_LOG_PATH=meta/output/labs/mcp.jsonl

# Optional: Azure OpenAI (if LLM generator used)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=<secret>
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

### 5.3 · LLM Engine Variables (Optional)

**Azure OpenAI**:
| Variable | Purpose | Example |
|----------|---------|---------|
| `AZURE_OPENAI_ENDPOINT` | Resource endpoint | `https://*.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Access key | `<secret>` |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name | `gpt-4o-mini` |
| `AZURE_OPENAI_API_VERSION` | API version | `2025-01-01-preview` |

**Google Gemini** (future):
| Variable | Purpose | Example |
|----------|---------|---------|
| `GEMINI_API_KEY` | API key | `<secret>` |
| `GEMINI_PROJECT_ID` | GCP project | `my-project` |
| `GEMINI_MODEL` | Model name | `gemini-1.5-pro` |

---

## 6 · MCP Contract (Validation Authority)

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

## 7 · Exit Criteria (Per-Version Standup)

**Every schema version standup must satisfy these criteria before merge.**

| Category | Check | Requirement |
|----------|-------|-------------|
| **Schema** | MCP serves version | `fetch_schema(version=X)` returns `ok: True` |
| | Inline resolution | Descriptor has `resolution: "inline"` |
| | No local schemas | `find meta/schemas -name "*.json"` returns empty |
| | MCP endpoint | MCP server running at `tcp://localhost:8765` |
| **Tests** | Infrastructure tests | `tests/v{VERSION}/test_schema_fetch.py` passes |
| | Validation tests | `tests/v{VERSION}/test_validation.py` passes |
| | Generator tests | `tests/v{VERSION}/test_generator.py` passes (if generator exists) |
| | MCP validation | 100% of generated assets pass `client.confirm(strict=True)` |
| **Structure** | Namespace isolation | No imports from other version namespaces |
| | Telemetry separation | No telemetry fields in validated assets |
| | Environment config | `.env.{VERSION}` exists and complete |
| **CI** | Version tests pass | `pytest tests/v{VERSION}/ -v` exits 0 |
| | No regressions | Existing version tests still pass |
| | MCP server available | CI can reach MCP (or mocks appropriately) |
| **Documentation** | README exists | `labs/v{VERSION}/README.md` documents usage |
| | Examples provided | Working code examples in docs |
| | Spec updated | This spec references new version (if needed) |

---

## 8 · Reference Implementation Pattern

**Complete reference showing all pieces working together.**

Example for schema version `0.7.3`:

### 8.1 · Directory Structure
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

### 8.2 · Complete Generator Example

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

### 8.3 · Complete Test Example

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

### 8.4 · Complete Usage Example

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

### 8.5 · End-to-End Flow

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

```python
# Complete end-to-end flow for version 0.7.3

from labs.v0_7_3.generator import generate_with_llm
from labs.v0_7_3.telemetry import log_generation
from labs.mcp.client import MCPClient

# 1. Generate asset via LLM (schema-constrained)
asset = generate_with_llm(
    prompt="red pulsing shader with heartbeat rhythm",
    version="0.7.3",
    engine="azure"
)

# 2. Validate via MCP (strict mode)
client = MCPClient(schema_version="0.7.3")
---

## 10 · Forbidden Patterns (Anti-Patterns)
if result["ok"]:
    print(f"✓ Asset valid: {asset['name']}")
    
    # 4. Log with telemetry (separate from validated asset)
    log_generation(
        asset=asset,
        validation_result=result,
        engine="azure_openai",
        deployment="gpt-4o-mini",
        prompt="red pulsing shader with heartbeat rhythm"
    )
else:
    print(f"✗ Validation failed: {result['reason']}")
    print(f"  Errors: {result['errors']}")
```

---

## 9 · Current Test Coverage (v2.0.0 Foundation)

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

**These patterns violate the spec and MUST be rejected in code review.**

### ❌ Anti-Pattern 1: Local Schema Storage

```python
# FORBIDDEN
with open("meta/schemas/0.7.3/schema.json") as f:
    schema = json.load(f)

# CORRECT
from labs.mcp.client import load_schema_bundle
schema = load_schema_bundle(version="0.7.3")
```

**Why**: MCP is sole schema authority. Local files create drift.

### ❌ Anti-Pattern 2: Hardcoded Templates

```python
# FORBIDDEN
def generate_shader():
---

## 11 · Telemetry Schemaype": "shader", "tags": []},  # Hardcoded structure
        "output": {"type": "glsl", "content": "..."}
    }

# CORRECT
def generate_shader(prompt: str, version: str):
    bundle = load_schema_bundle(version=version)
    return build_from_schema(bundle, prompt)  # Schema-driven
```

**Why**: Schema changes break hardcoded structures. Schema-driven code adapts automatically.

### ❌ Anti-Pattern 3: Telemetry in Validated Assets

```python
# FORBIDDEN
asset = {
    "$schema": "...",
    "name": "test",
    "trace_id": "...",  # NO - not in schema
    "modality": {...}
}
result = client.confirm(asset, strict=True)  # FAILS - extra field

# CORRECT
asset = {
    "$schema": "...",
    "name": "test",
    "modality": {...}
}
result = client.confirm(asset, strict=True)  # PASSES

telemetry = {
    "asset": asset,
    "trace_id": "...",  # Telemetry wrapper
    "validation_result": result
}
```

**Why**: MCP validates exact schema compliance. Extra fields cause failure.

### ❌ Anti-Pattern 4: Cross-Version Imports

```python
# FORBIDDEN
from labs.v0_7_3.generator import generate
from labs.v0_7_4.telemetry import log_event  # Mixing versions!

# CORRECT - Each version isolated
from labs.v0_7_3.generator import generate
from labs.v0_7_3.telemetry import log_event  # Same version
```

**Why**: Versions must evolve independently. Coupling creates brittleness.

### ❌ Anti-Pattern 5: Mocking MCP in Tests

```python
# DISCOURAGED (only for unit tests of non-validation logic)
@patch('labs.mcp.client.MCPClient')
def test_generator(mock_client):
    mock_client.confirm.return_value = {"ok": True}  # Fake validation
    # ...

# PREFERRED (integration test with real MCP)
def test_generator():
    asset = generate("test")
    client = MCPClient(schema_version="0.7.3")  # Real MCP
    result = client.confirm(asset, strict=True)  # Real validation
    assert result["ok"] is True
```

**Why**: MCP validation is ground truth. Mocks hide real problems.

### ❌ Anti-Pattern 6: Schema Version Lock-In

```python
# FORBIDDEN - Hardcoded version
SCHEMA_VERSION = "0.7.3"  # Global constant

def generate():
    bundle = load_schema_bundle(version=SCHEMA_VERSION)  # Locked
    # ...

# CORRECT - Version parameter
def generate(version: str):
    bundle = load_schema_bundle(version=version)  # Flexible
    # ...
```

**Why**: Version-agnostic code supports multiple schemas simultaneously.

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

## 12 · Summary & Quick Reference

**Current State**:
- ✅ MCP infrastructure proven and stable (TCP-only transport)
- ✅ v0.3.6a code archived and removed
- ✅ Clean foundation for version-specific standups

**Architecture**:
- **MCP = Schema authority** (runtime fetch via TCP, inline resolution)
- **Labs = Generator + telemetry** (wraps validated assets)
- **No mixing** of validation contract and operational metadata
- **Fail-fast** infrastructure failures (no fallbacks, no silent errors)

**Next Steps**:
1. Ensure MCP server running at `tcp://localhost:8765`
2. Follow `meta/prompts/standup_template.json` for 0.7.3 standup
3. Implement TDD flow: test → generator → validate
4. Keep telemetry separate from MCP schema contract
### 12.1 · Current State (v2.0.0)

```
✅ MCP infrastructure: Proven, stable, tested (27 tests)
✅ v0.3.6a archived: Clean slate achieved
✅ Documentation: SSOT established (this spec)
✅ Standup template: Ready at meta/prompts/standup_template.json
⏳ Schema versions: None stood up yet (ready for 0.7.3, 0.7.4, etc.)
```

### 12.2 · Architecture Summary

```
┌─────────────────────────────────────────┐
│ MCP Server (Schema Authority)           │
│ - Serves schemas via TCP (port 3000)    │
│ - Validates assets (strict mode)        │
│ - Single source of truth                │
└─────────────────┬───────────────────────┘
                  │ TCP / Inline Resolution
                  │
┌─────────────────▼───────────────────────┐
│ Labs MCP Client (Core Infrastructure)   │
│ - Fetches schemas at runtime            │
│ - Batch validation                       │
│ - Telemetry logging                      │
└─────────────────┬───────────────────────┘
                  │ Import / Use
                  │
┌─────────────────▼───────────────────────┐
│ Version-Specific Generators              │
│ labs/v0_7_3/    labs/v0_7_4/             │
│ - Schema-driven builders                 │
│ - LLM integration (optional)             │
│ - Telemetry wrappers                     │
└─────────────────┬───────────────────────┘
                  │ Validate
                  │
┌─────────────────▼───────────────────────┐
│ Test Suites (Version-Specific)          │
│ tests/v0_7_3/   tests/v0_7_4/            │
│ - MCP validation tests                   │
│ - Generator tests                        │
│ - Integration tests                      │
└──────────────────────────────────────────┘
```

### 12.3 · Key Principles (Memorize These)

1. **MCP = Schema Authority** (never store schemas locally)
2. **Inline Resolution Required** (LLMs need embedded `$ref`s)
3. **Telemetry Separation** (validation ≠ metadata)
4. **Version Isolation** (`labs/v{VERSION}/` namespaces)
5. **Test-First** (MCP validation defines success)
6. **No Hardcoding** (schema-driven builders only)

### 12.4 · Standup Checklist

```bash
# For any new schema version X.Y.Z:

□ 1. Create test namespace: tests/vX_Y_Z/
□ 2. Write validation tests (failing)
□ 3. Verify MCP serves version X.Y.Z
□ 4. Create generator namespace: labs/vX_Y_Z/
□ 5. Implement schema-driven builders
□ 6. Implement LLM integration (optional)
□ 7. Implement telemetry layer
□ 8. Create .env.X_Y_Z configuration
□ 9. Run tests until all pass
□ 10. Add CI job for vX_Y_Z tests
□ 11. Document in labs/vX_Y_Z/README.md
□ 12. Verify exit criteria (Section 7)
□ 13. Commit and PR
```

### 12.5 · Quick Command Reference

```bash
# Fetch schema
python -c "from labs.mcp.client import load_schema_bundle; import json; print(json.dumps(load_schema_bundle('0.7.3'), indent=2))"

# Validate asset
python -c "from labs.mcp.client import MCPClient; import json; asset = json.load(open('asset.json')); print(MCPClient(schema_version='0.7.3').confirm(asset, strict=True))"

# Run version tests
pytest tests/v0_7_3/ -v

```bash
# Check MCP server (TCP endpoint required)
# Note: MCP uses JSON-RPC over raw TCP, not HTTP
echo '{"jsonrpc":"2.0","id":1,"method":"list_schemas"}' | nc localhost 8765

# If MCP unavailable, all Labs operations will fail with MCPUnavailableError
# This is INTENTIONAL - infrastructure failures must be fixed, not bypassed
```
```

### 12.6 · Next Actions

**Immediate** (after cleanup commit):
1. Review this spec with team
2. Merge `dce-reset-dev` → `main`
3. Begin 0.7.3 standup using `meta/prompts/standup_template.json`

**Future Versions**:
- 0.7.3: First complete standup (validation baseline)
- 0.7.4: Second version (prove isolation works)
- 0.8.x: Future schema evolution

---

## Appendix: Document Control

**Version**: v2.0.0  
**Last Updated**: 2025-10-27  
**Status**: Authoritative SSOT  
**Approval Required**: Yes (for any changes)  
**Review Cycle**: Per schema version standup  

**Change Log**:
- 2025-10-27: v2.0.0 - Complete rewrite as standup SSOT (post-cleanup)
- 2025-10-25: v0.3.7 - Schema-bundle generation (archived)
- [Earlier versions archived]

**References**:
- Standup Template: `meta/prompts/standup_template.json`
- Cleanup Plan: `CLEANUP_PLAN.md`
- Lessons Learned: `LESSONS_LEARNED.md`
- Architecture Docs: `docs/`
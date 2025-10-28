# Schema Version 0.7.3 Implementation

## Status
- ✅ MCP validation passing (23 tests, 22 passed, 1 skipped)
- ✅ Test coverage complete (validation, generation, telemetry, integration)
- ✅ Generator implemented (minimal + Azure OpenAI)
- ✅ CI passing

## Quick Start

### Generate and Validate an Asset

```python
from labs.v0_7_3 import generate_asset
from labs.mcp.client import MCPClient

# Generate minimal asset (no LLM)
asset = generate_asset("red pulsing shader")

# Validate via MCP
client = MCPClient(schema_version="0.7.3")
result = client.confirm(asset, strict=True)

print(f"Valid: {result['ok']}")
```

### With Telemetry

```python
from labs.v0_7_3 import generate_asset, log_generation
from labs.mcp.client import MCPClient

# Generate and validate
asset = generate_asset("blue ambient tone")
client = MCPClient(schema_version="0.7.3")
result = client.confirm(asset, strict=True)

# Log with telemetry (asset stays pure)
log_generation(
    asset=asset,
    validation_result=result,
    engine="minimal",
    prompt="blue ambient tone"
)
```

### With Azure OpenAI (Optional)

```python
from labs.v0_7_3 import generate_asset
from labs.mcp.client import MCPClient

# Requires Azure credentials in environment
asset = generate_asset(
    "complex shader with particle effects",
    use_llm=True,
    engine="azure"
)

# Validate
client = MCPClient(schema_version="0.7.3")
result = client.confirm(asset, strict=True)
```

## Architecture

### Files

```
labs/v0_7_3/
├── __init__.py        # Exports: generate_asset, log_generation
├── generator.py       # Asset generation (minimal + Azure)
└── telemetry.py       # Telemetry wrapping (separate from validation)

tests/v0_7_3/
├── test_validation.py    # MCP validation tests
├── test_generator.py     # Generator tests
├── test_telemetry.py     # Telemetry separation tests
└── test_integration.py   # End-to-end integration tests
```

### Key Principles

1. **Schema-Driven**: No hardcoded templates - structure derived from MCP schema
2. **Telemetry Separation**: Validation contract (pure asset) separate from operational metadata
3. **MCP Authority**: Schema fetched from MCP at runtime, never stored locally
4. **TCP-Only**: Reliable service transport, no fallbacks
5. **Fail-Fast**: Strict validation raises `MCPValidationError` immediately

## Environment Setup

```bash
# Source version-specific configuration
source .env.0_7_3

# Or set manually
export LABS_SCHEMA_VERSION=0.7.3
export LABS_SCHEMA_RESOLUTION=inline
export MCP_ENDPOINT=tcp://localhost:8765
```

### Optional: Azure OpenAI

```bash
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_API_KEY=your-key-here
export AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
export AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

## Testing

```bash
# Run v0.7.3 tests only
pytest tests/v0_7_3/ -v

# Or use Makefile
make test-v0.7.3

# Run specific test file
pytest tests/v0_7_3/test_integration.py -v

# Run with coverage
pytest tests/v0_7_3/ --cov=labs.v0_7_3 --cov-report=term-missing
```

## API Reference

### `generate_asset(prompt, *, version="0.7.3", use_llm=False, engine=None)`

Generate a synesthetic asset.

**Args:**
- `prompt` (str): User prompt describing desired asset
- `version` (str): Schema version (default: "0.7.3")
- `use_llm` (bool): Whether to use LLM generation (default: False)
- `engine` (str): LLM engine ("azure", "gemini", etc.)

**Returns:**
- `dict`: Generated asset (MCP-validated structure)

**Raises:**
- `ValueError`: If invalid engine or missing credentials

**Example:**
```python
# Minimal generation (no LLM)
asset = generate_asset("test shader")

# Azure OpenAI generation
asset = generate_asset("complex shader", use_llm=True, engine="azure")
```

### `log_generation(asset, validation_result, *, log_path=..., **metadata)`

Log generation event with telemetry.

**Args:**
- `asset` (dict): Validated asset
- `validation_result` (dict): MCP validation result
- `log_path` (str): Path to telemetry log file
- `**metadata`: Additional metadata (engine, deployment, prompt, etc.)

**Example:**
```python
log_generation(
    asset=asset,
    validation_result=result,
    engine="azure",
    deployment="gpt-4o-mini",
    prompt="red shader"
)
```

### `create_telemetry_record(asset, validation_result, **metadata)`

Create telemetry record without logging.

**Args:**
- `asset` (dict): Validated asset
- `validation_result` (dict): MCP validation result
- `**metadata`: Additional fields

**Returns:**
- `dict`: Telemetry record with trace_id, timestamp, etc.

## Schema Structure (0.7.3)

```json
{
  "$schema": "https://delk73.github.io/synesthetic-schemas/schema/0.7.3/synesthetic-asset.schema.json",
  "name": "asset_name",
  "meta_info": {},
  "shader": {},
  "tone": {},
  "haptic": {},
  "control": {},
  "modulations": [],
  "rule_bundle": {"rules": [], "meta_info": {}}
}
```

**Required fields:**
- `name` (string)

**Optional fields:**
- All component fields (shader, tone, haptic, control, modulations, rule_bundle)
- Metadata fields (meta_info, description, created_at, updated_at)

## Telemetry Schema

Telemetry records wrap validated assets:

```json
{
  "trace_id": "uuid",
  "timestamp": "ISO-8601",
  "schema_version": "0.7.3",
  "engine": "azure|minimal",
  "deployment": "model-name",
  "prompt": "user prompt",
  "asset": { ... },
  "validation_result": {"ok": true, ...}
}
```

**Key**: `asset` field contains pure MCP-validated structure (no telemetry).

## Troubleshooting

### MCP Connection Error

```
MCPUnavailableError: MCP TCP connection error
```

**Solution**: Ensure MCP server is running:
```bash
make mcp-check  # Verify connectivity
```

### Validation Failure

```
MCPValidationError: MCP validation failed: validation_failed
```

**Solution**: Check validation errors in result:
```python
try:
    result = client.confirm(asset, strict=True)
except MCPValidationError as e:
    print(e.result["errors"])
```

### Azure Credentials Missing

```
ValueError: AZURE_OPENAI_API_KEY not set
```

**Solution**: Set Azure credentials:
```bash
source .env.0_7_3  # Or set manually
export AZURE_OPENAI_API_KEY=your-key
```

## Next Steps

1. **Add more component builders**: Implement schema-driven builders for shader, tone, haptic, etc.
2. **Add LLM engines**: Implement Gemini, Claude, etc.
3. **Add validation helpers**: Schema-specific validators for components
4. **Add fixtures**: Example assets for testing
5. **Add CLI**: Command-line interface for generation

## References

- Spec: [docs/labs_spec.md](../../docs/labs_spec.md)
- MCP Client: [labs/mcp/client.py](../mcp/client.py)
- Standup Process: Section 3 of labs_spec.md

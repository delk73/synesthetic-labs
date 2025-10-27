# Schema-Version-Confined Labs Architecture

## Core Principle

**Each schema version gets its own isolated, self-contained namespace.**

This prevents version mixing, enables side-by-side support, and provides a repeatable template for standup.

---

## Why Version Confinement?

### Problems with Mixed Versions (v0.3.6a)

- Tried to support 0.7.3 and 0.7.4 simultaneously
- No clear separation between version-specific code
- Version normalization layers added complexity
- Tests didn't enforce version boundaries
- Impossible to tell which code worked with which schema

### Benefits of Version Confinement

1. **No Version Mixing** - Clear namespace boundaries prevent bugs
2. **Parallel Support** - Can maintain 0.7.3 while developing 0.7.4
3. **Easy Upgrades** - New version = new namespace, old code untouched
4. **Testable** - Each version has dedicated test suite
5. **Self-Contained** - All version-specific code in one place
6. **Templated** - Repeatable standup pattern

---

## Directory Structure Pattern

```
synesthetic-labs/
├── labs/
│   ├── mcp/                    # Shared MCP client (version-agnostic)
│   ├── transport.py            # Shared transport layer
│   ├── logging.py              # Shared logging
│   ├── core.py                 # Shared utilities
│   │
│   └── v0_7_3/                 # 0.7.3 NAMESPACE
│       ├── __init__.py         # Version lock, env loading
│       ├── generator.py        # Schema-driven generator for 0.7.3
│       └── validator.py        # 0.7.3-specific helpers
│
├── tests/
│   ├── conftest.py             # Shared test config
│   ├── test_mcp.py             # MCP client tests (shared)
│   │
│   └── v0_7_3/                 # 0.7.3 TEST NAMESPACE
│       ├── __init__.py
│       ├── test_validation.py  # THE test - MCP validation
│       └── test_generator.py   # 0.7.3 generator tests
│
├── meta/
│   ├── prompts/
│   │   ├── v2standup.json      # 0.7.3 standup script
│   │   └── template_standup.json  # Template for future versions
│   ├── schemas/
│   │   └── 0.7.3/              # Cached reference (MCP is authority)
│   └── output/
│       └── v0_7_3/             # 0.7.3-specific logs
│
└── .env.0.7.3                  # Version-specific environment
```

---

## Version Namespace Pattern

### `labs/v0_7_3/__init__.py`

```python
"""Synesthetic Labs - Schema version 0.7.3 namespace."""

import os
from pathlib import Path
from dotenv import load_dotenv

SCHEMA_VERSION = '0.7.3'

# Load version-specific environment
env_file = Path(__file__).parent.parent.parent / f'.env.{SCHEMA_VERSION}'
if env_file.exists():
    load_dotenv(env_file)

# Verify schema version lock
loaded_version = os.getenv('LABS_SCHEMA_VERSION')
if loaded_version and loaded_version != SCHEMA_VERSION:
    raise ValueError(
        f'Schema version mismatch: '
        f'namespace={SCHEMA_VERSION}, env={loaded_version}'
    )

from .generator import generate_asset

__all__ = ['generate_asset', 'SCHEMA_VERSION']
```

### `labs/v0_7_3/generator.py`

```python
"""Schema-driven generator for synesthetic assets (0.7.3)."""

from labs.mcp.client import load_schema_bundle

SCHEMA_VERSION = '0.7.3'

def generate_asset(mcp_client, prompt: str) -> dict:
    """Generate asset for schema version 0.7.3."""
    
    # Fetch schema - single source of truth
    schema = load_schema_bundle(
        client=mcp_client,
        version=SCHEMA_VERSION
    )
    
    # Build asset matching 0.7.3 schema
    asset = {
        '$schema': f'https://synesthetic.dev/schemas/{SCHEMA_VERSION}/synesthetic-asset.schema.json',
        'version': SCHEMA_VERSION  # Version lock
    }
    
    # ... schema-driven construction
    
    return asset
```

### `tests/v0_7_3/test_validation.py`

```python
"""Validation tests for 0.7.3 generator."""

from labs.mcp.client import MCPClient
from labs.v0_7_3.generator import generate_asset, SCHEMA_VERSION

def test_mcp_validation_0_7_3():
    """THE test: Generator produces valid 0.7.3 asset."""
    
    client = MCPClient(schema_version=SCHEMA_VERSION)
    asset = generate_asset(client, 'peaceful waves')
    
    # Version confinement check
    assert asset['version'] == SCHEMA_VERSION, \
        f"Expected {SCHEMA_VERSION}, got {asset['version']}"
    
    # MCP strict validation
    result = client.validate(asset, strict=True)
    assert result['valid'] is True, \
        f"MCP validation failed: {result.get('errors', [])}"
    
    print(f'✅ Asset validated for {SCHEMA_VERSION}')
```

### `.env.0.7.3`

```env
# Schema version 0.7.3 environment
LABS_SCHEMA_VERSION=0.7.3
LABS_SCHEMA_RESOLUTION=inline
LABS_SCHEMA_NAMESPACE=v0_7_3

# MCP connectivity (TCP only)
LABS_MCP_TRANSPORT=tcp
LABS_MCP_HOST=localhost
LABS_MCP_PORT=3000

# Output
LABS_OUTPUT_DIR=meta/output/v0_7_3/
```

---

## Import Pattern

### ✅ Correct - Version-Explicit

```python
# In tests
from labs.v0_7_3.generator import generate_asset, SCHEMA_VERSION

# In application code
from labs.v0_7_3 import generate_asset

# Version is always explicit in import path
```

### ❌ Wrong - Version-Ambiguous

```python
# Don't do this - which version?
from labs.generator import generate_asset

# Don't do this - mixed versions
from labs.v0_7_3.generator import generate_asset_v3
from labs.v0_7_4.generator import generate_asset_v4
```

---

## Standup Template for Future Versions

When MCP releases 0.7.4, 0.8.0, etc.:

### Step 1: Create Version Namespace

```bash
# Create 0.7.4 namespace
mkdir -p labs/v0_7_4
mkdir -p tests/v0_7_4
mkdir -p meta/output/v0_7_4
mkdir -p meta/schemas/0.7.4
```

### Step 2: Copy Template Files

```bash
# Copy standup script
cp meta/prompts/v2standup.json meta/prompts/v0_7_4_standup.json

# Update version references
sed -i 's/0.7.3/0.7.4/g' meta/prompts/v0_7_4_standup.json
```

### Step 3: Create Version Files

```bash
# Create namespace __init__.py
cat > labs/v0_7_4/__init__.py << 'EOF'
"""Synesthetic Labs - Schema version 0.7.4 namespace."""
SCHEMA_VERSION = '0.7.4'
# ... (same pattern as v0_7_3)
EOF

# Create generator stub
cat > labs/v0_7_4/generator.py << 'EOF'
"""Schema-driven generator for 0.7.4."""
SCHEMA_VERSION = '0.7.4'
# ... (same pattern as v0_7_3)
EOF

# Create test stub
cat > tests/v0_7_4/test_validation.py << 'EOF'
"""Validation tests for 0.7.4."""
from labs.v0_7_4.generator import generate_asset, SCHEMA_VERSION
# ... (same pattern as v0_7_3)
EOF

# Create environment file
```bash
# Create environment file
cat > .env.0.7.4 << 'EOF'
LABS_SCHEMA_VERSION=0.7.4
LABS_SCHEMA_RESOLUTION=inline
LABS_SCHEMA_NAMESPACE=v0_7_4
LABS_MCP_TRANSPORT=tcp
LABS_MCP_HOST=localhost
LABS_MCP_PORT=3000
LABS_OUTPUT_DIR=meta/output/v0_7_4/
EOF
```
```

### Step 4: TDD Workflow

```bash
# Follow same TDD loop as 0.7.3
pytest tests/v0_7_4/test_validation.py -v
# Fix labs/v0_7_4/generator.py
# Repeat until MCP validation passes
```

### Step 5: Parallel Support

```python
# Both versions work simultaneously
from labs.v0_7_3 import generate_asset as generate_0_7_3
from labs.v0_7_4 import generate_asset as generate_0_7_4

# No cross-contamination
asset_v3 = generate_0_7_3(client, "waves")  # version = '0.7.3'
asset_v4 = generate_0_7_4(client, "waves")  # version = '0.7.4'
```

---

## Version Lifecycle

### Phase 1: Active Development (0.7.3)
```
labs/v0_7_3/ - Current development
tests/v0_7_3/ - Active tests
.env.0.7.3 - Active environment
```

### Phase 2: Parallel Support (0.7.3 + 0.7.4)
```
labs/v0_7_3/ - Stable, maintenance mode
labs/v0_7_4/ - Active development
tests/v0_7_3/ - Regression tests
tests/v0_7_4/ - Active tests
```

### Phase 3: Deprecation (0.7.3 deprecated, 0.7.4 stable)
```
labs/v0_7_3/ - Marked deprecated, kept for reference
labs/v0_7_4/ - Stable production
labs/v0_7_5/ - New active development
```

### Phase 4: Removal (Optional)
```
# Can remove old namespace if no longer needed
rm -rf labs/v0_7_3 tests/v0_7_3
# But keep in git history for reference
```

---

## Self-Contained Checklist

For each version namespace, verify:

- [ ] **Version lock**: `SCHEMA_VERSION` constant in `__init__.py` and `generator.py`
- [ ] **Namespace isolation**: All code in `labs/v{version}/`, all tests in `tests/v{version}/`
- [ ] **Environment file**: `.env.{version}` exists and loads in namespace `__init__.py`
- [ ] **Import pattern**: Tests import from `labs.v{version}`, never ambiguous
- [ ] **Output isolation**: Logs go to `meta/output/v{version}/`
- [ ] **Schema reference**: Cached copy in `meta/schemas/{version}/` (MCP is authority)
- [ ] **Test suite**: `tests/v{version}/test_validation.py` passes MCP strict validation
- [ ] **Standup script**: `meta/prompts/v{version}_standup.json` documents setup

---

## Benefits Over v0.3.6a

| Aspect | v0.3.6a (Mixed) | v2 (Version-Confined) |
|--------|-----------------|------------------------|
| **Version clarity** | Ambiguous which code for which version | Explicit namespace per version |
| **Version mixing** | Easy to mix accidentally | Impossible - compile error |
| **Parallel support** | Complex normalization layers | Clean namespace separation |
| **Upgrades** | Risky - changes affect all versions | Safe - new namespace, old untouched |
| **Testing** | Tests didn't enforce versions | Version-specific test suites |
| **Environment** | Single .env for all versions | `.env.{version}` per version |
| **Imports** | `from labs.generator` (which version?) | `from labs.v0_7_3` (explicit) |
| **Standup** | Manual, ad-hoc | Templated, repeatable pattern |

---

## Future: Multi-Version CLI

When you have multiple versions:

```python
#!/usr/bin/env python
"""CLI supporting multiple schema versions."""

import argparse
from labs.v0_7_3 import generate_asset as generate_0_7_3
from labs.v0_7_4 import generate_asset as generate_0_7_4

GENERATORS = {
    '0.7.3': generate_0_7_3,
    '0.7.4': generate_0_7_4,
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', choices=GENERATORS.keys(), required=True)
    parser.add_argument('prompt')
    
    args = parser.parse_args()
    
    generator = GENERATORS[args.version]
    asset = generator(client, args.prompt)
    
    print(f"Generated {args.version} asset: {asset}")

if __name__ == '__main__':
    main()
```

---

## Summary

**Key Insight**: Schema versions are first-class namespaces, not runtime parameters.

**Pattern**:
- Each schema version → dedicated namespace
- Self-contained: code, tests, environment, output
- Templated: repeatable standup for new versions
- Isolated: no cross-version contamination

**Result**:
- Clear version boundaries
- Safe parallel support
- Easy upgrades
- Testable per version
- Repeatable process

This architecture turns "support multiple schemas" from a complexity nightmare into a simple template pattern.

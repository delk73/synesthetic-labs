.PHONY: help mcp-check mcp-list mcp-schema mcp-validate test clean

# Default target
help:
	@echo "Synesthetic Labs - MCP Verification Targets"
	@echo ""
	@echo "MCP Health & Discovery:"
	@echo "  make mcp-check        - Check if MCP server is reachable (raw TCP)"
	@echo "  make mcp-list         - List available schemas (raw JSON-RPC)"
	@echo "  make mcp-schema       - Fetch schema bundle (raw JSON-RPC)"
	@echo "  make mcp-validate     - Test Labs MCP client (Python)"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run full pytest suite"
	@echo "  make test-mcp         - Run MCP-specific tests only"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            - Remove __pycache__ and .pyc files"
	@echo ""
	@echo "Environment Variables:"
	@echo "  MCP_HOST              - MCP server host (default: 127.0.0.1)"
	@echo "  MCP_PORT              - MCP server port (default: 8765)"
	@echo "  SCHEMA_VERSION        - Schema version (default: 0.7.3)"

# MCP server host/port (override with: make mcp-check MCP_HOST=synesthetic-mcp-serve-1)
MCP_HOST ?= 127.0.0.1
MCP_PORT ?= 8765
SCHEMA_VERSION ?= 0.7.3

# Check if MCP server is reachable
mcp-check:
	@echo "Checking MCP server at $(MCP_HOST):$(MCP_PORT)..."
	@echo '{"jsonrpc":"2.0","id":1,"method":"list_schemas"}' | nc -w 2 $(MCP_HOST) $(MCP_PORT) > /dev/null 2>&1 \
		&& echo "✓ MCP server is responding" \
		|| (echo "✗ MCP server unreachable - is it running?" && exit 1)

# List available schemas
mcp-list:
	@echo "Fetching schema list from $(MCP_HOST):$(MCP_PORT)..."
	@echo '{"jsonrpc":"2.0","id":1,"method":"list_schemas"}' | nc -w 2 $(MCP_HOST) $(MCP_PORT) | python3 -m json.tool

# Fetch schema with inline resolution
mcp-schema:
	@echo "Fetching schema: synesthetic-asset version $(SCHEMA_VERSION) (inline resolution)"
	@echo '{"jsonrpc":"2.0","id":2,"method":"get_schema","params":{"name":"synesthetic-asset","version":"$(SCHEMA_VERSION)","resolution":"inline"}}' \
		| nc -w 2 $(MCP_HOST) $(MCP_PORT) | python3 -m json.tool

# Test MCP validation endpoint (with Python - uses Labs MCP client)
mcp-validate:
	@echo "Testing MCP validation via Labs client..."
	@python3 -c "from labs.mcp.client import MCPClient; client = MCPClient(schema_version='$(SCHEMA_VERSION)'); print('✓ MCPClient initialized'); descriptor = client.fetch_schema('synesthetic-asset'); print(f'✓ Schema fetched: {descriptor.get(\"version\")}')"

# Run full test suite
test:
	pytest -v

# Run only MCP-related tests
test-mcp:
	pytest -v tests/test_mcp*.py tests/test_tcp.py tests/test_socket.py

# Clean Python cache files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned Python cache files"

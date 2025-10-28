#!/usr/bin/env python3
"""
Simple CLI for generating and validating synesthetic assets.
Usage: python -m labs.v0_7_3.cli [prompt]
"""

import argparse
import json
import sys
from labs.v0_7_3 import generate_asset, log_generation
from labs.mcp.client import MCPClient, MCPValidationError


def main():
    parser = argparse.ArgumentParser(
        description="Generate and validate synesthetic assets (v0.7.3)"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default="minimal test asset",
        help="Prompt describing the desired asset"
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use LLM generation (requires Azure credentials)"
    )
    parser.add_argument(
        "--engine",
        default="azure",
        help="LLM engine to use (default: azure)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Log generation with telemetry"
    )
    parser.add_argument(
        "--log-path",
        default="meta/output/labs/v0_7_3_generation.jsonl",
        help="Telemetry log file path"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip MCP validation"
    )
    
    args = parser.parse_args()
    
    try:
        # Generate asset
        print(f"Generating asset: {args.prompt}", file=sys.stderr)
        asset = generate_asset(
            args.prompt,
            use_llm=args.llm,
            engine=args.engine if args.llm else None
        )
        
        # Validate via MCP
        if not args.no_validate:
            print("Validating via MCP...", file=sys.stderr)
            client = MCPClient(schema_version="0.7.3")
            result = client.confirm(asset, strict=True)
            print(f"✓ Validation passed", file=sys.stderr)
        else:
            result = {"ok": True, "reason": "skipped"}
        
        # Log telemetry if requested
        if args.log:
            log_generation(
                asset=asset,
                validation_result=result,
                log_path=args.log_path,
                engine="azure" if args.llm else "minimal",
                prompt=args.prompt
            )
            print(f"✓ Logged to {args.log_path}", file=sys.stderr)
        
        # Output asset
        output = json.dumps(asset, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"✓ Saved to {args.output}", file=sys.stderr)
        else:
            print(output)
        
        return 0
        
    except MCPValidationError as e:
        print(f"✗ Validation failed:", file=sys.stderr)
        print(json.dumps(e.result, indent=2), file=sys.stderr)
        return 1
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

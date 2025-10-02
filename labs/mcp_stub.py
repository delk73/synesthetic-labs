"""Minimal STDIO MCP adapter stub for local development and CI."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict


def _load_request() -> Dict[str, Any]:
    data = sys.stdin.read()
    if not data:
        raise ValueError("no input provided to MCP stub")
    return json.loads(data)


def _success_response(request: Dict[str, Any]) -> Dict[str, Any]:
    if request.get("jsonrpc") == "2.0":
        params = request.get("params")
        asset: Dict[str, Any] = {}
        if isinstance(params, dict):
            asset = params.get("asset", {})
        asset_id = asset.get("asset_id")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "status": "ok",
                "asset_id": asset_id,
                "issues": [],
            },
        }

    asset = request.get("asset", {})
    asset_id = asset.get("asset_id")
    return {
        "status": "ok",
        "asset_id": asset_id,
        "issues": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stub MCP adapter for Labs")
    parser.add_argument(
        "--fail",
        action="store_true",
        help="Force the stub to exit with a non-zero status after reading the request.",
    )
    args = parser.parse_args(argv)

    try:
        request = _load_request()
    except Exception as exc:  # pragma: no cover - defensive input guard
        print(f"invalid request: {exc}", file=sys.stderr)
        return 1

    if args.fail:
        print("stub failure requested", file=sys.stderr)
        return 1

    response = _success_response(request)
    print(json.dumps(response))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

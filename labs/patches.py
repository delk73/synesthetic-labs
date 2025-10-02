"""Patch lifecycle orchestration stubs for Synesthetic Labs."""

from __future__ import annotations

import datetime as _dt
import os
import uuid
from typing import Any, Dict, Mapping, Optional

from labs.agents.critic import CriticAgent
from labs.logging import log_jsonl
from labs.mcp_stdio import resolve_mcp_endpoint

_DEFAULT_PATCH_LOG = "meta/output/labs/patches.jsonl"


def _strict_mode_enabled() -> bool:
    raw = os.getenv("LABS_FAIL_FAST")
    if raw is None:
        return True
    lowered = raw.strip().lower()
    return lowered not in {"0", "false", "no", "off"}


def _trace_id_from_asset(asset: Mapping[str, Any]) -> str:
    if isinstance(asset, Mapping):
        meta = asset.get("meta_info")
        if isinstance(meta, Mapping):
            provenance = meta.get("provenance")
            if isinstance(provenance, Mapping):
                trace_id = provenance.get("trace_id")
                if trace_id:
                    return str(trace_id)
        provenance = asset.get("provenance")
        if isinstance(provenance, Mapping):
            generator_block = provenance.get("generator")
            if isinstance(generator_block, Mapping):
                trace_id = generator_block.get("trace_id")
                if trace_id:
                    return str(trace_id)
    return str(uuid.uuid4())

def _timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()


def preview_patch(
    asset: Mapping[str, Any],
    patch: Mapping[str, Any],
    *,
    log_path: str = _DEFAULT_PATCH_LOG,
) -> Dict[str, Any]:
    """Record a preview of *patch* against *asset* without modifying the asset."""

    strict_flag = _strict_mode_enabled()
    record = {
        "action": "preview",
        "asset_id": asset.get("asset_id"),
        "patch_id": patch.get("id"),
        "changes": patch.get("updates", {}),
        "timestamp": _timestamp(),
        "trace_id": _trace_id_from_asset(asset),
        "strict": strict_flag,
        "mode": "strict" if strict_flag else "relaxed",
        "transport": resolve_mcp_endpoint(),
    }
    log_jsonl(log_path, record)
    return record


def apply_patch(
    asset: Mapping[str, Any],
    patch: Mapping[str, Any],
    *,
    critic: Optional[CriticAgent] = None,
    log_path: str = _DEFAULT_PATCH_LOG,
) -> Dict[str, Any]:
    """Apply *patch* onto *asset*, validate via critic, and log the operation."""

    updates = patch.get("updates", {})
    patched_asset: Dict[str, Any] = dict(asset)
    if isinstance(updates, Mapping):
        patched_asset.update(updates)

    patched_asset.setdefault("asset_id", asset.get("asset_id"))
    patch_id = patch.get("id")

    critic = critic or CriticAgent()
    review = critic.review(dict(patched_asset), patch_id=patch_id)

    record = {
        "action": "apply",
        "asset_id": asset.get("asset_id"),
        "patch_id": patch_id,
        "timestamp": _timestamp(),
        "review": review,
        "trace_id": review.get("trace_id") or _trace_id_from_asset(asset),
        "strict": review.get("strict"),
        "mode": review.get("mode"),
        "transport": review.get("transport"),
    }

    if record["strict"] is None:
        record["strict"] = _strict_mode_enabled()
    if not record.get("mode"):
        record["mode"] = "strict" if record["strict"] else "relaxed"
    if not record.get("transport"):
        record["transport"] = resolve_mcp_endpoint()
    if not record.get("trace_id"):
        record["trace_id"] = _trace_id_from_asset(asset)

    if not review.get("ok"):
        record["failure"] = review.get("validation_error") or {
            "reason": "validation_failed",
            "detail": review.get("validation_reason"),
        }
    log_jsonl(log_path, record)
    return {"asset": patched_asset, "review": review}


def rate_patch(
    patch_id: str,
    rating: Mapping[str, Any],
    *,
    asset_id: Optional[str] = None,
    critic: Optional[CriticAgent] = None,
    log_path: str = _DEFAULT_PATCH_LOG,
) -> Dict[str, Any]:
    """Log a rating stub for *patch_id* with optional asset linkage."""

    critic = critic or CriticAgent()
    critic_record = critic.record_rating(patch_id=patch_id, rating=rating, asset_id=asset_id)

    record = {
        "action": "rate",
        "patch_id": patch_id,
        "asset_id": asset_id,
        "rating": dict(rating),
        "critic_record": critic_record,
        "timestamp": _timestamp(),
        "trace_id": critic_record.get("trace_id") or str(uuid.uuid4()),
        "strict": critic_record.get("strict"),
        "mode": critic_record.get("mode"),
        "transport": critic_record.get("transport"),
    }

    if record["strict"] is None:
        record["strict"] = _strict_mode_enabled()
    if not record.get("mode"):
        record["mode"] = "strict" if record["strict"] else "relaxed"
    if not record.get("transport"):
        record["transport"] = resolve_mcp_endpoint()
    if not record.get("trace_id"):
        record["trace_id"] = str(uuid.uuid4())
    log_jsonl(log_path, record)
    return record


__all__ = ["apply_patch", "preview_patch", "rate_patch"]

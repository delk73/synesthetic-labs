"""Patch lifecycle orchestration stubs for Synesthetic Labs."""

from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, Mapping, Optional

from labs.agents.critic import CriticAgent
from labs.logging import log_jsonl

_DEFAULT_PATCH_LOG = "meta/output/labs/patches.jsonl"


def _timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()


def preview_patch(
    asset: Mapping[str, Any],
    patch: Mapping[str, Any],
    *,
    log_path: str = _DEFAULT_PATCH_LOG,
) -> Dict[str, Any]:
    """Record a preview of *patch* against *asset* without modifying the asset."""

    record = {
        "action": "preview",
        "asset_id": asset.get("id"),
        "patch_id": patch.get("id"),
        "changes": patch.get("updates", {}),
        "timestamp": _timestamp(),
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

    patched_asset.setdefault("id", asset.get("id"))
    patch_id = patch.get("id")

    critic = critic or CriticAgent()
    review = critic.review(dict(patched_asset), patch_id=patch_id)

    record = {
        "action": "apply",
        "asset_id": asset.get("id"),
        "patch_id": patch_id,
        "timestamp": _timestamp(),
        "review": review,
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
    }
    log_jsonl(log_path, record)
    return record


__all__ = ["apply_patch", "preview_patch", "rate_patch"]

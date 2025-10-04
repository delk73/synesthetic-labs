"""Generator agent responsible for proposing candidate assets."""

from __future__ import annotations

import datetime as _dt
import logging
import os
import uuid
from typing import Any, Dict, Optional

from labs.generator.assembler import AssetAssembler
from labs.logging import log_jsonl
from labs.mcp_stdio import resolve_mcp_endpoint

_DEFAULT_LOG_PATH = "meta/output/labs/generator.jsonl"


def _strict_mode_enabled() -> bool:
    raw = os.getenv("LABS_FAIL_FAST")
    if raw is None:
        return True
    lowered = raw.strip().lower()
    return lowered not in {"0", "false", "no", "off"}


class GeneratorAgent:
    """Generate asset proposals based on an input prompt.

    Parameters
    ----------
    log_path:
        Location of the JSONL log sink. The default targets the shared
        repository log directory under ``meta/output``.
    """

    def __init__(
        self,
        log_path: str = _DEFAULT_LOG_PATH,
        *,
        version: str = "v0.2",
        assembler: Optional[AssetAssembler] = None,
    ) -> None:
        self.log_path = log_path
        self._logger = logging.getLogger(self.__class__.__name__)
        self.version = version
        self._assembler = assembler or AssetAssembler(version=version)

    @staticmethod
    def resolve_identifier(asset: Dict[str, Any]) -> Optional[str]:
        """Return a stable identifier for *asset* when available."""

        candidate = asset.get("asset_id")
        if isinstance(candidate, str) and candidate.strip():
            return candidate

        meta_info = asset.get("meta_info") if isinstance(asset, dict) else None
        if isinstance(meta_info, dict):
            provenance = meta_info.get("provenance")
            if isinstance(provenance, dict):
                trace_id = provenance.get("trace_id")
                if isinstance(trace_id, str) and trace_id.strip():
                    return trace_id

        name = asset.get("name") if isinstance(asset, dict) else None
        if isinstance(name, str) and name.strip():
            return name

        return None

    def propose(
        self,
        prompt: str,
        *,
        seed: Optional[int] = None,
        schema_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return a fully assembled asset for *prompt*.

        The payload mirrors the canonical Synesthetic schema sections produced
        by :class:`AssetAssembler` and is logged to the configured JSONL sink
        for traceability.
        """

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        resolved_schema_version = (
            schema_version
            or os.getenv("LABS_SCHEMA_VERSION", AssetAssembler.DEFAULT_SCHEMA_VERSION)
        )
        asset = self._assembler.generate(
            prompt, seed=seed, schema_version=resolved_schema_version
        )

        timestamp = asset.get("timestamp") or _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        schema_url = str(asset.get("$schema", ""))
        is_legacy = "0.7.3" in schema_url

        meta = asset.setdefault("meta_info", {})
        meta_provenance = meta.setdefault("provenance", {})

        if is_legacy:
            trace_id = meta_provenance.get("trace_id") or str(uuid.uuid4())
            meta_provenance.setdefault("trace_id", trace_id)
            meta_provenance.setdefault("mode", "local")
            meta_provenance.setdefault("timestamp", timestamp)
            generator_block = {
                "agent": self.__class__.__name__,
                "version": self.version,
                "generated_at": timestamp,
                "trace_id": trace_id,
            }
        else:
            provenance = asset.setdefault("provenance", {})
            provenance.setdefault("agent", "AssetAssembler")
            provenance.setdefault("version", self._assembler.version)
            generator_block = provenance.setdefault("generator", {})
            generator_block.setdefault("agent", self.__class__.__name__)
            generator_block.setdefault("version", self.version)
            generator_block.setdefault("generated_at", timestamp)
            trace_id = generator_block.get("trace_id") or str(uuid.uuid4())
            generator_block["trace_id"] = trace_id

            meta_provenance.setdefault("trace_id", trace_id)
            meta_provenance.setdefault("mode", "local")
            meta_provenance.setdefault("timestamp", timestamp)

        self._logger.info("Generated asset %s", asset.get("asset_id"))

        log_entry = dict(asset)
        log_entry["trace_id"] = trace_id
        log_entry["mode"] = "local"
        log_entry["strict"] = _strict_mode_enabled()
        log_entry["transport"] = resolve_mcp_endpoint()
        log_entry["schema_version"] = resolved_schema_version
        if is_legacy:
            log_entry.setdefault("provenance", {})
            log_entry["provenance"]["generator"] = generator_block

        log_jsonl(self.log_path, log_entry)
        return asset

    def record_experiment(
        self,
        *,
        asset: Dict[str, Any],
        review: Dict[str, Any],
        experiment_path: Optional[str],
    ) -> Dict[str, Any]:
        """Log a validated experiment linking the asset to persisted output."""

        asset_identifier = self.resolve_identifier(asset)
        if not asset_identifier:
            raise ValueError("asset must include an identifier")

        timestamp = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()

        trace_id = review.get("trace_id") or asset.get("meta_info", {}).get("provenance", {}).get("trace_id")
        if not trace_id:
            trace_id = asset.get("provenance", {}).get("generator", {}).get("trace_id") or str(uuid.uuid4())

        strict_flag = review.get("strict")
        if strict_flag is None:
            strict_flag = _strict_mode_enabled()

        mode = review.get("mode") or ("strict" if strict_flag else "relaxed")
        transport = review.get("transport") or resolve_mcp_endpoint()

        record = {
            "asset_id": asset_identifier,
            "prompt": asset.get("prompt"),
            "experiment_path": experiment_path,
            "trace_id": trace_id,
            "mode": mode,
            "strict": strict_flag,
            "transport": transport,
            "validation": {
                "ok": review.get("ok"),
                "issues": review.get("issues"),
                "status": review.get("validation_status"),
                "reviewed_at": review.get("reviewed_at"),
            },
            "provenance": {
                "agent": self.__class__.__name__,
                "version": self.version,
                "recorded_at": timestamp,
            },
        }

        if "timestamp" in asset:
            record["asset_timestamp"] = asset["timestamp"]

        if not review.get("ok"):
            record["failure"] = review.get("validation_error") or {
                "reason": "validation_failed",
                "detail": review.get("validation_reason"),
            }

        log_jsonl(self.log_path, record)
        self._logger.info(
            "Recorded experiment for asset %s (persisted=%s)",
            asset_identifier,
            bool(experiment_path),
        )
        return record

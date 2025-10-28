"""Schema version 0.7.3 implementation."""

from labs.v0_7_3.generator import generate_asset
from labs.v0_7_3.telemetry import create_telemetry_record, log_generation

__all__ = ["generate_asset", "create_telemetry_record", "log_generation"]

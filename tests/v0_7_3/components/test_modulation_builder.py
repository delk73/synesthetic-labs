"""Modulation builder tests for schema version 0.7.3."""

from jsonschema import Draft202012Validator

from labs.v0_7_3.components.modulation import build_modulations
from labs.v0_7_3.schema_analyzer import SchemaAnalyzer


def test_modulation_builder_generates_temporal_targets():
    """Modulation builder produces tempo-synchronised modulation entries."""
    analyzer = SchemaAnalyzer(version="0.7.3")
    component = analyzer.get_component_schema("modulations")

    modulations = build_modulations("pulsing shader at 90 BPM", component.schema)

    assert isinstance(modulations, list)
    assert modulations[0]["target"].startswith("shader.")
    assert modulations[0]["frequency"] > 0

    validator = Draft202012Validator(component.schema)
    validator.validate(modulations)

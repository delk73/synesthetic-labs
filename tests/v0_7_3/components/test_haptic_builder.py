"""Haptic component builder tests for schema version 0.7.3."""

from jsonschema import Draft202012Validator

from labs.v0_7_3.components.haptic import build_haptic
from labs.v0_7_3.schema_analyzer import SchemaAnalyzer


def test_haptic_builder_generates_device():
    """Haptic builder produces device configuration with adjustable parameters."""
    analyzer = SchemaAnalyzer(version="0.7.3")
    component = analyzer.get_component_schema("haptic")

    metadata = analyzer.describe_component("haptic")
    haptic = build_haptic(
        "vibration vest pattern with strong pulses",
        component.schema,
        metadata=metadata,
    )

    assert haptic["device"]["type"] == "generic"
    options = haptic["device"]["options"]
    assert "maxIntensity" in options
    assert "defaultDuration" in options
    assert haptic["input_parameters"][0]["parameter"] == "intensity"

    validator = Draft202012Validator(component.schema)
    validator.validate(haptic)

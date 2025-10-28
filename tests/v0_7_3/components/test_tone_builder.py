"""Tone component builder tests for schema version 0.7.3."""

from jsonschema import Draft202012Validator

from labs.v0_7_3.components.tone import build_tone
from labs.v0_7_3.schema_analyzer import SchemaAnalyzer


def test_tone_builder_generates_synth():
    """Tone builder produces Tone.js compatible configuration."""
    analyzer = SchemaAnalyzer(version="0.7.3")
    component = analyzer.get_component_schema("tone")

    tone = build_tone("ambient tone at 440Hz with gentle swell", component.schema)

    assert tone["synth"]["type"].startswith("Tone.")
    assert tone["synth"]["options"]["oscillator"]["type"]
    assert tone["patterns"][0]["options"]["notes"]
    assert tone["input_parameters"][0]["path"].startswith("synth.")

    validator = Draft202012Validator(component.schema)
    validator.validate(tone)

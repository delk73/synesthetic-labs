"""
Shader component builder tests for schema version 0.7.3.
"""

from jsonschema import Draft202012Validator

from labs.v0_7_3.components.shader import build_shader
from labs.v0_7_3.schema_analyzer import SchemaAnalyzer


def test_shader_builder_generates_glsl():
    """Shader builder produces valid GLSL code."""
    analyzer = SchemaAnalyzer(version="0.7.3")
    component = analyzer.get_component_schema("shader")

    shader = build_shader("red pulsing shader with heartbeat rhythm", component.schema)

    assert shader["fragment_shader"]
    assert "red" in shader["fragment_shader"].lower()
    assert shader["vertex_shader"]
    assert shader["name"]

    validator = Draft202012Validator(component.schema)
    validator.validate(shader)


def test_shader_builder_infers_effect_tags():
    """Extracted tags include colour and effect hints."""
    analyzer = SchemaAnalyzer(version="0.7.3")
    component = analyzer.get_component_schema("shader")

    shader = build_shader("teal waveform glsl shader", component.schema)

    meta = shader.get("meta_info", {})
    assert "tags" in meta
    assert "teal" in meta["tags"]
    assert any(tag in meta["tags"] for tag in ("wave", "waveform"))

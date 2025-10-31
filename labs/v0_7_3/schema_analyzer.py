"""Utilities for introspecting the 0.7.3 schema bundle."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Tuple
from urllib.parse import urlparse

from labs.mcp.client import load_schema_bundle


JsonDict = Dict[str, Any]


@dataclass(frozen=True)
class ComponentSchema:
    """Resolved component schema metadata."""

    name: str
    schema: JsonDict
    nullable: bool = False
    raw: JsonDict | None = None


class SchemaAnalyzer:
    """Resolve component subschemas from the 0.7.3 asset bundle."""

    def __init__(self, *, version: str = "0.7.3", schema: JsonDict | None = None) -> None:
        self._version = version
        self._root = copy.deepcopy(schema) if schema is not None else load_schema_bundle(version=version)
        if not isinstance(self._root, Mapping):
            raise TypeError("schema bundle must be a mapping")
        self._properties = self._root.get("properties", {})
        if not isinstance(self._properties, Mapping):
            raise TypeError("schema bundle properties must be a mapping")
        self._component_cache: Dict[str, ComponentSchema] = {}

    @property
    def version(self) -> str:
        return self._version

    def available_components(self) -> Tuple[str, ...]:
        """Return the component property names exposed by the asset schema."""
        return tuple(sorted(self._properties.keys()))

    def describe_component(self, name: str) -> Dict[str, Any]:
        """
        Return lightweight metadata describing the resolved schema for *name*.

        The metadata includes the ``required`` list, the top-level properties
        mapping, and lookup tables for enum/const values discovered within the
        schema tree. The enum/const tables are keyed by property path using dot
        notation (e.g. ``device.type``).
        """
        component = self.get_component_schema(name)
        schema = component.schema
        properties = schema.get("properties", {})
        required = tuple(schema.get("required", ()))
        enums: Dict[str, list] = {}
        consts: Dict[str, Any] = {}
        self._collect_scalar_metadata(schema, path=(), enums=enums, consts=consts)
        return {
            "required": required,
            "properties": copy.deepcopy(properties) if isinstance(properties, Mapping) else {},
            "enums": enums,
            "consts": consts,
        }

    def strict_component_schema(self, name: str) -> JsonDict:
        """
        Return a copy of the component schema with all object properties marked
        as required. Azure strict JSON schema enforcement expects every object
        to specify a ``required`` array that enumerates each declared property.
        """
        schema = self.get_component_schema(name).schema
        strict_schema = copy.deepcopy(schema)
        self._enforce_required_fields(strict_schema)
        return strict_schema

    def get_component_schema(self, name: str) -> ComponentSchema:
        """Return the resolved schema for *name* inside the asset bundle."""
        if not name or not isinstance(name, str):
            raise ValueError("component name must be a non-empty string")
        if name in self._component_cache:
            return copy.deepcopy(self._component_cache[name])

        raw_schema = self._properties.get(name)
        if raw_schema is None:
            raise KeyError(f"component '{name}' not present in schema")
        if not isinstance(raw_schema, Mapping):
            raise TypeError(f"component '{name}' schema must be a mapping")

        resolved_schema, nullable = self._materialise_schema(raw_schema)
        component = ComponentSchema(
            name=name,
            schema=resolved_schema,
            nullable=nullable,
            raw=copy.deepcopy(raw_schema),
        )
        self._component_cache[name] = copy.deepcopy(component)
        return component

    def resolve_def(self, ref: str) -> JsonDict:
        """
        Resolve a local ``$ref`` pointer such as ``#/ $defs/Example``.

        Only intra-bundle references are currently supported. Unknown or
        malformed references raise ValueError to surface schema issues to
        callers.
        """
        if not isinstance(ref, str) or not ref:
            raise ValueError("ref must be a non-empty string")
        if ref.startswith("#/") or ref == "#":
            return self._resolve_local_ref(ref)
        raise ValueError(f"unsupported ref: {ref}")

    # Internal helpers -------------------------------------------------

    def _materialise_schema(self, candidate: Mapping[str, Any]) -> Tuple[JsonDict, bool]:
        """
        Resolve ``candidate`` into a concrete schema dictionary.
        Returns (schema, is_nullable).
        """
        nullable = False
        queue: Iterable[Mapping[str, Any]] = (candidate,)

        if "anyOf" in candidate:
            queue = candidate["anyOf"]
        elif "oneOf" in candidate:
            queue = candidate["oneOf"]

        resolved: JsonDict | None = None
        for entry in queue:
            if not isinstance(entry, Mapping):
                continue
            if entry.get("type") == "null":
                nullable = True
                continue
            fragment = self._resolve_node(entry, root=self._root)
            if resolved is None:
                resolved = fragment
            else:
                resolved = self._merge_all_of(resolved, fragment)

        if resolved is None:
            resolved = self._resolve_node(candidate, root=self._root)

        if not isinstance(resolved, Mapping):
            raise TypeError("resolved schema must be a mapping")

        return resolved, nullable

    def _resolve_node(self, node: Any, *, root: Mapping[str, Any]) -> Any:
        if isinstance(node, Mapping):
            ref = node.get("$ref")
            if isinstance(ref, str):
                target, target_root = self._resolve_ref_with_root(ref, root)
                return self._resolve_node(target, root=target_root)
            resolved: Dict[str, Any] = {}
            for key, value in node.items():
                if key == "$ref":
                    continue
                resolved[key] = self._resolve_node(value, root=root)
            return resolved
        if isinstance(node, list):
            return [self._resolve_node(item, root=root) for item in node]
        return copy.deepcopy(node)

    def _collect_scalar_metadata(
        self,
        node: Any,
        *,
        path: Tuple[str, ...],
        enums: Dict[str, list],
        consts: Dict[str, Any],
    ) -> None:
        """Traverse *node* capturing enum/const leaves keyed by dotted paths."""
        if isinstance(node, Mapping):
            if "const" in node:
                key = ".".join(path)
                consts[key] = copy.deepcopy(node["const"])
            if "enum" in node:
                key = ".".join(path)
                value = node.get("enum")
                if isinstance(value, list):
                    enums[key] = copy.deepcopy(value)
            for branch_key in ("allOf", "anyOf", "oneOf"):
                branch = node.get(branch_key)
                if isinstance(branch, list):
                    for entry in branch:
                        self._collect_scalar_metadata(entry, path=path, enums=enums, consts=consts)
            props = node.get("properties")
            if isinstance(props, Mapping):
                for prop_name, prop_schema in props.items():
                    self._collect_scalar_metadata(
                        prop_schema,
                        path=(*path, prop_name),
                        enums=enums,
                        consts=consts,
                    )
            items = node.get("items")
            if isinstance(items, list):
                for index, item_schema in enumerate(items):
                    self._collect_scalar_metadata(
                        item_schema,
                        path=(*path, f"[{index}]"),
                        enums=enums,
                        consts=consts,
                    )
            elif isinstance(items, Mapping):
                self._collect_scalar_metadata(
                    items,
                    path=(*path, "[]"),
                    enums=enums,
                    consts=consts,
                )
            defs = node.get("$defs")
            if isinstance(defs, Mapping):
                for def_name, def_schema in defs.items():
                    self._collect_scalar_metadata(
                        def_schema,
                        path=(*path, f"$defs.{def_name}"),
                        enums=enums,
                        consts=consts,
                    )
            # If a ref escaped resolution (shouldn't happen) try to resolve now
            ref = node.get("$ref")
            if isinstance(ref, str):
                resolved = self.resolve_def(ref)
                self._collect_scalar_metadata(
                    resolved,
                    path=path,
                    enums=enums,
                    consts=consts,
                )

    def _resolve_ref_with_root(self, ref: str, root: Mapping[str, Any]) -> Tuple[JsonDict, Mapping[str, Any]]:
        if ref.startswith("#"):
            fragment = self._resolve_pointer(root, ref)
            return fragment, root
        parsed = urlparse(ref)
        if not parsed.path:
            raise ValueError(f"unsupported schema reference: {ref}")
        schema_name = Path(parsed.path).name
        if not schema_name:
            raise ValueError(f"schema filename missing in reference: {ref}")
        if schema_name.endswith(".schema.json"):
            schema_name = schema_name[: -len(".schema.json")]
        remote = load_schema_bundle(schema_name=schema_name, version=self._version)
        fragment = parsed.fragment
        if fragment:
            pointer = f"#{fragment if fragment.startswith('/') else '/' + fragment}"
            resolved = self._resolve_pointer(remote, pointer)
        else:
            resolved = remote
        return resolved, remote

    def _resolve_local_ref(self, pointer: str) -> JsonDict:
        return self._resolve_pointer(self._root, pointer)

    @staticmethod
    def _resolve_pointer(root: Mapping[str, Any], pointer: str) -> JsonDict:
        if pointer == "#" or pointer == "":
            return copy.deepcopy(root)
        if pointer.startswith("#/"):
            pointer = pointer[2:]
        tokens = [token.replace("~1", "/").replace("~0", "~") for token in pointer.split("/") if token]
        target: Any = root
        for token in tokens:
            if isinstance(target, Mapping):
                target = target.get(token)
            elif isinstance(target, list):
                try:
                    index = int(token)
                except ValueError as exc:
                    raise ValueError(f"invalid pointer token: {token}") from exc
                if index < 0 or index >= len(target):
                    raise IndexError(f"pointer index out of range: {token}")
                target = target[index]
            else:
                raise ValueError(f"unable to resolve pointer '{pointer}'")
        return copy.deepcopy(target)

    @staticmethod
    def _merge_all_of(lhs: Mapping[str, Any], rhs: Mapping[str, Any]) -> JsonDict:
        merged: JsonDict = {}
        for source in (lhs, rhs):
            for key, value in source.items():
                if key not in merged:
                    merged[key] = copy.deepcopy(value)
                    continue
                if isinstance(merged[key], Mapping) and isinstance(value, Mapping):
                    merged[key] = SchemaAnalyzer._merge_all_of(merged[key], value)
                elif isinstance(merged[key], list) and isinstance(value, list):
                    merged[key] = [*merged[key], *value]
                else:
                    merged[key] = copy.deepcopy(value)
        return merged

    def _enforce_required_fields(self, node: Any) -> None:
        """Recursively ensure objects declare every property in ``required``."""
        if isinstance(node, Mapping):
            properties = node.get("properties")
            if isinstance(properties, Mapping) and properties:
                explicit_required = node.get("required")
                required_set = {key for key in properties.keys()}
                if isinstance(explicit_required, list):
                    required_set.update(str(item) for item in explicit_required)
                node["required"] = sorted(required_set)
            for key in ("properties", "$defs"):
                nested = node.get(key)
                if isinstance(nested, Mapping):
                    for child in nested.values():
                        self._enforce_required_fields(child)
            for branch_key in ("allOf", "anyOf", "oneOf"):
                branch = node.get(branch_key)
                if isinstance(branch, list):
                    for child in branch:
                        self._enforce_required_fields(child)
            items = node.get("items")
            if isinstance(items, list):
                for child in items:
                    self._enforce_required_fields(child)
            elif isinstance(items, Mapping):
                self._enforce_required_fields(items)
        elif isinstance(node, list):
            for entry in node:
                self._enforce_required_fields(entry)


__all__ = ["ComponentSchema", "SchemaAnalyzer"]

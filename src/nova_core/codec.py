from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Callable

from .canonical import canonical_json
from .errors import DecodeError
from .model import Edge, Graph, Module, Node, Project, SchemaHeader


def _split(data: Mapping[str, Any], known: set[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    body = {k: data[k] for k in known if k in data}
    ext = {k: v for k, v in data.items() if k not in known}
    return body, ext


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DecodeError(f"{label} must be an object")
    return value


def decode_header(value: Any) -> SchemaHeader:
    data = _mapping(value, "header")
    known = {"nova_core_version", "schema_version", "feature_flags", "migration_history", "provenance", "extensions"}
    body, unknown = _split(data, known)
    ext = dict(body.pop("extensions", {}) or {})
    ext.update(unknown)
    return SchemaHeader(extensions=ext, **body)


def decode_node(value: Any) -> Node:
    data = _mapping(value, "node")
    known = {"id", "kind", "inputs", "outputs", "value_type", "shape_type", "effect_type", "differentiation_type", "source_projection", "constraints", "attributes", "provenance", "extensions"}
    body, unknown = _split(data, known)
    ext = dict(body.pop("extensions", {}) or {})
    ext.update(unknown)
    try:
        return Node(extensions=ext, **body)
    except TypeError as exc:
        raise DecodeError(f"invalid node: {exc}") from exc


def decode_edge(value: Any) -> Edge:
    data = _mapping(value, "edge")
    known = {"source", "target", "kind", "constraints", "attributes", "provenance", "extensions"}
    body, unknown = _split(data, known)
    ext = dict(body.pop("extensions", {}) or {})
    ext.update(unknown)
    try:
        return Edge(extensions=ext, **body)
    except TypeError as exc:
        raise DecodeError(f"invalid edge: {exc}") from exc


def decode_graph(value: Any) -> Graph:
    data = _mapping(value, "graph")
    known = {"id", "inputs", "outputs", "nodes", "edges", "constraints", "attributes", "provenance", "extensions"}
    body, unknown = _split(data, known)
    ext = dict(body.pop("extensions", {}) or {})
    ext.update(unknown)
    body["nodes"] = tuple(decode_node(v) for v in body.get("nodes", ()))
    body["edges"] = tuple(decode_edge(v) for v in body.get("edges", ()))
    try:
        return Graph(extensions=ext, **body)
    except TypeError as exc:
        raise DecodeError(f"invalid graph: {exc}") from exc


def decode_module(value: Any) -> Module:
    data = _mapping(value, "module")
    known = {"id", "graphs", "imports", "exports", "attributes", "provenance", "extensions"}
    body, unknown = _split(data, known)
    ext = dict(body.pop("extensions", {}) or {})
    ext.update(unknown)
    body["graphs"] = tuple(decode_graph(v) for v in body.get("graphs", ()))
    try:
        return Module(extensions=ext, **body)
    except TypeError as exc:
        raise DecodeError(f"invalid module: {exc}") from exc


def decode_project(value: str | bytes | Mapping[str, Any]) -> Project:
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise DecodeError(f"invalid JSON: {exc.msg}") from exc
    data = _mapping(value, "project")
    known = {"header", "modules", "constraints", "artifacts", "attributes", "provenance", "extensions"}
    body, unknown = _split(data, known)
    ext = dict(body.pop("extensions", {}) or {})
    ext.update(unknown)
    body["header"] = decode_header(body.get("header", {}))
    body["modules"] = tuple(decode_module(v) for v in body.get("modules", ()))
    try:
        return Project(extensions=ext, **body)
    except TypeError as exc:
        raise DecodeError(f"invalid project: {exc}") from exc


def encode_project(project: Project) -> str:
    return canonical_json(project, semantic=False)

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from typing import Any

from .model import Edge, Graph, Module, Node, Project, SchemaHeader


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


def _merge_extensions(base: dict[str, Any], extensions: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in sorted(extensions.items()):
        if key not in out:
            out[key] = _thaw(value)
    return out


def header_record(header: SchemaHeader, *, semantic: bool) -> dict[str, Any]:
    base = {
        "nova_core_version": header.nova_core_version,
        "schema_version": header.schema_version,
        "feature_flags": sorted(header.feature_flags),
    }
    if not semantic:
        base["migration_history"] = list(header.migration_history)
        base["provenance"] = _thaw(header.provenance)
    return _merge_extensions(base, header.extensions)


def node_record(node: Node, *, semantic: bool) -> dict[str, Any]:
    base = {
        "id": node.id,
        "kind": node.kind,
        "inputs": list(node.inputs),
        "outputs": list(node.outputs),
        "value_type": _thaw(node.value_type),
        "shape_type": _thaw(node.shape_type),
        "effect_type": _thaw(node.effect_type),
        "differentiation_type": _thaw(node.differentiation_type),
        "constraints": sorted((_thaw(v) for v in node.constraints), key=_stable_key),
        "attributes": _thaw(node.attributes),
    }
    if not semantic:
        base["source_projection"] = _thaw(node.source_projection)
        base["provenance"] = _thaw(node.provenance)
    return _merge_extensions(base, node.extensions)


def edge_record(edge: Edge, *, semantic: bool) -> dict[str, Any]:
    base = {
        "source": edge.source,
        "target": edge.target,
        "kind": edge.kind,
        "constraints": sorted((_thaw(v) for v in edge.constraints), key=_stable_key),
        "attributes": _thaw(edge.attributes),
    }
    if not semantic:
        base["provenance"] = _thaw(edge.provenance)
    return _merge_extensions(base, edge.extensions)


def graph_record(graph: Graph, *, semantic: bool) -> dict[str, Any]:
    base = {
        "id": graph.id,
        "inputs": list(graph.inputs),
        "outputs": list(graph.outputs),
        "nodes": [node_record(n, semantic=semantic) for n in sorted(graph.nodes, key=lambda n: n.id)],
        "edges": [edge_record(e, semantic=semantic) for e in sorted(graph.edges, key=lambda e: e.key)],
        "constraints": sorted((_thaw(v) for v in graph.constraints), key=_stable_key),
        "attributes": _thaw(graph.attributes),
    }
    if not semantic:
        base["provenance"] = _thaw(graph.provenance)
    return _merge_extensions(base, graph.extensions)


def module_record(module: Module, *, semantic: bool) -> dict[str, Any]:
    base = {
        "id": module.id,
        "imports": sorted(module.imports),
        "exports": sorted(module.exports),
        "graphs": [graph_record(g, semantic=semantic) for g in sorted(module.graphs, key=lambda g: g.id)],
        "attributes": _thaw(module.attributes),
    }
    if not semantic:
        base["provenance"] = _thaw(module.provenance)
    return _merge_extensions(base, module.extensions)


def project_record(project: Project, *, semantic: bool = False) -> dict[str, Any]:
    base = {
        "header": header_record(project.header, semantic=semantic),
        "modules": [module_record(m, semantic=semantic) for m in sorted(project.modules, key=lambda m: m.id)],
        "constraints": sorted((_thaw(v) for v in project.constraints), key=_stable_key),
        "attributes": _thaw(project.attributes),
    }
    if not semantic:
        base["artifacts"] = sorted((_thaw(v) for v in project.artifacts), key=_stable_key)
        base["provenance"] = _thaw(project.provenance)
    return _merge_extensions(base, project.extensions)


def _stable_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_json(project: Project, *, semantic: bool = False) -> str:
    return json.dumps(
        project_record(project, semantic=semantic),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_bytes(project: Project, *, semantic: bool = False) -> bytes:
    return canonical_json(project, semantic=semantic).encode("utf-8")


def semantic_hash(project: Project) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(project, semantic=True)).hexdigest()


def record_hash(project: Project) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(project, semantic=False)).hexdigest()

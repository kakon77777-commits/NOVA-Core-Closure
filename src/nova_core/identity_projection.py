from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .canonical import project_record
from .errors import DecodeError
from .identity_model import IdentityManifest, StructuralID
from .model import Project


def _sid(
    manifest: IdentityManifest,
    kind: str,
    label: str,
    parent: StructuralID,
) -> StructuralID:
    return manifest.resolve(kind, label, parent=parent)


def identity_core_record(project: Project, manifest: IdentityManifest) -> dict[str, Any]:
    """Replace mutable module/graph/node/value labels with persistent IDs."""

    record = deepcopy(project_record(project, semantic=True))
    modules_out: list[dict[str, Any]] = []
    for module in record.get("modules", ()) or ():
        m_sid = _sid(manifest, "module", str(module["id"]), manifest.project_sid)
        m = dict(module)
        m["id"] = m_sid.raw
        graphs_out: list[dict[str, Any]] = []
        for graph in module.get("graphs", ()) or ():
            g_sid = _sid(manifest, "graph", str(graph["id"]), m_sid)
            g = dict(graph)
            g["id"] = g_sid.raw
            g["inputs"] = [
                _sid(manifest, "value", str(value), g_sid).raw
                for value in graph.get("inputs", ()) or ()
            ]
            g["outputs"] = [
                _sid(manifest, "value", str(value), g_sid).raw
                for value in graph.get("outputs", ()) or ()
            ]
            nodes: list[dict[str, Any]] = []
            for node in graph.get("nodes", ()) or ():
                n = dict(node)
                n["id"] = _sid(manifest, "node", str(node["id"]), g_sid).raw
                n["inputs"] = [
                    _sid(manifest, "value", str(value), g_sid).raw
                    for value in node.get("inputs", ()) or ()
                ]
                n["outputs"] = [
                    _sid(manifest, "value", str(value), g_sid).raw
                    for value in node.get("outputs", ()) or ()
                ]
                nodes.append(n)
            g["nodes"] = sorted(nodes, key=lambda item: bytes(item["id"]))
            edges: list[dict[str, Any]] = []
            for edge in graph.get("edges", ()) or ():
                e = dict(edge)
                e["source"] = _sid(
                    manifest, "node", str(edge["source"]), g_sid
                ).raw
                e["target"] = _sid(
                    manifest, "node", str(edge["target"]), g_sid
                ).raw
                edges.append(e)
            g["edges"] = sorted(
                edges,
                key=lambda item: (
                    bytes(item["source"]),
                    bytes(item["target"]),
                    str(item.get("kind", "")),
                ),
            )
            graphs_out.append(g)
        m["graphs"] = sorted(graphs_out, key=lambda item: bytes(item["id"]))
        modules_out.append(m)
    record["modules"] = sorted(modules_out, key=lambda item: bytes(item["id"]))
    return record


def _label(
    manifest: IdentityManifest,
    raw: bytes,
    kind: str,
    parent: StructuralID,
) -> str:
    entry = manifest.entry_by_sid(StructuralID(raw))
    if entry.kind != kind or entry.parent != parent:
        raise DecodeError(f"StructuralID outside expected {kind} scope: {entry.sid.text}")
    return entry.label


def restore_legacy_record(
    identity_record: Mapping[str, Any],
    manifest: IdentityManifest,
) -> dict[str, Any]:
    record = deepcopy(dict(identity_record))
    modules_out: list[dict[str, Any]] = []
    for module in record.get("modules", ()) or ():
        m_sid = StructuralID(bytes(module["id"]))
        m = dict(module)
        m["id"] = _label(manifest, m_sid.raw, "module", manifest.project_sid)
        graphs_out: list[dict[str, Any]] = []
        for graph in module.get("graphs", ()) or ():
            g_sid = StructuralID(bytes(graph["id"]))
            g = dict(graph)
            g["id"] = _label(manifest, g_sid.raw, "graph", m_sid)
            g["inputs"] = [
                _label(manifest, bytes(value), "value", g_sid)
                for value in graph.get("inputs", ()) or ()
            ]
            g["outputs"] = [
                _label(manifest, bytes(value), "value", g_sid)
                for value in graph.get("outputs", ()) or ()
            ]
            nodes: list[dict[str, Any]] = []
            for node in graph.get("nodes", ()) or ():
                n = dict(node)
                n["id"] = _label(manifest, bytes(node["id"]), "node", g_sid)
                n["inputs"] = [
                    _label(manifest, bytes(value), "value", g_sid)
                    for value in node.get("inputs", ()) or ()
                ]
                n["outputs"] = [
                    _label(manifest, bytes(value), "value", g_sid)
                    for value in node.get("outputs", ()) or ()
                ]
                nodes.append(n)
            g["nodes"] = nodes
            edges: list[dict[str, Any]] = []
            for edge in graph.get("edges", ()) or ():
                e = dict(edge)
                e["source"] = _label(
                    manifest, bytes(edge["source"]), "node", g_sid
                )
                e["target"] = _label(
                    manifest, bytes(edge["target"]), "node", g_sid
                )
                edges.append(e)
            g["edges"] = edges
            graphs_out.append(g)
        m["graphs"] = graphs_out
        modules_out.append(m)
    record["modules"] = modules_out
    return record


__all__ = ["identity_core_record", "restore_legacy_record"]

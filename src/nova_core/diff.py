from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .canonical import semantic_hash
from .model import Edge, Graph, Node


def _plain(value: Any) -> Any:
    to_record = getattr(value, "to_record", None)
    if callable(to_record):
        return _plain(to_record())
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple):
        return [_plain(v) for v in value]
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


@dataclass(frozen=True)
class FieldChange:
    field: str
    before: Any
    after: Any
    semantic: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "before": _plain(self.before),
            "after": _plain(self.after),
            "semantic": self.semantic,
        }


@dataclass(frozen=True)
class NodeDelta:
    node_id: str
    changes: tuple[FieldChange, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"node_id": self.node_id, "changes": [change.to_dict() for change in self.changes]}


@dataclass(frozen=True)
class EdgeDelta:
    key: tuple[str, str, str]
    changes: tuple[FieldChange, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"key": list(self.key), "changes": [change.to_dict() for change in self.changes]}


@dataclass(frozen=True)
class GraphDiff:
    base_hash: str
    target_hash: str
    semantic_changed: bool
    added_nodes: tuple[str, ...] = ()
    removed_nodes: tuple[str, ...] = ()
    modified_nodes: tuple[NodeDelta, ...] = ()
    added_edges: tuple[tuple[str, str, str], ...] = ()
    removed_edges: tuple[tuple[str, str, str], ...] = ()
    modified_edges: tuple[EdgeDelta, ...] = ()
    graph_changes: tuple[FieldChange, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not (
            self.added_nodes
            or self.removed_nodes
            or self.modified_nodes
            or self.added_edges
            or self.removed_edges
            or self.modified_edges
            or self.graph_changes
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_hash": self.base_hash,
            "target_hash": self.target_hash,
            "semantic_changed": self.semantic_changed,
            "is_empty": self.is_empty,
            "added_nodes": list(self.added_nodes),
            "removed_nodes": list(self.removed_nodes),
            "modified_nodes": [delta.to_dict() for delta in self.modified_nodes],
            "added_edges": [list(key) for key in self.added_edges],
            "removed_edges": [list(key) for key in self.removed_edges],
            "modified_edges": [delta.to_dict() for delta in self.modified_edges],
            "graph_changes": [change.to_dict() for change in self.graph_changes],
        }


_NODE_FIELDS: tuple[tuple[str, bool], ...] = (
    ("kind", True),
    ("inputs", True),
    ("outputs", True),
    ("value_type", True),
    ("shape_type", True),
    ("effect_type", True),
    ("differentiation_type", True),
    ("constraints", True),
    ("attributes", True),
    ("extensions", True),
    ("source_projection", False),
    ("provenance", False),
)

_EDGE_FIELDS: tuple[tuple[str, bool], ...] = (
    ("constraints", True),
    ("attributes", True),
    ("extensions", True),
    ("provenance", False),
)

_GRAPH_FIELDS: tuple[tuple[str, bool], ...] = (
    ("inputs", True),
    ("outputs", True),
    ("constraints", True),
    ("attributes", True),
    ("extensions", True),
    ("provenance", False),
)


def _field_changes(before: Any, after: Any, fields: tuple[tuple[str, bool], ...]) -> tuple[FieldChange, ...]:
    changes: list[FieldChange] = []
    for name, semantic in fields:
        left = _plain(getattr(before, name))
        right = _plain(getattr(after, name))
        if left != right:
            changes.append(FieldChange(name, left, right, semantic))
    return tuple(changes)


def diff_graphs(before: Graph, after: Graph) -> GraphDiff:
    before_nodes = {node.id: node for node in before.nodes}
    after_nodes = {node.id: node for node in after.nodes}
    before_ids = set(before_nodes)
    after_ids = set(after_nodes)

    modified_nodes = tuple(
        NodeDelta(node_id=node_id, changes=changes)
        for node_id in sorted(before_ids & after_ids)
        if (changes := _field_changes(before_nodes[node_id], after_nodes[node_id], _NODE_FIELDS))
    )

    before_edges = {edge.key: edge for edge in before.edges}
    after_edges = {edge.key: edge for edge in after.edges}
    before_edge_keys = set(before_edges)
    after_edge_keys = set(after_edges)
    modified_edges = tuple(
        EdgeDelta(key=key, changes=changes)
        for key in sorted(before_edge_keys & after_edge_keys)
        if (changes := _field_changes(before_edges[key], after_edges[key], _EDGE_FIELDS))
    )

    return GraphDiff(
        base_hash=semantic_hash(before),
        target_hash=semantic_hash(after),
        semantic_changed=semantic_hash(before) != semantic_hash(after),
        added_nodes=tuple(sorted(after_ids - before_ids)),
        removed_nodes=tuple(sorted(before_ids - after_ids)),
        modified_nodes=modified_nodes,
        added_edges=tuple(sorted(after_edge_keys - before_edge_keys)),
        removed_edges=tuple(sorted(before_edge_keys - after_edge_keys)),
        modified_edges=modified_edges,
        graph_changes=_field_changes(before, after, _GRAPH_FIELDS),
    )

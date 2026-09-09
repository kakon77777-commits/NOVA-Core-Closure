from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any, TypeAlias

from .codec import decode_edge, decode_node
from .editing import ProjectionEditCandidate, build_projection_edit_candidate
from .errors import ProjectionEditError
from .model import Edge, Graph, Node, Project


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class AddNodeEdit:
    node: Node


@dataclass(frozen=True)
class ReplaceNodeEdit:
    node_id: str
    node: Node


@dataclass(frozen=True)
class RemoveNodeEdit:
    node_id: str


@dataclass(frozen=True)
class SetNodeInputsEdit:
    node_id: str
    inputs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "inputs", tuple(str(v) for v in self.inputs))


@dataclass(frozen=True)
class SetNodeAttributesEdit:
    node_id: str
    attributes: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", _freeze_mapping(self.attributes))


@dataclass(frozen=True)
class AddEdgeEdit:
    edge: Edge


@dataclass(frozen=True)
class RemoveEdgeEdit:
    edge_key: tuple[str, str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "edge_key", tuple(str(v) for v in self.edge_key))


@dataclass(frozen=True)
class SetGraphOutputsEdit:
    outputs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "outputs", tuple(str(v) for v in self.outputs))


NodeGraphEdit: TypeAlias = (
    AddNodeEdit
    | ReplaceNodeEdit
    | RemoveNodeEdit
    | SetNodeInputsEdit
    | SetNodeAttributesEdit
    | AddEdgeEdit
    | RemoveEdgeEdit
    | SetGraphOutputsEdit
)


def _find_graph(project: Project, module_id: str, graph_id: str) -> Graph:
    for module in project.modules:
        if module.id != module_id:
            continue
        for graph in module.graphs:
            if graph.id == graph_id:
                return graph
        break
    raise ProjectionEditError(f"graph not found: {module_id}/{graph_id}")


def _replace_node(nodes: list[Node], node_id: str, replacement: Node) -> None:
    if replacement.id != node_id:
        raise ProjectionEditError(
            "replacement node id must match targeted node id",
            context={"node_id": node_id, "replacement_id": replacement.id},
        )
    for index, node in enumerate(nodes):
        if node.id == node_id:
            nodes[index] = replacement
            return
    raise ProjectionEditError("node not found for replacement", source_nodes=(node_id,))


def _edit_node(nodes: list[Node], node_id: str, fn) -> None:
    for index, node in enumerate(nodes):
        if node.id == node_id:
            nodes[index] = fn(node)
            return
    raise ProjectionEditError("node not found for edit", source_nodes=(node_id,))


def apply_node_graph_edits(graph: Graph, operations: Sequence[NodeGraphEdit]) -> Graph:
    nodes = list(graph.nodes)
    edges = list(graph.edges)
    outputs = graph.outputs

    for operation in operations:
        if isinstance(operation, AddNodeEdit):
            if any(node.id == operation.node.id for node in nodes):
                raise ProjectionEditError("added node id already exists", source_nodes=(operation.node.id,))
            nodes.append(operation.node)
        elif isinstance(operation, ReplaceNodeEdit):
            _replace_node(nodes, operation.node_id, operation.node)
        elif isinstance(operation, RemoveNodeEdit):
            before = len(nodes)
            nodes[:] = [node for node in nodes if node.id != operation.node_id]
            if len(nodes) == before:
                raise ProjectionEditError("node not found for removal", source_nodes=(operation.node_id,))
        elif isinstance(operation, SetNodeInputsEdit):
            _edit_node(nodes, operation.node_id, lambda node: replace(node, inputs=operation.inputs))
        elif isinstance(operation, SetNodeAttributesEdit):
            _edit_node(nodes, operation.node_id, lambda node: replace(node, attributes=dict(operation.attributes)))
        elif isinstance(operation, AddEdgeEdit):
            if any(edge.key == operation.edge.key for edge in edges):
                raise ProjectionEditError("edge key already exists", context={"edge_key": list(operation.edge.key)})
            edges.append(operation.edge)
        elif isinstance(operation, RemoveEdgeEdit):
            before = len(edges)
            edges[:] = [edge for edge in edges if edge.key != operation.edge_key]
            if len(edges) == before:
                raise ProjectionEditError("edge not found for removal", context={"edge_key": list(operation.edge_key)})
        elif isinstance(operation, SetGraphOutputsEdit):
            outputs = operation.outputs
        else:  # pragma: no cover - guarded by public type/decoder
            raise ProjectionEditError("unsupported node graph edit operation")

    return replace(graph, nodes=tuple(nodes), edges=tuple(edges), outputs=tuple(outputs))


def preview_node_graph_edit(
    project: Project,
    module_id: str,
    graph_id: str,
    operations: Sequence[NodeGraphEdit],
    *,
    rationale: str = "",
    provenance: Mapping[str, Any] | None = None,
) -> ProjectionEditCandidate:
    before = _find_graph(project, module_id, graph_id)
    after = apply_node_graph_edits(before, operations)
    return build_projection_edit_candidate(
        project,
        module_id,
        graph_id,
        after,
        rationale=rationale,
        provenance=provenance,
    )


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProjectionEditError(f"{label} must be an object")
    return value


def decode_node_graph_edits(value: Any) -> tuple[NodeGraphEdit, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ProjectionEditError("node graph edits must be an array")
    out: list[NodeGraphEdit] = []
    for index, raw in enumerate(value):
        item = _mapping(raw, f"edit[{index}]")
        kind = item.get("op")
        try:
            if kind == "add_node":
                out.append(AddNodeEdit(decode_node(item["node"])))
            elif kind == "replace_node":
                out.append(ReplaceNodeEdit(str(item["node_id"]), decode_node(item["node"])))
            elif kind == "remove_node":
                out.append(RemoveNodeEdit(str(item["node_id"])))
            elif kind == "set_node_inputs":
                out.append(SetNodeInputsEdit(str(item["node_id"]), tuple(item.get("inputs", ()))))
            elif kind == "set_node_attributes":
                out.append(SetNodeAttributesEdit(str(item["node_id"]), _mapping(item.get("attributes", {}), "attributes")))
            elif kind == "add_edge":
                out.append(AddEdgeEdit(decode_edge(item["edge"])))
            elif kind == "remove_edge":
                key = item.get("edge_key")
                if not isinstance(key, Sequence) or isinstance(key, (str, bytes, bytearray)) or len(key) != 3:
                    raise ProjectionEditError("remove_edge edge_key must contain source, target, kind")
                out.append(RemoveEdgeEdit(tuple(str(v) for v in key)))
            elif kind == "set_graph_outputs":
                out.append(SetGraphOutputsEdit(tuple(item.get("outputs", ()))))
            else:
                raise ProjectionEditError("unknown node graph edit operation", context={"op": kind, "index": index})
        except KeyError as exc:
            raise ProjectionEditError(
                "node graph edit is missing a required field",
                context={"op": kind, "field": str(exc), "index": index},
            ) from exc
    return tuple(out)

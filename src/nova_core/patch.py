from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any

from .canonical import record_hash, semantic_hash
from .errors import ConflictError, PatchError
from .model import Edge, Graph, Module, Node, Project, validate_project


@dataclass(frozen=True)
class GraphPatch:
    base_hash: str
    module_id: str
    graph_id: str
    base_record_hash: str | None = None
    added_nodes: tuple[Node, ...] = ()
    removed_node_ids: tuple[str, ...] = ()
    replaced_nodes: tuple[Node, ...] = ()
    added_edges: tuple[Edge, ...] = ()
    removed_edge_keys: tuple[tuple[str, str, str], ...] = ()
    replaced_edges: tuple[Edge, ...] = ()
    changed_inputs: tuple[str, ...] | None = None
    changed_outputs: tuple[str, ...] | None = None
    changed_constraints: tuple[Any, ...] | None = None
    changed_attributes: Mapping[str, Any] | None = None
    changed_provenance: Mapping[str, Any] | None = None
    changed_extensions: Mapping[str, Any] | None = None
    proof_obligations: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    rationale: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PatchResult:
    project: Project
    before_hash: str
    after_hash: str
    patch: GraphPatch
    before_record_hash: str | None = None
    after_record_hash: str | None = None


def _find_module(project: Project, module_id: str) -> tuple[int, Module]:
    for idx, module in enumerate(project.modules):
        if module.id == module_id:
            return idx, module
    raise PatchError(f"module not found: {module_id}")


def _find_graph(module: Module, graph_id: str) -> tuple[int, Graph]:
    for idx, graph in enumerate(module.graphs):
        if graph.id == graph_id:
            return idx, graph
    raise PatchError(f"graph not found: {graph_id}")


def _replace_nodes(graph: Graph, patch: GraphPatch) -> tuple[Node, ...]:
    existing = {node.id: node for node in graph.nodes}
    removed = set(patch.removed_node_ids)
    replacements = {node.id: node for node in patch.replaced_nodes}
    if len(replacements) != len(patch.replaced_nodes):
        raise PatchError("duplicate node id in replaced_nodes")
    unknown_replacements = sorted(set(replacements) - set(existing))
    if unknown_replacements:
        raise PatchError("replacement node does not exist", context={"node_ids": unknown_replacements})
    if removed & set(replacements):
        raise PatchError("node cannot be removed and replaced in the same patch")

    retained_ids = set(existing) - removed
    added_ids = [node.id for node in patch.added_nodes]
    if len(set(added_ids)) != len(added_ids):
        raise PatchError("duplicate node id in added_nodes")
    collisions = sorted(set(added_ids) & retained_ids)
    if collisions:
        raise PatchError("added node id already exists", context={"node_ids": collisions})

    out: list[Node] = []
    for node in graph.nodes:
        if node.id in removed:
            continue
        out.append(replacements.get(node.id, node))
    out.extend(patch.added_nodes)
    return tuple(out)


def _replace_edges(graph: Graph, patch: GraphPatch) -> tuple[Edge, ...]:
    existing = {edge.key: edge for edge in graph.edges}
    removed = set(patch.removed_edge_keys)
    replacements = {edge.key: edge for edge in patch.replaced_edges}
    if len(replacements) != len(patch.replaced_edges):
        raise PatchError("duplicate edge key in replaced_edges")
    unknown_replacements = sorted(set(replacements) - set(existing))
    if unknown_replacements:
        raise PatchError("replacement edge does not exist", context={"edge_keys": unknown_replacements})
    if removed & set(replacements):
        raise PatchError("edge cannot be removed and replaced in the same patch")

    retained_keys = set(existing) - removed
    added_keys = [edge.key for edge in patch.added_edges]
    if len(set(added_keys)) != len(added_keys):
        raise PatchError("duplicate edge key in added_edges")
    collisions = sorted(set(added_keys) & retained_keys)
    if collisions:
        raise PatchError("added edge key already exists", context={"edge_keys": collisions})

    out: list[Edge] = []
    for edge in graph.edges:
        if edge.key in removed:
            continue
        out.append(replacements.get(edge.key, edge))
    out.extend(patch.added_edges)
    return tuple(out)


def apply_graph_patch(project: Project, patch: GraphPatch) -> PatchResult:
    before = semantic_hash(project)
    before_record = record_hash(project)
    if before != patch.base_hash:
        raise ConflictError(
            "GraphPatch base semantic hash does not match working project",
            context={"expected": before, "received": patch.base_hash},
        )
    if patch.base_record_hash is not None and before_record != patch.base_record_hash:
        raise ConflictError(
            "GraphPatch base record hash does not match working project",
            context={"expected": before_record, "received": patch.base_record_hash},
        )

    module_index, module = _find_module(project, patch.module_id)
    graph_index, graph = _find_graph(module, patch.graph_id)

    candidate_graph = replace(
        graph,
        inputs=graph.inputs if patch.changed_inputs is None else tuple(patch.changed_inputs),
        outputs=graph.outputs if patch.changed_outputs is None else tuple(patch.changed_outputs),
        nodes=_replace_nodes(graph, patch),
        edges=_replace_edges(graph, patch),
        constraints=graph.constraints if patch.changed_constraints is None else tuple(patch.changed_constraints),
        attributes=graph.attributes if patch.changed_attributes is None else dict(patch.changed_attributes),
        provenance=graph.provenance if patch.changed_provenance is None else dict(patch.changed_provenance),
        extensions=graph.extensions if patch.changed_extensions is None else dict(patch.changed_extensions),
    )
    candidate_graphs = list(module.graphs)
    candidate_graphs[graph_index] = candidate_graph
    candidate_module = replace(module, graphs=tuple(candidate_graphs))
    candidate_modules = list(project.modules)
    candidate_modules[module_index] = candidate_module

    candidate = replace(project, modules=tuple(candidate_modules))
    validate_project(candidate)
    return PatchResult(
        project=candidate,
        before_hash=before,
        after_hash=semantic_hash(candidate),
        before_record_hash=before_record,
        after_record_hash=record_hash(candidate),
        patch=patch,
    )


class GraphTransaction:
    def __init__(self, project: Project) -> None:
        self._current = project
        self._history: list[Project] = []

    @property
    def current(self) -> Project:
        return self._current

    @property
    def semantic_hash(self) -> str:
        return semantic_hash(self._current)

    @property
    def record_hash(self) -> str:
        return record_hash(self._current)

    @property
    def history_depth(self) -> int:
        return len(self._history)

    def apply(self, patch: GraphPatch) -> PatchResult:
        result = apply_graph_patch(self._current, patch)
        self._history.append(self._current)
        self._current = result.project
        return result

    def rollback(self) -> Project:
        if not self._history:
            raise PatchError("no committed GraphPatch to roll back")
        self._current = self._history.pop()
        return self._current

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from .canonical import semantic_hash
from .errors import ConflictError, PatchError
from .model import Edge, Graph, Module, Node, Project, validate_project


@dataclass(frozen=True)
class GraphPatch:
    base_hash: str
    module_id: str
    graph_id: str
    added_nodes: tuple[Node, ...] = ()
    removed_node_ids: tuple[str, ...] = ()
    added_edges: tuple[Edge, ...] = ()
    removed_edge_keys: tuple[tuple[str, str, str], ...] = ()
    changed_constraints: tuple[Any, ...] | None = None
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


def apply_graph_patch(project: Project, patch: GraphPatch) -> PatchResult:
    before = semantic_hash(project)
    if before != patch.base_hash:
        raise ConflictError(
            "GraphPatch base semantic hash does not match working project",
            context={"expected": before, "received": patch.base_hash},
        )

    module_index, module = _find_module(project, patch.module_id)
    graph_index, graph = _find_graph(module, patch.graph_id)

    removed_ids = set(patch.removed_node_ids)
    nodes = tuple(n for n in graph.nodes if n.id not in removed_ids) + tuple(patch.added_nodes)
    removed_edge_keys = set(patch.removed_edge_keys)
    edges = tuple(e for e in graph.edges if e.key not in removed_edge_keys) + tuple(patch.added_edges)
    constraints = graph.constraints if patch.changed_constraints is None else tuple(patch.changed_constraints)

    candidate_graph = replace(graph, nodes=nodes, edges=edges, constraints=constraints)
    candidate_graphs = list(module.graphs)
    candidate_graphs[graph_index] = candidate_graph
    candidate_module = replace(module, graphs=tuple(candidate_graphs))
    candidate_modules = list(project.modules)
    candidate_modules[module_index] = candidate_module

    # Project construction performs full candidate validation before commit.
    candidate = replace(project, modules=tuple(candidate_modules))
    validate_project(candidate)
    return PatchResult(
        project=candidate,
        before_hash=before,
        after_hash=semantic_hash(candidate),
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
    def history_depth(self) -> int:
        return len(self._history)

    def apply(self, patch: GraphPatch) -> PatchResult:
        # Candidate calculation can fail; working state is mutated only after success.
        result = apply_graph_patch(self._current, patch)
        self._history.append(self._current)
        self._current = result.project
        return result

    def rollback(self) -> Project:
        if not self._history:
            raise PatchError("no committed GraphPatch to roll back")
        self._current = self._history.pop()
        return self._current

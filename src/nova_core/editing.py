from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from .canonical import edge_record, node_record, record_hash, semantic_hash
from .diff import GraphDiff, diff_graphs
from .errors import DecodeError, PatchError, ProjectionEditError
from .model import Edge, Graph, Node, Project
from .patch import GraphPatch, GraphTransaction, PatchResult, apply_graph_patch
from .projection import parse_editable_text


def _find_graph(project: Project, module_id: str, graph_id: str) -> Graph:
    for module in project.modules:
        if module.id != module_id:
            continue
        for graph in module.graphs:
            if graph.id == graph_id:
                return graph
        break
    raise PatchError(f"graph not found: {module_id}/{graph_id}")


def _record_equal_node(left: Node, right: Node) -> bool:
    return node_record(left, semantic=False) == node_record(right, semantic=False)


def _record_equal_edge(left: Edge, right: Edge) -> bool:
    return edge_record(left, semantic=False) == edge_record(right, semantic=False)


def _graph_patch_from_graphs(
    project: Project,
    module_id: str,
    graph_id: str,
    before: Graph,
    after: Graph,
    *,
    rationale: str = "",
    provenance: Mapping[str, Any] | None = None,
) -> GraphPatch:
    before_nodes = {node.id: node for node in before.nodes}
    after_nodes = {node.id: node for node in after.nodes}
    before_edges = {edge.key: edge for edge in before.edges}
    after_edges = {edge.key: edge for edge in after.edges}

    return GraphPatch(
        base_hash=semantic_hash(project),
        base_record_hash=record_hash(project),
        module_id=module_id,
        graph_id=graph_id,
        added_nodes=tuple(after_nodes[node_id] for node_id in sorted(set(after_nodes) - set(before_nodes))),
        removed_node_ids=tuple(sorted(set(before_nodes) - set(after_nodes))),
        replaced_nodes=tuple(
            after_nodes[node_id]
            for node_id in sorted(set(before_nodes) & set(after_nodes))
            if not _record_equal_node(before_nodes[node_id], after_nodes[node_id])
        ),
        added_edges=tuple(after_edges[key] for key in sorted(set(after_edges) - set(before_edges))),
        removed_edge_keys=tuple(sorted(set(before_edges) - set(after_edges))),
        replaced_edges=tuple(
            after_edges[key]
            for key in sorted(set(before_edges) & set(after_edges))
            if not _record_equal_edge(before_edges[key], after_edges[key])
        ),
        changed_inputs=None if before.inputs == after.inputs else after.inputs,
        changed_outputs=None if before.outputs == after.outputs else after.outputs,
        changed_constraints=None if before.constraints == after.constraints else after.constraints,
        changed_attributes=None if dict(before.attributes) == dict(after.attributes) else dict(after.attributes),
        changed_provenance=None if dict(before.provenance) == dict(after.provenance) else dict(after.provenance),
        changed_extensions=None if dict(before.extensions) == dict(after.extensions) else dict(after.extensions),
        rationale=rationale,
        provenance=dict(provenance or {}),
    )


@dataclass(frozen=True)
class ProjectionEditCandidate:
    patch: GraphPatch
    diff: GraphDiff
    candidate_project: Project
    before_semantic_hash: str
    candidate_semantic_hash: str
    before_record_hash: str
    candidate_record_hash: str
    validation: str = "passed"

    @property
    def no_change(self) -> bool:
        return self.diff.is_empty

    def to_dict(self) -> dict[str, Any]:
        return {
            "before_semantic_hash": self.before_semantic_hash,
            "candidate_semantic_hash": self.candidate_semantic_hash,
            "before_record_hash": self.before_record_hash,
            "candidate_record_hash": self.candidate_record_hash,
            "validation": self.validation,
            "no_change": self.no_change,
            "diff": self.diff.to_dict(),
        }


def interpret_structured_text_edit(
    project: Project,
    module_id: str,
    graph_id: str,
    edited_text: str,
    *,
    rationale: str = "",
    provenance: Mapping[str, Any] | None = None,
) -> ProjectionEditCandidate:
    before_graph = _find_graph(project, module_id, graph_id)
    try:
        after_graph = parse_editable_text(edited_text)
    except DecodeError as exc:
        raise ProjectionEditError(
            "editable structured text could not be parsed",
            context={"cause": exc.to_dict()},
        ) from exc
    if after_graph.id != graph_id:
        raise ProjectionEditError(
            "projection edit cannot change targeted graph identity",
            context={"expected_graph_id": graph_id, "received_graph_id": after_graph.id},
        )

    diff = diff_graphs(before_graph, after_graph)
    patch = _graph_patch_from_graphs(
        project,
        module_id,
        graph_id,
        before_graph,
        after_graph,
        rationale=rationale,
        provenance=provenance,
    )
    result = apply_graph_patch(project, patch)
    return ProjectionEditCandidate(
        patch=patch,
        diff=diff,
        candidate_project=result.project,
        before_semantic_hash=result.before_hash,
        candidate_semantic_hash=result.after_hash,
        before_record_hash=result.before_record_hash or record_hash(project),
        candidate_record_hash=result.after_record_hash or record_hash(result.project),
    )


def commit_projection_edit(transaction: GraphTransaction, candidate: ProjectionEditCandidate) -> PatchResult:
    result = transaction.apply(candidate.patch)
    if result.after_hash != candidate.candidate_semantic_hash or record_hash(result.project) != candidate.candidate_record_hash:
        raise ProjectionEditError(
            "committed projection edit does not match previewed candidate",
            context={
                "preview_semantic_hash": candidate.candidate_semantic_hash,
                "committed_semantic_hash": result.after_hash,
                "preview_record_hash": candidate.candidate_record_hash,
                "committed_record_hash": record_hash(result.project),
            },
        )
    return result

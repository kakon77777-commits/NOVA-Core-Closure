from __future__ import annotations

from typing import Any

from .editing import ProjectionEditCandidate
from .errors import NovaError
from .patch import GraphPatch


def project_error_view(error: NovaError) -> dict[str, Any]:
    payload = error.to_dict()
    payload["summary"] = f"{payload['category']}: {payload['message']}"
    return payload


def _patch_view(patch: GraphPatch) -> dict[str, Any]:
    return {
        "module_id": patch.module_id,
        "graph_id": patch.graph_id,
        "base_hash": patch.base_hash,
        "base_record_hash": patch.base_record_hash,
        "added_nodes": [node.id for node in patch.added_nodes],
        "removed_nodes": list(patch.removed_node_ids),
        "replaced_nodes": [node.id for node in patch.replaced_nodes],
        "added_edges": [list(edge.key) for edge in patch.added_edges],
        "removed_edges": [list(key) for key in patch.removed_edge_keys],
        "replaced_edges": [list(edge.key) for edge in patch.replaced_edges],
        "changed_inputs": None if patch.changed_inputs is None else list(patch.changed_inputs),
        "changed_outputs": None if patch.changed_outputs is None else list(patch.changed_outputs),
        "changed_constraints": None if patch.changed_constraints is None else list(patch.changed_constraints),
        "changed_attributes": None if patch.changed_attributes is None else dict(patch.changed_attributes),
        "changed_provenance": None if patch.changed_provenance is None else dict(patch.changed_provenance),
        "changed_extensions": None if patch.changed_extensions is None else dict(patch.changed_extensions),
        "proof_obligations": list(patch.proof_obligations),
        "tests": list(patch.tests),
        "rationale": patch.rationale,
        "provenance": dict(patch.provenance),
    }


def project_audit_view(candidate: ProjectionEditCandidate) -> dict[str, Any]:
    return {
        "validation": candidate.validation,
        "no_change": candidate.no_change,
        "semantic_changed": candidate.diff.semantic_changed,
        "before_semantic_hash": candidate.before_semantic_hash,
        "candidate_semantic_hash": candidate.candidate_semantic_hash,
        "before_record_hash": candidate.before_record_hash,
        "candidate_record_hash": candidate.candidate_record_hash,
        "patch": _patch_view(candidate.patch),
        "diff": candidate.diff.to_dict(),
    }

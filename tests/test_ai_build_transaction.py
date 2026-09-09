from __future__ import annotations

from dataclasses import replace

import pytest

from nova_core import Graph, GraphPatch, Module, Node, Project, record_hash, semantic_hash
from nova_core.ai_build import (
    AIProvenance, AISandboxPolicy, AIBuildRequest, AIBuildTransaction,
    BuildConstraint, BuildStatus,
)
from nova_core.errors import AIBuildConflictError, AIBuildError


def base_project() -> Project:
    graph = Graph(
        id="main", inputs=("x",), outputs=("y",),
        nodes=(Node(id="op", kind="Identity", inputs=("x",), outputs=("y",)),),
    )
    return Project(modules=(Module(id="app", graphs=(graph,)),))


def request_for(kind: str, request_id: str = "r1") -> AIBuildRequest:
    project = base_project()
    replacement = Node(id="op", kind=kind, inputs=("x",) if kind != "Multiply" else ("x", "x"), outputs=("y",))
    patch = GraphPatch(
        base_hash=semantic_hash(project), base_record_hash=record_hash(project),
        module_id="app", graph_id="main", replaced_nodes=(replacement,), rationale=kind,
    )
    return AIBuildRequest(
        provenance=AIProvenance(request_id=request_id, actor_id="agent"),
        patch=patch,
        constraints=(BuildConstraint(kind="require_node_kind", subject="op", expected=kind),),
        sandbox=AISandboxPolicy(allowed_node_kinds=("Identity","Relu","Tanh","Multiply"), max_replaced_nodes=1),
    )


def test_preview_does_not_mutate_transaction_current():
    tx = AIBuildTransaction(base_project())
    before = tx.record_hash
    candidate = tx.preview(request_for("Relu"))
    assert candidate.status is BuildStatus.READY
    assert tx.record_hash == before
    assert tx.history_depth == 0


def test_commit_reproduces_preview_hash_and_records_history():
    tx = AIBuildTransaction(base_project())
    candidate = tx.preview(request_for("Relu"))
    result = tx.commit(candidate)
    assert result.after_semantic_hash == candidate.candidate_semantic_hash
    assert result.after_record_hash == candidate.candidate_record_hash
    assert tx.semantic_hash == candidate.candidate_semantic_hash
    assert tx.history_depth == 1


def test_rollback_restores_exact_base_record():
    tx = AIBuildTransaction(base_project())
    base_sem, base_rec = tx.semantic_hash, tx.record_hash
    tx.commit(tx.preview(request_for("Relu")))
    restored = tx.rollback()
    assert semantic_hash(restored) == base_sem
    assert record_hash(restored) == base_rec
    assert tx.history_depth == 0


def test_rejected_candidate_cannot_commit():
    tx = AIBuildTransaction(base_project())
    request = request_for("Relu")
    rejected_request = AIBuildRequest(
        provenance=request.provenance,
        patch=request.patch,
        constraints=(BuildConstraint(kind="require_node_kind", subject="op", expected="Add"),),
        sandbox=request.sandbox,
    )
    candidate = tx.preview(rejected_request)
    assert candidate.status is BuildStatus.REJECTED
    with pytest.raises(AIBuildError):
        tx.commit(candidate)
    assert tx.history_depth == 0


def test_stale_candidate_is_refused_after_working_project_changes():
    tx = AIBuildTransaction(base_project())
    stale = tx.preview(request_for("Relu", "stale"))
    fresh = tx.preview(request_for("Tanh", "fresh"))
    tx.commit(fresh)
    with pytest.raises(AIBuildConflictError):
        tx.commit(stale)


def test_tampered_candidate_request_hash_is_refused():
    tx = AIBuildTransaction(base_project())
    candidate = tx.preview(request_for("Relu"))
    tampered = replace(candidate, request_hash="sha256:tampered")
    with pytest.raises(AIBuildConflictError):
        tx.commit(tampered)
    assert tx.history_depth == 0


def test_preview_commit_divergence_is_refused():
    tx = AIBuildTransaction(base_project())
    candidate = tx.preview(request_for("Relu"))
    tampered = replace(candidate, candidate_record_hash="sha256:tampered")
    with pytest.raises(AIBuildConflictError):
        tx.commit(tampered)
    assert tx.history_depth == 0


def test_commit_result_keeps_request_and_candidate_identity():
    tx = AIBuildTransaction(base_project())
    candidate = tx.preview(request_for("Relu", "identity"))
    result = tx.commit(candidate)
    assert result.request_hash == candidate.request_hash
    assert result.request_id == "identity"
    assert result.candidate_semantic_hash == candidate.candidate_semantic_hash

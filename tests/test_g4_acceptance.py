from __future__ import annotations

import pytest

from nova_core import (
    Graph, GraphPatch, Module, Node, Project, Shape, TensorType,
    DifferentiationRequest, record_hash, semantic_hash,
)
from nova_core.ai_build import (
    AIProvenance, AISandboxPolicy, AIBuildRequest, AIBuildTransaction,
    BuildConstraint, BuildStatus, BuildTestCase, preview_ai_build,
)
from nova_core.errors import AIBuildConflictError


def base_project() -> Project:
    graph = Graph(
        id="main", inputs=("x",), outputs=("y",),
        nodes=(Node(id="op", kind="Identity", inputs=("x",), outputs=("y",)),),
    )
    return Project(modules=(Module(id="app", graphs=(graph,)),))


def add_layer_request(project: Project, request_id="add-layer") -> AIBuildRequest:
    patch = GraphPatch(
        base_hash=semantic_hash(project), base_record_hash=record_hash(project),
        module_id="app", graph_id="main",
        added_nodes=(Node(id="relu", kind="Relu", inputs=("y",), outputs=("z",)),),
        changed_outputs=("z",),
        rationale="add ReLU layer",
    )
    return AIBuildRequest(
        provenance=AIProvenance(request_id=request_id, actor_id="nova-a-test"),
        patch=patch,
        constraints=(
            BuildConstraint(kind="require_node_kind", subject="relu", expected="Relu"),
            BuildConstraint(kind="require_graph_output", subject="z"),
        ),
        tests=(BuildTestCase(name="relu-negative", inputs={"x": -2.0}, expected_outputs={"z": 0.0}),),
        differentiation_requests=(DifferentiationRequest(target="z", wrt=("x",), seed_input="__seed__"),),
        sandbox=AISandboxPolicy(
            max_added_nodes=1,
            allow_interface_change=True,
            allowed_node_kinds=("Identity", "Relu"),
        ),
    )


def typed_request(project: Project, shape, *, request_id="typed", expected_shape=(2, 4)) -> AIBuildRequest:
    t = TensorType("f32", Shape(shape))
    patch = GraphPatch(
        base_hash=semantic_hash(project), base_record_hash=record_hash(project),
        module_id="app", graph_id="main",
        replaced_nodes=(Node(id="op", kind="Identity", inputs=("x",), outputs=("y",), value_type=t, shape_type=t.shape),),
    )
    return AIBuildRequest(
        provenance=AIProvenance(request_id=request_id, actor_id="nova-a-test"),
        patch=patch,
        constraints=(
            BuildConstraint(kind="require_tensor_dtype", subject="op", expected="f32"),
            BuildConstraint(kind="require_tensor_shape", subject="op", expected=list(expected_shape)),
        ),
        sandbox=AISandboxPolicy(allowed_node_kinds=("Identity",), max_replaced_nodes=1),
    )


def test_g4_add_layer_test_and_differentiation_are_ready():
    candidate = preview_ai_build(base_project(), add_layer_request(base_project()))
    assert candidate.status is BuildStatus.READY
    assert candidate.tests[0].passed is True
    assert candidate.differentiation[0].passed is True
    assert "relu" in candidate.diff.added_nodes
    assert any(change.field == "outputs" for change in candidate.diff.graph_changes)


def test_g4_shape_type_change_and_constraint_driven_repair():
    project = base_project()
    bad = preview_ai_build(project, typed_request(project, (4, 2), request_id="bad"))
    good = preview_ai_build(project, typed_request(project, (2, 4), request_id="repair"))
    assert bad.status is BuildStatus.REJECTED
    assert bad.constraints[1].passed is False
    assert good.status is BuildStatus.READY
    assert all(item.passed for item in good.constraints)


def test_g4_effectful_patch_is_sandbox_rejected():
    project = base_project()
    patch = GraphPatch(
        base_hash=semantic_hash(project), base_record_hash=record_hash(project),
        module_id="app", graph_id="main",
        added_nodes=(Node(id="net", kind="Identity", inputs=("y",), outputs=("n",), effect_type=("Network",)),),
    )
    request = AIBuildRequest(
        provenance=AIProvenance(request_id="effect", actor_id="nova-a-test"),
        patch=patch,
    )
    candidate = preview_ai_build(project, request)
    assert candidate.status is BuildStatus.REJECTED
    assert "effects_forbidden" in {v.kind for v in candidate.sandbox.violations}


def test_g4_stale_candidate_rejection_and_rollback():
    project = base_project()
    tx = AIBuildTransaction(project)
    stale = tx.preview(add_layer_request(project, request_id="stale"))

    tanh_patch = GraphPatch(
        base_hash=semantic_hash(project), base_record_hash=record_hash(project),
        module_id="app", graph_id="main",
        replaced_nodes=(Node(id="op", kind="Tanh", inputs=("x",), outputs=("y",)),),
    )
    fresh_req = AIBuildRequest(
        provenance=AIProvenance(request_id="fresh", actor_id="nova-a-test"),
        patch=tanh_patch,
        constraints=(BuildConstraint(kind="require_node_kind", subject="op", expected="Tanh"),),
        sandbox=AISandboxPolicy(allowed_node_kinds=("Identity", "Tanh"), max_replaced_nodes=1),
    )
    fresh = tx.preview(fresh_req)
    base_record = tx.record_hash
    tx.commit(fresh)
    with pytest.raises(AIBuildConflictError):
        tx.commit(stale)
    tx.rollback()
    assert tx.record_hash == base_record

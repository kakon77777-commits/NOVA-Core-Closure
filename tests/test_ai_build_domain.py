from __future__ import annotations

from dataclasses import replace

import pytest

from nova_core import Graph, GraphPatch, Module, Node, Project, Shape, TensorType, semantic_hash, record_hash
from nova_core.ai_build import (
    AIProvenance,
    AISandboxPolicy,
    AIBuildRequest,
    BuildConstraint,
    BuildTestCase,
    ai_build_request_hash,
    check_ai_sandbox,
    decode_ai_build_request,
    encode_ai_build_request,
    evaluate_build_constraints,
)


def base_project() -> Project:
    node = Node(id="op", kind="Identity", inputs=("x",), outputs=("y",))
    graph = Graph(id="main", inputs=("x",), outputs=("y",), nodes=(node,))
    return Project(modules=(Module(id="app", graphs=(graph,)),))


def request_with_patch(patch: GraphPatch, **kwargs) -> AIBuildRequest:
    return AIBuildRequest(
        provenance=AIProvenance(request_id="r1", actor_id="agent-a", model_id="local-test"),
        patch=patch,
        **kwargs,
    )


def test_request_codec_roundtrip_preserves_hash_and_structured_fields():
    project = base_project()
    patch = GraphPatch(
        base_hash=semantic_hash(project),
        base_record_hash=record_hash(project),
        module_id="app",
        graph_id="main",
        replaced_nodes=(Node(id="op", kind="Relu", inputs=("x",), outputs=("y",)),),
        rationale="replace identity",
        provenance={"request_id": "r1"},
    )
    request = request_with_patch(
        patch,
        constraints=(BuildConstraint(kind="require_node_kind", subject="op", expected="Relu"),),
        tests=(BuildTestCase(name="positive", inputs={"x": [1.0]}, expected_outputs={"y": [1.0]}),),
        sandbox=AISandboxPolicy(allowed_node_kinds=("Relu", "Identity"), max_replaced_nodes=2),
    )
    restored = decode_ai_build_request(encode_ai_build_request(request))
    assert ai_build_request_hash(restored) == ai_build_request_hash(request)
    assert restored.provenance.request_id == "r1"
    assert restored.patch.replaced_nodes[0].kind == "Relu"
    assert restored.constraints[0].expected == "Relu"
    assert restored.tests[0].backend == "interpreter"


def test_effectful_added_node_is_rejected_by_default_sandbox():
    project = base_project()
    patch = GraphPatch(
        base_hash=semantic_hash(project),
        base_record_hash=record_hash(project),
        module_id="app",
        graph_id="main",
        added_nodes=(Node(id="net", kind="Identity", inputs=("x",), outputs=("n",), effect_type=("Network",)),),
    )
    report = check_ai_sandbox(project, request_with_patch(patch))
    assert report.passed is False
    assert "effects_forbidden" in {item.kind for item in report.violations}


def test_sandbox_enforces_patch_budget_and_node_kind_allowlist():
    project = base_project()
    patch = GraphPatch(
        base_hash=semantic_hash(project),
        base_record_hash=record_hash(project),
        module_id="app",
        graph_id="main",
        added_nodes=(Node(id="a", kind="Add", inputs=("x", "x"), outputs=("a",)),),
    )
    policy = AISandboxPolicy(max_added_nodes=0, allowed_node_kinds=("Identity",))
    report = check_ai_sandbox(project, request_with_patch(patch, sandbox=policy))
    kinds = {item.kind for item in report.violations}
    assert "added_node_budget" in kinds
    assert "node_kind_forbidden" in kinds


def test_sandbox_rejects_interface_change_when_disabled():
    project = base_project()
    patch = GraphPatch(
        base_hash=semantic_hash(project),
        base_record_hash=record_hash(project),
        module_id="app",
        graph_id="main",
        changed_outputs=("x",),
    )
    report = check_ai_sandbox(project, request_with_patch(patch))
    assert "interface_change_forbidden" in {item.kind for item in report.violations}


def test_sandbox_rejects_disabled_tests_and_differentiation_requests():
    project = base_project()
    patch = GraphPatch(
        base_hash=semantic_hash(project),
        base_record_hash=record_hash(project),
        module_id="app",
        graph_id="main",
    )
    request = request_with_patch(
        patch,
        tests=(BuildTestCase(name="t", inputs={"x": [1.0]}, expected_outputs={"y": [1.0]}),),
        differentiation_requests=({"target": "y", "wrt": ["x"]},),
        sandbox=AISandboxPolicy(allow_test_execution=False, allow_differentiation=False),
    )
    report = check_ai_sandbox(project, request)
    kinds = {item.kind for item in report.violations}
    assert "test_execution_forbidden" in kinds
    assert "differentiation_forbidden" in kinds


def typed_graph() -> Graph:
    t = TensorType("f32", Shape((2, 4)))
    node = Node(id="proj", kind="Identity", inputs=("x",), outputs=("y",), value_type=t, shape_type=t.shape)
    return Graph(id="main", inputs=("x",), outputs=("y",), nodes=(node,))


def test_constraint_api_reads_candidate_graph_not_request_metadata():
    graph = typed_graph()
    results = evaluate_build_constraints(
        graph,
        (
            BuildConstraint(kind="require_graph_output", subject="y"),
            BuildConstraint(kind="require_node", subject="proj"),
            BuildConstraint(kind="require_node_kind", subject="proj", expected="Identity"),
            BuildConstraint(kind="require_tensor_dtype", subject="proj", expected="f32"),
            BuildConstraint(kind="require_tensor_shape", subject="proj", expected=[2, 4]),
            BuildConstraint(kind="forbid_effects", subject="*"),
        ),
    )
    assert all(item.passed for item in results)


def test_constraint_api_reports_mismatch_and_unknown_kind():
    graph = typed_graph()
    result = evaluate_build_constraints(
        graph,
        (BuildConstraint(kind="require_tensor_shape", subject="proj", expected=[4, 2]),),
    )[0]
    assert result.passed is False
    assert result.kind == "require_tensor_shape"
    with pytest.raises(ValueError):
        BuildConstraint(kind="made_up", subject="x")


def test_provenance_requires_explicit_identity_and_is_deterministic():
    p = AIProvenance(request_id="r9", actor_id="agent-9", metadata={"time": "2026-08-20T14:44+08:00"})
    q = AIProvenance(request_id="r9", actor_id="agent-9", metadata={"time": "2026-08-20T14:44+08:00"})
    assert p == q
    with pytest.raises(ValueError):
        AIProvenance(request_id="", actor_id="a")
    with pytest.raises(ValueError):
        AIProvenance(request_id="r", actor_id="")

from __future__ import annotations

from nova_core import (
    Graph, GraphPatch, Module, Node, Project, TensorType, Shape,
    DifferentiationRequest, semantic_hash, record_hash,
)
from nova_core.ai_build import (
    AIProvenance, AISandboxPolicy, AIBuildRequest, BuildConstraint, BuildStatus,
    BuildTestCase, preview_ai_build,
)
from nova_core.audit import project_ai_build_audit


def base_project() -> Project:
    t = TensorType("f64", Shape(()))
    node = Node(
        id="op", kind="Identity", inputs=("x",), outputs=("y",),
        value_type=t, shape_type=t.shape, differentiation_type="Differentiable",
    )
    graph = Graph(id="main", inputs=("x",), outputs=("y",), nodes=(node,))
    return Project(modules=(Module(id="app", graphs=(graph,)),))


def valid_request(*, expected=2.0, with_diff=True) -> AIBuildRequest:
    project = base_project()
    replacement = Node(
        id="op", kind="Multiply", inputs=("x", "x"), outputs=("y",),
        value_type=TensorType.scalar("f64"), shape_type=Shape(()), differentiation_type="Differentiable",
    )
    patch = GraphPatch(
        base_hash=semantic_hash(project), base_record_hash=record_hash(project),
        module_id="app", graph_id="main", replaced_nodes=(replacement,),
        rationale="square x", provenance={"request_id":"r-preview"},
    )
    diffs = (DifferentiationRequest(target="y", wrt=("x",)),) if with_diff else ()
    return AIBuildRequest(
        provenance=AIProvenance(request_id="r-preview", actor_id="agent"),
        patch=patch,
        constraints=(
            BuildConstraint(kind="require_node_kind", subject="op", expected="Multiply"),
            BuildConstraint(kind="require_graph_output", subject="y"),
        ),
        tests=(BuildTestCase(name="square", inputs={"x": 2.0}, expected_outputs={"y": expected}),),
        differentiation_requests=diffs,
        sandbox=AISandboxPolicy(allowed_node_kinds=("Identity","Multiply"), max_replaced_nodes=1),
    )


def test_preview_is_pure_and_ready_when_all_obligations_pass():
    project = base_project()
    before_sem = semantic_hash(project)
    before_rec = record_hash(project)
    candidate = preview_ai_build(project, valid_request(expected=4.0))
    assert candidate.status is BuildStatus.READY
    assert semantic_hash(project) == before_sem
    assert record_hash(project) == before_rec
    assert candidate.candidate_project is not None
    assert candidate.tests[0].passed is True
    assert candidate.constraints and all(x.passed for x in candidate.constraints)
    assert candidate.differentiation[0].passed is True
    assert candidate.differentiation[0].derivative_semantic_hash.startswith("sha256:")
    assert candidate.diff is not None and candidate.diff.semantic_changed is True


def test_failed_structured_test_rejects_candidate_but_keeps_diff_evidence():
    candidate = preview_ai_build(base_project(), valid_request(expected=5.0))
    assert candidate.status is BuildStatus.REJECTED
    assert candidate.tests[0].passed is False
    assert candidate.candidate_project is not None
    assert candidate.diff is not None


def test_failed_constraint_rejects_candidate_without_mutating_project():
    project = base_project()
    request = valid_request(expected=4.0, with_diff=False)
    request = AIBuildRequest(
        provenance=request.provenance,
        patch=request.patch,
        constraints=(BuildConstraint(kind="require_node_kind", subject="op", expected="Add"),),
        tests=request.tests,
        sandbox=request.sandbox,
    )
    before = record_hash(project)
    candidate = preview_ai_build(project, request)
    assert candidate.status is BuildStatus.REJECTED
    assert candidate.constraints[0].passed is False
    assert record_hash(project) == before


def test_sandbox_rejection_does_not_apply_patch_or_tests():
    project = base_project()
    request = valid_request(expected=4.0)
    request = AIBuildRequest(
        provenance=request.provenance,
        patch=request.patch,
        constraints=request.constraints,
        tests=request.tests,
        differentiation_requests=request.differentiation_requests,
        sandbox=AISandboxPolicy(max_replaced_nodes=0),
    )
    candidate = preview_ai_build(project, request)
    assert candidate.status is BuildStatus.REJECTED
    assert candidate.candidate_project is None
    assert candidate.tests == ()
    assert "replaced_node_budget" in {v.kind for v in candidate.sandbox.violations}


def test_patch_conflict_becomes_rejected_audit_evidence():
    project = base_project()
    request = valid_request(expected=4.0)
    bad_patch = GraphPatch(
        **{**request.patch.__dict__, "base_hash": "sha256:deadbeef"}
    )
    bad = AIBuildRequest(
        provenance=request.provenance, patch=bad_patch, constraints=request.constraints,
        tests=request.tests, differentiation_requests=request.differentiation_requests, sandbox=request.sandbox,
    )
    candidate = preview_ai_build(project, bad)
    assert candidate.status is BuildStatus.REJECTED
    assert candidate.error is not None
    assert candidate.error["category"] == "ConflictError"


def test_differentiation_failure_rejects_candidate():
    request = valid_request(expected=4.0, with_diff=False)
    bad_diff = DifferentiationRequest(target="missing", wrt=("x",))
    request = AIBuildRequest(
        provenance=request.provenance, patch=request.patch, constraints=request.constraints,
        tests=request.tests, differentiation_requests=(bad_diff,), sandbox=request.sandbox,
    )
    candidate = preview_ai_build(base_project(), request)
    assert candidate.status is BuildStatus.REJECTED
    assert candidate.differentiation[0].passed is False


def test_audit_view_contains_request_sandbox_diff_and_validation_evidence():
    candidate = preview_ai_build(base_project(), valid_request(expected=4.0))
    view = project_ai_build_audit(candidate)
    assert view["status"] == "ready"
    assert view["request"]["request_id"] == "r-preview"
    assert view["sandbox"]["passed"] is True
    assert view["tests"][0]["passed"] is True
    assert view["differentiation"][0]["passed"] is True
    assert view["diff"]["semantic_changed"] is True

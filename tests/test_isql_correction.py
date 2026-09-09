from __future__ import annotations

import pytest

from nova_core import (
    AIProvenance, AISandboxPolicy, AIBuildRequest, BuildStatus,
    DimensionPredicate, Graph, GraphPatch, Module, Node, Project,
    SemanticBridgeTemplate, SemanticCorrection, SemanticDimension,
    SemanticField, SemanticProvenance, SemanticRelation, SemanticTensor,
    SemanticTopology, Shape, TensorType, apply_semantic_correction,
    bridge_semantic_tensor, record_hash, resolve_semantic_candidate,
    semantic_hash, semantic_tensor_hash, ISQLResolutionError,
)


def base_project() -> Project:
    t = TensorType("f64", Shape(()))
    return Project(modules=(Module(id="app", graphs=(Graph(
        id="main", inputs=("x",), outputs=("y",),
        nodes=(Node(id="op", kind="Identity", inputs=("x",), outputs=("y",), value_type=t, shape_type=t.shape),),
    ),)),))


def tensor() -> SemanticTensor:
    return SemanticTensor(
        dimensions=(SemanticDimension("operation_family", "activation", weight=2.0),),
        phase=SemanticField("intent-phase", "candidate_generation"),
        spectrum=(SemanticField("bounded_output", 0.8),),
        topology=SemanticTopology("relation_graph", {"connected": True}),
        relations=(), confidence=0.75,
        provenance=SemanticProvenance(
            protocol_version="ISQL-Core/0.2", registry_id="ISQL-NOVA-G7", registry_version="1",
            domain="PROGRAM_INTENT", decoder_contract="semantic-candidate-set/v1", source_id="intent-1",
        ),
    )


def template(kind: str, template_id: str, *, stale: bool = False) -> SemanticBridgeTemplate:
    project = base_project(); t = TensorType("f64", Shape(()))
    patch = GraphPatch(
        base_hash="sha256:stale" if stale else semantic_hash(project),
        base_record_hash=record_hash(project), module_id="app", graph_id="main",
        replaced_nodes=(Node(id="op", kind=kind, inputs=("x",), outputs=("y",), value_type=t, shape_type=t.shape),),
    )
    req = AIBuildRequest(
        provenance=AIProvenance(request_id=f"req-{template_id}", actor_id="bridge", source="isql"),
        patch=patch,
        sandbox=AISandboxPolicy(allowed_node_kinds=("Identity","Sigmoid","Tanh"), max_replaced_nodes=1),
    )
    return SemanticBridgeTemplate(
        template_id=template_id, version="1", request=req,
        dimension_predicates=(DimensionPredicate("operation_family", "activation"),),
        unresolved_obligations=("confirm_range",), support_weight=0.9,
    )


def candidates(project: Project | None = None):
    project = project or base_project()
    return bridge_semantic_tensor(project, tensor(), (template("Sigmoid", "sigmoid"), template("Tanh", "tanh")))


def test_set_dimension_creates_parent_linked_derived_tensor_without_mutating_original():
    original = tensor(); before = semantic_tensor_hash(original)
    correction = SemanticCorrection(
        correction_id="corr-1", actor_id="human", source_tensor_hash=before,
        action="set_dimension", subject="smoothness", value="preferred", rationale="prefer smooth activation",
    )
    derived = apply_semantic_correction(original, correction)
    assert semantic_tensor_hash(original) == before
    assert semantic_tensor_hash(derived) != before
    assert derived.provenance.parent_tensor_hash == before
    assert derived.provenance.metadata["last_correction_id"] == "corr-1"
    assert {d.name: d.value for d in derived.dimensions}["smoothness"] == "preferred"


def test_add_relation_creates_derived_tensor_and_preserves_existing_semantics():
    original = tensor(); before = semantic_tensor_hash(original)
    correction = SemanticCorrection(
        correction_id="corr-rel", actor_id="human", source_tensor_hash=before,
        action="add_relation", subject="operation_family:prefers:smoothness",
        value={"source":"operation_family","predicate":"prefers","target":"smoothness"},
    )
    derived = apply_semantic_correction(original, correction)
    assert len(original.relations) == 0
    assert derived.relations[0].predicate == "prefers"
    assert derived.provenance.parent_tensor_hash == before


def test_correction_source_hash_must_match_tensor():
    with pytest.raises(ISQLResolutionError, match="source tensor hash"):
        apply_semantic_correction(tensor(), SemanticCorrection(
            correction_id="bad", actor_id="human", source_tensor_hash="sha256:nope",
            action="set_dimension", subject="x", value=1,
        ))


def test_select_candidate_does_not_mutate_tensor_or_project():
    project = base_project(); original = tensor(); cset = candidates(project)
    before_tensor = semantic_tensor_hash(original); before_project = record_hash(project)
    correction = SemanticCorrection(
        correction_id="select-1", actor_id="human", source_tensor_hash=before_tensor,
        action="select_candidate", candidate_id="sigmoid", rationale="human chose sigmoid",
    )
    resolution = resolve_semantic_candidate(project, cset, correction)
    assert resolution.status == "selected"
    assert resolution.selected_candidate_id == "sigmoid"
    assert resolution.selected_project is not None
    assert semantic_tensor_hash(original) == before_tensor
    assert record_hash(project) == before_project


def test_rejected_candidate_cannot_be_selected():
    project = base_project(); original = tensor()
    cset = bridge_semantic_tensor(project, original, (template("Sigmoid", "bad", stale=True),))
    assert cset.candidates[0].validation_status == BuildStatus.REJECTED.value
    correction = SemanticCorrection(
        correction_id="select-bad", actor_id="human", source_tensor_hash=semantic_tensor_hash(original),
        action="select_candidate", candidate_id="bad",
    )
    with pytest.raises(ISQLResolutionError, match="READY"):
        resolve_semantic_candidate(project, cset, correction)


def test_stale_base_project_cannot_resolve_old_candidate_set():
    project = base_project(); original = tensor(); cset = candidates(project)
    changed = Project(modules=project.modules, attributes={"changed": True})
    correction = SemanticCorrection(
        correction_id="select-stale", actor_id="human", source_tensor_hash=semantic_tensor_hash(original),
        action="select_candidate", candidate_id="sigmoid",
    )
    with pytest.raises(ISQLResolutionError, match="base project"):
        resolve_semantic_candidate(changed, cset, correction)


def test_reject_candidate_creates_resolution_evidence_without_project():
    project = base_project(); original = tensor(); cset = candidates(project)
    correction = SemanticCorrection(
        correction_id="reject-1", actor_id="human", source_tensor_hash=semantic_tensor_hash(original),
        action="reject_candidate", candidate_id="tanh", rationale="not desired",
    )
    resolution = resolve_semantic_candidate(project, cset, correction)
    assert resolution.status == "rejected"
    assert resolution.selected_project is None
    assert resolution.selected_candidate_id == "tanh"

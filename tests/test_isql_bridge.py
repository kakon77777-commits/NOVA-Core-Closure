from __future__ import annotations

from nova_core import (
    AIProvenance,
    AISandboxPolicy,
    AIBuildRequest,
    BuildStatus,
    DimensionPredicate,
    Graph,
    GraphPatch,
    Module,
    Node,
    Project,
    RelationPredicate,
    SemanticBridgeTemplate,
    SemanticDimension,
    SemanticField,
    SemanticProvenance,
    SemanticRelation,
    SemanticTensor,
    SemanticTopology,
    Shape,
    TensorType,
    bridge_semantic_tensor,
    record_hash,
    semantic_hash,
    semantic_tensor_hash,
)


def base_project() -> Project:
    t = TensorType("f64", Shape(()))
    node = Node(
        id="op",
        kind="Identity",
        inputs=("x",),
        outputs=("y",),
        value_type=t,
        shape_type=t.shape,
        differentiation_type="Differentiable",
    )
    return Project(modules=(Module(id="app", graphs=(Graph(id="main", inputs=("x",), outputs=("y",), nodes=(node,)),)),))


def activation_tensor(*, include_smoothness: bool = True) -> SemanticTensor:
    dims = [SemanticDimension("operation_family", "activation", weight=2.0)]
    if include_smoothness:
        dims.append(SemanticDimension("smoothness", "preferred", weight=1.0))
    return SemanticTensor(
        dimensions=tuple(dims),
        phase=SemanticField("intent-phase", "candidate_generation"),
        spectrum=(SemanticField("bounded_output", 0.8),),
        topology=SemanticTopology("relation_graph", {"connected": True}),
        relations=(SemanticRelation("operation_family", "prefers", "smoothness"),),
        confidence=0.8,
        provenance=SemanticProvenance(
            protocol_version="ISQL-Core/0.2",
            registry_id="ISQL-NOVA-G7",
            registry_version="1",
            domain="PROGRAM_INTENT",
            decoder_contract="semantic-candidate-set/v1",
            source_id="intent-activation",
        ),
    )


def template(kind: str, *, template_id: str, support_weight: float = 0.9, bad_base: bool = False) -> SemanticBridgeTemplate:
    project = base_project()
    t = TensorType("f64", Shape(()))
    replacement = Node(
        id="op",
        kind=kind,
        inputs=("x",),
        outputs=("y",),
        value_type=t,
        shape_type=t.shape,
        differentiation_type="Differentiable",
    )
    patch = GraphPatch(
        base_hash="sha256:stale" if bad_base else semantic_hash(project),
        base_record_hash=record_hash(project),
        module_id="app",
        graph_id="main",
        replaced_nodes=(replacement,),
        rationale=f"activation candidate {kind}",
    )
    request = AIBuildRequest(
        provenance=AIProvenance(request_id=f"req-{template_id}", actor_id="isql-bridge", source="isql"),
        patch=patch,
        sandbox=AISandboxPolicy(allowed_node_kinds=("Identity", "Sigmoid", "Tanh", "Relu"), max_replaced_nodes=1),
    )
    return SemanticBridgeTemplate(
        template_id=template_id,
        version="1",
        request=request,
        dimension_predicates=(
            DimensionPredicate("operation_family", "activation", required=True, weight=2.0),
            DimensionPredicate("smoothness", "preferred", required=False, weight=1.0),
        ),
        relation_predicates=(
            RelationPredicate("operation_family", "prefers", "smoothness", required=False, weight=0.5),
        ),
        unresolved_obligations=("confirm_activation_range",),
        support_weight=support_weight,
        rationale=f"{kind} is a supported smooth activation candidate",
    )


def test_same_tensor_can_produce_two_validated_candidates():
    project = base_project()
    tensor = activation_tensor()
    result = bridge_semantic_tensor(project, tensor, (template("Sigmoid", template_id="sigmoid"), template("Tanh", template_id="tanh")))
    assert len(result.candidates) == 2
    assert all(c.validation_status == BuildStatus.READY.value for c in result.candidates)
    assert len({c.candidate_semantic_hash for c in result.candidates}) == 2
    assert {c.template_id for c in result.candidates} == {"sigmoid", "tanh"}
    assert any(a.kind == "multiple_template_match" for a in result.ambiguities)


def test_partial_optional_match_surfaces_ambiguity_and_obligation():
    result = bridge_semantic_tensor(base_project(), activation_tensor(include_smoothness=False), (template("Sigmoid", template_id="sigmoid"),))
    candidate = result.candidates[0]
    assert any(a.kind == "missing_dimension" and a.subject == "smoothness" for a in candidate.ambiguities)
    assert any(o.kind == "resolve_dimension" and o.subject == "smoothness" for o in candidate.obligations)
    assert any(o.subject == "confirm_activation_range" for o in candidate.obligations)


def test_required_mismatch_excludes_template_instead_of_silently_assuming():
    tensor = activation_tensor()
    wrong = SemanticBridgeTemplate(
        **{
            **template("Sigmoid", template_id="wrong").__dict__,
            "dimension_predicates": (DimensionPredicate("operation_family", "reduction", required=True),),
        }
    )
    result = bridge_semantic_tensor(base_project(), tensor, (wrong, template("Tanh", template_id="tanh")))
    assert [c.template_id for c in result.candidates] == ["tanh"]


def test_validation_failure_has_zero_confidence_and_cannot_rank_over_ready():
    result = bridge_semantic_tensor(
        base_project(),
        activation_tensor(),
        (
            template("Sigmoid", template_id="bad", support_weight=1.0, bad_base=True),
            template("Tanh", template_id="good", support_weight=0.5),
        ),
    )
    assert result.candidates[0].template_id == "good"
    bad = next(c for c in result.candidates if c.template_id == "bad")
    assert bad.validation_status == BuildStatus.REJECTED.value
    assert bad.bridge_confidence == 0.0


def test_bridge_confidence_breakdown_is_bounded_and_visible():
    candidate = bridge_semantic_tensor(base_project(), activation_tensor(), (template("Sigmoid", template_id="sigmoid"),)).candidates[0]
    assert 0.0 <= candidate.bridge_confidence <= 1.0
    breakdown = candidate.confidence_breakdown
    assert breakdown.source_confidence == 0.8
    assert 0.0 <= breakdown.dimension_coverage <= 1.0
    assert 0.0 <= breakdown.relation_coverage <= 1.0
    assert breakdown.template_support == 0.9
    assert breakdown.obligation_penalty < 1.0


def test_bridge_is_deterministic_and_does_not_mutate_tensor_or_project():
    project = base_project()
    tensor = activation_tensor()
    before_project_sem = semantic_hash(project)
    before_project_rec = record_hash(project)
    before_tensor = semantic_tensor_hash(tensor)
    templates = (template("Tanh", template_id="tanh"), template("Sigmoid", template_id="sigmoid"))
    a = bridge_semantic_tensor(project, tensor, templates)
    b = bridge_semantic_tensor(project, tensor, tuple(reversed(templates)))
    assert a.candidate_set_hash == b.candidate_set_hash
    assert [c.candidate_id for c in a.candidates] == [c.candidate_id for c in b.candidates]
    assert semantic_hash(project) == before_project_sem
    assert record_hash(project) == before_project_rec
    assert semantic_tensor_hash(tensor) == before_tensor


def test_relation_match_is_recorded():
    candidate = bridge_semantic_tensor(base_project(), activation_tensor(), (template("Tanh", template_id="tanh"),)).candidates[0]
    assert "operation_family:prefers:smoothness" in candidate.matched_relations


def test_no_required_template_match_returns_empty_candidate_set_with_ambiguity():
    wrong = SemanticBridgeTemplate(
        **{
            **template("Sigmoid", template_id="wrong").__dict__,
            "dimension_predicates": (DimensionPredicate("operation_family", "reduction", required=True),),
        }
    )
    result = bridge_semantic_tensor(base_project(), activation_tensor(), (wrong,))
    assert result.candidates == ()
    assert any(a.kind == "no_template_match" for a in result.ambiguities)

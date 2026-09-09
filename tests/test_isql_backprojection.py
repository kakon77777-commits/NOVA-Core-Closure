from __future__ import annotations

from nova_core import (
    AIProvenance, AISandboxPolicy, AIBuildRequest, DimensionPredicate,
    Graph, GraphPatch, Module, Node, Project, SemanticBridgeTemplate,
    SemanticCorrection, SemanticDimension, SemanticField, SemanticProvenance,
    SemanticRelation, SemanticTensor, SemanticTopology, Shape, TensorType,
    back_project_semantics, bridge_semantic_tensor, record_hash, semantic_hash,
    semantic_tensor_hash,
)


def base_project() -> Project:
    t=TensorType("f64",Shape(()))
    return Project(modules=(Module(id="app",graphs=(Graph(id="main",inputs=("x",),outputs=("y",),nodes=(Node(id="op",kind="Identity",inputs=("x",),outputs=("y",),value_type=t,shape_type=t.shape),)),)),))


def tensor() -> SemanticTensor:
    return SemanticTensor(
        dimensions=(SemanticDimension("operation_family","activation",weight=2),SemanticDimension("smoothness","preferred",weight=1),SemanticDimension("latency","low",weight=1)),
        phase=SemanticField("phase","candidate_generation"), spectrum=(),
        topology=SemanticTopology("relation_graph",{}),
        relations=(SemanticRelation("operation_family","prefers","smoothness"),SemanticRelation("latency","constrains","operation_family")),
        confidence=.8,
        provenance=SemanticProvenance(protocol_version="ISQL-Core/0.2",registry_id="ISQL-NOVA-G7",registry_version="1",domain="PROGRAM_INTENT",decoder_contract="semantic-candidate-set/v1",source_id="intent-bp"),
    )


def template() -> SemanticBridgeTemplate:
    p=base_project(); t=TensorType("f64",Shape(()))
    patch=GraphPatch(base_hash=semantic_hash(p),base_record_hash=record_hash(p),module_id="app",graph_id="main",replaced_nodes=(Node(id="op",kind="Sigmoid",inputs=("x",),outputs=("y",),value_type=t,shape_type=t.shape),))
    req=AIBuildRequest(provenance=AIProvenance(request_id="req-bp",actor_id="bridge",source="isql"),patch=patch,sandbox=AISandboxPolicy(allowed_node_kinds=("Identity","Sigmoid"),max_replaced_nodes=1))
    return SemanticBridgeTemplate(template_id="sigmoid",version="1",request=req,dimension_predicates=(DimensionPredicate("operation_family","activation",weight=2),DimensionPredicate("smoothness","preferred",required=False,weight=1)),unresolved_obligations=("confirm_range",))


def test_back_projection_reports_preserved_unresolved_and_traceability():
    t=tensor(); p=base_project(); cset=bridge_semantic_tensor(p,t,(template(),))
    view=back_project_semantics(t,cset,"sigmoid")
    assert view.source_tensor_hash == semantic_tensor_hash(t)
    assert view.candidate_graph_hash == cset.candidates[0].candidate_semantic_hash
    assert set(view.preserved_dimensions) == {"operation_family","smoothness"}
    assert "latency" in view.unresolved_dimensions
    assert view.fidelity.dimension_preservation_ratio == 0.75
    assert view.fidelity.relation_preservation_ratio == 0.0
    assert view.fidelity.unresolved_obligation_count >= 1
    assert view.fidelity.provenance_complete is True
    assert view.fidelity.traceable is True


def test_back_projection_tracks_correction_count_and_is_deterministic():
    t=tensor(); cset=bridge_semantic_tensor(base_project(),t,(template(),))
    corrections=(SemanticCorrection(correction_id="c1",actor_id="human",source_tensor_hash=semantic_tensor_hash(t),action="select_candidate",candidate_id="sigmoid"),)
    a=back_project_semantics(t,cset,"sigmoid",corrections=corrections)
    b=back_project_semantics(t,cset,"sigmoid",corrections=corrections)
    assert a == b
    assert a.fidelity.correction_count == 1
    assert a.exact_reconstruction_claimed is False

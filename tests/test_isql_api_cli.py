from __future__ import annotations

import json
from pathlib import Path

import pytest

from nova_core import (
    AIProvenance,
    AISandboxPolicy,
    AIBuildRequest,
    DimensionPredicate,
    Graph,
    GraphPatch,
    Module,
    Node,
    Project,
    RelationPredicate,
    SemanticBridgeTemplate,
    SemanticCorrection,
    SemanticDimension,
    SemanticField,
    SemanticProvenance,
    SemanticRelation,
    SemanticTensor,
    SemanticTopology,
    Shape,
    TensorType,
    decode_semantic_bridge_templates,
    decode_semantic_correction,
    encode_project,
    encode_semantic_bridge_templates,
    encode_semantic_correction,
    encode_semantic_tensor,
    record_hash,
    semantic_hash,
    semantic_tensor_hash,
)
from nova_core.api import (
    back_project_project_semantics,
    bridge_project_semantics,
    correct_semantic_tensor,
    load_semantic_bridge_templates,
    load_semantic_correction,
    load_semantic_tensor,
    resolve_project_semantics,
)
from nova_core.cli import main


def base_project() -> Project:
    t = TensorType("f64", Shape(()))
    return Project(modules=(Module(id="app", graphs=(Graph(
        id="main", inputs=("x",), outputs=("y",),
        nodes=(Node(id="op", kind="Identity", inputs=("x",), outputs=("y",), value_type=t, shape_type=t.shape),),
    ),)),))


def tensor() -> SemanticTensor:
    return SemanticTensor(
        dimensions=(
            SemanticDimension("operation_family", "activation", weight=2.0),
            SemanticDimension("smoothness", "preferred", weight=1.0),
            SemanticDimension("bounded_output", "desired", weight=1.0),
        ),
        phase=SemanticField("intent-phase", "candidate_generation"),
        spectrum=(SemanticField("confidence_band", [0.6, 0.9]),),
        topology=SemanticTopology("relation_graph", {"connected": True}),
        relations=(SemanticRelation("operation_family", "prefers", "smoothness"),),
        confidence=0.8,
        provenance=SemanticProvenance(
            protocol_version="ISQL-Core/0.2", registry_id="ISQL-NOVA-G7", registry_version="1",
            domain="PROGRAM_INTENT", decoder_contract="semantic-candidate-set/v1",
            registry_hash="sha256:registry", encoder_version="isql-encoder/v1",
            model_id="fixture-decoder", resolution="R2", context_policy="bounded",
            source_id="intent-activation",
        ),
    )


def template(kind: str, template_id: str, support: float) -> SemanticBridgeTemplate:
    project = base_project(); t = TensorType("f64", Shape(()))
    patch = GraphPatch(
        base_hash=semantic_hash(project), base_record_hash=record_hash(project),
        module_id="app", graph_id="main",
        replaced_nodes=(Node(id="op", kind=kind, inputs=("x",), outputs=("y",), value_type=t, shape_type=t.shape),),
        rationale=f"{kind} activation candidate",
    )
    request = AIBuildRequest(
        provenance=AIProvenance(request_id=f"req-{template_id}", actor_id="isql-bridge", source="isql"),
        patch=patch,
        sandbox=AISandboxPolicy(allowed_node_kinds=("Identity", "Sigmoid", "Tanh"), max_replaced_nodes=1),
    )
    return SemanticBridgeTemplate(
        template_id=template_id, version="1", request=request,
        dimension_predicates=(
            DimensionPredicate("operation_family", "activation", required=True, weight=2.0),
            DimensionPredicate("smoothness", "preferred", required=False, weight=1.0),
        ),
        relation_predicates=(RelationPredicate("operation_family", "prefers", "smoothness", required=False, weight=0.5),),
        unresolved_obligations=("confirm_activation_range",), support_weight=support,
        rationale=f"{kind} candidate",
    )


def templates():
    return (template("Sigmoid", "sigmoid", 0.95), template("Tanh", "tanh", 0.9))


def write_inputs(tmp_path: Path):
    p = tmp_path / "project.json"; t = tmp_path / "tensor.json"; b = tmp_path / "templates.json"
    p.write_text(encode_project(base_project()), encoding="utf-8")
    t.write_text(encode_semantic_tensor(tensor()), encoding="utf-8")
    b.write_text(encode_semantic_bridge_templates(templates()), encoding="utf-8")
    return p, t, b


def test_bridge_template_and_correction_codecs_round_trip():
    encoded = encode_semantic_bridge_templates(tuple(reversed(templates())))
    decoded = decode_semantic_bridge_templates(encoded)
    assert [item.template_id for item in decoded] == ["sigmoid", "tanh"]
    assert decoded[0].request.patch.graph_id == "main"
    correction = SemanticCorrection(
        correction_id="corr-1", actor_id="human", source_tensor_hash=semantic_tensor_hash(tensor()),
        action="select_candidate", candidate_id="sigmoid", rationale="prefer sigmoid",
    )
    assert decode_semantic_correction(encode_semantic_correction(correction)) == correction


def test_python_api_load_bridge_correct_resolve_and_backproject(tmp_path: Path):
    project_path, tensor_path, templates_path = write_inputs(tmp_path)
    loaded_tensor = load_semantic_tensor(tensor_path)
    loaded_templates = load_semantic_bridge_templates(templates_path)
    candidate_set = bridge_project_semantics(project_path, loaded_tensor, loaded_templates)
    assert len(candidate_set.candidates) == 2
    correction = SemanticCorrection(
        correction_id="select-1", actor_id="human", source_tensor_hash=semantic_tensor_hash(loaded_tensor),
        action="select_candidate", candidate_id="sigmoid",
    )
    resolution = resolve_project_semantics(project_path, loaded_tensor, loaded_templates, correction)
    assert resolution.status == "selected"
    back = back_project_project_semantics(project_path, loaded_tensor, loaded_templates, "sigmoid", corrections=(correction,))
    assert back.fidelity.traceable is True
    assert back.exact_reconstruction_claimed is False
    refine = SemanticCorrection(
        correction_id="refine-1", actor_id="human", source_tensor_hash=semantic_tensor_hash(loaded_tensor),
        action="set_dimension", subject="bounded_output", value="required",
    )
    derived = correct_semantic_tensor(loaded_tensor, refine)
    assert derived.provenance.parent_tensor_hash == semantic_tensor_hash(loaded_tensor)


def test_cli_isql_inspect_bridge_resolve_and_backproject(tmp_path: Path, capsys):
    project_path, tensor_path, templates_path = write_inputs(tmp_path)
    assert main(["isql", "inspect", str(tensor_path)]) == 0
    inspect = json.loads(capsys.readouterr().out)
    assert inspect["tensor_hash"] == semantic_tensor_hash(tensor())
    assert main(["isql", "bridge", str(project_path), str(tensor_path), str(templates_path)]) == 0
    bridged = json.loads(capsys.readouterr().out)
    assert len(bridged["candidates"]) == 2
    assert bridged["selected_candidate_id"] is None
    assert main(["isql", "resolve", str(project_path), str(tensor_path), str(templates_path), "--candidate", "sigmoid", "--actor", "human"]) == 0
    resolved = json.loads(capsys.readouterr().out)
    assert resolved["status"] == "selected"
    assert resolved["selected_candidate_id"] == "sigmoid"
    assert main(["isql", "back-project", str(project_path), str(tensor_path), str(templates_path), "--candidate", "sigmoid"]) == 0
    back = json.loads(capsys.readouterr().out)
    assert back["exact_reconstruction_claimed"] is False
    assert back["fidelity"]["traceable"] is True


def test_cli_isql_correct_is_append_only_and_refuses_overwrite(tmp_path: Path, capsys):
    _, tensor_path, _ = write_inputs(tmp_path)
    correction = SemanticCorrection(
        correction_id="refine-1", actor_id="human", source_tensor_hash=semantic_tensor_hash(tensor()),
        action="set_dimension", subject="bounded_output", value="required",
    )
    correction_path = tmp_path / "correction.json"
    correction_path.write_text(encode_semantic_correction(correction), encoding="utf-8")
    before = tensor_path.read_bytes()
    output = tmp_path / "derived.json"
    assert main(["isql", "correct", str(tensor_path), str(correction_path), "--output", str(output)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["parent_tensor_hash"] == semantic_tensor_hash(tensor())
    assert tensor_path.read_bytes() == before
    assert output.exists()
    assert main(["isql", "correct", str(tensor_path), str(correction_path), "--output", str(tensor_path)]) == 1
    err = json.loads(capsys.readouterr().err)
    assert err["ok"] is False


def test_loaders_accept_objects_paths_and_json(tmp_path: Path):
    _, tensor_path, templates_path = write_inputs(tmp_path)
    correction = SemanticCorrection(
        correction_id="c", actor_id="human", source_tensor_hash=semantic_tensor_hash(tensor()),
        action="resolve_obligation", subject="confirm_activation_range",
    )
    cp = tmp_path / "correction.json"; cp.write_text(encode_semantic_correction(correction), encoding="utf-8")
    assert load_semantic_tensor(tensor()) is tensor() or load_semantic_tensor(tensor()) == tensor()
    assert load_semantic_tensor(tensor_path) == tensor()
    assert len(load_semantic_bridge_templates(templates_path)) == 2
    assert load_semantic_correction(cp) == correction

import json
from dataclasses import replace

from nova_core import Graph, Module, Node, Project, Shape, TensorType, encode_project


def make_project():
    t = TensorType("f32", Shape((4,)))
    graph = Graph(
        id="main",
        inputs=("x",),
        outputs=("c",),
        nodes=(
            Node(id="n1", kind="Add", inputs=("x", "x"), outputs=("a",), value_type=t),
            Node(id="n2", kind="Multiply", inputs=("a", "a"), outputs=("b",), value_type=t),
            Node(id="n3", kind="Add", inputs=("b", "b"), outputs=("c",), value_type=t),
        ),
    )
    return Project(modules=(Module(id="app", graphs=(graph,)),)), {"x": t}


def test_memory_plan_codec_roundtrip_keeps_hash():
    from nova_core import decode_memory_plan, encode_memory_plan, memory_plan_hash, plan_memory

    project, facts = make_project()
    graph = project.modules[0].graphs[0]
    plan = plan_memory(graph, facts)
    restored = decode_memory_plan(encode_memory_plan(plan))
    assert memory_plan_hash(restored) == memory_plan_hash(plan)
    assert restored.to_record() == plan.to_record()


def test_project_resource_api_plans_and_verifies():
    from nova_core import VerificationStatus, plan_project_memory, verify_project_memory_plan

    project, facts = make_project()
    plan = plan_project_memory(project, "app", "main", facts)
    report = verify_project_memory_plan(project, "app", "main", plan, facts)
    assert plan.peak_reserved_bytes == 32
    assert report.status is VerificationStatus.SAFE


def test_cli_resource_plan_and_verify_emit_machine_json(tmp_path, capsys):
    from nova_core.cli import main

    project, facts = make_project()
    program = tmp_path / "program.json"
    types = tmp_path / "types.json"
    plan_file = tmp_path / "plan.json"
    program.write_text(encode_project(project), encoding="utf-8")
    types.write_text(json.dumps({name: value.to_record() for name, value in facts.items()}), encoding="utf-8")

    assert main(["resource-plan", str(program), "--types", str(types), "--mode", "optimized"]) == 0
    planned = json.loads(capsys.readouterr().out)
    assert planned["ok"] is True
    assert planned["plan"]["peak_reserved_bytes"] == 32
    plan_file.write_text(json.dumps(planned["plan"]), encoding="utf-8")

    assert main(["resource-verify", str(program), str(plan_file), "--types", str(types)]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified["verification"]["status"] == "safe"


def test_cli_resource_select_falls_back_for_forged_ai_plan(tmp_path, capsys):
    from nova_core import encode_memory_plan, plan_memory
    from nova_core.cli import main

    project, facts = make_project()
    graph = project.modules[0].graphs[0]
    program = tmp_path / "program.json"
    types = tmp_path / "types.json"
    plan_file = tmp_path / "ai-plan.json"
    program.write_text(encode_project(project), encoding="utf-8")
    types.write_text(json.dumps({name: value.to_record() for name, value in facts.items()}), encoding="utf-8")

    candidate = plan_memory(graph, facts, proposer="ai", confidence=0.99)
    forged = replace(candidate, peak_reserved_bytes=1, verification_mode="external")
    plan_file.write_text(encode_memory_plan(forged), encoding="utf-8")

    assert main(["resource-select", str(program), str(plan_file), "--types", str(types)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["selection"]["fallback_used"] is True
    assert payload["selection"]["candidate_verification"]["status"] == "unsafe"
    assert payload["selected_plan"]["verification_mode"] == "conservative"
    assert payload["selected_plan"]["peak_reserved_bytes"] == 48


def test_symbol_type_json_decoder_requires_tensor_type_records():
    import pytest
    from nova_core import ResourcePlanningError, decode_symbol_types

    good = {"x": TensorType("f32", Shape((4,))).to_record()}
    decoded = decode_symbol_types(good)
    assert decoded["x"] == TensorType("f32", Shape((4,)))
    with pytest.raises(ResourcePlanningError):
        decode_symbol_types({"x": {"kind": "not_tensor"}})

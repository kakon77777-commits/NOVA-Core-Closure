from __future__ import annotations

import json
from pathlib import Path

from nova_core import Graph, GraphPatch, Module, Node, Project, record_hash, semantic_hash
from nova_core.ai_build import AIProvenance, AISandboxPolicy, AIBuildRequest, BuildConstraint, BuildStatus, encode_ai_build_request
from nova_core.api import audit_project_ai_build, commit_project_ai_build, preview_project_ai_build
from nova_core.cli import main
from nova_core.codec import encode_project, decode_project


def base_project() -> Project:
    graph = Graph(id="main", inputs=("x",), outputs=("y",), nodes=(Node(id="op", kind="Identity", inputs=("x",), outputs=("y",)),))
    return Project(modules=(Module(id="app", graphs=(graph,)),))


def valid_request(project: Project) -> AIBuildRequest:
    patch = GraphPatch(
        base_hash=semantic_hash(project), base_record_hash=record_hash(project),
        module_id="app", graph_id="main",
        replaced_nodes=(Node(id="op", kind="Relu", inputs=("x",), outputs=("y",)),),
        rationale="AI replace Identity with Relu",
    )
    return AIBuildRequest(
        provenance=AIProvenance(request_id="api-r1", actor_id="agent-api"),
        patch=patch,
        constraints=(BuildConstraint(kind="require_node_kind", subject="op", expected="Relu"),),
        sandbox=AISandboxPolicy(allowed_node_kinds=("Identity","Relu"), max_replaced_nodes=1),
    )


def test_project_api_preview_audit_commit():
    project = base_project()
    request = valid_request(project)
    candidate = preview_project_ai_build(project, request)
    assert candidate.status is BuildStatus.READY
    audit = audit_project_ai_build(project, request)
    assert audit["status"] == "ready"
    committed = commit_project_ai_build(project, request)
    assert committed.after_semantic_hash == candidate.candidate_semantic_hash
    assert record_hash(project) != committed.after_record_hash


def test_cli_preview_audit_commit_and_input_immutability(tmp_path, capsys):
    project = base_project()
    request = valid_request(project)
    program = tmp_path / "program.json"
    request_file = tmp_path / "request.json"
    output = tmp_path / "output.json"
    program.write_text(encode_project(project), encoding="utf-8")
    request_file.write_text(encode_ai_build_request(request), encoding="utf-8")
    before = program.read_bytes()

    assert main(["ai-build-preview", str(program), str(request_file)]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["status"] == "ready"

    assert main(["ai-build-audit", str(program), str(request_file)]) == 0
    audit = json.loads(capsys.readouterr().out)
    assert audit["status"] == "ready"
    assert audit["request"]["request_id"] == "api-r1"

    assert main(["ai-build-commit", str(program), str(request_file), "--output", str(output)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert program.read_bytes() == before
    changed = decode_project(output.read_text(encoding="utf-8"))
    assert semantic_hash(changed) == payload["after_semantic_hash"]


def test_cli_commit_refuses_overwrite_input(tmp_path, capsys):
    project = base_project()
    request = valid_request(project)
    program = tmp_path / "program.json"
    request_file = tmp_path / "request.json"
    program.write_text(encode_project(project), encoding="utf-8")
    request_file.write_text(encode_ai_build_request(request), encoding="utf-8")
    assert main(["ai-build-commit", str(program), str(request_file), "--output", str(program)]) == 1
    error = json.loads(capsys.readouterr().err)
    assert error["error"]["category"] == "AIBuildError"


def test_cli_rejected_sandbox_request_returns_preview_not_commit(tmp_path, capsys):
    project = base_project()
    request = valid_request(project)
    rejected = AIBuildRequest(
        provenance=request.provenance, patch=request.patch, constraints=request.constraints,
        sandbox=AISandboxPolicy(max_replaced_nodes=0),
    )
    program = tmp_path / "program.json"
    request_file = tmp_path / "request.json"
    output = tmp_path / "output.json"
    program.write_text(encode_project(project), encoding="utf-8")
    request_file.write_text(encode_ai_build_request(rejected), encoding="utf-8")
    assert main(["ai-build-preview", str(program), str(request_file)]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["status"] == "rejected"
    assert main(["ai-build-commit", str(program), str(request_file), "--output", str(output)]) == 1
    assert not output.exists()

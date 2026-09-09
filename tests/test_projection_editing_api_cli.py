import json
from pathlib import Path

from nova_core import Graph, Module, Node, Project, encode_project, record_hash, semantic_hash
from nova_core.api import diff_project_graphs, preview_structured_edit
from nova_core.audit import project_audit_view, project_error_view
from nova_core.cli import main
from nova_core.errors import ProjectionEditError
from nova_core.projection import project_editable_text


def project(kind="Add") -> Project:
    return Project(modules=(Module(id="app", graphs=(Graph(id="main", inputs=("x", "b"), outputs=("y",), nodes=(Node(id="op", kind=kind, inputs=("x", "b"), outputs=("y",)),)),)),))


def write_project(path: Path, value: Project) -> None:
    path.write_text(encode_project(value), encoding="utf-8")


def edited_text(value: Project, kind="Multiply") -> str:
    payload = json.loads(project_editable_text(value.modules[0].graphs[0]))
    payload["nodes"][0]["kind"] = kind
    return json.dumps(payload)


def test_api_diff_and_preview_expose_candidate_without_mutation():
    base = project("Add")
    target = project("Multiply")
    diff = diff_project_graphs(base, target, "app", "main")
    assert diff.semantic_changed is True
    before = record_hash(base)
    candidate = preview_structured_edit(base, "app", "main", edited_text(base))
    assert record_hash(base) == before
    audit = project_audit_view(candidate)
    assert audit["validation"] == "passed"
    assert audit["semantic_changed"] is True
    assert audit["patch"]["replaced_nodes"] == ["op"]


def test_error_view_uses_typed_error_payload():
    error = ProjectionEditError("bad edit", context={"reason": "test"})
    view = project_error_view(error)
    assert view["category"] == "ProjectionEditError"
    assert view["message"] == "bad edit"
    assert view["context"]["reason"] == "test"
    assert "summary" in view


def test_cli_project_graph_and_editable_views(tmp_path, capsys):
    program = tmp_path / "program.json"
    write_project(program, project())
    assert main(["project", str(program), "--view", "graph"]) == 0
    graph_payload = json.loads(capsys.readouterr().out)
    assert graph_payload["semantic_hash"] == semantic_hash(project().modules[0].graphs[0])
    assert main(["project", str(program), "--view", "editable"]) == 0
    editable = capsys.readouterr().out
    assert json.loads(editable)["id"] == "main"


def test_cli_diff_and_edit_preview(tmp_path, capsys):
    base_path = tmp_path / "base.json"
    target_path = tmp_path / "target.json"
    edited_path = tmp_path / "edited.json"
    base = project("Add")
    write_project(base_path, base)
    write_project(target_path, project("Multiply"))
    edited_path.write_text(edited_text(base), encoding="utf-8")

    assert main(["diff", str(base_path), str(target_path), "--module", "app", "--graph", "main"]) == 0
    diff_payload = json.loads(capsys.readouterr().out)
    assert diff_payload["semantic_changed"] is True
    assert main(["edit-preview", str(base_path), "--edited", str(edited_path), "--module", "app", "--graph", "main"]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["validation"] == "passed"
    assert preview["patch"]["replaced_nodes"] == ["op"]


def test_cli_edit_commit_writes_new_project_without_overwriting_input(tmp_path, capsys):
    base_path = tmp_path / "base.json"
    edited_path = tmp_path / "edited.json"
    output_path = tmp_path / "committed.json"
    base = project("Add")
    write_project(base_path, base)
    original = base_path.read_bytes()
    edited_path.write_text(edited_text(base, "Subtract"), encoding="utf-8")

    assert main(["edit-commit", str(base_path), "--edited", str(edited_path), "--output", str(output_path), "--module", "app", "--graph", "main"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert output_path.exists()
    assert base_path.read_bytes() == original
    committed = json.loads(output_path.read_text(encoding="utf-8"))
    assert committed["modules"][0]["graphs"][0]["nodes"][0]["kind"] == "Subtract"


def test_cli_edit_commit_rejects_overwriting_input(tmp_path, capsys):
    base_path = tmp_path / "base.json"
    edited_path = tmp_path / "edited.json"
    base = project()
    write_project(base_path, base)
    edited_path.write_text(edited_text(base), encoding="utf-8")
    assert main(["edit-commit", str(base_path), "--edited", str(edited_path), "--output", str(base_path)]) == 1
    error = json.loads(capsys.readouterr().err)
    assert error["error"]["category"] == "ProjectionEditError"

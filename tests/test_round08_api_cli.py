import json
from pathlib import Path

import numpy as np

from nova_core import (
    AddNodeEdit,
    Graph,
    Module,
    Node,
    Project,
    SetGraphOutputsEdit,
    encode_project,
)
from nova_core.api import preview_formula_edit_project, preview_node_graph_edit_project, run_project_notebook
from nova_core.cli import main
from nova_core.notebook import CellOutput, ExternalInput, Notebook, NotebookCell


def base_project() -> Project:
    return Project(
        modules=(
            Module(
                id="app",
                graphs=(
                    Graph(
                        id="main",
                        inputs=("x", "b"),
                        outputs=("y",),
                        nodes=(Node(id="op", kind="Add", inputs=("x", "b"), outputs=("y",)),),
                    ),
                ),
            ),
        )
    )


def write_project(path: Path, project: Project) -> None:
    path.write_text(encode_project(project), encoding="utf-8")


def test_api_wrappers_accept_project_sources_for_node_formula_and_notebook(tmp_path):
    program = tmp_path / "program.json"
    write_project(program, base_project())
    node_candidate = preview_node_graph_edit_project(
        program,
        "app",
        "main",
        (
            AddNodeEdit(Node(id="relu", kind="Relu", inputs=("y",), outputs=("z",))),
            SetGraphOutputsEdit(("z",)),
        ),
    )
    assert node_candidate.candidate_semantic_hash != node_candidate.before_semantic_hash

    formula_candidate = preview_formula_edit_project(program, "app", "main", "op", "y = x - b")
    assert formula_candidate.candidate_project.modules[0].graphs[0].nodes[0].kind == "Subtract"

    nb = Notebook(cells=(NotebookCell(id="c1", module_id="app", graph_id="main", bindings={"x": ExternalInput("x"), "b": ExternalInput("b")}),))
    result = run_project_notebook(program, nb, {"x": np.array([1.0]), "b": np.array([2.0])}, backend="numpy")
    np.testing.assert_allclose(result.cells[0].outputs["y"], [3.0])


def test_cli_node_edit_preview_and_commit(tmp_path, capsys):
    program = tmp_path / "program.json"
    ops = tmp_path / "ops.json"
    output = tmp_path / "node-committed.json"
    write_project(program, base_project())
    ops.write_text(json.dumps([
        {"op": "add_node", "node": {"id": "relu", "kind": "Relu", "inputs": ["y"], "outputs": ["z"]}},
        {"op": "set_graph_outputs", "outputs": ["z"]},
    ]), encoding="utf-8")
    assert main(["node-edit-preview", str(program), "--ops", str(ops)]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["validation"] == "passed"
    assert preview["patch"]["added_nodes"] == ["relu"]
    assert main(["node-edit-commit", str(program), "--ops", str(ops), "--output", str(output)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert json.loads(output.read_text(encoding="utf-8"))["modules"][0]["graphs"][0]["outputs"] == ["z"]


def test_cli_formula_edit_preview_and_commit(tmp_path, capsys):
    program = tmp_path / "program.json"
    output = tmp_path / "formula-committed.json"
    write_project(program, base_project())
    assert main(["formula-edit-preview", str(program), "--node", "op", "--formula", "y = x * b"]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["patch"]["replaced_nodes"] == ["op"]
    assert main(["formula-edit-commit", str(program), "--node", "op", "--formula", "y = x / b", "--output", str(output)]) == 0
    capsys.readouterr()
    assert json.loads(output.read_text(encoding="utf-8"))["modules"][0]["graphs"][0]["nodes"][0]["kind"] == "Divide"


def test_cli_edit_commit_variants_refuse_to_overwrite_source(tmp_path, capsys):
    program = tmp_path / "program.json"
    ops = tmp_path / "ops.json"
    write_project(program, base_project())
    ops.write_text(json.dumps([{"op": "set_node_inputs", "node_id": "op", "inputs": ["b", "x"]}]), encoding="utf-8")
    assert main(["node-edit-commit", str(program), "--ops", str(ops), "--output", str(program)]) == 1
    err = json.loads(capsys.readouterr().err)
    assert err["error"]["category"] == "ProjectionEditError"
    assert main(["formula-edit-commit", str(program), "--node", "op", "--formula", "y = x - b", "--output", str(program)]) == 1
    err = json.loads(capsys.readouterr().err)
    assert err["error"]["category"] == "ProjectionEditError"


def test_cli_notebook_run_returns_cell_evidence(tmp_path, capsys):
    g1 = Graph(id="add", inputs=("x", "b"), outputs=("y",), nodes=(Node(id="add", kind="Add", inputs=("x", "b"), outputs=("y",)),))
    g2 = Graph(id="relu", inputs=("y",), outputs=("z",), nodes=(Node(id="relu", kind="Relu", inputs=("y",), outputs=("z",)),))
    p = Project(modules=(Module(id="app", graphs=(g1, g2)),))
    program = tmp_path / "program.json"
    nb_path = tmp_path / "notebook.json"
    inputs = tmp_path / "inputs.json"
    write_project(program, p)
    nb_path.write_text(json.dumps({
        "version":"0.1",
        "cells":[
            {"id":"c1","module_id":"app","graph_id":"add","bindings":{"x":{"kind":"external","name":"x"},"b":{"kind":"external","name":"b"}}},
            {"id":"c2","module_id":"app","graph_id":"relu","bindings":{"y":{"kind":"cell_output","cell_id":"c1","output":"y"}}},
        ],
    }), encoding="utf-8")
    inputs.write_text(json.dumps({"x":[-1.0,2.0],"b":[0.5,0.5]}), encoding="utf-8")
    assert main(["notebook-run", str(program), "--notebook", str(nb_path), "--inputs", str(inputs), "--backend", "numpy"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["cells"][-1]["outputs"]["z"] == [0.0, 2.5]
    assert payload["cells"][-1]["dependency_cells"] == ["c1"]
    assert payload["cells"][-1]["output_digest"].startswith("sha256:")

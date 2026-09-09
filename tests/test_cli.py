import json

from nova_core import Graph, Module, Node, Project
from nova_core.cli import main
from nova_core.codec import encode_project


def write_program(tmp_path):
    project = Project(modules=(Module(id="app", graphs=(Graph(
        id="main",
        inputs=("X", "W", "b"),
        outputs=("Y",),
        nodes=(
            Node(id="mm", kind="MatMul", inputs=("X", "W"), outputs=("XW",)),
            Node(id="add", kind="Add", inputs=("XW", "b"), outputs=("Y",)),
        ),
    ),)),))
    path = tmp_path / "linear.json"
    path.write_text(encode_project(project), encoding="utf-8")
    return path


def test_cli_check_and_hash(tmp_path, capsys):
    path = write_program(tmp_path)
    assert main(["check", str(path)]) == 0
    checked = json.loads(capsys.readouterr().out)
    assert checked["ok"] is True
    assert checked["semantic_hash"].startswith("sha256:")

    assert main(["hash", str(path)]) == 0
    hashed = json.loads(capsys.readouterr().out)
    assert hashed["semantic_hash"] == checked["semantic_hash"]


def test_cli_run_numpy_backend(tmp_path, capsys):
    path = write_program(tmp_path)
    inputs = tmp_path / "inputs.json"
    inputs.write_text(json.dumps({"X": [[1.0, 2.0]], "W": [[2.0], [3.0]], "b": [0.5]}), encoding="utf-8")
    assert main(["run", str(path), "--module", "app", "--graph", "main", "--inputs", str(inputs), "--backend", "numpy"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["outputs"]["Y"] == [[8.5]]


def test_cli_project_text_and_formula(tmp_path, capsys):
    path = write_program(tmp_path)
    assert main(["project", str(path), "--module", "app", "--graph", "main", "--view", "text"]) == 0
    text = capsys.readouterr().out
    assert "XW = matmul(X, W)" in text

    assert main(["project", str(path), "--module", "app", "--graph", "main", "--view", "formula"]) == 0
    formula = capsys.readouterr().out.strip()
    assert formula == "Y = (X \\cdot W) + b"

from __future__ import annotations

import json

import numpy as np

from nova_core import Graph, Module, Node, Project, TensorType
from nova_core.api import train_project
from nova_core.cli import main
from nova_core.codec import encode_project
from nova_core.training import TrainingConfig


def trainable_project() -> Project:
    graph = Graph(
        id="main",
        inputs=("T",),
        outputs=("loss",),
        nodes=(
            Node(id="w", kind="Parameter", outputs=("w",), attributes={"name": "weight"}),
            Node(id="err", kind="Subtract", inputs=("w", "T"), outputs=("e",)),
            Node(id="sq", kind="Multiply", inputs=("e", "e"), outputs=("e2",)),
            Node(id="loss", kind="Mean", inputs=("e2",), outputs=("loss",), attributes={"axis": None}, value_type=TensorType.scalar("f64")),
        ),
    )
    return Project(modules=(Module(id="app", graphs=(graph,)),))


def test_train_project_api_returns_deterministic_training_result() -> None:
    config = TrainingConfig(target="loss", wrt=("w",), steps=10, learning_rate=0.2)
    result = train_project(
        trainable_project(),
        "app",
        "main",
        {"T": np.array(3.0)},
        {"weight": np.array(0.0)},
        config,
    )
    assert result.initial_loss == 9.0
    assert result.final_loss < 1e-3
    assert result.state.step == 10
    assert result.derivative_semantic_hash.startswith("sha256:")


def test_cli_train_outputs_structured_training_summary(tmp_path, capsys) -> None:
    program = tmp_path / "program.json"
    program.write_text(encode_project(trainable_project()), encoding="utf-8")
    inputs = tmp_path / "inputs.json"
    inputs.write_text(json.dumps({"T": 3.0}), encoding="utf-8")
    parameters = tmp_path / "parameters.json"
    parameters.write_text(json.dumps({"weight": 0.0}), encoding="utf-8")

    rc = main([
        "train", str(program),
        "--module", "app",
        "--graph", "main",
        "--target", "loss",
        "--wrt", "w",
        "--inputs", str(inputs),
        "--parameters", str(parameters),
        "--steps", "10",
        "--learning-rate", "0.2",
        "--backend", "numpy",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["initial_loss"] == 9.0
    assert payload["final_loss"] < 1e-3
    assert len(payload["loss_history"]) == 11
    assert payload["final_parameters"]["weight"] != 0.0
    assert payload["parameter_state_hash"].startswith("sha256:")
    assert payload["graph_semantic_hash"].startswith("sha256:")
    assert payload["derivative_semantic_hash"].startswith("sha256:")

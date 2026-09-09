from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from nova_core import Graph, Node, TensorType
from nova_core.api import run_graph
from nova_core.canonical import semantic_hash
from nova_core.training import TrainingConfig, train_graph


def linear_graph() -> Graph:
    return Graph(
        id="linear_regression",
        inputs=("X", "T"),
        outputs=("loss",),
        nodes=(
            Node(id="W", kind="Parameter", outputs=("W",)),
            Node(id="b", kind="Parameter", outputs=("b",)),
            Node(id="mm", kind="MatMul", inputs=("X", "W"), outputs=("XW",)),
            Node(id="add", kind="Add", inputs=("XW", "b"), outputs=("Y",)),
            Node(id="err", kind="Subtract", inputs=("Y", "T"), outputs=("E",)),
            Node(id="sq", kind="Multiply", inputs=("E", "E"), outputs=("E2",)),
            Node(id="loss", kind="Mean", inputs=("E2",), outputs=("loss",), attributes={"axis": None}, value_type=TensorType.scalar("f64")),
        ),
    )


def mlp_graph() -> Graph:
    return Graph(
        id="mlp",
        inputs=("X", "T"),
        outputs=("loss",),
        nodes=(
            Node(id="W1", kind="Parameter", outputs=("W1",)),
            Node(id="b1", kind="Parameter", outputs=("b1",)),
            Node(id="W2", kind="Parameter", outputs=("W2",)),
            Node(id="b2", kind="Parameter", outputs=("b2",)),
            Node(id="mm1", kind="MatMul", inputs=("X", "W1"), outputs=("Z1",)),
            Node(id="add1", kind="Add", inputs=("Z1", "b1"), outputs=("P1",)),
            Node(id="tanh", kind="Tanh", inputs=("P1",), outputs=("H",)),
            Node(id="mm2", kind="MatMul", inputs=("H", "W2"), outputs=("Z2",)),
            Node(id="add2", kind="Add", inputs=("Z2", "b2"), outputs=("Y",)),
            Node(id="err", kind="Subtract", inputs=("Y", "T"), outputs=("E",)),
            Node(id="sq", kind="Multiply", inputs=("E", "E"), outputs=("E2",)),
            Node(id="loss", kind="Mean", inputs=("E2",), outputs=("loss",), attributes={"axis": None}, value_type=TensorType.scalar("f64")),
        ),
    )


def linear_data():
    x = np.array([[0., 0.], [1., 0.], [0., 1.], [1., 1.], [2., -1.], [-1., 2.]])
    target = x @ np.array([[2.], [-1.]]) + 0.5
    params = {"W": np.zeros((2, 1)), "b": np.zeros((1,))}
    return {"X": x, "T": target}, params


def mlp_data():
    x = np.array([[-2.], [-1.5], [-1.], [-0.5], [0.], [0.5], [1.], [1.5], [2.]])
    teacher = {
        "W1": np.array([[1., -0.8, 0.5]]),
        "b1": np.array([0.2, -0.1, 0.3]),
        "W2": np.array([[1.2], [-0.7], [0.5]]),
        "b2": np.array([0.1]),
    }
    target = np.tanh(x @ teacher["W1"] + teacher["b1"]) @ teacher["W2"] + teacher["b2"]
    params = {
        "W1": np.array([[0.2, 0.4, -0.3]]),
        "b1": np.array([0., 0.1, -0.1]),
        "W2": np.array([[0.3], [-0.2], [0.1]]),
        "b2": np.array([0.0]),
    }
    return {"X": x, "T": target}, params


def test_linear_regression_closes_execution_and_training_gate() -> None:
    graph = linear_graph()
    inputs, params = linear_data()
    before = semantic_hash(graph)
    interpreter = run_graph(graph, inputs, parameters=params, backend="interpreter").outputs["loss"]
    numpy_loss = run_graph(graph, inputs, parameters=params, backend="numpy").outputs["loss"]
    np.testing.assert_allclose(interpreter, numpy_loss, rtol=0, atol=0)
    trained = train_graph(
        graph, inputs, params,
        TrainingConfig(target="loss", wrt=("W", "b"), steps=60, learning_rate=0.2),
    )
    assert trained.final_loss < trained.initial_loss * 0.01
    assert semantic_hash(graph) == before


def test_mlp_closes_training_gate_with_deterministic_replay() -> None:
    graph = mlp_graph()
    inputs, params = mlp_data()
    config = TrainingConfig(target="loss", wrt=("W1", "b1", "W2", "b2"), steps=100, learning_rate=0.05)
    first = train_graph(graph, inputs, params, config)
    second = train_graph(graph, inputs, params, config)
    assert first.final_loss < first.initial_loss * 0.001
    assert first.state.loss_history == second.state.loss_history
    assert first.state.parameter_state_hash == second.state.parameter_state_hash

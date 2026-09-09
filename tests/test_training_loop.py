from __future__ import annotations

import numpy as np
import pytest

from nova_core.canonical import semantic_hash
from nova_core.errors import TrainingError
from nova_core.model import Graph, Node
from nova_core.training import TrainingConfig, train_graph


def quadratic_graph() -> Graph:
    return Graph(
        id="quadratic_train",
        inputs=("T",),
        outputs=("loss",),
        nodes=(
            Node(id="w", kind="Parameter", outputs=("w",), differentiation_type="Differentiable"),
            Node(id="err", kind="Subtract", inputs=("w", "T"), outputs=("e",), differentiation_type="Differentiable"),
            Node(id="sq", kind="Multiply", inputs=("e", "e"), outputs=("e2",), differentiation_type="Differentiable"),
            Node(id="loss", kind="Mean", inputs=("e2",), outputs=("loss",), attributes={"axis": None}, differentiation_type="Differentiable"),
        ),
    )


def test_train_graph_reduces_scalar_loss_and_preserves_graph_identity() -> None:
    graph = quadratic_graph()
    before = semantic_hash(graph)
    initial = {"w": np.array(0.0)}
    result = train_graph(
        graph,
        {"T": np.array(3.0)},
        initial,
        TrainingConfig(target="loss", wrt=("w",), steps=12, learning_rate=0.2),
    )
    assert result.initial_loss == pytest.approx(9.0)
    assert result.final_loss < 1e-4
    assert len(result.state.loss_history) == 13
    assert len(result.records) == 12
    assert result.state.step == 12
    assert semantic_hash(graph) == before == result.state.graph_semantic_hash
    assert np.array_equal(initial["w"], np.array(0.0))
    assert result.state.parameters["w"].flags.writeable is False


def test_training_replay_is_deterministic() -> None:
    graph = quadratic_graph()
    config = TrainingConfig(target="loss", wrt=("w",), steps=8, learning_rate=0.1)
    a = train_graph(graph, {"T": np.array(2.0)}, {"w": np.array(-1.0)}, config)
    b = train_graph(graph, {"T": np.array(2.0)}, {"w": np.array(-1.0)}, config)
    assert a.state.loss_history == b.state.loss_history
    assert a.state.parameter_state_hash == b.state.parameter_state_hash
    assert a.derivative_graph_id == b.derivative_graph_id
    assert a.derivative_semantic_hash == b.derivative_semantic_hash


def test_training_records_state_hash_transition_and_gradient_norm() -> None:
    result = train_graph(
        quadratic_graph(),
        {"T": np.array(1.0)},
        {"w": np.array(0.0)},
        TrainingConfig(target="loss", wrt=("w",), steps=1, learning_rate=0.25),
    )
    record = result.records[0]
    assert record.step == 1
    assert record.loss_before == pytest.approx(1.0)
    assert record.loss_after == pytest.approx(0.25)
    assert record.gradient_l2_norm == pytest.approx(2.0)
    assert record.parameter_state_hash_before != record.parameter_state_hash_after


def test_train_graph_rejects_non_parameter_optimizer_target() -> None:
    graph = quadratic_graph()
    with pytest.raises(TrainingError, match="not a Parameter output"):
        train_graph(
            graph,
            {"T": np.array(1.0)},
            {"w": np.array(0.0)},
            TrainingConfig(target="loss", wrt=("e",), steps=1, learning_rate=0.1),
        )


def test_train_graph_rejects_missing_parameter_binding() -> None:
    with pytest.raises(TrainingError, match="missing runtime parameter binding"):
        train_graph(
            quadratic_graph(),
            {"T": np.array(1.0)},
            {},
            TrainingConfig(target="loss", wrt=("w",), steps=1, learning_rate=0.1),
        )


def test_train_graph_requires_target_to_be_graph_output() -> None:
    with pytest.raises(TrainingError, match="training target must be a graph output"):
        train_graph(
            quadratic_graph(),
            {"T": np.array(1.0)},
            {"w": np.array(0.0)},
            TrainingConfig(target="e2", wrt=("w",), steps=1, learning_rate=0.1),
        )

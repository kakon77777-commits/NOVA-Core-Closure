from __future__ import annotations

import math

import numpy as np
import pytest

from nova_core.errors import TrainingError
from nova_core.model import Graph, Node
from nova_core.training import (
    TrainingConfig,
    TrainingState,
    parameter_bindings,
    parameter_state_hash,
    sgd_update,
)


def _graph() -> Graph:
    return Graph(
        id="trainable",
        inputs=("X",),
        outputs=("Y",),
        nodes=(
            Node(id="w", kind="Parameter", outputs=("W",), attributes={"name": "weight"}),
            Node(id="b", kind="Parameter", outputs=("b",)),
            Node(id="mm", kind="MatMul", inputs=("X", "W"), outputs=("XW",)),
            Node(id="add", kind="Add", inputs=("XW", "b"), outputs=("Y",)),
        ),
    )


def test_parameter_bindings_map_canonical_symbols_to_runtime_names() -> None:
    assert parameter_bindings(_graph()) == {"W": "weight", "b": "b"}


def test_parameter_bindings_reject_invalid_parameter_node_shape() -> None:
    graph = Graph(
        id="bad",
        outputs=("x",),
        nodes=(Node(id="p", kind="Parameter", outputs=("x", "y")),),
    )
    with pytest.raises(TrainingError, match="exactly one output"):
        parameter_bindings(graph)


def test_training_config_validates_bounded_reference_sgd_contract() -> None:
    config = TrainingConfig(target="loss", wrt=("W", "b"), steps=10, learning_rate=0.1)
    assert config.backend == "numpy"
    assert config.wrt == ("W", "b")

    for kwargs in (
        {"steps": 0, "learning_rate": 0.1},
        {"steps": -1, "learning_rate": 0.1},
        {"steps": 1, "learning_rate": 0.0},
        {"steps": 1, "learning_rate": -0.1},
        {"steps": 1, "learning_rate": float("nan")},
        {"steps": 1, "learning_rate": float("inf")},
    ):
        with pytest.raises(TrainingError):
            TrainingConfig(target="loss", wrt=("W",), **kwargs)


def test_training_state_copies_and_freezes_parameter_arrays() -> None:
    original = np.array([[1.0], [2.0]], dtype=np.float64)
    state = TrainingState(
        step=0,
        parameters={"weight": original},
        loss_history=(3.0,),
        graph_semantic_hash="sha256:graph",
    )
    frozen = state.parameters["weight"]
    assert np.array_equal(frozen, original)
    assert frozen is not original
    assert frozen.flags.writeable is False
    original[0, 0] = 99.0
    assert float(frozen[0, 0]) == 1.0
    with pytest.raises(ValueError):
        frozen[0, 0] = 5.0


def test_parameter_state_hash_is_deterministic_and_order_independent() -> None:
    a = {
        "W": np.array([[1.0, 2.0]], dtype=np.float64),
        "b": np.array([0.5], dtype=np.float64),
    }
    b = {"b": a["b"].copy(), "W": a["W"].copy()}
    assert parameter_state_hash(a) == parameter_state_hash(b)
    changed = {"W": np.array([[1.0, 3.0]]), "b": np.array([0.5])}
    assert parameter_state_hash(a) != parameter_state_hash(changed)


def test_sgd_update_returns_fresh_read_only_arrays_without_mutating_input() -> None:
    parameters = {
        "weight": np.array([[2.0], [3.0]], dtype=np.float64),
        "b": np.array([0.5], dtype=np.float64),
    }
    before_w = parameters["weight"].copy()
    before_b = parameters["b"].copy()
    gradients = {
        "W": np.array([[1.5], [3.0]], dtype=np.float64),
        "b": np.array([1.5], dtype=np.float64),
    }
    updated = sgd_update(
        parameters,
        gradients,
        {"W": "weight", "b": "b"},
        learning_rate=0.1,
    )
    assert np.allclose(updated["weight"], [[1.85], [2.7]])
    assert np.allclose(updated["b"], [0.35])
    assert np.array_equal(parameters["weight"], before_w)
    assert np.array_equal(parameters["b"], before_b)
    assert updated["weight"] is not parameters["weight"]
    assert updated["weight"].flags.writeable is False


def test_sgd_update_rejects_missing_nonfinite_and_shape_mismatched_gradient() -> None:
    parameters = {"weight": np.array([1.0, 2.0])}
    bindings = {"W": "weight"}
    with pytest.raises(TrainingError, match="missing gradient"):
        sgd_update(parameters, {}, bindings, learning_rate=0.1)
    with pytest.raises(TrainingError, match="shape mismatch"):
        sgd_update(parameters, {"W": np.array([[1.0, 2.0]])}, bindings, learning_rate=0.1)
    with pytest.raises(TrainingError, match="non-finite gradient"):
        sgd_update(parameters, {"W": np.array([math.inf, 0.0])}, bindings, learning_rate=0.1)

import numpy as np
import pytest

from nova_core import Graph, Node, Shape, TensorType
from nova_core.autodiff import DifferentiationRequest
from nova_core.errors import DiffError
from nova_core.gradcheck import check_gradient, finite_difference_gradient


def test_finite_difference_matches_scalar_square():
    graph = Graph(
        id="square",
        inputs=("x",),
        outputs=("loss",),
        nodes=(Node(id="sq", kind="Multiply", inputs=("x", "x"), outputs=("loss",), value_type=TensorType.scalar("f64")),),
    )
    numeric = finite_difference_gradient(graph, {"x": np.array(2.5)}, target="loss", wrt="x")
    np.testing.assert_allclose(numeric, 5.0, rtol=1e-6, atol=1e-7)


def test_gradient_check_passes_broadcast_bias():
    graph = Graph(
        id="bias",
        inputs=("X", "b"),
        outputs=("loss",),
        nodes=(
            Node(id="add", kind="Add", inputs=("X", "b"), outputs=("Y",), value_type=TensorType("f64", Shape.of(2, 3))),
            Node(id="sum", kind="ReduceSum", inputs=("Y",), outputs=("loss",), attributes={"axis": None}, value_type=TensorType.scalar("f64")),
        ),
    )
    result = check_gradient(
        graph,
        {"X": np.arange(6.0).reshape(2, 3), "b": np.array([0.2, -0.1, 0.5])},
        DifferentiationRequest(target="loss", wrt=("b",)),
    )
    assert result.passed
    np.testing.assert_allclose(result.analytic["b"], np.array([2.0, 2.0, 2.0]))
    np.testing.assert_allclose(result.numeric["b"], np.array([2.0, 2.0, 2.0]), rtol=1e-6, atol=1e-7)


def test_gradient_check_passes_matmul_for_input_and_parameter():
    graph = Graph(
        id="linear_param",
        inputs=("X",),
        outputs=("loss",),
        nodes=(
            Node(id="param", kind="Parameter", outputs=("W",), attributes={"name": "weight"}),
            Node(id="mm", kind="MatMul", inputs=("X", "W"), outputs=("Y",)),
            Node(id="mean", kind="Mean", inputs=("Y",), outputs=("loss",), attributes={"axis": None}, value_type=TensorType.scalar("f64")),
        ),
    )
    inputs = {"X": np.array([[1.0, 2.0], [3.0, -1.0]])}
    parameters = {"weight": np.array([[0.5, 1.25], [-2.0, 0.75]])}
    result = check_gradient(
        graph,
        inputs,
        DifferentiationRequest(target="loss", wrt=("X", "W")),
        parameters=parameters,
        rtol=2e-5,
        atol=2e-7,
    )
    assert result.passed
    assert result.max_abs_error["X"] < 1e-6
    assert result.max_abs_error["W"] < 1e-6


def test_gradient_check_passes_smooth_activation_chain():
    graph = Graph(
        id="activation",
        inputs=("x",),
        outputs=("loss",),
        nodes=(
            Node(id="sig", kind="Sigmoid", inputs=("x",), outputs=("s",)),
            Node(id="tanh", kind="Tanh", inputs=("s",), outputs=("t",)),
            Node(id="sum", kind="ReduceSum", inputs=("t",), outputs=("loss",), attributes={"axis": None}, value_type=TensorType.scalar("f64")),
        ),
    )
    result = check_gradient(
        graph,
        {"x": np.array([-0.7, 0.2, 1.1])},
        DifferentiationRequest(target="loss", wrt=("x",)),
        rtol=2e-5,
        atol=2e-7,
    )
    assert result.passed


def test_finite_difference_rejects_non_scalar_target():
    graph = Graph(
        id="vector",
        inputs=("x",),
        outputs=("y",),
        nodes=(Node(id="id", kind="Identity", inputs=("x",), outputs=("y",)),),
    )
    with pytest.raises(DiffError):
        finite_difference_gradient(graph, {"x": np.array([1.0, 2.0])}, target="y", wrt="x")


def test_finite_difference_rejects_non_leaf_wrt_symbol():
    graph = Graph(
        id="intermediate",
        inputs=("x",),
        outputs=("loss",),
        nodes=(
            Node(id="sq", kind="Multiply", inputs=("x", "x"), outputs=("mid",)),
            Node(id="sum", kind="ReduceSum", inputs=("mid",), outputs=("loss",), attributes={"axis": None}, value_type=TensorType.scalar("f64")),
        ),
    )
    with pytest.raises(DiffError):
        finite_difference_gradient(graph, {"x": np.array([1.0, 2.0])}, target="loss", wrt="mid")

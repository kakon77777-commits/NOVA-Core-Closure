import numpy as np

from nova_core import Graph, Node, Shape, TensorType
from nova_core.autodiff import DifferentiationRequest, differentiate_graph, gradient_symbol
from nova_core.backends.numpy_backend import NumPyBackend
from nova_core.interpreter import Interpreter


def _run_both(graph, request, inputs, *, parameters=None):
    derivative = differentiate_graph(graph, request).graph
    expected = Interpreter().run_graph(derivative, inputs, parameters=parameters or {}).outputs
    actual = NumPyBackend().run_graph(derivative, inputs, parameters=parameters or {}).outputs
    assert expected.keys() == actual.keys()
    for key in expected:
        np.testing.assert_allclose(actual[key], expected[key], rtol=1e-7, atol=1e-9)
    return actual


def test_square_gradient_executes_as_derivative_graph():
    graph = Graph(
        id="square",
        inputs=("x",),
        outputs=("loss",),
        nodes=(Node(id="sq", kind="Multiply", inputs=("x", "x"), outputs=("loss",), value_type=TensorType.scalar("f64")),),
    )
    outputs = _run_both(graph, DifferentiationRequest(target="loss", wrt=("x",)), {"x": np.array(3.0)})
    np.testing.assert_allclose(outputs[gradient_symbol("x")], 6.0)


def test_broadcast_bias_gradient_reduces_to_original_shape():
    graph = Graph(
        id="broadcast_bias",
        inputs=("X", "b"),
        outputs=("loss",),
        nodes=(
            Node(id="add", kind="Add", inputs=("X", "b"), outputs=("Y",), value_type=TensorType("f64", Shape.of(2, 3))),
            Node(id="sum", kind="ReduceSum", inputs=("Y",), outputs=("loss",), attributes={"axis": None}, value_type=TensorType.scalar("f64")),
        ),
    )
    inputs = {"X": np.arange(6.0).reshape(2, 3), "b": np.array([0.1, 0.2, 0.3])}
    outputs = _run_both(graph, DifferentiationRequest(target="loss", wrt=("b",)), inputs)
    np.testing.assert_allclose(outputs[gradient_symbol("b")], np.array([2.0, 2.0, 2.0]))


def test_matmul_gradient_executes_for_both_inputs():
    graph = Graph(
        id="matmul_loss",
        inputs=("X", "W"),
        outputs=("loss",),
        nodes=(
            Node(id="mm", kind="MatMul", inputs=("X", "W"), outputs=("Y",), value_type=TensorType("f64", Shape.of(2, 2))),
            Node(id="sum", kind="ReduceSum", inputs=("Y",), outputs=("loss",), attributes={"axis": None}, value_type=TensorType.scalar("f64")),
        ),
    )
    X = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    W = np.array([[0.5, 1.0], [1.5, -1.0], [2.0, 0.25]])
    outputs = _run_both(graph, DifferentiationRequest(target="loss", wrt=("X", "W")), {"X": X, "W": W})
    ones = np.ones((2, 2))
    np.testing.assert_allclose(outputs[gradient_symbol("X")], ones @ W.T)
    np.testing.assert_allclose(outputs[gradient_symbol("W")], X.T @ ones)


def test_reshape_transpose_mean_reverse_path_executes():
    graph = Graph(
        id="shape_reverse",
        inputs=("x",),
        outputs=("loss",),
        nodes=(
            Node(id="reshape", kind="Reshape", inputs=("x",), outputs=("r",), attributes={"shape": [3, 2]}),
            Node(id="transpose", kind="Transpose", inputs=("r",), outputs=("t",), attributes={"axes": [1, 0]}),
            Node(id="mean", kind="Mean", inputs=("t",), outputs=("loss",), attributes={"axis": None}, value_type=TensorType.scalar("f64")),
        ),
    )
    x = np.arange(6.0).reshape(2, 3)
    outputs = _run_both(graph, DifferentiationRequest(target="loss", wrt=("x",)), {"x": x})
    np.testing.assert_allclose(outputs[gradient_symbol("x")], np.full((2, 3), 1.0 / 6.0))


def test_relu_sigmoid_tanh_gradients_execute():
    x = np.array([-1.0, 0.5, 2.0])
    for kind, expected_local in (
        ("Relu", (x > 0).astype(float)),
        ("Sigmoid", None),
        ("Tanh", None),
    ):
        graph = Graph(
            id=f"{kind.lower()}_loss",
            inputs=("x",),
            outputs=("loss",),
            nodes=(
                Node(id="act", kind=kind, inputs=("x",), outputs=("y",)),
                Node(id="sum", kind="ReduceSum", inputs=("y",), outputs=("loss",), attributes={"axis": None}, value_type=TensorType.scalar("f64")),
            ),
        )
        outputs = _run_both(graph, DifferentiationRequest(target="loss", wrt=("x",)), {"x": x})
        if kind == "Sigmoid":
            y = 1.0 / (1.0 + np.exp(-x))
            expected_local = y * (1.0 - y)
        elif kind == "Tanh":
            y = np.tanh(x)
            expected_local = 1.0 - y * y
        np.testing.assert_allclose(outputs[gradient_symbol("x")], expected_local, rtol=1e-7, atol=1e-9)


def test_softmax_explicit_vjp_executes():
    graph = Graph(
        id="softmax",
        inputs=("x",),
        outputs=("y",),
        nodes=(Node(id="soft", kind="Softmax", inputs=("x",), outputs=("y",), attributes={"axis": -1}, value_type=TensorType("f64", Shape.of(3))),),
    )
    x = np.array([1.0, 2.0, -1.0])
    dy = np.array([0.5, -0.25, 2.0])
    outputs = _run_both(graph, DifferentiationRequest(target="y", wrt=("x",), seed_input="dy"), {"x": x, "dy": dy})
    shifted = x - np.max(x)
    y = np.exp(shifted) / np.sum(np.exp(shifted))
    expected = y * (dy - np.sum(dy * y))
    np.testing.assert_allclose(outputs[gradient_symbol("x")], expected, rtol=1e-7, atol=1e-9)


def test_stop_gradient_executes_as_zero_cotangent():
    graph = Graph(
        id="stop",
        inputs=("x",),
        outputs=("loss",),
        nodes=(
            Node(id="stop", kind="StopGradient", inputs=("x",), outputs=("s",)),
            Node(id="sq", kind="Multiply", inputs=("s", "s"), outputs=("loss",), value_type=TensorType.scalar("f64")),
        ),
    )
    outputs = _run_both(graph, DifferentiationRequest(target="loss", wrt=("x",)), {"x": np.array(4.0)})
    np.testing.assert_allclose(outputs[gradient_symbol("x")], 0.0)

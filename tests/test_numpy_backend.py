import numpy as np

from nova_core import Graph, Node
from nova_core.backends.numpy_backend import NumPyBackend
from nova_core.interpreter import Interpreter


def _assert_same(graph, inputs):
    expected = Interpreter().run_graph(graph, inputs).outputs
    actual = NumPyBackend().run_graph(graph, inputs).outputs
    assert expected.keys() == actual.keys()
    for key in expected:
        np.testing.assert_allclose(actual[key], expected[key], rtol=1e-6, atol=1e-7)


def test_numpy_backend_matches_matmul_bias():
    graph = Graph(
        id="linear",
        inputs=("X", "W", "b"),
        outputs=("Y",),
        nodes=(
            Node(id="mm", kind="MatMul", inputs=("X", "W"), outputs=("XW",)),
            Node(id="add", kind="Add", inputs=("XW", "b"), outputs=("Y",)),
        ),
    )
    _assert_same(
        graph,
        {
            "X": np.arange(6, dtype=np.float32).reshape(2, 3),
            "W": np.arange(12, dtype=np.float32).reshape(3, 4),
            "b": np.arange(4, dtype=np.float32),
        },
    )


def test_numpy_backend_matches_reshape_transpose_reduce():
    graph = Graph(
        id="shape_ops",
        inputs=("x",),
        outputs=("out",),
        nodes=(
            Node(id="reshape", kind="Reshape", inputs=("x",), outputs=("r",), attributes={"shape": [2, 3]}),
            Node(id="transpose", kind="Transpose", inputs=("r",), outputs=("t",), attributes={"axes": [1, 0]}),
            Node(id="sum", kind="ReduceSum", inputs=("t",), outputs=("out",), attributes={"axis": 1}),
        ),
    )
    _assert_same(graph, {"x": np.arange(6, dtype=np.float32)})


def test_numpy_backend_matches_mean_and_activations():
    graph = Graph(
        id="activation",
        inputs=("x",),
        outputs=("mean", "sig", "tanh", "soft"),
        nodes=(
            Node(id="mean", kind="Mean", inputs=("x",), outputs=("mean",), attributes={"axis": 0}),
            Node(id="sig", kind="Sigmoid", inputs=("x",), outputs=("sig",)),
            Node(id="tanh", kind="Tanh", inputs=("x",), outputs=("tanh",)),
            Node(id="soft", kind="Softmax", inputs=("x",), outputs=("soft",), attributes={"axis": -1}),
        ),
    )
    _assert_same(graph, {"x": np.array([[1.0, -2.0, 3.0], [0.5, 0.25, -1.0]], dtype=np.float32)})


def test_numpy_backend_matches_control_flow_subset():
    graph = Graph(
        id="control",
        inputs=("cond", "a", "b", "step"),
        outputs=("out",),
        nodes=(
            Node(id="if", kind="If", inputs=("cond", "a", "b"), outputs=("selected",)),
            Node(id="loop", kind="BoundedLoop", inputs=("selected", "step"), outputs=("out",), attributes={"trip_count": 3, "body_kind": "Add"}),
        ),
    )
    _assert_same(graph, {"cond": True, "a": np.array([1.0, 2.0]), "b": np.array([9.0, 9.0]), "step": np.array([0.5, 1.0])})

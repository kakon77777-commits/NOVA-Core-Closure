import numpy as np
import pytest

from nova_core import Graph, Node, Shape, TensorType, semantic_hash
from nova_core.errors import DependencyError, UnsupportedOperationError
from nova_core.interpreter import Interpreter


def linear_graph():
    return Graph(
        id="linear",
        inputs=("X", "W", "b"),
        outputs=("Y",),
        nodes=(
            # Intentionally out of declaration order: scheduler must use dependencies.
            Node(id="add", kind="Add", inputs=("XW", "b"), outputs=("Y",), value_type=TensorType("f32", Shape.of("B", "O"))),
            Node(id="mm", kind="MatMul", inputs=("X", "W"), outputs=("XW",), value_type=TensorType("f32", Shape.of("B", "O"))),
        ),
    )


def test_interpreter_executes_linear_graph_and_preserves_hash():
    graph = linear_graph()
    before = semantic_hash(graph)
    X = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    W = np.array([[2.0], [1.0]], dtype=np.float32)
    b = np.array([0.5], dtype=np.float32)

    result = Interpreter().run_graph(graph, {"X": X, "W": W, "b": b})

    np.testing.assert_allclose(result.outputs["Y"], np.array([[4.5], [10.5]], dtype=np.float32))
    assert [r.node_id for r in result.trace.records] == ["mm", "add"]
    assert semantic_hash(graph) == before


def test_interpreter_pure_arithmetic_and_activations():
    graph = Graph(
        id="pure",
        inputs=("a", "b"),
        outputs=("z",),
        nodes=(
            Node(id="sub", kind="Subtract", inputs=("a", "b"), outputs=("d",)),
            Node(id="neg", kind="Negate", inputs=("d",), outputs=("n",)),
            Node(id="relu", kind="Relu", inputs=("n",), outputs=("z",)),
        ),
    )
    result = Interpreter().run_graph(graph, {"a": np.array([-2.0, 3.0]), "b": np.array([1.0, 1.0])})
    np.testing.assert_allclose(result.outputs["z"], np.array([3.0, 0.0]))


def test_interpreter_constant_and_parameter_nodes():
    graph = Graph(
        id="params",
        outputs=("y",),
        nodes=(
            Node(id="p", kind="Parameter", outputs=("pval",), attributes={"name": "p"}),
            Node(id="c", kind="Constant", outputs=("cval",), attributes={"value": 2.0}),
            Node(id="mul", kind="Multiply", inputs=("pval", "cval"), outputs=("y",)),
        ),
    )
    result = Interpreter().run_graph(graph, {}, parameters={"p": 4.0})
    assert result.outputs["y"] == 8.0


def test_interpreter_unsupported_node_is_typed_error():
    graph = Graph(id="bad", inputs=("x",), outputs=("y",), nodes=(Node(id="x1", kind="Magic", inputs=("x",), outputs=("y",)),))
    with pytest.raises(UnsupportedOperationError) as exc:
        Interpreter().run_graph(graph, {"x": 1})
    assert exc.value.to_dict()["source_nodes"] == ["x1"]


def test_interpreter_reports_dependency_deadlock():
    # Graph validation accepts the symbols because both are produced; runtime must reject the cycle.
    graph = Graph(
        id="cycle",
        outputs=("a",),
        nodes=(
            Node(id="a", kind="Identity", inputs=("b",), outputs=("a",)),
            Node(id="b", kind="Identity", inputs=("a",), outputs=("b",)),
        ),
    )
    with pytest.raises(DependencyError):
        Interpreter().run_graph(graph, {})


def test_interpreter_call_invokes_named_graph_as_pure_function():
    callee = Graph(
        id="double",
        inputs=("x",),
        outputs=("y",),
        nodes=(Node(id="mul", kind="Multiply", inputs=("x", "x"), outputs=("y",)),),
    )
    caller = Graph(
        id="caller",
        inputs=("v",),
        outputs=("out",),
        nodes=(Node(id="call", kind="Call", inputs=("v",), outputs=("out",), attributes={"callee": "double"}),),
    )
    result = Interpreter().run_graph(caller, {"v": 3}, graph_lookup={"double": callee})
    assert result.outputs["out"] == 9

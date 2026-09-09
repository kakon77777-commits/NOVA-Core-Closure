import numpy as np

from nova_core import Graph, Node
from nova_core.interpreter import Interpreter


def test_if_selects_then_or_else_value():
    graph = Graph(
        id="branch",
        inputs=("cond", "a", "b"),
        outputs=("out",),
        nodes=(Node(id="if1", kind="If", inputs=("cond", "a", "b"), outputs=("out",)),),
    )
    interp = Interpreter()
    assert interp.run_graph(graph, {"cond": True, "a": 10, "b": 20}).outputs["out"] == 10
    assert interp.run_graph(graph, {"cond": False, "a": 10, "b": 20}).outputs["out"] == 20


def test_bounded_loop_has_explicit_finite_trip_count():
    graph = Graph(
        id="loop",
        inputs=("start", "step"),
        outputs=("out",),
        nodes=(
            Node(
                id="loop1",
                kind="BoundedLoop",
                inputs=("start", "step"),
                outputs=("out",),
                attributes={"trip_count": 4, "body_kind": "Add"},
            ),
        ),
    )
    assert Interpreter().run_graph(graph, {"start": 1, "step": 3}).outputs["out"] == 13


def test_bounded_loop_supports_tensor_accumulator():
    graph = Graph(
        id="loop_tensor",
        inputs=("start", "step"),
        outputs=("out",),
        nodes=(
            Node(id="loop1", kind="BoundedLoop", inputs=("start", "step"), outputs=("out",), attributes={"trip_count": 2, "body_kind": "Multiply"}),
        ),
    )
    out = Interpreter().run_graph(graph, {"start": np.array([1.0, 2.0]), "step": np.array([3.0, 4.0])}).outputs["out"]
    np.testing.assert_allclose(out, np.array([9.0, 32.0]))

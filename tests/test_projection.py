import pytest

from nova_core import Graph, Node, Shape, TensorType, semantic_hash
from nova_core.errors import ProjectionError
from nova_core.projection import project_formula, project_text


def linear_graph(reverse=False):
    nodes = [
        Node(id="mm", kind="MatMul", inputs=("X", "W"), outputs=("XW",), value_type=TensorType("f32", Shape.of("B", "O"))),
        Node(id="add", kind="Add", inputs=("XW", "b"), outputs=("Y",), value_type=TensorType("f32", Shape.of("B", "O"))),
    ]
    if reverse:
        nodes.reverse()
    return Graph(id="linear", inputs=("X", "W", "b"), outputs=("Y",), nodes=tuple(nodes))


def test_structured_text_projection_is_deterministic_across_node_container_order():
    a = project_text(linear_graph(False))
    b = project_text(linear_graph(True))
    assert a == b
    assert "graph linear" in a
    assert "XW = matmul(X, W)" in a
    assert "Y = add(XW, b)" in a
    assert a.index("XW =") < a.index("Y =")


def test_formula_projection_linear_graph():
    formula = project_formula(linear_graph())
    assert formula == "Y = (X \\cdot W) + b"


def test_projection_does_not_change_semantic_hash():
    graph = linear_graph()
    before = semantic_hash(graph)
    project_text(graph)
    project_formula(graph)
    assert semantic_hash(graph) == before


def test_formula_projection_rejects_control_flow_instead_of_inventing_notation():
    graph = Graph(
        id="branch",
        inputs=("cond", "a", "b"),
        outputs=("out",),
        nodes=(Node(id="if", kind="If", inputs=("cond", "a", "b"), outputs=("out",)),),
    )
    with pytest.raises(ProjectionError):
        project_formula(graph)


def test_text_projection_includes_tensor_type_without_becoming_authoritative_source():
    graph = Graph(
        id="identity",
        inputs=("x",),
        outputs=("y",),
        nodes=(Node(id="id", kind="Identity", inputs=("x",), outputs=("y",), value_type=TensorType("f32", Shape.of("B", 3))),),
    )
    text = project_text(graph)
    assert "Tensor[f32; B,3]" in text
    assert "y = identity(x)" in text


def test_formula_projection_parenthesizes_composite_multiply_operands():
    graph = Graph(
        id="formula_precedence",
        inputs=("x", "y"),
        outputs=("sq",),
        nodes=(
            Node(id="sub", kind="Subtract", inputs=("x", "y"), outputs=("d",)),
            Node(id="mul", kind="Multiply", inputs=("d", "d"), outputs=("sq",)),
        ),
    )
    assert project_formula(graph) == "sq = (x - y) \\odot (x - y)"

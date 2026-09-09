import pytest

from nova_core import Graph, Node, TensorType, semantic_hash
from nova_core.autodiff import DifferentiationRequest, differentiate_graph, gradient_symbol
from nova_core.errors import DiffError


def scalar_square_graph() -> Graph:
    return Graph(
        id="square",
        inputs=("x",),
        outputs=("loss",),
        nodes=(
            Node(
                id="square_node",
                kind="Multiply",
                inputs=("x", "x"),
                outputs=("loss",),
                value_type=TensorType.scalar("f64"),
                differentiation_type="Differentiable",
            ),
        ),
    )


def test_scalar_reverse_transform_inserts_unit_seed_and_gradient_output():
    graph = scalar_square_graph()
    result = differentiate_graph(graph, DifferentiationRequest(target="loss", wrt=("x",)))

    assert result.graph.id.startswith("square__rev__loss__")
    assert result.graph.inputs == ("x",)
    assert result.graph.outputs == (gradient_symbol("x"),)
    assert result.gradients == {"x": gradient_symbol("x")}
    assert any(node.kind == "Constant" and node.attributes.get("value") == 1.0 for node in result.graph.nodes)
    assert any(node.kind == "Add" and node.attributes.get("ad_role") == "accumulate" for node in result.graph.nodes)


def test_explicit_seed_builds_vjp_for_non_scalar_target():
    graph = Graph(
        id="vector_square",
        inputs=("x",),
        outputs=("y",),
        nodes=(
            Node(
                id="square_node",
                kind="Multiply",
                inputs=("x", "x"),
                outputs=("y",),
                value_type=TensorType("f64", shape=(3,)),
            ),
        ),
    )
    result = differentiate_graph(
        graph,
        DifferentiationRequest(target="y", wrt=("x",), seed_input="dy"),
    )

    assert result.graph.inputs == ("x", "dy")
    assert not any(node.kind == "Constant" and node.attributes.get("ad_role") == "seed" for node in result.graph.nodes)
    assert result.graph.outputs == (gradient_symbol("x"),)


def test_non_scalar_target_without_explicit_seed_is_rejected():
    graph = Graph(
        id="vector",
        inputs=("x",),
        outputs=("y",),
        nodes=(Node(id="id", kind="Identity", inputs=("x",), outputs=("y",), value_type=TensorType("f64", shape=(2,))),),
    )
    with pytest.raises(DiffError) as exc:
        differentiate_graph(graph, DifferentiationRequest(target="y", wrt=("x",)))
    assert exc.value.to_dict()["context"]["target"] == "y"


def test_transform_is_deterministic_and_does_not_mutate_primal_hash():
    graph = scalar_square_graph()
    before = semantic_hash(graph)
    request = DifferentiationRequest(target="loss", wrt=("x",))

    first = differentiate_graph(graph, request)
    second = differentiate_graph(graph, request)

    assert semantic_hash(first.graph) == semantic_hash(second.graph)
    assert semantic_hash(graph) == before


def test_fanout_contributions_are_accumulated_explicitly():
    graph = Graph(
        id="fanout",
        inputs=("x",),
        outputs=("loss",),
        nodes=(
            Node(id="sq", kind="Multiply", inputs=("x", "x"), outputs=("sqv",)),
            Node(id="double", kind="Add", inputs=("x", "x"), outputs=("doublev",)),
            Node(id="loss", kind="Add", inputs=("sqv", "doublev"), outputs=("loss",), value_type=TensorType.scalar("f64")),
        ),
    )
    result = differentiate_graph(graph, DifferentiationRequest(target="loss", wrt=("x",)))
    accumulators = [node for node in result.graph.nodes if node.attributes.get("ad_role") == "accumulate" and node.attributes.get("symbol") == "x"]
    assert accumulators


def test_stop_gradient_creates_explicit_zero_gradient_for_requested_symbol():
    graph = Graph(
        id="stop",
        inputs=("x",),
        outputs=("loss",),
        nodes=(
            Node(id="stop", kind="StopGradient", inputs=("x",), outputs=("stopped",)),
            Node(id="loss", kind="Multiply", inputs=("stopped", "stopped"), outputs=("loss",), value_type=TensorType.scalar("f64")),
        ),
    )
    result = differentiate_graph(graph, DifferentiationRequest(target="loss", wrt=("x",)))
    assert any(node.kind == "ADZeroLike" and node.attributes.get("ad_role") == "zero_gradient" for node in result.graph.nodes)


def test_non_differentiable_active_node_is_typed_failure():
    graph = Graph(
        id="blocked",
        inputs=("x",),
        outputs=("loss",),
        nodes=(
            Node(
                id="relu",
                kind="Relu",
                inputs=("x",),
                outputs=("loss",),
                value_type=TensorType.scalar("f64"),
                differentiation_type="NonDifferentiable",
            ),
        ),
    )
    with pytest.raises(DiffError) as exc:
        differentiate_graph(graph, DifferentiationRequest(target="loss", wrt=("x",)))
    assert exc.value.to_dict()["source_nodes"] == ["relu"]


def test_unknown_differentiability_is_typed_failure():
    graph = Graph(
        id="unknown",
        inputs=("x",),
        outputs=("loss",),
        nodes=(
            Node(
                id="mystery",
                kind="Identity",
                inputs=("x",),
                outputs=("loss",),
                value_type=TensorType.scalar("f64"),
                differentiation_type="UnknownDifferentiability",
            ),
        ),
    )
    with pytest.raises(DiffError):
        differentiate_graph(graph, DifferentiationRequest(target="loss", wrt=("x",)))


def test_unsupported_active_node_is_typed_failure():
    graph = Graph(
        id="unsupported",
        inputs=("x",),
        outputs=("loss",),
        nodes=(Node(id="magic", kind="Magic", inputs=("x",), outputs=("loss",), value_type=TensorType.scalar("f64")),),
    )
    with pytest.raises(DiffError) as exc:
        differentiate_graph(graph, DifferentiationRequest(target="loss", wrt=("x",)))
    assert exc.value.to_dict()["context"]["kind"] == "Magic"


def test_missing_target_and_wrt_symbols_are_rejected():
    graph = scalar_square_graph()
    with pytest.raises(DiffError):
        differentiate_graph(graph, DifferentiationRequest(target="missing", wrt=("x",), seed_input="seed"))
    with pytest.raises(DiffError):
        differentiate_graph(graph, DifferentiationRequest(target="loss", wrt=("missing",)))

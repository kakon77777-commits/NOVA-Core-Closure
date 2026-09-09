import pytest

from nova_core import Graph, Node, Shape, TensorType


def sequential_graph():
    t = TensorType("f32", Shape((4,)))
    return Graph(
        id="sequential",
        inputs=("x",),
        outputs=("c",),
        nodes=(
            Node(id="n3", kind="Add", inputs=("b", "b"), outputs=("c",), value_type=t),
            Node(id="n1", kind="Add", inputs=("x", "x"), outputs=("a",), value_type=t),
            Node(id="n2", kind="Multiply", inputs=("a", "a"), outputs=("b",), value_type=t),
        ),
    )


def test_sequential_lifetimes_are_deterministic():
    from nova_core import OwnershipState, analyze_resources

    t = TensorType("f32", Shape((4,)))
    analysis = analyze_resources(sequential_graph(), {"x": t})
    assert analysis.schedule == ("n1", "n2", "n3")
    assert analysis.exit_step == 3

    x = analysis.value("x")
    a = analysis.value("a")
    b = analysis.value("b")
    c = analysis.value("c")

    assert (x.first_step, x.last_step, x.ownership) == (-1, 0, OwnershipState.BORROWED_IMMUTABLE)
    assert (a.first_step, a.last_step, a.ownership, a.size_bytes) == (0, 1, OwnershipState.OWNED, 16)
    assert (b.first_step, b.last_step, b.ownership, b.size_bytes) == (1, 2, OwnershipState.OWNED, 16)
    assert (c.first_step, c.last_step, c.ownership, c.size_bytes) == (2, 3, OwnershipState.OWNED, 16)
    assert c.graph_output is True


def test_parameter_and_constant_ownership_are_explicit():
    from nova_core import OwnershipState, analyze_resources

    t = TensorType("f64", Shape((2,)))
    graph = Graph(
        id="owned",
        outputs=("y",),
        nodes=(
            Node(id="p", kind="Parameter", outputs=("p",), value_type=t),
            Node(id="k", kind="Constant", outputs=("k",), value_type=t, attributes={"value": [1.0, 2.0]}),
            Node(id="sum", kind="Add", inputs=("p", "k"), outputs=("y",), value_type=t),
        ),
    )
    analysis = analyze_resources(graph)
    assert analysis.value("p").ownership is OwnershipState.BORROWED_IMMUTABLE
    assert analysis.value("k").ownership is OwnershipState.SHARED_IMMUTABLE
    assert analysis.value("y").ownership is OwnershipState.OWNED


def test_non_cpu_owned_tensor_is_device_resident():
    from nova_core import OwnershipState, analyze_resources

    gpu = TensorType("f32", Shape((4,)), device="gpu0")
    cpu = TensorType("f32", Shape((4,)))
    graph = Graph(
        id="gpu",
        inputs=("x",),
        outputs=("y",),
        nodes=(Node(id="gpu_op", kind="Identity", inputs=("x",), outputs=("y",), value_type=gpu),),
    )
    analysis = analyze_resources(graph, {"x": cpu})
    assert analysis.value("y").ownership is OwnershipState.DEVICE_RESIDENT
    assert analysis.value("y").device == "gpu0"


def test_symbolic_size_becomes_runtime_obligation():
    from nova_core import analyze_resources

    dynamic = TensorType("f32", Shape(("N",)))
    graph = Graph(
        id="dynamic",
        inputs=("x",),
        outputs=("y",),
        nodes=(Node(id="id", kind="Identity", inputs=("x",), outputs=("y",), value_type=dynamic),),
    )
    analysis = analyze_resources(graph, {"x": dynamic})
    assert analysis.value("y").size_bytes is None
    assert any(o.kind == "runtime_size" and o.symbol == "y" and o.runtime_guard for o in analysis.obligations)


def test_dtype_nbytes_is_explicit_and_unknown_dtype_fails():
    from nova_core import ResourcePlanningError, dtype_nbytes

    assert dtype_nbytes("f16") == 2
    assert dtype_nbytes("f32") == 4
    assert dtype_nbytes("f64") == 8
    assert dtype_nbytes("complex128") == 16
    with pytest.raises(ResourcePlanningError):
        dtype_nbytes("mystery128")


def test_resource_analysis_does_not_mutate_graph_identity():
    from nova_core import analyze_resources, semantic_hash

    graph = sequential_graph()
    before = semantic_hash(graph)
    analyze_resources(graph, {"x": TensorType("f32", Shape((4,)))})
    assert semantic_hash(graph) == before

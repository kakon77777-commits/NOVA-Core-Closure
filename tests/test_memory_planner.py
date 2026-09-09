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


def test_conservative_plan_uses_unique_physical_buffers():
    from nova_core import conservative_memory_plan

    t = TensorType("f32", Shape((4,)))
    plan = conservative_memory_plan(sequential_graph(), {"x": t})
    assert plan.verification_mode == "conservative"
    assert len(plan.buffers) == 3
    assert len({plan.buffer_for(s) for s in ("a", "b", "c")}) == 3
    assert plan.peak_reserved_bytes == 48


def test_optimized_plan_reuses_non_overlapping_buffer_and_reduces_reserved_bytes():
    from nova_core import conservative_memory_plan, plan_memory

    t = TensorType("f32", Shape((4,)))
    graph = sequential_graph()
    conservative = conservative_memory_plan(graph, {"x": t})
    optimized = plan_memory(graph, {"x": t}, mode="optimized")

    assert optimized.peak_reserved_bytes == 32
    assert optimized.peak_reserved_bytes < conservative.peak_reserved_bytes
    assert optimized.buffer_for("a") == optimized.buffer_for("c")
    assert optimized.buffer_for("b") != optimized.buffer_for("c")


def test_memory_plan_hash_is_deterministic():
    from nova_core import memory_plan_hash, plan_memory

    t = TensorType("f32", Shape((4,)))
    a = plan_memory(sequential_graph(), {"x": t})
    b = plan_memory(sequential_graph(), {"x": t})
    assert memory_plan_hash(a) == memory_plan_hash(b)


def test_device_mismatch_generates_explicit_transfers():
    from nova_core import plan_memory

    cpu = TensorType("f32", Shape((4,)), device="cpu")
    gpu = TensorType("f32", Shape((4,)), device="gpu0")
    graph = Graph(
        id="device",
        inputs=("x",),
        outputs=("z",),
        nodes=(
            Node(id="gpu_op", kind="Identity", inputs=("x",), outputs=("y",), value_type=gpu),
            Node(id="cpu_op", kind="Identity", inputs=("y",), outputs=("z",), value_type=cpu),
        ),
    )
    plan = plan_memory(graph, {"x": cpu})
    transfers = {
        (t.symbol, t.source_device, t.target_device, t.before_node)
        for t in plan.transfers
    }
    assert ("x", "cpu", "gpu0", "gpu_op") in transfers
    assert ("y", "gpu0", "cpu", "cpu_op") in transfers


def test_unknown_size_values_are_never_reused():
    from nova_core import plan_memory

    dyn = TensorType("f32", Shape(("N",)))
    graph = Graph(
        id="dynamic",
        inputs=("x",),
        outputs=("c",),
        nodes=(
            Node(id="n1", kind="Identity", inputs=("x",), outputs=("a",), value_type=dyn),
            Node(id="n2", kind="Identity", inputs=("a",), outputs=("b",), value_type=dyn),
            Node(id="n3", kind="Identity", inputs=("b",), outputs=("c",), value_type=dyn),
        ),
    )
    plan = plan_memory(graph, {"x": dyn})
    assert plan.peak_reserved_bytes is None
    assert len({plan.buffer_for(s) for s in ("a", "b", "c")}) == 3
    assert any(o.kind == "runtime_size" for o in plan.obligations)


def test_same_device_has_no_redundant_transfer():
    from nova_core import plan_memory

    t = TensorType("f32", Shape((4,)), device="cpu")
    plan = plan_memory(sequential_graph(), {"x": t})
    assert plan.transfers == ()

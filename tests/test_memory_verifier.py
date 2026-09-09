from dataclasses import replace

from nova_core import BufferBinding, Graph, Node, Shape, TensorType


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


def device_graph():
    cpu = TensorType("f32", Shape((4,)), device="cpu")
    gpu = TensorType("f32", Shape((4,)), device="gpu0")
    return Graph(
        id="device",
        inputs=("x",),
        outputs=("z",),
        nodes=(
            Node(id="gpu_op", kind="Identity", inputs=("x",), outputs=("y",), value_type=gpu),
            Node(id="cpu_op", kind="Identity", inputs=("y",), outputs=("z",), value_type=cpu),
        ),
    ), {"x": cpu}


def test_valid_optimized_plan_is_safe():
    from nova_core import VerificationStatus, plan_memory, verify_memory_plan

    facts = {"x": TensorType("f32", Shape((4,)))}
    plan = plan_memory(sequential_graph(), facts)
    report = verify_memory_plan(sequential_graph(), plan, facts)
    assert report.status is VerificationStatus.SAFE
    assert report.violations == ()
    assert report.recomputed_peak_reserved_bytes == 32


def test_overlapping_alias_candidate_is_unsafe():
    from nova_core import VerificationStatus, conservative_memory_plan, verify_memory_plan

    graph = sequential_graph()
    facts = {"x": TensorType("f32", Shape((4,)))}
    base = conservative_memory_plan(graph, facts)
    c_buffer = next(b for b in base.buffers if "c" in b.symbols)
    evil = BufferBinding(
        buffer_id="buf:evil",
        symbols=("a", "b"),
        dtype="f32",
        layout="dense",
        device="cpu",
        capacity_bytes=16,
        first_step=0,
        last_step=2,
    )
    bad = replace(base, buffers=(evil, c_buffer), peak_reserved_bytes=32, verification_mode="external", proposer="ai")
    report = verify_memory_plan(graph, bad, facts)
    assert report.status is VerificationStatus.UNSAFE
    assert "overlapping_lifetime" in {v.kind for v in report.violations}


def test_missing_transfer_candidate_is_unsafe():
    from nova_core import VerificationStatus, plan_memory, verify_memory_plan

    graph, facts = device_graph()
    plan = plan_memory(graph, facts)
    bad = replace(plan, transfers=(), verification_mode="external", proposer="ai")
    report = verify_memory_plan(graph, bad, facts)
    assert report.status is VerificationStatus.UNSAFE
    assert "missing_transfer" in {v.kind for v in report.violations}


def test_forged_peak_bytes_are_recomputed_and_rejected():
    from nova_core import VerificationStatus, plan_memory, verify_memory_plan

    facts = {"x": TensorType("f32", Shape((4,)))}
    graph = sequential_graph()
    plan = plan_memory(graph, facts)
    bad = replace(plan, peak_reserved_bytes=1, verification_mode="external", proposer="ai")
    report = verify_memory_plan(graph, bad, facts)
    assert report.status is VerificationStatus.UNSAFE
    assert report.recomputed_peak_reserved_bytes == 32
    assert "peak_mismatch" in {v.kind for v in report.violations}


def test_graph_hash_mismatch_is_unsafe():
    from nova_core import VerificationStatus, plan_memory, verify_memory_plan

    facts = {"x": TensorType("f32", Shape((4,)))}
    graph = sequential_graph()
    plan = plan_memory(graph, facts)
    bad = replace(plan, graph_semantic_hash="sha256:" + "0" * 64, verification_mode="external")
    report = verify_memory_plan(graph, bad, facts)
    assert report.status is VerificationStatus.UNSAFE
    assert "graph_hash_mismatch" in {v.kind for v in report.violations}


def test_dynamic_size_plan_is_conditionally_safe_with_runtime_obligation():
    from nova_core import VerificationStatus, plan_memory, verify_memory_plan

    dyn = TensorType("f32", Shape(("N",)))
    graph = Graph(
        id="dynamic",
        inputs=("x",),
        outputs=("y",),
        nodes=(Node(id="id", kind="Identity", inputs=("x",), outputs=("y",), value_type=dyn),),
    )
    plan = plan_memory(graph, {"x": dyn})
    report = verify_memory_plan(graph, plan, {"x": dyn})
    assert report.status is VerificationStatus.CONDITIONALLY_SAFE
    assert report.violations == ()
    assert any(o.kind == "runtime_size" for o in report.obligations)


def test_unsafe_external_candidate_falls_back_to_conservative_plan():
    from nova_core import plan_memory, select_memory_plan

    graph = sequential_graph()
    facts = {"x": TensorType("f32", Shape((4,)))}
    good = plan_memory(graph, facts)
    bad = replace(good, peak_reserved_bytes=1, verification_mode="external", proposer="ai", confidence=0.99)
    selection = select_memory_plan(graph, bad, facts)
    assert selection.fallback_used is True
    assert selection.candidate_verification.status.value == "unsafe"
    assert selection.selected.verification_mode == "conservative"
    assert selection.selected_verification.status.value == "safe"
    assert selection.rejected_candidate_hash is not None
    assert selection.selected.peak_reserved_bytes == 48


def test_valid_ai_candidate_is_accepted_without_special_trust():
    from nova_core import plan_memory, select_memory_plan

    graph = sequential_graph()
    facts = {"x": TensorType("f32", Shape((4,)))}
    candidate = plan_memory(graph, facts, proposer="ai", confidence=0.77)
    selection = select_memory_plan(graph, candidate, facts)
    assert selection.fallback_used is False
    assert selection.selected is candidate
    assert selection.selected_verification.status.value == "safe"

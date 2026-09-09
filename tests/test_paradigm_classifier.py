from nova_core import Graph, Node


def _fills(graph):
    from nova_core.paradigm import PlannerProfile, classify_region, extract_strategy_regions
    out = []
    for region in extract_strategy_regions(graph):
        out.extend(item.tag.fill.value for item in classify_region(region, PlannerProfile()))
    return out


def test_dense_independent_tensor_region_supports_parallel_candidate():
    graph = Graph(id="dense", inputs=("x","w"), outputs=("y",), nodes=(
        Node(id="mm", kind="MatMul", inputs=("x","w"), outputs=("m",)),
        Node(id="act", kind="Relu", inputs=("m",), outputs=("y",)),
    ))
    assert "P" in _fills(graph)


def test_sparse_selective_region_supports_jump_candidate():
    graph = Graph(id="sparse", inputs=("x","idx"), outputs=("y",), nodes=(
        Node(id="g", kind="Gather", inputs=("x","idx"), outputs=("y",), attributes={"access_pattern":"selective"}),
    ))
    assert "J" in _fills(graph)


def test_bounded_loop_region_supports_sequential_candidate():
    graph = Graph(id="seq", inputs=("x",), outputs=("y",), nodes=(
        Node(id="loop", kind="BoundedLoop", inputs=("x",), outputs=("y",), attributes={"iterations":4}),
    ))
    fills = _fills(graph)
    assert "C" in fills
    assert "P" not in fills


def test_recognition_requires_explicit_stable_cache_evidence():
    graph = Graph(id="recognition", inputs=("key",), outputs=("y",), nodes=(
        Node(id="lookup", kind="Lookup", inputs=("key",), outputs=("y",), attributes={"stable_recognition":True,"precomputed":True}),
    ))
    assert "R" in _fills(graph)


def test_plain_parameterized_model_is_not_assumed_to_be_recognition():
    graph = Graph(id="model", inputs=("x",), outputs=("y",), nodes=(
        Node(id="w", kind="Parameter", outputs=("w",)),
        Node(id="mm", kind="MatMul", inputs=("x","w"), outputs=("y",)),
    ))
    assert "R" not in _fills(graph)

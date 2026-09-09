from nova_core import Graph, Node


def _selected(graph, profile=None):
    from nova_core.paradigm import PlannerProfile, extract_strategy_regions
    from nova_core.paradigm_planner import rank_candidates
    profile = profile or PlannerProfile()
    region = extract_strategy_regions(graph)[0]
    return rank_candidates(region, profile)[0]


def test_default_dense_region_ranks_parallel_first():
    graph = Graph(id="dense", inputs=("x","w"), outputs=("y",), nodes=(
        Node(id="mm", kind="MatMul", inputs=("x","w"), outputs=("y",)),
    ))
    assert _selected(graph).tag.fill.value == "P"


def test_default_sparse_region_ranks_jump_first():
    graph = Graph(id="sparse", inputs=("x","i"), outputs=("y",), nodes=(
        Node(id="g", kind="Gather", inputs=("x","i"), outputs=("y",), attributes={"access_pattern":"selective"}),
    ))
    assert _selected(graph).tag.fill.value == "J"


def test_sequential_region_ranks_sequential_first():
    graph = Graph(id="seq", inputs=("x",), outputs=("y",), nodes=(
        Node(id="loop", kind="BoundedLoop", inputs=("x",), outputs=("y",), attributes={"iterations":3}),
    ))
    assert _selected(graph).tag.fill.value == "C"


def test_explicit_stable_recognition_region_ranks_recognition_first():
    graph = Graph(id="rec", inputs=("k",), outputs=("y",), nodes=(
        Node(id="r", kind="Lookup", inputs=("k",), outputs=("y",), attributes={"stable_recognition":True,"precomputed":True}),
    ))
    assert _selected(graph).tag.fill.value == "R"


def test_profile_can_make_sequential_fallback_cheaper_than_parallel():
    from nova_core.paradigm import PlannerProfile
    graph = Graph(id="dense", inputs=("x","w"), outputs=("y",), nodes=(
        Node(id="mm", kind="MatMul", inputs=("x","w"), outputs=("y",)),
    ))
    selected = _selected(graph, PlannerProfile(parallelism=1, synchronization_weight=20.0))
    assert selected.tag.fill.value == "C"

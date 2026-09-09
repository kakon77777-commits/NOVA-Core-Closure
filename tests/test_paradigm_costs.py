from nova_core import Graph, Node


def _region(graph):
    from nova_core.paradigm import extract_strategy_regions
    return extract_strategy_regions(graph)[0]


def test_recognition_cost_keeps_offline_costs_nonzero():
    from nova_core.paradigm import PlannerProfile
    from nova_core.paradigm_planner import candidate_strategies
    graph = Graph(id="r", inputs=("k",), outputs=("y",), nodes=(
        Node(id="r1", kind="Lookup", inputs=("k",), outputs=("y",), attributes={"stable_recognition":True,"precomputed":True}),
    ))
    candidates = candidate_strategies(_region(graph), PlannerProfile())
    r = next(item for item in candidates if item.tag.fill.value == "R")
    assert r.cost.online_work == 0
    assert r.cost.precompute > 0
    assert r.cost.storage > 0
    assert r.cost.maintenance > 0
    assert r.cost.total > 0


def test_parallel_cost_responds_to_profile_parallelism_and_sync_weight():
    from nova_core.paradigm import PlannerProfile
    from nova_core.paradigm_planner import candidate_strategies
    graph = Graph(id="d", inputs=("x","w"), outputs=("y",), nodes=(
        Node(id="mm", kind="MatMul", inputs=("x","w"), outputs=("y",)),
    ))
    region = _region(graph)
    fast = candidate_strategies(region, PlannerProfile(parallelism=16, synchronization_weight=0.2))
    slow = candidate_strategies(region, PlannerProfile(parallelism=1, synchronization_weight=20.0))
    fast_p = next(item for item in fast if item.tag.fill.value == "P")
    slow_p = next(item for item in slow if item.tag.fill.value == "P")
    assert fast_p.cost.total < slow_p.cost.total

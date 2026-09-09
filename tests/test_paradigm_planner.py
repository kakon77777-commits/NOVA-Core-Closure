from nova_core import Graph, Node, semantic_hash


def test_plan_is_deterministic_and_does_not_change_graph_hash():
    from nova_core.paradigm_planner import plan_graph, plan_hash
    graph = Graph(id="g", inputs=("x","w"), outputs=("y",), nodes=(
        Node(id="mm", kind="MatMul", inputs=("x","w"), outputs=("m",)),
        Node(id="r", kind="Relu", inputs=("m",), outputs=("y",)),
    ))
    before = semantic_hash(graph)
    p1 = plan_graph(graph)
    p2 = plan_graph(graph)
    assert plan_hash(p1) == plan_hash(p2)
    assert semantic_hash(graph) == before
    assert [x.tag.fill.value for x in p1.selected] == ["P","P"]


def test_illegal_ranked_chain_falls_back_to_conservative_sequential_chain():
    from nova_core.paradigm_planner import plan_graph
    graph = Graph(id="mixed", inputs=("x","w"), outputs=("y",), nodes=(
        Node(id="mm", kind="MatMul", inputs=("x","w"), outputs=("m",)),
        Node(id="loop", kind="BoundedLoop", inputs=("m",), outputs=("y",), attributes={"iterations":2}),
    ))
    plan = plan_graph(graph)
    assert plan.fallback_used
    assert [item.tag.fill.value for item in plan.selected] == ["C","C"]
    assert plan.bond_decision.legal


def test_profile_changes_ranking_not_graph_identity():
    from nova_core.paradigm import PlannerProfile
    from nova_core.paradigm_planner import plan_graph
    graph = Graph(id="g", inputs=("x","w"), outputs=("y",), nodes=(
        Node(id="mm", kind="MatMul", inputs=("x","w"), outputs=("y",)),
    ))
    before = semantic_hash(graph)
    fast = plan_graph(graph, PlannerProfile(parallelism=16, synchronization_weight=0.1))
    slow = plan_graph(graph, PlannerProfile(parallelism=1, synchronization_weight=20.0))
    assert fast.selected[0].tag.fill.value == "P"
    assert slow.selected[0].tag.fill.value == "C"
    assert semantic_hash(graph) == before


def test_recognition_plan_has_nonzero_total_cost():
    from nova_core.paradigm_planner import plan_graph
    graph = Graph(id="r", inputs=("k",), outputs=("y",), nodes=(
        Node(id="lookup", kind="Lookup", inputs=("k",), outputs=("y",), attributes={"stable_recognition":True,"precomputed":True}),
    ))
    plan = plan_graph(graph)
    assert plan.selected[0].tag.fill.value == "R"
    assert plan.selected[0].cost.total > 0
    assert plan.selected[0].cost.online_work == 0

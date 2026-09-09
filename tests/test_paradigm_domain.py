from nova_core import Graph, Node, semantic_hash


def test_paradigm_table_has_all_sixteen_unique_triples_and_codes():
    from nova_core.paradigm import PARADIGMS, FillMode
    assert len(PARADIGMS) == 16
    assert len({item.code for item in PARADIGMS}) == 16
    assert len({item.triple for item in PARADIGMS}) == 16
    assert {item.fill for item in PARADIGMS} == set(FillMode)
    assert PARADIGMS[0].index == 1 and PARADIGMS[0].code == "CCC"
    assert PARADIGMS[3].index == 4 and PARADIGMS[3].code == "DCD"
    assert PARADIGMS[11].index == 12 and PARADIGMS[11].code == "DPD"
    assert PARADIGMS[15].index == 16 and PARADIGMS[15].code == "DRD"


def test_paradigm_tag_roundtrip_lookup():
    from nova_core.paradigm import paradigm_by_code, paradigm_by_index
    assert paradigm_by_code("DPC") == paradigm_by_index(11)
    assert paradigm_by_code("DRD").index == 16


def test_domain_inspection_never_changes_graph_identity():
    from nova_core.paradigm import extract_strategy_regions
    graph = Graph(id="g", inputs=("x",), outputs=("y",), nodes=(
        Node(id="n1", kind="Relu", inputs=("x",), outputs=("y",)),
    ))
    before = semantic_hash(graph)
    regions = extract_strategy_regions(graph)
    after = semantic_hash(graph)
    assert regions
    assert before == after

from nova_core import Edge, Graph, Module, Node, Project, SchemaHeader, canonical_json, record_hash, semantic_hash


def make(order=False, provenance=None, migration=()):
    a = Node(id="a", kind="InputAlias", inputs=("x",), outputs=("u",))
    b = Node(id="b", kind="Identity", inputs=("u",), outputs=("y",), provenance={"source":"p"} if provenance else {})
    nodes = (b, a) if order else (a, b)
    edges = (Edge(source="b", target="a", kind="control"), Edge(source="a", target="b", kind="value")) if order else (Edge(source="a", target="b", kind="value"), Edge(source="b", target="a", kind="control"))
    return Project(
        header=SchemaHeader(feature_flags=("z","a"), migration_history=migration),
        modules=(Module(id="m", graphs=(Graph(id="g", inputs=("x",), outputs=("y",), nodes=nodes, edges=edges),)),),
        provenance=provenance or {},
    )


def test_node_and_edge_insertion_order_do_not_change_semantic_hash():
    assert semantic_hash(make(False)) == semantic_hash(make(True))


def test_canonical_json_is_byte_stable_for_equivalent_projects():
    assert canonical_json(make(False)) == canonical_json(make(True))


def test_provenance_does_not_change_semantic_hash():
    assert semantic_hash(make(False)) == semantic_hash(make(False, provenance={"author":"x"}))


def test_provenance_changes_record_hash():
    assert record_hash(make(False)) != record_hash(make(False, provenance={"author":"x"}))


def test_migration_history_does_not_change_semantic_hash():
    assert semantic_hash(make(False, migration=())) == semantic_hash(make(False, migration=("0.0->0.1",)))


def test_executable_node_kind_changes_semantic_hash():
    p1 = Project(modules=(Module(id="m", graphs=(Graph(id="g", inputs=("x",), outputs=("y",), nodes=(Node(id="n", kind="Identity", inputs=("x",), outputs=("y",)),)),)),))
    p2 = Project(modules=(Module(id="m", graphs=(Graph(id="g", inputs=("x",), outputs=("y",), nodes=(Node(id="n", kind="Negate", inputs=("x",), outputs=("y",)),)),)),))
    assert semantic_hash(p1) != semantic_hash(p2)


def test_node_input_order_is_semantic():
    p1 = Project(modules=(Module(id="m", graphs=(Graph(id="g", inputs=("a","b"), outputs=("y",), nodes=(Node(id="n", kind="Subtract", inputs=("a","b"), outputs=("y",)),)),)),))
    p2 = Project(modules=(Module(id="m", graphs=(Graph(id="g", inputs=("a","b"), outputs=("y",), nodes=(Node(id="n", kind="Subtract", inputs=("b","a"), outputs=("y",)),)),)),))
    assert semantic_hash(p1) != semantic_hash(p2)

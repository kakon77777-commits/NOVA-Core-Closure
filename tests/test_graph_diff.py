from dataclasses import replace

from nova_core import Edge, Graph, Node, Shape, TensorType
from nova_core.diff import diff_graphs


def base_graph() -> Graph:
    return Graph(
        id="g",
        inputs=("x", "b"),
        outputs=("y",),
        nodes=(
            Node(id="add", kind="Add", inputs=("x", "b"), outputs=("y",), provenance={"line": 1}),
        ),
        attributes={"purpose": "base"},
    )


def test_diff_detects_added_and_removed_nodes_deterministically():
    before = Graph(
        id="g",
        inputs=("x",),
        outputs=("y",),
        nodes=(Node(id="a", kind="Identity", inputs=("x",), outputs=("y",)), Node(id="z", kind="Probe")),
    )
    after = Graph(
        id="g",
        inputs=("x",),
        outputs=("y",),
        nodes=(Node(id="m", kind="Probe"), Node(id="a", kind="Identity", inputs=("x",), outputs=("y",))),
    )
    diff = diff_graphs(before, after)
    assert diff.added_nodes == ("m",)
    assert diff.removed_nodes == ("z",)
    assert diff.semantic_changed is True


def test_diff_reports_field_level_semantic_node_changes():
    before = base_graph()
    changed = replace(
        before.nodes[0],
        kind="Multiply",
        inputs=("b", "x"),
        value_type=TensorType("f32", Shape.of(2)),
        effect_type=("IO",),
        differentiation_type="NonDifferentiable",
        attributes={"axis": 0},
    )
    after = replace(before, nodes=(changed,))
    delta = diff_graphs(before, after).modified_nodes[0]
    assert delta.node_id == "add"
    fields = {change.field: change for change in delta.changes}
    assert {"kind", "inputs", "value_type", "effect_type", "differentiation_type", "attributes"} <= set(fields)
    assert all(fields[name].semantic for name in ("kind", "inputs", "value_type", "effect_type", "differentiation_type", "attributes"))


def test_provenance_only_change_is_structural_but_not_semantic():
    before = base_graph()
    after = replace(before, nodes=(replace(before.nodes[0], provenance={"line": 99}),))
    diff = diff_graphs(before, after)
    assert diff.semantic_changed is False
    assert len(diff.modified_nodes) == 1
    change = diff.modified_nodes[0].changes[0]
    assert change.field == "provenance"
    assert change.semantic is False


def test_edge_attribute_change_is_detected_as_modification_not_remove_add():
    before = replace(base_graph(), edges=(Edge(source="add", target="add", kind="trace", attributes={"level": 1}),))
    after = replace(before, edges=(Edge(source="add", target="add", kind="trace", attributes={"level": 2}),))
    diff = diff_graphs(before, after)
    assert diff.added_edges == ()
    assert diff.removed_edges == ()
    assert len(diff.modified_edges) == 1
    assert diff.modified_edges[0].key == ("add", "add", "trace")
    assert diff.modified_edges[0].changes[0].field == "attributes"
    assert diff.semantic_changed is True


def test_graph_interface_constraint_attribute_and_provenance_changes_are_classified():
    before = base_graph()
    after = replace(
        before,
        inputs=("x", "b", "scale"),
        outputs=("y", "scale"),
        constraints=("scale > 0",),
        attributes={"purpose": "changed"},
        provenance={"review": "round07"},
    )
    diff = diff_graphs(before, after)
    fields = {change.field: change for change in diff.graph_changes}
    assert {"inputs", "outputs", "constraints", "attributes", "provenance"} <= set(fields)
    assert fields["provenance"].semantic is False
    assert fields["inputs"].semantic is True
    assert diff.semantic_changed is True


def test_diff_to_dict_is_stable_and_contains_hashes():
    before = base_graph()
    after = replace(before, attributes={"purpose": "next"})
    payload = diff_graphs(before, after).to_dict()
    assert payload["base_hash"].startswith("sha256:")
    assert payload["target_hash"].startswith("sha256:")
    assert payload["semantic_changed"] is True
    assert payload["graph_changes"][0]["field"] == "attributes"

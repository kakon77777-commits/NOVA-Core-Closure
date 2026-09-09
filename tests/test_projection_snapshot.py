import json

from nova_core import Edge, Graph, Node, Shape, TensorType, record_hash, semantic_hash
from nova_core.projection import parse_editable_text, project_editable_text, project_graph_view, project_snapshot


def rich_graph() -> Graph:
    return Graph(
        id="linear",
        inputs=("X", "W", "b"),
        outputs=("Y",),
        nodes=(
            Node(
                id="mm",
                kind="MatMul",
                inputs=("X", "W"),
                outputs=("XW",),
                value_type=TensorType("f32", Shape.of("B", "O")),
                provenance={"source": "round07"},
                extensions={"ui_hint": "matrix"},
            ),
            Node(id="add", kind="Add", inputs=("XW", "b"), outputs=("Y",)),
        ),
        edges=(Edge(source="mm", target="add", kind="value", attributes={"slot": 0}),),
        constraints=("B > 0",),
        attributes={"purpose": "projection-test"},
        provenance={"author": "test"},
        extensions={"graph_hint": "keep"},
    )


def test_editable_projection_round_trips_full_graph_record_and_semantic_hash():
    graph = rich_graph()
    text = project_editable_text(graph)
    restored = parse_editable_text(text)
    assert record_hash(restored) == record_hash(graph)
    assert semantic_hash(restored) == semantic_hash(graph)
    payload = json.loads(text)
    assert payload["id"] == "linear"
    assert next(node for node in payload["nodes"] if node["id"] == "mm")["ui_hint"] == "matrix"
    assert payload["graph_hint"] == "keep"


def test_graph_view_is_machine_readable_and_carries_same_identity():
    graph = rich_graph()
    view = project_graph_view(graph)
    assert view["semantic_hash"] == semantic_hash(graph)
    assert [node["id"] for node in view["nodes"]] == ["add", "mm"]
    assert view["edges"][0]["kind"] == "value"


def test_projection_snapshot_preserves_hash_across_all_supported_views():
    graph = rich_graph()
    before = semantic_hash(graph)
    snapshot = project_snapshot(graph)
    assert snapshot.semantic_hash == before
    assert snapshot.formula == "Y = (X \\cdot W) + b"
    assert snapshot.text.startswith("graph linear")
    assert snapshot.graph_view["semantic_hash"] == before
    assert record_hash(parse_editable_text(snapshot.editable_text)) == record_hash(graph)
    assert snapshot.reversibility["editable"] == "lossless"
    assert snapshot.reversibility["formula"] == "read_only"
    assert semantic_hash(graph) == before


def test_snapshot_marks_formula_unsupported_without_breaking_other_views():
    graph = Graph(
        id="branch",
        inputs=("cond", "a", "b"),
        outputs=("out",),
        nodes=(Node(id="if", kind="If", inputs=("cond", "a", "b"), outputs=("out",)),),
    )
    snapshot = project_snapshot(graph)
    assert snapshot.formula is None
    assert snapshot.formula_error is not None
    assert snapshot.formula_error["category"] == "ProjectionError"
    assert snapshot.reversibility["formula"] == "unsupported"
    assert record_hash(parse_editable_text(snapshot.editable_text)) == record_hash(graph)

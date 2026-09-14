from nova_core.canonical import semantic_hash
from nova_core.model import Graph, Module, Node, Project, SchemaHeader
from nova_core.symbol_minimal import (
    annotation_sidecar,
    decode_semantic_core,
    encode_semantic_core,
    semantic_roundtrip_ok,
)


def _project(*, provenance_note: str = "human note") -> Project:
    node = Node(
        id="n0",
        kind="Const",
        outputs=("x",),
        attributes={"value": 3.0},
        source_projection={"label": "Human-facing constant"},
        provenance={"comment": provenance_note},
    )
    graph = Graph(id="g0", outputs=("x",), nodes=(node,))
    module = Module(id="m0", graphs=(graph,))
    return Project(
        header=SchemaHeader(provenance={"authoring_surface": "test"}),
        modules=(module,),
        artifacts=({"doc": "not semantic"},),
        provenance={"comment": provenance_note},
    )


def test_semantic_core_is_deterministic_and_roundtrips() -> None:
    project = _project()
    first = encode_semantic_core(project)
    second = encode_semantic_core(project)
    assert first == second
    assert first.startswith(b"NSM1")
    restored = decode_semantic_core(first)
    assert semantic_hash(restored) == semantic_hash(project)
    assert semantic_roundtrip_ok(project)


def test_nonsemantic_notes_do_not_change_semantic_blob() -> None:
    left = _project(provenance_note="A")
    right = _project(provenance_note="B")
    assert semantic_hash(left) == semantic_hash(right)
    assert encode_semantic_core(left) == encode_semantic_core(right)


def test_schema_field_names_are_not_repeated_in_binary_body() -> None:
    blob = encode_semantic_core(_project())
    assert b"modules" not in blob
    assert b"nodes" not in blob
    assert b"outputs" not in blob
    assert b"value_type" not in blob


def test_annotation_sidecar_is_separate_and_hash_linked() -> None:
    project = _project()
    sidecar = annotation_sidecar(project)
    assert sidecar["semantic_hash"] == semantic_hash(project)
    assert sidecar["modules"]["m0"]["graphs"]["g0"]["nodes"]["n0"]["source_projection"]
    assert sidecar["project_provenance"]["comment"] == "human note"

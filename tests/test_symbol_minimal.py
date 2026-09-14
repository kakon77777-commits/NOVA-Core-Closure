from nova_core.canonical import semantic_hash
from nova_core.model import Graph, Module, Node, Project, SchemaHeader
from nova_core.shape import Shape
from nova_core.types import TensorType
from nova_core.symbol_minimal import (
    annotation_sidecar,
    decode_semantic_core,
    encode_semantic_core,
    semantic_roundtrip_ok,
)


def _project(*, provenance_note: str = "human note", kind: str = "Identity") -> Project:
    tensor = TensorType(dtype="f32", shape=Shape.of("B", 128), layout="row_major", device="cpu")
    node = Node(
        id="n0",
        kind=kind,
        inputs=("input_x",),
        outputs=("x",),
        value_type=tensor,
        shape_type=tensor.shape,
        effect_type="Pure",
        differentiation_type="Differentiable",
        attributes={"human_key": "attribute-value"},
        source_projection={"label": "Human-facing identity"},
        provenance={"comment": provenance_note},
    )
    graph = Graph(id="g0", inputs=("input_x",), outputs=("x",), nodes=(node,))
    module = Module(id="m0", graphs=(graph,))
    return Project(
        header=SchemaHeader(provenance={"authoring_surface": "test"}),
        modules=(module,),
        artifacts=({"doc": "not semantic"},),
        provenance={"comment": provenance_note},
    )


def test_nsm2_is_deterministic_and_roundtrips() -> None:
    project = _project()
    first = encode_semantic_core(project)
    second = encode_semantic_core(project)
    assert first == second
    assert first.startswith(b"NSM2")
    restored = decode_semantic_core(first)
    assert semantic_hash(restored) == semantic_hash(project)
    assert semantic_roundtrip_ok(project)


def test_nsm1_remains_decodable() -> None:
    project = _project()
    blob = encode_semantic_core(project, version=1)
    assert blob.startswith(b"NSM1")
    restored = decode_semantic_core(blob)
    assert semantic_hash(restored) == semantic_hash(project)


def test_nonsemantic_notes_do_not_change_semantic_blob() -> None:
    left = _project(provenance_note="A")
    right = _project(provenance_note="B")
    assert semantic_hash(left) == semantic_hash(right)
    assert encode_semantic_core(left) == encode_semantic_core(right)


def test_schema_field_names_and_known_semantic_atoms_are_not_text_in_nsm2() -> None:
    blob = encode_semantic_core(_project())
    # Known structural field names are numeric field codes.
    for text in (b"modules", b"nodes", b"outputs", b"value_type"):
        assert text not in blob
    # Known core semantic atoms are global numeric identities in NSM2.
    for text in (b"Identity", b"f32", b"row_major", b"cpu", b"Pure", b"Differentiable"):
        assert text not in blob


def test_unknown_operator_falls_back_to_local_symbol_and_roundtrips() -> None:
    project = _project(kind="FutureQuantumOp")
    blob = encode_semantic_core(project)
    assert b"FutureQuantumOp" in blob
    restored = decode_semantic_core(blob)
    assert restored.modules[0].graphs[0].nodes[0].kind == "FutureQuantumOp"
    assert semantic_hash(restored) == semantic_hash(project)


def test_user_identity_and_attribute_strings_remain_local_in_v02() -> None:
    blob = encode_semantic_core(_project())
    # Stable structural identity is deliberately postponed to v0.3.
    assert b"input_x" in blob
    assert b"attribute-value" in blob


def test_annotation_sidecar_is_separate_and_hash_linked() -> None:
    project = _project()
    sidecar = annotation_sidecar(project)
    assert sidecar["semantic_hash"] == semantic_hash(project)
    assert sidecar["modules"]["m0"]["graphs"]["g0"]["nodes"]["n0"]["source_projection"]
    assert sidecar["project_provenance"]["comment"] == "human note"

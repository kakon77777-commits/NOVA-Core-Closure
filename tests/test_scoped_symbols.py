import pytest

from nova_core.canonical import semantic_hash
from nova_core.errors import ValidationError
from nova_core.model import Graph, Module, Node, Project
from nova_core.purified_identity import bootstrap_purified_identity_manifest
from nova_core.scoped_identity import (
    apply_scoped_symbol_projection,
    decode_scoped_core,
    encode_scoped_core,
    scoped_machine_hash,
    scoped_roundtrip_ok,
    scoped_symbol_sidecar,
)
from nova_core.scoped_symbols import (
    bootstrap_scoped_symbol_manifest,
    scoped_symbol_manifest_hash,
)
from nova_core.shape import DimExpr, Shape
from nova_core.types import TensorType


def _project(batch="B", width="N", *, width_coeff=1, graph_id="main") -> Project:
    shape = Shape((DimExpr.symbol(batch), DimExpr(0, ((width, width_coeff),))))
    tensor = TensorType("f32", shape=shape, layout="row_major", device="cpu")
    node = Node(
        id="x_node",
        kind="Identity",
        inputs=("x",),
        outputs=("y",),
        value_type=tensor,
        shape_type=shape,
        effect_type="Pure",
        differentiation_type="Differentiable",
    )
    graph = Graph(id=graph_id, inputs=("x",), outputs=("y",), nodes=(node,))
    return Project(modules=(Module(id="app", graphs=(graph,)),))


def _manifests(project):
    structural = bootstrap_purified_identity_manifest(project)
    scoped = bootstrap_scoped_symbol_manifest(project, structural)
    return structural, scoped


def _shape_symbols(project: Project):
    shape = project.modules[0].graphs[0].nodes[0].value_type.shape
    return tuple(term[0] for dim in shape.dims for term in dim.terms)


def test_scoped_bootstrap_is_label_independent_for_same_structural_manifest() -> None:
    left = _project("B", "N")
    right = _project("Batch", "Width")
    structural = bootstrap_purified_identity_manifest(left)
    left_scoped = bootstrap_scoped_symbol_manifest(left, structural)
    right_scoped = bootstrap_scoped_symbol_manifest(right, structural)
    left_id = sorted((e.scope_sid.raw, e.signature, e.symbol_id.raw) for e in left_scoped.entries)
    right_id = sorted((e.scope_sid.raw, e.signature, e.symbol_id.raw) for e in right_scoped.entries)
    assert left_id == right_id
    assert scoped_symbol_manifest_hash(left_scoped, include_labels=False) == scoped_symbol_manifest_hash(right_scoped, include_labels=False)
    assert scoped_symbol_manifest_hash(left_scoped, include_labels=True) != scoped_symbol_manifest_hash(right_scoped, include_labels=True)


def test_alpha_rename_does_not_change_nsm6_machine_identity() -> None:
    project = _project()
    structural, scoped = _manifests(project)
    graph_sid = structural.resolve("graph", "main", parent=structural.resolve("module", "app", parent=structural.project_sid))
    b_id = scoped.resolve(graph_sid, "B")
    n_id = scoped.resolve(graph_sid, "N")
    renamed, renamed_scoped = apply_scoped_symbol_projection(
        project,
        structural,
        scoped,
        {b_id: "Batch", n_id: "Width"},
    )
    assert semantic_hash(project) != semantic_hash(renamed)
    assert encode_scoped_core(project, structural, scoped) == encode_scoped_core(renamed, structural, renamed_scoped)
    assert scoped_machine_hash(project, structural, scoped) == scoped_machine_hash(renamed, structural, renamed_scoped)


def test_same_nsm6_blob_can_reproject_new_symbol_names() -> None:
    project = _project()
    structural, scoped = _manifests(project)
    module_sid = structural.resolve("module", "app", parent=structural.project_sid)
    graph_sid = structural.resolve("graph", "main", parent=module_sid)
    b_id = scoped.resolve(graph_sid, "B")
    n_id = scoped.resolve(graph_sid, "N")
    renamed, renamed_scoped = apply_scoped_symbol_projection(
        project,
        structural,
        scoped,
        {b_id: "Batch", n_id: "Width"},
    )
    blob = encode_scoped_core(project, structural, scoped)
    reprojection = decode_scoped_core(blob, structural, renamed_scoped)
    assert semantic_hash(reprojection) == semantic_hash(renamed)
    assert set(_shape_symbols(reprojection)) == {"Batch", "Width"}


def test_nsm6_removes_scoped_symbol_spellings_from_payload() -> None:
    project = _project("BatchDimension", "WidthDimension")
    structural, scoped = _manifests(project)
    blob = encode_scoped_core(project, structural, scoped)
    assert blob.startswith(b"NSM6")
    for token in (b"BatchDimension", b"WidthDimension", b"scoped_semantic_symbol"):
        assert token not in blob
    assert scoped_roundtrip_ok(project, structural, scoped)


def test_same_label_in_different_graph_scopes_has_different_identity() -> None:
    left = _project("B", "N", graph_id="g1").modules[0].graphs[0]
    right = _project("B", "N", graph_id="g2").modules[0].graphs[0]
    project = Project(modules=(Module(id="app", graphs=(left, right)),))
    structural = bootstrap_purified_identity_manifest(project)
    scoped = bootstrap_scoped_symbol_manifest(project, structural)
    module_sid = structural.resolve("module", "app", parent=structural.project_sid)
    g1 = structural.resolve("graph", "g1", parent=module_sid)
    g2 = structural.resolve("graph", "g2", parent=module_sid)
    assert scoped.resolve(g1, "B") != scoped.resolve(g2, "B")
    assert scoped.resolve(g1, "N") != scoped.resolve(g2, "N")


def test_semantic_coefficient_change_changes_machine_identity() -> None:
    project = _project(width_coeff=1)
    changed = _project(width_coeff=2)
    structural, scoped = _manifests(project)
    assert scoped_machine_hash(project, structural, scoped) != scoped_machine_hash(changed, structural, scoped)


def test_structurally_ambiguous_fresh_binders_are_rejected() -> None:
    mixed = DimExpr(0, (("B", 1), ("N", 1)))
    shape = Shape((mixed,))
    tensor = TensorType("f32", shape=shape)
    project = Project(modules=(Module(id="app", graphs=(Graph(
        id="main",
        inputs=("x",),
        outputs=("y",),
        nodes=(Node(id="n", kind="Identity", inputs=("x",), outputs=("y",), value_type=tensor, shape_type=shape),),
    ),)),))
    structural = bootstrap_purified_identity_manifest(project)
    with pytest.raises(ValidationError, match="structurally ambiguous"):
        bootstrap_scoped_symbol_manifest(project, structural)


def test_scoped_symbol_sidecar_separates_projection_hash_from_machine_hash() -> None:
    project = _project()
    structural, scoped = _manifests(project)
    module_sid = structural.resolve("module", "app", parent=structural.project_sid)
    graph_sid = structural.resolve("graph", "main", parent=module_sid)
    b_id = scoped.resolve(graph_sid, "B")
    renamed, renamed_scoped = apply_scoped_symbol_projection(project, structural, scoped, {b_id: "Batch"})
    left = scoped_symbol_sidecar(project, structural, scoped)
    right = scoped_symbol_sidecar(renamed, structural, renamed_scoped)
    assert left["scoped_machine_hash"] == right["scoped_machine_hash"]
    assert left["scoped_manifest_identity_hash"] == right["scoped_manifest_identity_hash"]
    assert left["scoped_manifest_projection_hash"] != right["scoped_manifest_projection_hash"]
    assert all(entry["projection_anchor"].startswith("sha256:") for entry in left["entries"])

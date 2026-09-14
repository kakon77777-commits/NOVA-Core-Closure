from nova_core.canonical import project_record, semantic_hash
from nova_core.codec import decode_project
from nova_core.model import Graph, Module, Node, Project
from nova_core.structural_identity import (
    apply_label_projection,
    bootstrap_identity_manifest,
    decode_identity_core,
    encode_identity_core,
    identity_roundtrip_ok,
    identity_sidecar,
    machine_identity_hash,
)


def _project(kind: str = "Add") -> Project:
    node = Node(
        id="add_node",
        kind=kind,
        inputs=("left", "right"),
        outputs=("sum",),
        effect_type="Pure",
        differentiation_type="Differentiable",
        source_projection={"label": "human add"},
        provenance={"note": "human documentation"},
    )
    graph = Graph(
        id="main",
        inputs=("left", "right"),
        outputs=("sum",),
        nodes=(node,),
    )
    return Project(modules=(Module(id="app", graphs=(graph,)),))


def _rename_all(project: Project):
    manifest = bootstrap_identity_manifest(project)
    module_sid = manifest.resolve("module", "app", parent=manifest.project_sid)
    graph_sid = manifest.resolve("graph", "main", parent=module_sid)
    node_sid = manifest.resolve("node", "add_node", parent=graph_sid)
    left_sid = manifest.resolve("value", "left", parent=graph_sid)
    right_sid = manifest.resolve("value", "right", parent=graph_sid)
    sum_sid = manifest.resolve("value", "sum", parent=graph_sid)
    renamed, renamed_manifest = apply_label_projection(
        project,
        manifest,
        {
            module_sid: "human_module",
            graph_sid: "renamed_graph",
            node_sid: "sum_operator",
            left_sid: "a",
            right_sid: "b",
            sum_sid: "c",
        },
    )
    return manifest, renamed, renamed_manifest


def test_nsm3_removes_structural_human_labels_and_roundtrips() -> None:
    project = _project()
    manifest = bootstrap_identity_manifest(project)
    blob = encode_identity_core(project, manifest)
    assert blob.startswith(b"NSM3")
    for token in (
        b"app",
        b"main",
        b"add_node",
        b"left",
        b"right",
        b"sum",
        b"Add",
        b"Pure",
        b"Differentiable",
    ):
        assert token not in blob
    restored = decode_identity_core(blob, manifest)
    assert semantic_hash(restored) == semantic_hash(project)
    assert identity_roundtrip_ok(project, manifest)


def test_alpha_rename_changes_legacy_hash_but_not_machine_identity() -> None:
    project = _project()
    manifest, renamed, renamed_manifest = _rename_all(project)
    assert semantic_hash(renamed) != semantic_hash(project)
    assert machine_identity_hash(renamed, renamed_manifest) == machine_identity_hash(project, manifest)
    assert encode_identity_core(renamed, renamed_manifest) == encode_identity_core(project, manifest)


def test_same_nsm3_blob_can_project_to_new_human_labels() -> None:
    project = _project()
    manifest, renamed, renamed_manifest = _rename_all(project)
    blob = encode_identity_core(project, manifest)
    reprojection = decode_identity_core(blob, renamed_manifest)
    assert semantic_hash(reprojection) == semantic_hash(renamed)
    assert project_record(reprojection, semantic=True) == project_record(renamed, semantic=True)


def test_semantic_state_change_keeps_sid_but_changes_machine_hash() -> None:
    project = _project("Add")
    manifest = bootstrap_identity_manifest(project)
    changed_record = project_record(project, semantic=False)
    changed_record["modules"][0]["graphs"][0]["nodes"][0]["kind"] = "Subtract"
    changed = decode_project(changed_record)
    assert machine_identity_hash(changed, manifest) != machine_identity_hash(project, manifest)


def test_bootstrap_is_deterministic_for_same_legacy_project() -> None:
    project = _project()
    first = bootstrap_identity_manifest(project)
    second = bootstrap_identity_manifest(project)
    assert first.to_record() == second.to_record()


def test_identity_sidecar_uses_stable_ids_for_human_annotations() -> None:
    project = _project()
    manifest = bootstrap_identity_manifest(project)
    module_sid = manifest.resolve("module", "app", parent=manifest.project_sid)
    graph_sid = manifest.resolve("graph", "main", parent=module_sid)
    node_sid = manifest.resolve("node", "add_node", parent=graph_sid)
    sidecar = identity_sidecar(project, manifest)
    assert sidecar["project_sid"] == manifest.project_sid.text
    assert sidecar["machine_identity_hash"] == machine_identity_hash(project, manifest)
    assert sidecar["entries"][node_sid.text]["label"] == "add_node"
    assert sidecar["entries"][node_sid.text]["source_projection"]["label"] == "human add"
    assert sidecar["entries"][node_sid.text]["provenance"]["note"] == "human documentation"

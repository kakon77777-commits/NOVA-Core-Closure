from nova_core.canonical import semantic_hash
from nova_core.human_projection import contains_human_projection
from nova_core.identity_model import bootstrap_identity_manifest
from nova_core.model import Graph, Module, Node, Project
from nova_core.purified_identity import (
    bootstrap_purified_identity_manifest,
    decode_purified_core,
    encode_purified_core,
    human_projection_sidecar,
    purification_result,
    purified_machine_hash,
    purified_roundtrip_ok,
)


def _constraint(reason: str, *, relation: str = "eq"):
    return {
        "kind": "shape_obligation",
        "proof_status": "unknown",
        "required_relation": relation,
        "runtime_guard": True,
        "reason": reason,
    }


def _project(reason: str = "human explanation", *, op: str = "Add", projection: str = "visible note") -> Project:
    return Project(
        modules=(
            Module(
                id="app",
                graphs=(
                    Graph(
                        id="main",
                        inputs=("x", "y"),
                        outputs=("z",),
                        nodes=(
                            Node(id="lhs", kind="Input", outputs=("x",), attributes={"name": "input.left"}),
                            Node(id="rhs", kind="Input", outputs=("y",), attributes={"name": "input.right"}),
                            Node(
                                id="combine",
                                kind=op,
                                inputs=("x", "y"),
                                outputs=("z",),
                                constraints=(_constraint(reason),),
                                source_projection={"label": projection},
                                provenance={"comment": projection},
                            ),
                        ),
                    ),
                ),
            ),
        ),
        provenance={"project_note": projection},
    )


def test_purification_removes_embedded_human_projection() -> None:
    project = _project()
    manifest = bootstrap_identity_manifest(project)
    result = purification_result(project, manifest)
    assert result.pure
    assert not contains_human_projection(result.record)
    assert any(entry.text == "human explanation" for entry in result.entries)
    blob = encode_purified_core(project, manifest)
    assert blob.startswith(b"NSM5")
    assert b"human explanation" not in blob


def test_reason_change_does_not_change_purified_machine_identity_with_persisted_manifest() -> None:
    left = _project("note A")
    right = _project("note B")
    manifest = bootstrap_identity_manifest(left)
    assert semantic_hash(left) != semantic_hash(right)
    assert encode_purified_core(left, manifest) == encode_purified_core(right, manifest)
    assert purified_machine_hash(left, manifest) == purified_machine_hash(right, manifest)


def test_nonsemantic_projection_changes_only_sidecar() -> None:
    left = _project(projection="human A")
    right = _project(projection="human B")
    manifest = bootstrap_identity_manifest(left)
    assert encode_purified_core(left, manifest) == encode_purified_core(right, manifest)
    left_sidecar = human_projection_sidecar(left, manifest)
    right_sidecar = human_projection_sidecar(right, manifest)
    assert left_sidecar["sidecar_hash"] != right_sidecar["sidecar_hash"]
    assert left_sidecar["purified_machine_hash"] == right_sidecar["purified_machine_hash"]


def test_semantic_mutation_changes_purified_machine_identity() -> None:
    left = _project(op="Add")
    right = _project(op="Subtract")
    manifest = bootstrap_identity_manifest(left)
    assert purified_machine_hash(left, manifest) != purified_machine_hash(right, manifest)


def test_nsm5_roundtrip_is_byte_stable_after_projection_removal() -> None:
    project = _project()
    manifest = bootstrap_identity_manifest(project)
    blob = encode_purified_core(project, manifest)
    restored = decode_purified_core(blob, manifest)
    constraint = restored.modules[0].graphs[0].nodes[2].constraints[0]
    assert "reason" not in constraint
    assert encode_purified_core(restored, manifest) == blob
    assert purified_roundtrip_ok(project, manifest)


def test_fresh_purity_bootstrap_ignores_human_projection() -> None:
    left = _project("reason A", projection="projection A")
    right = _project("reason B", projection="projection B")
    left_manifest = bootstrap_purified_identity_manifest(left)
    right_manifest = bootstrap_purified_identity_manifest(right)
    assert left_manifest.project_sid == right_manifest.project_sid
    left_entries = [(e.kind, e.label, e.parent, e.sid) for e in left_manifest.entries]
    right_entries = [(e.kind, e.label, e.parent, e.sid) for e in right_manifest.entries]
    assert left_entries == right_entries


def test_sidecar_is_hash_linked_to_purified_core() -> None:
    project = _project()
    manifest = bootstrap_identity_manifest(project)
    sidecar = human_projection_sidecar(project, manifest)
    assert sidecar["format"] == "nova.human-projection-sidecar/0.5"
    assert sidecar["project_sid"] == manifest.project_sid.text
    assert sidecar["purified_machine_hash"] == purified_machine_hash(project, manifest)
    assert sidecar["embedded_human_projection"]
    assert sidecar["nonsemantic_projection"]["project_provenance"]["project_note"] == "visible note"
    assert sidecar["sidecar_hash"].startswith("sha256:")


def test_embedded_projection_anchor_is_stable_across_text_edits() -> None:
    left = _project("reason A")
    right = _project("reason B")
    manifest = bootstrap_identity_manifest(left)
    l_entry = purification_result(left, manifest).entries[0]
    r_entry = purification_result(right, manifest).entries[0]
    assert l_entry.semantic_anchor == r_entry.semantic_anchor
    assert l_entry.owner_sid == r_entry.owner_sid


def test_constraint_order_cannot_be_perturbed_by_human_reason_sorting() -> None:
    def project(a_reason, b_reason):
        return Project(modules=(Module(id="app", graphs=(Graph(
            id="main", outputs=("z",), nodes=(Node(
                id="n", kind="Identity", outputs=("z",), constraints=(
                    {"kind": "shape_obligation", "proof_status": "unknown", "required_relation": "eq", "runtime_guard": True, "reason": a_reason},
                    {"kind": "shape_obligation", "proof_status": "unknown", "required_relation": "broadcast_compatible", "runtime_guard": True, "reason": b_reason},
                )
            ),),
        ),)),))
    left = project("zzz", "aaa")
    right = project("aaa", "zzz")
    manifest = bootstrap_identity_manifest(left)
    assert encode_purified_core(left, manifest) == encode_purified_core(right, manifest)

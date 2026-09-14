import pytest

from nova_core.canonical import semantic_hash
from nova_core.domain_identity import (
    decode_domain_core,
    domain_machine_hash,
    domain_roundtrip_ok,
    domain_sidecar,
    encode_domain_core,
)
from nova_core.errors import ValidationError
from nova_core.identity_model import bootstrap_identity_manifest
from nova_core.model import Graph, Module, Node, Project
from nova_core.symbol_domains import SymbolDomain, classify_project_symbols


def _typed_shape():
    return {
        "kind": "tensor_type",
        "dtype": "f32",
        "shape": {
            "kind": "shape",
            "dims": [
                {"kind": "affine_dim", "const": 0, "terms": [["B", 1]]},
                {"kind": "affine_dim", "const": 8, "terms": []},
            ],
        },
        "layout": "row_major",
        "device": "cpu",
    }


def _project() -> Project:
    helper = Graph(
        id="helper",
        inputs=("hx",),
        outputs=("hy",),
        nodes=(Node(id="identity", kind="Identity", inputs=("hx",), outputs=("hy",)),),
    )
    main = Graph(
        id="main",
        inputs=("x",),
        outputs=("y",),
        nodes=(
            Node(
                id="input_node",
                kind="Input",
                outputs=("x",),
                value_type=_typed_shape(),
                attributes={"name": "user.tensor"},
            ),
            Node(
                id="call_node",
                kind="Call",
                inputs=("x",),
                outputs=("y",),
                attributes={"callee": "helper"},
                constraints=({"kind": "shape_obligation", "proof_status": "unknown", "reason": "explain only"},),
                source_projection={"label": "human call"},
                provenance={"note": "human documentation"},
                extensions={"vendor_hint": "opaque text"},
            ),
            Node(
                id="message",
                kind="Constant",
                outputs=("msg",),
                attributes={"value": "hello world"},
            ),
        ),
    )
    return Project(
        modules=(Module(id="app", graphs=(main, helper), imports=("ffi.math",), exports=("public.api",)),),
    )


def _values(report, domain):
    return {item.value for item in report.occurrences if item.domain is domain}


def test_classifier_separates_seven_text_domains() -> None:
    report = classify_project_symbols(_project())
    assert report.complete
    assert "app" in _values(report, SymbolDomain.STRUCTURAL_IDENTITY)
    assert "helper" in _values(report, SymbolDomain.STRUCTURAL_IDENTITY)
    assert "Call" in _values(report, SymbolDomain.SEMANTIC_ATOM)
    assert "B" in _values(report, SymbolDomain.SCOPED_SEMANTIC_SYMBOL)
    assert "hello world" in _values(report, SymbolDomain.SEMANTIC_LITERAL)
    assert "user.tensor" in _values(report, SymbolDomain.EXTERNAL_CONTRACT)
    assert "ffi.math" in _values(report, SymbolDomain.EXTERNAL_CONTRACT)
    assert "human call" in _values(report, SymbolDomain.HUMAN_PROJECTION)
    assert "opaque text" in _values(report, SymbolDomain.EXTENSION_PAYLOAD)


def test_reason_is_detected_as_human_projection_leaking_into_semantic_core() -> None:
    report = classify_project_symbols(_project())
    leaks = report.semantic_human_projection_leaks
    assert any(item.value == "explain only" for item in leaks)


def test_nsm4_roundtrip_and_known_text_elimination() -> None:
    project = _project()
    manifest = bootstrap_identity_manifest(project)
    blob = encode_domain_core(project, manifest)
    assert blob.startswith(b"NSM4")
    for token in (b"app", b"main", b"helper", b"call_node", b"Call", b"Input", b"f32", b"row_major", b"cpu"):
        assert token not in blob
    assert b"hello world" in blob
    assert b"user.tensor" in blob
    assert b"B" in blob
    restored = decode_domain_core(blob, manifest)
    assert semantic_hash(restored) == semantic_hash(project)
    assert domain_roundtrip_ok(project, manifest)


def test_call_callee_becomes_structural_id_and_reprojects_under_rename() -> None:
    project = _project()
    manifest = bootstrap_identity_manifest(project)
    module_sid = manifest.resolve("module", "app", parent=manifest.project_sid)
    helper_sid = manifest.resolve("graph", "helper", parent=module_sid)
    main_sid = manifest.resolve("graph", "main", parent=module_sid)
    call_sid = manifest.resolve("node", "call_node", parent=main_sid)
    renamed_manifest = manifest.with_labels({
        module_sid: "module_human",
        helper_sid: "helper_human",
        main_sid: "main_human",
        call_sid: "call_human",
    })
    blob = encode_domain_core(project, manifest)
    renamed = decode_domain_core(blob, renamed_manifest)
    graphs = {g.id: g for g in renamed.modules[0].graphs}
    call_node = next(n for n in graphs["main_human"].nodes if n.id == "call_human")
    assert call_node.attributes["callee"] == "helper_human"
    assert encode_domain_core(renamed, renamed_manifest) == blob
    assert domain_machine_hash(renamed, renamed_manifest) == domain_machine_hash(project, manifest)


def test_known_operator_unknown_attribute_is_rejected_in_strict_mode() -> None:
    project = Project(modules=(Module(id="app", graphs=(Graph(
        id="main",
        outputs=("y",),
        nodes=(Node(id="n", kind="Add", outputs=("y",), attributes={"mystery": "text"}),),
    ),)),))
    report = classify_project_symbols(project)
    assert not report.complete
    assert "mystery" in _values(report, SymbolDomain.UNCLASSIFIED)
    manifest = bootstrap_identity_manifest(project)
    with pytest.raises(ValidationError):
        encode_domain_core(project, manifest)
    assert encode_domain_core(project, manifest, strict=False).startswith(b"NSM4")


def test_unknown_operator_owns_its_extension_attributes() -> None:
    project = Project(modules=(Module(id="app", graphs=(Graph(
        id="main", outputs=("y",), nodes=(Node(
            id="n", kind="FutureQuantumOp", outputs=("y",), attributes={"mode": "phase weave"}
        ),),
    ),)),))
    report = classify_project_symbols(project)
    assert report.complete
    assert "phase weave" in _values(report, SymbolDomain.EXTENSION_PAYLOAD)
    manifest = bootstrap_identity_manifest(project)
    restored = decode_domain_core(encode_domain_core(project, manifest), manifest)
    assert restored.modules[0].graphs[0].nodes[0].kind == "FutureQuantumOp"
    assert restored.modules[0].graphs[0].nodes[0].attributes["mode"] == "phase weave"


def test_domain_sidecar_exposes_counts_and_audit_fingerprint() -> None:
    project = _project()
    manifest = bootstrap_identity_manifest(project)
    sidecar = domain_sidecar(project, manifest)
    assert sidecar["format"] == "nova.symbol-domain-report/0.4"
    assert sidecar["complete"] is True
    assert sidecar["counts"]["scoped_semantic_symbol"] >= 1
    assert sidecar["semantic_human_projection_leak_count"] >= 1
    assert sidecar["fingerprint"].startswith("sha256:")
    assert sidecar["domain_machine_hash"].startswith("sha256:")

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .canonical import project_record, semantic_hash
from .codec import decode_project
from .domain_identity import (
    _restore_embedded_structural_refs,
    _undomain,
    domain_core_record,
)
from .errors import DecodeError
from .human_projection import (
    PURIFICATION_REVISION,
    PurificationResult,
    projection_entries_record,
    purify_domain_record,
)
from .identity_model import IdentityEntry, IdentityManifest, StructuralID, bootstrap_identity_manifest
from .identity_projection import restore_legacy_record
from .model import Project
from .purified_wire import decode_purified_record, encode_purified_record
from .symbol_minimal import annotation_sidecar


_PURE_BOOTSTRAP_TAG = b"NOVA-PROJECT-ID-v0.5-PURE\0"
_PURE_SID_TAG = b"NOVA-STRUCTURAL-ID-v0.5-PURE\0"


def _thaw(value: Any) -> Any:
    to_record = getattr(value, "to_record", None)
    if callable(to_record):
        return _thaw(to_record())
    if isinstance(value, Mapping):
        return {str(k): _thaw(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_thaw(v) for v in value]
    return value


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        _thaw(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _value_labels(graph: Mapping[str, Any]) -> tuple[str, ...]:
    labels = {
        str(value)
        for field in ("inputs", "outputs")
        for value in graph.get(field, ()) or ()
    }
    for node in graph.get("nodes", ()) or ():
        labels.update(
            str(value)
            for field in ("inputs", "outputs")
            for value in node.get(field, ()) or ()
        )
    return tuple(sorted(labels, key=lambda item: item.encode("utf-8")))


def _derive(project_sid: StructuralID, kind: str, label: str, parent: StructuralID | None) -> StructuralID:
    h = hashlib.sha256()
    for part in (
        _PURE_SID_TAG,
        project_sid.raw,
        kind.encode("ascii"),
        b"\0",
        b"" if parent is None else parent.raw,
        b"\0",
        label.encode("utf-8"),
    ):
        h.update(part)
    return StructuralID(h.digest()[:16])


def _purity_seed_record(project: Project) -> Mapping[str, Any]:
    provisional = bootstrap_identity_manifest(project)
    domain = domain_core_record(project, provisional, strict=True)
    purified = purify_domain_record(domain, provisional).record
    legacy_identity = _restore_embedded_structural_refs(_undomain(purified), provisional)
    legacy_record = restore_legacy_record(legacy_identity, provisional)
    pure_project = decode_project(legacy_record)
    return project_record(pure_project, semantic=True)


def bootstrap_purified_identity_manifest(project: Project) -> IdentityManifest:
    """Fresh v0.5 migration bootstrap.

    Existing manifests remain authoritative and MUST NOT be regenerated.
    This helper is only for projects that do not yet have a persistent identity manifest.
    Human Projection fields do not participate in the bootstrap seed.
    """

    record = _purity_seed_record(project)
    seed = hashlib.sha256(_PURE_BOOTSTRAP_TAG + _canonical_json_bytes(record)).digest()
    project_sid = StructuralID(hashlib.sha256(_PURE_BOOTSTRAP_TAG + seed).digest()[:16])
    entries: list[IdentityEntry] = []
    for module in record.get("modules", ()) or ():
        m_label = str(module["id"])
        m_sid = _derive(project_sid, "module", m_label, project_sid)
        entries.append(IdentityEntry(m_sid, "module", m_label, project_sid))
        for graph in module.get("graphs", ()) or ():
            g_label = str(graph["id"])
            g_sid = _derive(project_sid, "graph", g_label, m_sid)
            entries.append(IdentityEntry(g_sid, "graph", g_label, m_sid))
            for node in graph.get("nodes", ()) or ():
                n_label = str(node["id"])
                entries.append(IdentityEntry(_derive(project_sid, "node", n_label, g_sid), "node", n_label, g_sid))
            for label in _value_labels(graph):
                entries.append(IdentityEntry(_derive(project_sid, "value", label, g_sid), "value", label, g_sid))
    return IdentityManifest(project_sid, tuple(entries))


def purification_result(project: Project, manifest: IdentityManifest, *, strict: bool = True) -> PurificationResult:
    return purify_domain_record(domain_core_record(project, manifest, strict=strict), manifest)


def purified_core_record(project: Project, manifest: IdentityManifest, *, strict: bool = True) -> Any:
    return purification_result(project, manifest, strict=strict).record


def encode_purified_core(project: Project, manifest: IdentityManifest, *, strict: bool = True) -> bytes:
    record = purified_core_record(project, manifest, strict=strict)
    envelope = [PURIFICATION_REVISION, manifest.project_sid.raw, record]
    return encode_purified_record(envelope)


def decode_purified_core(blob: bytes | bytearray | memoryview, manifest: IdentityManifest) -> Project:
    wrapper = decode_purified_record(blob)
    if not isinstance(wrapper, list) or len(wrapper) != 3:
        raise DecodeError("invalid NSM5 envelope")
    revision, root, purified = wrapper
    if int(revision) != PURIFICATION_REVISION:
        raise DecodeError("unsupported NSM5 purification revision")
    if not isinstance(root, (bytes, bytearray)) or bytes(root) != manifest.project_sid.raw:
        raise DecodeError("NSM5 identity root does not match manifest")
    if not isinstance(purified, Mapping):
        raise DecodeError("NSM5 payload must be a mapping")
    identity_record = _restore_embedded_structural_refs(_undomain(purified), manifest)
    return decode_project(restore_legacy_record(identity_record, manifest))


def purified_machine_hash(project: Project, manifest: IdentityManifest, *, strict: bool = True) -> str:
    return "sha256:" + hashlib.sha256(encode_purified_core(project, manifest, strict=strict)).hexdigest()


def purified_roundtrip_ok(project: Project, manifest: IdentityManifest, *, strict: bool = True) -> bool:
    blob = encode_purified_core(project, manifest, strict=strict)
    restored = decode_purified_core(blob, manifest)
    return encode_purified_core(restored, manifest, strict=strict) == blob


def human_projection_sidecar(project: Project, manifest: IdentityManifest, *, strict: bool = True) -> dict[str, Any]:
    result = purification_result(project, manifest, strict=strict)
    legacy = _thaw(annotation_sidecar(project))
    sidecar: dict[str, Any] = {
        "format": "nova.human-projection-sidecar/0.5",
        "purification_revision": PURIFICATION_REVISION,
        "project_sid": manifest.project_sid.text,
        "purified_machine_hash": purified_machine_hash(project, manifest, strict=strict),
        "legacy_semantic_hash": semantic_hash(project),
        "embedded_human_projection": projection_entries_record(result.entries),
        "nonsemantic_projection": legacy,
    }
    sidecar_payload = dict(sidecar)
    sidecar["sidecar_hash"] = "sha256:" + hashlib.sha256(
        b"NOVA-HUMAN-PROJECTION-SIDECAR-v0.5\0" + _canonical_json_bytes(sidecar_payload)
    ).hexdigest()
    return sidecar


__all__ = [
    "bootstrap_purified_identity_manifest",
    "decode_purified_core",
    "encode_purified_core",
    "human_projection_sidecar",
    "purification_result",
    "purified_core_record",
    "purified_machine_hash",
    "purified_roundtrip_ok",
]

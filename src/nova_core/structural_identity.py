from __future__ import annotations

import hashlib
from typing import Any, Mapping

from .canonical import semantic_hash
from .codec import decode_project
from .errors import DecodeError
from .identity_model import (
    IDENTITY_REVISION,
    IdentityEntry,
    IdentityManifest,
    StructuralID,
    bootstrap_identity_manifest,
)
from .identity_projection import identity_core_record, restore_legacy_record
from .identity_wire import decode_identity_record, encode_identity_record
from .model import Project


def _sid(
    manifest: IdentityManifest,
    kind: str,
    label: str,
    parent: StructuralID,
) -> StructuralID:
    return manifest.resolve(kind, label, parent=parent)


def _wire(project: Project, manifest: IdentityManifest) -> list[Any]:
    # Positional envelope avoids human-readable wrapper field names.
    return [
        IDENTITY_REVISION,
        manifest.project_sid.raw,
        identity_core_record(project, manifest),
    ]


def encode_identity_core(project: Project, manifest: IdentityManifest) -> bytes:
    return encode_identity_record(_wire(project, manifest))


def decode_identity_core(
    blob: bytes | bytearray | memoryview,
    manifest: IdentityManifest,
) -> Project:
    data = bytes(blob)
    if not data.startswith(b"NSM3"):
        raise DecodeError("identity core requires NSM3 magic")
    wrapper = decode_identity_record(data)
    if not isinstance(wrapper, list) or len(wrapper) != 3:
        raise DecodeError("invalid NSM3 identity envelope")
    revision, root, identity_record = wrapper
    if int(revision) != IDENTITY_REVISION:
        raise DecodeError("unsupported NSM3 identity revision")
    if not isinstance(root, (bytes, bytearray)) or bytes(root) != manifest.project_sid.raw:
        raise DecodeError("NSM3 identity root does not match manifest")
    if not isinstance(identity_record, Mapping):
        raise DecodeError("NSM3 project payload must be a mapping")
    return decode_project(restore_legacy_record(identity_record, manifest))


def machine_identity_hash(project: Project, manifest: IdentityManifest) -> str:
    return "sha256:" + hashlib.sha256(encode_identity_core(project, manifest)).hexdigest()


def identity_roundtrip_ok(project: Project, manifest: IdentityManifest) -> bool:
    restored = decode_identity_core(encode_identity_core(project, manifest), manifest)
    return (
        semantic_hash(restored) == semantic_hash(project)
        and machine_identity_hash(restored, manifest)
        == machine_identity_hash(project, manifest)
    )


def apply_label_projection(
    project: Project,
    manifest: IdentityManifest,
    updates: Mapping[str | StructuralID, str],
) -> tuple[Project, IdentityManifest]:
    """Rename human projection labels without minting new structural IDs."""

    core = identity_core_record(project, manifest)
    renamed_manifest = manifest.with_labels(updates)
    return decode_project(restore_legacy_record(core, renamed_manifest)), renamed_manifest


def identity_sidecar(project: Project, manifest: IdentityManifest) -> dict[str, Any]:
    """Labels and non-authoritative annotations keyed by StructuralID."""

    entries: dict[str, dict[str, Any]] = {
        entry.sid.text: {
            "kind": entry.kind,
            "label": entry.label,
            "parent": None if entry.parent is None else entry.parent.text,
        }
        for entry in manifest.entries
    }
    for module in project.modules:
        m_sid = _sid(manifest, "module", module.id, manifest.project_sid)
        if module.provenance:
            entries[m_sid.text]["provenance"] = dict(module.provenance)
        for graph in module.graphs:
            g_sid = _sid(manifest, "graph", graph.id, m_sid)
            if graph.provenance:
                entries[g_sid.text]["provenance"] = dict(graph.provenance)
            for node in graph.nodes:
                n_sid = _sid(manifest, "node", node.id, g_sid)
                if node.source_projection is not None:
                    entries[n_sid.text]["source_projection"] = node.source_projection
                if node.provenance:
                    entries[n_sid.text]["provenance"] = dict(node.provenance)
    sidecar: dict[str, Any] = {
        "format": "nova.identity-sidecar/0.3",
        "identity_revision": manifest.revision,
        "project_sid": manifest.project_sid.text,
        "machine_identity_hash": machine_identity_hash(project, manifest),
        "entries": entries,
    }
    if project.header.provenance:
        sidecar["header_provenance"] = dict(project.header.provenance)
    if project.artifacts:
        sidecar["artifacts"] = list(project.artifacts)
    if project.provenance:
        sidecar["project_provenance"] = dict(project.provenance)
    return sidecar


__all__ = [
    "IDENTITY_REVISION",
    "IdentityEntry",
    "IdentityManifest",
    "StructuralID",
    "apply_label_projection",
    "bootstrap_identity_manifest",
    "decode_identity_core",
    "encode_identity_core",
    "identity_core_record",
    "identity_roundtrip_ok",
    "identity_sidecar",
    "machine_identity_hash",
    "restore_legacy_record",
]

from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any, Mapping

from .canonical import project_record
from .codec import decode_project
from .domain_identity import _restore_embedded_structural_refs, _undomain
from .errors import DecodeError, ValidationError
from .identity_model import IdentityManifest, StructuralID
from .identity_projection import restore_legacy_record
from .model import Project
from .purified_identity import purified_core_record
from .scoped_symbols import (
    SCOPED_SYMBOL_REVISION,
    ScopedSymbolID,
    ScopedSymbolManifest,
    scoped_symbol_manifest_hash,
    symbol_projection_anchor,
)
from .scoped_wire import ScopedSymbolRef, decode_scoped_record, encode_scoped_record
from .symbol_domains import DomainText, SymbolDomain


def _replace_scoped_for_graph(
    value: Any,
    *,
    scope_sid: StructuralID,
    manifest: ScopedSymbolManifest,
) -> Any:
    if isinstance(value, DomainText):
        if value.domain is SymbolDomain.SCOPED_SEMANTIC_SYMBOL:
            try:
                symbol_id = manifest.resolve(scope_sid, value.text)
            except KeyError as exc:
                raise ValidationError(
                    "scoped semantic symbol has no persistent binder identity",
                    context={"scope_sid": scope_sid.text, "label": value.text},
                ) from exc
            return ScopedSymbolRef(scope_sid.raw, symbol_id)
        return value
    if isinstance(value, Mapping):
        return {
            _replace_scoped_for_graph(key, scope_sid=scope_sid, manifest=manifest):
            _replace_scoped_for_graph(item, scope_sid=scope_sid, manifest=manifest)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            _replace_scoped_for_graph(item, scope_sid=scope_sid, manifest=manifest)
            for item in value
        ]
    return value


def _contains_scoped_text(value: Any) -> bool:
    if isinstance(value, DomainText):
        return value.domain is SymbolDomain.SCOPED_SEMANTIC_SYMBOL
    if isinstance(value, Mapping):
        return any(_contains_scoped_text(k) or _contains_scoped_text(v) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains_scoped_text(v) for v in value)
    return False


def scoped_core_record(
    project: Project,
    identity_manifest: IdentityManifest,
    scoped_manifest: ScopedSymbolManifest,
    *,
    strict: bool = True,
) -> dict[Any, Any]:
    if scoped_manifest.project_sid != identity_manifest.project_sid:
        raise ValidationError("scoped symbol manifest belongs to a different project identity")
    record = deepcopy(purified_core_record(project, identity_manifest, strict=strict))
    modules_out = []
    for module in record.get("modules", ()) or ():
        m = dict(module)
        graphs_out = []
        for graph in module.get("graphs", ()) or ():
            g = dict(graph)
            raw_scope = g.get("id")
            if not isinstance(raw_scope, (bytes, bytearray)) or len(raw_scope) != 16:
                raise ValidationError("NSM6 graph scope must be a StructuralID")
            scope_sid = StructuralID(bytes(raw_scope))
            g = _replace_scoped_for_graph(g, scope_sid=scope_sid, manifest=scoped_manifest)
            graphs_out.append(g)
        m["graphs"] = graphs_out
        modules_out.append(m)
    record["modules"] = modules_out
    if _contains_scoped_text(record):
        raise ValidationError("NSM6 canonical core still contains textual scoped semantic symbols")
    return record


def _restore_scoped_for_graph(
    value: Any,
    *,
    graph_scope: StructuralID,
    manifest: ScopedSymbolManifest,
) -> Any:
    if isinstance(value, ScopedSymbolRef):
        if value.scope_sid != graph_scope.raw:
            raise DecodeError("NSM6 ScopedSymbolRef escaped its graph scope")
        entry = manifest.entry_by_id(value.symbol_id)
        if entry.scope_sid != graph_scope:
            raise DecodeError("NSM6 scoped symbol identity belongs to a different scope")
        return DomainText(SymbolDomain.SCOPED_SEMANTIC_SYMBOL, entry.label)
    if isinstance(value, Mapping):
        return {
            _restore_scoped_for_graph(k, graph_scope=graph_scope, manifest=manifest):
            _restore_scoped_for_graph(v, graph_scope=graph_scope, manifest=manifest)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_restore_scoped_for_graph(v, graph_scope=graph_scope, manifest=manifest) for v in value]
    return value


def encode_scoped_core(
    project: Project,
    identity_manifest: IdentityManifest,
    scoped_manifest: ScopedSymbolManifest,
    *,
    strict: bool = True,
) -> bytes:
    record = scoped_core_record(project, identity_manifest, scoped_manifest, strict=strict)
    identity_hash = scoped_symbol_manifest_hash(scoped_manifest, include_labels=False)
    envelope = [
        SCOPED_SYMBOL_REVISION,
        identity_manifest.project_sid.raw,
        bytes.fromhex(identity_hash.split(":", 1)[1]),
        record,
    ]
    return encode_scoped_record(envelope)


def decode_scoped_core(
    blob: bytes | bytearray | memoryview,
    identity_manifest: IdentityManifest,
    scoped_manifest: ScopedSymbolManifest,
) -> Project:
    wrapper = decode_scoped_record(blob)
    if not isinstance(wrapper, list) or len(wrapper) != 4:
        raise DecodeError("invalid NSM6 envelope")
    revision, root, manifest_hash, record = wrapper
    if int(revision) != SCOPED_SYMBOL_REVISION:
        raise DecodeError("unsupported NSM6 scoped-symbol revision")
    if not isinstance(root, (bytes, bytearray)) or bytes(root) != identity_manifest.project_sid.raw:
        raise DecodeError("NSM6 identity root does not match structural manifest")
    if scoped_manifest.project_sid != identity_manifest.project_sid:
        raise DecodeError("NSM6 scoped-symbol manifest belongs to a different project")
    expected_manifest_hash = bytes.fromhex(
        scoped_symbol_manifest_hash(scoped_manifest, include_labels=False).split(":", 1)[1]
    )
    if not isinstance(manifest_hash, (bytes, bytearray)) or bytes(manifest_hash) != expected_manifest_hash:
        raise DecodeError("NSM6 scoped-symbol manifest identity hash mismatch")
    if not isinstance(record, Mapping):
        raise DecodeError("NSM6 payload must be a mapping")

    restored = deepcopy(dict(record))
    modules_out = []
    for module in restored.get("modules", ()) or ():
        m = dict(module)
        graphs_out = []
        for graph in module.get("graphs", ()) or ():
            g = dict(graph)
            raw_scope = g.get("id")
            if not isinstance(raw_scope, (bytes, bytearray)) or len(raw_scope) != 16:
                raise DecodeError("NSM6 decoded graph scope is invalid")
            scope_sid = StructuralID(bytes(raw_scope))
            graphs_out.append(
                _restore_scoped_for_graph(g, graph_scope=scope_sid, manifest=scoped_manifest)
            )
        m["graphs"] = graphs_out
        modules_out.append(m)
    restored["modules"] = modules_out
    identity_record = _restore_embedded_structural_refs(_undomain(restored), identity_manifest)
    return decode_project(restore_legacy_record(identity_record, identity_manifest))


def scoped_machine_hash(
    project: Project,
    identity_manifest: IdentityManifest,
    scoped_manifest: ScopedSymbolManifest,
    *,
    strict: bool = True,
) -> str:
    return "sha256:" + hashlib.sha256(
        encode_scoped_core(project, identity_manifest, scoped_manifest, strict=strict)
    ).hexdigest()


def scoped_roundtrip_ok(
    project: Project,
    identity_manifest: IdentityManifest,
    scoped_manifest: ScopedSymbolManifest,
    *,
    strict: bool = True,
) -> bool:
    blob = encode_scoped_core(project, identity_manifest, scoped_manifest, strict=strict)
    restored = decode_scoped_core(blob, identity_manifest, scoped_manifest)
    return encode_scoped_core(restored, identity_manifest, scoped_manifest, strict=strict) == blob


def _rename_terms(value: Any, replacements: Mapping[str, str]) -> Any:
    if isinstance(value, Mapping):
        out: dict[Any, Any] = {}
        for key, item in value.items():
            if str(key) == "terms" and isinstance(item, (list, tuple)):
                terms = []
                for term in item:
                    if isinstance(term, (list, tuple)) and len(term) >= 2 and isinstance(term[0], str):
                        terms.append([replacements.get(term[0], term[0]), *list(term[1:])])
                    else:
                        terms.append(_rename_terms(term, replacements))
                terms.sort(key=lambda t: str(t[0]).encode("utf-8") if isinstance(t, list) and t else b"")
                out[key] = terms
            else:
                out[key] = _rename_terms(item, replacements)
        return out
    if isinstance(value, list):
        return [_rename_terms(item, replacements) for item in value]
    return value


def _rename_graph_semantics(graph: dict[str, Any], replacements: Mapping[str, str]) -> None:
    for field in ("constraints", "attributes"):
        if field in graph:
            graph[field] = _rename_terms(graph[field], replacements)
    for node in graph.get("nodes", ()) or ():
        for field in ("value_type", "shape_type", "effect_type", "differentiation_type", "constraints", "attributes"):
            if field in node:
                node[field] = _rename_terms(node[field], replacements)
    for edge in graph.get("edges", ()) or ():
        for field in ("constraints", "attributes"):
            if field in edge:
                edge[field] = _rename_terms(edge[field], replacements)


def apply_scoped_symbol_projection(
    project: Project,
    identity_manifest: IdentityManifest,
    scoped_manifest: ScopedSymbolManifest,
    updates: Mapping[ScopedSymbolID | str, str],
) -> tuple[Project, ScopedSymbolManifest]:
    new_manifest = scoped_manifest.with_labels(updates)
    raw = deepcopy(project_record(project, semantic=False))
    raw["constraints"] = _rename_terms(raw.get("constraints", []), {})
    raw["attributes"] = _rename_terms(raw.get("attributes", {}), {})
    for module in raw.get("modules", ()) or ():
        try:
            m_sid = identity_manifest.resolve("module", str(module["id"]), parent=identity_manifest.project_sid)
        except KeyError as exc:
            raise ValidationError("module label cannot be resolved during scoped projection") from exc
        if "attributes" in module:
            module["attributes"] = _rename_terms(module["attributes"], {})
        for graph in module.get("graphs", ()) or ():
            g_sid = identity_manifest.resolve("graph", str(graph["id"]), parent=m_sid)
            replacements: dict[str, str] = {}
            for entry in scoped_manifest.entries:
                if entry.scope_sid == g_sid:
                    new_entry = new_manifest.entry_by_id(entry.symbol_id)
                    replacements[entry.label] = new_entry.label
            _rename_graph_semantics(graph, replacements)
    return decode_project(raw), new_manifest


def scoped_symbol_sidecar(
    project: Project,
    identity_manifest: IdentityManifest,
    scoped_manifest: ScopedSymbolManifest,
) -> dict[str, Any]:
    return {
        "format": "nova.scoped-symbol-projection/0.6",
        "project_sid": identity_manifest.project_sid.text,
        "scoped_manifest_identity_hash": scoped_symbol_manifest_hash(scoped_manifest, include_labels=False),
        "scoped_manifest_projection_hash": scoped_symbol_manifest_hash(scoped_manifest, include_labels=True),
        "scoped_machine_hash": scoped_machine_hash(project, identity_manifest, scoped_manifest),
        "entries": [
            {
                **entry.to_record(),
                "projection_anchor": symbol_projection_anchor(entry),
            }
            for entry in sorted(scoped_manifest.entries, key=lambda item: item.symbol_id.raw)
        ],
    }


__all__ = [
    "apply_scoped_symbol_projection",
    "decode_scoped_core",
    "encode_scoped_core",
    "scoped_core_record",
    "scoped_machine_hash",
    "scoped_roundtrip_ok",
    "scoped_symbol_sidecar",
]

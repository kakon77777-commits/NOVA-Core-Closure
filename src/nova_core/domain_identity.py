from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any, Mapping

from .canonical import semantic_hash
from .codec import decode_project
from .errors import DecodeError, ValidationError
from .identity_model import IdentityManifest, StructuralID
from .identity_projection import identity_core_record, restore_legacy_record
from .model import Project
from .semantic_registry import global_code
from .symbol_domains import (
    DOMAIN_REVISION,
    DomainText,
    SymbolDomain,
    classify_project_symbols,
    domain_report_sidecar,
)
from .symbol_minimal import _global_ref
from .domain_wire import decode_domain_record, encode_domain_record


_ATTR_KEYS = {
    "name", "value", "shape", "axes", "axis", "keepdims", "callee", "trip_count", "body_kind"
}
_SEMANTIC_ATOM_FIELDS = {
    "kind", "dtype", "layout", "device", "effect_type", "differentiation_type",
    "proof_status", "relation", "required_relation",
}

_PROJECT_KEYS = {"header", "modules", "constraints", "attributes"}
_HEADER_KEYS = {"nova_core_version", "schema_version", "feature_flags"}
_MODULE_KEYS = {"id", "imports", "exports", "graphs", "attributes"}
_GRAPH_KEYS = {"id", "inputs", "outputs", "nodes", "edges", "constraints", "attributes"}
_NODE_KEYS = {
    "id", "kind", "inputs", "outputs", "value_type", "shape_type", "effect_type",
    "differentiation_type", "constraints", "attributes",
}
_EDGE_KEYS = {"source", "target", "kind", "constraints", "attributes"}
_RECORD_KEYS = {
    "kind", "dtype", "shape", "layout", "device", "dims", "const", "terms", "relation",
    "reason", "required_relation", "proof_status", "runtime_guard", "left", "right",
}


def _global_or_domain(
    value: str,
    domain: SymbolDomain,
    *,
    field_name: str | None = None,
    container: Mapping[str, Any] | None = None,
) -> str | DomainText:
    ref = _global_ref(value, field_name=field_name, container=container)
    return value if ref is not None else DomainText(domain, value)


def _wrap_all(value: Any, domain: SymbolDomain) -> Any:
    to_record = getattr(value, "to_record", None)
    if callable(to_record): value = to_record()
    if isinstance(value, str): return DomainText(domain, value)
    if isinstance(value, Mapping):
        return {DomainText(domain, str(k)): _wrap_all(v, domain) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [_wrap_all(v, domain) for v in value]
    return value


def _domainize_record(value: Any, *, default: SymbolDomain = SymbolDomain.UNCLASSIFIED) -> Any:
    to_record = getattr(value, "to_record", None)
    if callable(to_record): value = to_record()
    if isinstance(value, str): return DomainText(default, value)
    if isinstance(value, (list, tuple)):
        return [_domainize_record(item, default=default) for item in value]
    if not isinstance(value, Mapping): return value

    out: dict[Any, Any] = {}
    kind = value.get("kind")
    known = _RECORD_KEYS if isinstance(kind, str) else set()
    for key, item in value.items():
        key_text = str(key)
        out_key: Any = key_text if key_text in known else DomainText(SymbolDomain.EXTENSION_PAYLOAD, key_text)
        if key_text in _SEMANTIC_ATOM_FIELDS and isinstance(item, str):
            out[out_key] = _global_or_domain(item, SymbolDomain.SEMANTIC_ATOM, field_name=key_text, container=value)
        elif key_text == "reason" and isinstance(item, str):
            out[out_key] = DomainText(SymbolDomain.HUMAN_PROJECTION, item)
        elif key_text == "terms" and isinstance(item, (list, tuple)):
            terms = []
            for term in item:
                if isinstance(term, (list, tuple)) and term and isinstance(term[0], str):
                    terms.append([DomainText(SymbolDomain.SCOPED_SEMANTIC_SYMBOL, term[0]), *list(term[1:])])
                else:
                    terms.append(_domainize_record(term, default=default))
            out[out_key] = terms
        else:
            out[out_key] = _domainize_record(item, default=default)
    return out


def _extension_entries(mapping: Mapping[str, Any], known: set[str], out: dict[Any, Any]) -> None:
    for key, item in mapping.items():
        key_text = str(key)
        if key_text in known: continue
        out[DomainText(SymbolDomain.EXTENSION_PAYLOAD, key_text)] = _wrap_all(item, SymbolDomain.EXTENSION_PAYLOAD)


def _domainize_attributes(
    attrs: Mapping[str, Any],
    *,
    node_kind: str,
    module_sid: StructuralID,
    manifest: IdentityManifest,
) -> dict[Any, Any]:
    out: dict[Any, Any] = {}
    known_operator = global_code("operator", node_kind) is not None
    for key, item in attrs.items():
        key_text = str(key)
        if key_text in _ATTR_KEYS:
            out_key: Any = key_text
        else:
            key_domain = SymbolDomain.UNCLASSIFIED if known_operator else SymbolDomain.EXTENSION_PAYLOAD
            out_key = DomainText(key_domain, key_text)

        if node_kind in {"Input", "Parameter"} and key_text == "name":
            out[out_key] = _wrap_all(item, SymbolDomain.EXTERNAL_CONTRACT)
        elif node_kind == "Call" and key_text == "callee" and isinstance(item, str):
            try:
                out[out_key] = manifest.resolve("graph", item, parent=module_sid).raw
            except KeyError as exc:
                raise ValidationError(
                    "Call callee cannot be resolved to a structural graph identity",
                    context={"callee": item, "module_sid": module_sid.text},
                ) from exc
        elif node_kind == "BoundedLoop" and key_text == "body_kind" and isinstance(item, str):
            out[out_key] = _global_or_domain(item, SymbolDomain.SEMANTIC_ATOM, field_name="kind", container={"id": b"x", "inputs": [], "outputs": [], "kind": item})
        elif node_kind == "Constant" and key_text == "value":
            out[out_key] = _wrap_all(item, SymbolDomain.SEMANTIC_LITERAL)
        elif key_text not in _ATTR_KEYS:
            out[out_key] = _wrap_all(item, SymbolDomain.UNCLASSIFIED if known_operator else SymbolDomain.EXTENSION_PAYLOAD)
        else:
            out[out_key] = _domainize_record(item)
    return out


def domain_core_record(project: Project, manifest: IdentityManifest, *, strict: bool = True) -> dict[Any, Any]:
    """Identity-normalized semantic record with every remaining text value domain-typed.

    Structural labels are already bytes from v0.3. Known semantic atoms remain strings only
    long enough for the NSM4 wire encoder to lower them to GlobalRefs. All other strings are
    wrapped as DomainText. In strict mode an audit containing UNCLASSIFIED occurrences is rejected.
    """

    report = classify_project_symbols(project)
    if strict and report.unclassified:
        first = report.unclassified[0]
        raise ValidationError(
            "NOVA v0.4 refuses unclassified semantic text",
            context={"path": list(first.path), "value": first.value, "count": len(report.unclassified)},
        )

    base = identity_core_record(project, manifest)
    out: dict[Any, Any] = {}

    header = dict(base.get("header", {}))
    header_out: dict[Any, Any] = {}
    for key, item in header.items():
        if key in {"nova_core_version", "schema_version"} and isinstance(item, str):
            header_out[key] = DomainText(SymbolDomain.SEMANTIC_ATOM, item)
        elif key == "feature_flags":
            header_out[key] = [DomainText(SymbolDomain.SEMANTIC_ATOM, str(v)) for v in item]
        elif key in _HEADER_KEYS:
            header_out[key] = _domainize_record(item)
        else:
            header_out[DomainText(SymbolDomain.EXTENSION_PAYLOAD, str(key))] = _wrap_all(item, SymbolDomain.EXTENSION_PAYLOAD)
    out["header"] = header_out

    modules_out = []
    for module in base.get("modules", ()) or ():
        m = dict(module)
        m_sid = StructuralID(bytes(m["id"]))
        m_out: dict[Any, Any] = {
            "id": m["id"],
            "imports": [_wrap_all(v, SymbolDomain.EXTERNAL_CONTRACT) for v in m.get("imports", ()) or ()],
            "exports": [_wrap_all(v, SymbolDomain.EXTERNAL_CONTRACT) for v in m.get("exports", ()) or ()],
            "attributes": _domainize_record(m.get("attributes", {})),
        }
        graphs_out = []
        for graph in m.get("graphs", ()) or ():
            g = dict(graph)
            g_out: dict[Any, Any] = {
                "id": g["id"],
                "inputs": list(g.get("inputs", ()) or ()),
                "outputs": list(g.get("outputs", ()) or ()),
                "constraints": [_domainize_record(v) for v in g.get("constraints", ()) or ()],
                "attributes": _domainize_record(g.get("attributes", {})),
            }
            nodes_out = []
            for node in g.get("nodes", ()) or ():
                n = dict(node)
                kind = str(n.get("kind", ""))
                n_out: dict[Any, Any] = {
                    "id": n["id"],
                    "kind": _global_or_domain(kind, SymbolDomain.SEMANTIC_ATOM, field_name="kind", container=n),
                    "inputs": list(n.get("inputs", ()) or ()),
                    "outputs": list(n.get("outputs", ()) or ()),
                    "value_type": _domainize_record(n.get("value_type")),
                    "shape_type": _domainize_record(n.get("shape_type")),
                    "effect_type": _global_or_domain(n["effect_type"], SymbolDomain.SEMANTIC_ATOM, field_name="effect_type", container=n) if isinstance(n.get("effect_type"), str) else _domainize_record(n.get("effect_type")),
                    "differentiation_type": _global_or_domain(n["differentiation_type"], SymbolDomain.SEMANTIC_ATOM, field_name="differentiation_type", container=n) if isinstance(n.get("differentiation_type"), str) else _domainize_record(n.get("differentiation_type")),
                    "constraints": [_domainize_record(v) for v in n.get("constraints", ()) or ()],
                    "attributes": _domainize_attributes(n.get("attributes", {}), node_kind=kind, module_sid=m_sid, manifest=manifest),
                }
                _extension_entries(n, _NODE_KEYS, n_out)
                nodes_out.append(n_out)
            g_out["nodes"] = nodes_out

            edges_out = []
            for edge in g.get("edges", ()) or ():
                e = dict(edge)
                e_out: dict[Any, Any] = {
                    "source": e["source"],
                    "target": e["target"],
                    "kind": _global_or_domain(str(e.get("kind", "value")), SymbolDomain.SEMANTIC_ATOM, field_name="kind", container=e),
                    "constraints": [_domainize_record(v) for v in e.get("constraints", ()) or ()],
                    "attributes": _domainize_record(e.get("attributes", {})),
                }
                _extension_entries(e, _EDGE_KEYS, e_out)
                edges_out.append(e_out)
            g_out["edges"] = edges_out
            _extension_entries(g, _GRAPH_KEYS, g_out)
            graphs_out.append(g_out)
        m_out["graphs"] = graphs_out
        _extension_entries(m, _MODULE_KEYS, m_out)
        modules_out.append(m_out)
    out["modules"] = modules_out
    out["constraints"] = [_domainize_record(v) for v in base.get("constraints", ()) or ()]
    out["attributes"] = _domainize_record(base.get("attributes", {}))
    _extension_entries(base, _PROJECT_KEYS, out)
    return out


def _undomain(value: Any) -> Any:
    if isinstance(value, DomainText): return value.text
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            raw_key = key.text if isinstance(key, DomainText) else key
            if not isinstance(raw_key, str): raise DecodeError("NSM4 map key did not restore to string")
            out[raw_key] = _undomain(item)
        return out
    if isinstance(value, list): return [_undomain(item) for item in value]
    return value


def _restore_embedded_structural_refs(record: Mapping[str, Any], manifest: IdentityManifest) -> dict[str, Any]:
    out = deepcopy(dict(record))
    for module in out.get("modules", ()) or ():
        m_sid = StructuralID(bytes(module["id"]))
        for graph in module.get("graphs", ()) or ():
            for node in graph.get("nodes", ()) or ():
                if node.get("kind") != "Call": continue
                attrs = node.get("attributes", {})
                callee = attrs.get("callee") if isinstance(attrs, Mapping) else None
                if not isinstance(callee, (bytes, bytearray)): continue
                entry = manifest.entry_by_sid(StructuralID(bytes(callee)))
                if entry.kind != "graph" or entry.parent != m_sid:
                    raise DecodeError("NSM4 Call callee StructuralID is outside module scope")
                attrs = dict(attrs); attrs["callee"] = entry.label; node["attributes"] = attrs
    return out


def encode_domain_core(project: Project, manifest: IdentityManifest, *, strict: bool = True) -> bytes:
    wire = [DOMAIN_REVISION, manifest.project_sid.raw, domain_core_record(project, manifest, strict=strict)]
    return encode_domain_record(wire)


def decode_domain_core(blob: bytes | bytearray | memoryview, manifest: IdentityManifest) -> Project:
    wrapper = decode_domain_record(blob)
    if not isinstance(wrapper, list) or len(wrapper) != 3: raise DecodeError("invalid NSM4 envelope")
    revision, root, domain_record = wrapper
    if int(revision) != DOMAIN_REVISION: raise DecodeError("unsupported NSM4 domain revision")
    if not isinstance(root, (bytes, bytearray)) or bytes(root) != manifest.project_sid.raw:
        raise DecodeError("NSM4 identity root does not match manifest")
    if not isinstance(domain_record, Mapping): raise DecodeError("NSM4 payload must be a mapping")
    identity_record = _restore_embedded_structural_refs(_undomain(domain_record), manifest)
    return decode_project(restore_legacy_record(identity_record, manifest))


def domain_machine_hash(project: Project, manifest: IdentityManifest, *, strict: bool = True) -> str:
    return "sha256:" + hashlib.sha256(encode_domain_core(project, manifest, strict=strict)).hexdigest()


def domain_roundtrip_ok(project: Project, manifest: IdentityManifest, *, strict: bool = True) -> bool:
    restored = decode_domain_core(encode_domain_core(project, manifest, strict=strict), manifest)
    return semantic_hash(restored) == semantic_hash(project)


def domain_sidecar(project: Project, manifest: IdentityManifest) -> dict[str, Any]:
    report = domain_report_sidecar(project)
    report["project_sid"] = manifest.project_sid.text
    report["domain_machine_hash"] = domain_machine_hash(project, manifest, strict=False)
    return report


__all__ = [
    "decode_domain_core",
    "domain_core_record",
    "domain_machine_hash",
    "domain_roundtrip_ok",
    "domain_sidecar",
    "encode_domain_core",
]

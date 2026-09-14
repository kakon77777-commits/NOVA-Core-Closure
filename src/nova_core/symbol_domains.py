from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping

from .model import Project
from .semantic_registry import global_code


DOMAIN_REVISION = 1


class SymbolDomain(str, Enum):
    STRUCTURAL_IDENTITY = "structural_identity"
    SEMANTIC_ATOM = "semantic_atom"
    SCOPED_SEMANTIC_SYMBOL = "scoped_semantic_symbol"
    SEMANTIC_LITERAL = "semantic_literal"
    EXTERNAL_CONTRACT = "external_contract"
    HUMAN_PROJECTION = "human_projection"
    EXTENSION_PAYLOAD = "extension_payload"
    UNCLASSIFIED = "unclassified"


_DOMAIN_CODE = {
    SymbolDomain.STRUCTURAL_IDENTITY: 1,
    SymbolDomain.SEMANTIC_ATOM: 2,
    SymbolDomain.SCOPED_SEMANTIC_SYMBOL: 3,
    SymbolDomain.SEMANTIC_LITERAL: 4,
    SymbolDomain.EXTERNAL_CONTRACT: 5,
    SymbolDomain.HUMAN_PROJECTION: 6,
    SymbolDomain.EXTENSION_PAYLOAD: 7,
    SymbolDomain.UNCLASSIFIED: 255,
}
_CODE_DOMAIN = {value: key for key, value in _DOMAIN_CODE.items()}


class DomainDisposition(str, Enum):
    STABLE_ID = "stable_id"
    GLOBAL_OR_TYPED_ATOM = "global_or_typed_atom"
    SCOPED_ID_PENDING = "scoped_id_pending"
    PRESERVE_LITERAL = "preserve_literal"
    PRESERVE_CONTRACT = "preserve_contract"
    SIDECAR = "sidecar"
    OPAQUE_OWNER = "opaque_owner"
    REJECT_UNTIL_CLASSIFIED = "reject_until_classified"


_DISPOSITION = {
    SymbolDomain.STRUCTURAL_IDENTITY: DomainDisposition.STABLE_ID,
    SymbolDomain.SEMANTIC_ATOM: DomainDisposition.GLOBAL_OR_TYPED_ATOM,
    SymbolDomain.SCOPED_SEMANTIC_SYMBOL: DomainDisposition.SCOPED_ID_PENDING,
    SymbolDomain.SEMANTIC_LITERAL: DomainDisposition.PRESERVE_LITERAL,
    SymbolDomain.EXTERNAL_CONTRACT: DomainDisposition.PRESERVE_CONTRACT,
    SymbolDomain.HUMAN_PROJECTION: DomainDisposition.SIDECAR,
    SymbolDomain.EXTENSION_PAYLOAD: DomainDisposition.OPAQUE_OWNER,
    SymbolDomain.UNCLASSIFIED: DomainDisposition.REJECT_UNTIL_CLASSIFIED,
}


@dataclass(frozen=True, order=True)
class DomainText:
    domain: SymbolDomain
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.domain, SymbolDomain):
            object.__setattr__(self, "domain", SymbolDomain(str(self.domain)))
        if not isinstance(self.text, str):
            object.__setattr__(self, "text", str(self.text))

    @property
    def code(self) -> int:
        return domain_code(self.domain)


@dataclass(frozen=True)
class SymbolOccurrence:
    path: tuple[str | int, ...]
    value: str
    domain: SymbolDomain
    disposition: DomainDisposition
    role: str = "value"
    in_semantic_core: bool = True
    reason: str = ""

    def to_record(self) -> dict[str, Any]:
        return {
            "path": list(self.path),
            "value": self.value,
            "domain": self.domain.value,
            "domain_code": domain_code(self.domain),
            "disposition": self.disposition.value,
            "role": self.role,
            "in_semantic_core": self.in_semantic_core,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class SymbolDomainReport:
    occurrences: tuple[SymbolOccurrence, ...]
    revision: int = DOMAIN_REVISION

    @property
    def unclassified(self) -> tuple[SymbolOccurrence, ...]:
        return tuple(item for item in self.occurrences if item.domain is SymbolDomain.UNCLASSIFIED)

    @property
    def semantic_human_projection_leaks(self) -> tuple[SymbolOccurrence, ...]:
        return tuple(
            item
            for item in self.occurrences
            if item.domain is SymbolDomain.HUMAN_PROJECTION and item.in_semantic_core
        )

    @property
    def counts(self) -> dict[str, int]:
        result = {domain.value: 0 for domain in SymbolDomain}
        for item in self.occurrences:
            result[item.domain.value] += 1
        return result

    @property
    def complete(self) -> bool:
        return not self.unclassified

    def to_record(self) -> dict[str, Any]:
        return {
            "format": "nova.symbol-domain-report/0.4",
            "domain_revision": self.revision,
            "complete": self.complete,
            "counts": self.counts,
            "unclassified_count": len(self.unclassified),
            "semantic_human_projection_leak_count": len(self.semantic_human_projection_leaks),
            "occurrences": [
                item.to_record()
                for item in sorted(
                    self.occurrences,
                    key=lambda item: (tuple(str(x) for x in item.path), item.role, item.value),
                )
            ],
        }

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(
            self.to_record(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(payload).hexdigest()


def domain_code(domain: SymbolDomain | str) -> int:
    key = domain if isinstance(domain, SymbolDomain) else SymbolDomain(str(domain))
    return _DOMAIN_CODE[key]


def domain_from_code(code: int) -> SymbolDomain:
    try:
        return _CODE_DOMAIN[int(code)]
    except KeyError as exc:
        raise KeyError(f"unknown NOVA symbol-domain code: {code}") from exc


def _occ(
    out: list[SymbolOccurrence],
    path: tuple[str | int, ...],
    value: str,
    domain: SymbolDomain,
    *,
    role: str = "value",
    in_semantic_core: bool = True,
    reason: str,
) -> None:
    out.append(
        SymbolOccurrence(
            path=path,
            value=value,
            domain=domain,
            disposition=_DISPOSITION[domain],
            role=role,
            in_semantic_core=in_semantic_core,
            reason=reason,
        )
    )


def _walk_generic(
    value: Any,
    out: list[SymbolOccurrence],
    path: tuple[str | int, ...],
    domain: SymbolDomain,
    *,
    in_semantic_core: bool,
    reason: str,
) -> None:
    to_record = getattr(value, "to_record", None)
    if callable(to_record):
        value = to_record()
    if isinstance(value, str):
        _occ(out, path, value, domain, in_semantic_core=in_semantic_core, reason=reason)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            _occ(
                out,
                path + ("<key>", key_text),
                key_text,
                domain,
                role="key",
                in_semantic_core=in_semantic_core,
                reason=reason + " map key",
            )
            _walk_generic(
                item,
                out,
                path + (key_text,),
                domain,
                in_semantic_core=in_semantic_core,
                reason=reason,
            )
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _walk_generic(
                item,
                out,
                path + (index,),
                domain,
                in_semantic_core=in_semantic_core,
                reason=reason,
            )


def _walk_semantic_record(
    value: Any,
    out: list[SymbolOccurrence],
    path: tuple[str | int, ...],
    *,
    default_domain: SymbolDomain = SymbolDomain.UNCLASSIFIED,
) -> None:
    to_record = getattr(value, "to_record", None)
    if callable(to_record):
        value = to_record()
    if isinstance(value, str):
        _occ(
            out,
            path,
            value,
            default_domain,
            reason="semantic payload without a more specific rule",
        )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            child = path + (key_text,)
            if key_text in {
                "kind",
                "dtype",
                "layout",
                "device",
                "effect_type",
                "differentiation_type",
                "proof_status",
                "relation",
                "required_relation",
            } and isinstance(item, str):
                _occ(out, child, item, SymbolDomain.SEMANTIC_ATOM, reason=f"{key_text} semantic atom")
                continue
            if key_text == "reason" and isinstance(item, str):
                _occ(
                    out,
                    child,
                    item,
                    SymbolDomain.HUMAN_PROJECTION,
                    reason="diagnostic/explanatory reason embedded in semantic structure",
                )
                continue
            if key_text == "terms" and isinstance(item, (list, tuple)):
                for index, term in enumerate(item):
                    if isinstance(term, (list, tuple)) and term and isinstance(term[0], str):
                        _occ(
                            out,
                            child + (index, 0),
                            term[0],
                            SymbolDomain.SCOPED_SEMANTIC_SYMBOL,
                            reason="affine dimension symbol",
                        )
                        for tail_index, tail in enumerate(term[1:], 1):
                            _walk_semantic_record(tail, out, child + (index, tail_index))
                    else:
                        _walk_semantic_record(term, out, child + (index,))
                continue
            _walk_semantic_record(item, out, child, default_domain=default_domain)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _walk_semantic_record(item, out, path + (index,), default_domain=default_domain)


def _walk_attributes(
    node: Any,
    out: list[SymbolOccurrence],
    path: tuple[str | int, ...],
) -> None:
    attrs = dict(node.attributes or {})
    known_operator = global_code("operator", str(node.kind)) is not None
    known_keys = {
        "name",
        "value",
        "shape",
        "axes",
        "axis",
        "keepdims",
        "callee",
        "trip_count",
        "body_kind",
    }
    for key, value in attrs.items():
        key_text = str(key)
        key_domain = SymbolDomain.SEMANTIC_ATOM if key_text in known_keys else (
            SymbolDomain.UNCLASSIFIED if known_operator else SymbolDomain.EXTENSION_PAYLOAD
        )
        _occ(
            out,
            path + ("<key>", key_text),
            key_text,
            key_domain,
            role="key",
            reason="known operator attribute key" if key_text in known_keys else "operator-owned attribute key",
        )
        child = path + (key_text,)
        if node.kind in {"Input", "Parameter"} and key_text == "name":
            _walk_generic(
                value,
                out,
                child,
                SymbolDomain.EXTERNAL_CONTRACT,
                in_semantic_core=True,
                reason="runtime input/parameter binding contract",
            )
        elif node.kind == "Call" and key_text == "callee":
            _walk_generic(
                value,
                out,
                child,
                SymbolDomain.STRUCTURAL_IDENTITY,
                in_semantic_core=True,
                reason="graph identity reference embedded in Call attributes",
            )
        elif node.kind == "BoundedLoop" and key_text == "body_kind":
            _walk_generic(
                value,
                out,
                child,
                SymbolDomain.SEMANTIC_ATOM,
                in_semantic_core=True,
                reason="embedded operator semantic atom",
            )
        elif node.kind == "Constant" and key_text == "value":
            _walk_generic(
                value,
                out,
                child,
                SymbolDomain.SEMANTIC_LITERAL,
                in_semantic_core=True,
                reason="runtime string/data literal",
            )
        elif key_text not in known_keys:
            _walk_generic(
                value,
                out,
                child,
                key_domain,
                in_semantic_core=True,
                reason="operator-owned attribute payload",
            )
        else:
            _walk_semantic_record(value, out, child)


def classify_project_symbols(project: Project) -> SymbolDomainReport:
    out: list[SymbolOccurrence] = []

    header = project.header
    for field_name, value in (
        ("nova_core_version", header.nova_core_version),
        ("schema_version", header.schema_version),
    ):
        _occ(out, ("header", field_name), str(value), SymbolDomain.SEMANTIC_ATOM, reason="version/schema semantic atom")
    for index, flag in enumerate(header.feature_flags):
        _occ(out, ("header", "feature_flags", index), str(flag), SymbolDomain.SEMANTIC_ATOM, reason="feature flag semantic atom")
    _walk_generic(header.migration_history, out, ("header", "migration_history"), SymbolDomain.HUMAN_PROJECTION, in_semantic_core=False, reason="migration/history projection")
    _walk_generic(header.provenance, out, ("header", "provenance"), SymbolDomain.HUMAN_PROJECTION, in_semantic_core=False, reason="provenance projection")
    _walk_generic(header.extensions, out, ("header", "extensions"), SymbolDomain.EXTENSION_PAYLOAD, in_semantic_core=True, reason="extension-owned payload")

    for m_index, module in enumerate(project.modules):
        m_path = ("modules", m_index)
        _occ(out, m_path + ("id",), module.id, SymbolDomain.STRUCTURAL_IDENTITY, reason="module projection label")
        for index, value in enumerate(module.imports):
            _occ(out, m_path + ("imports", index), str(value), SymbolDomain.EXTERNAL_CONTRACT, reason="module import boundary contract")
        for index, value in enumerate(module.exports):
            _occ(out, m_path + ("exports", index), str(value), SymbolDomain.EXTERNAL_CONTRACT, reason="module export boundary contract")
        _walk_semantic_record(module.attributes, out, m_path + ("attributes",))
        _walk_generic(module.provenance, out, m_path + ("provenance",), SymbolDomain.HUMAN_PROJECTION, in_semantic_core=False, reason="module provenance")
        _walk_generic(module.extensions, out, m_path + ("extensions",), SymbolDomain.EXTENSION_PAYLOAD, in_semantic_core=True, reason="module extension-owned payload")

        for g_index, graph in enumerate(module.graphs):
            g_path = m_path + ("graphs", g_index)
            _occ(out, g_path + ("id",), graph.id, SymbolDomain.STRUCTURAL_IDENTITY, reason="graph projection label")
            for field_name, values in (("inputs", graph.inputs), ("outputs", graph.outputs)):
                for index, value in enumerate(values):
                    _occ(out, g_path + (field_name, index), str(value), SymbolDomain.STRUCTURAL_IDENTITY, reason="graph value identity label")
            for index, constraint in enumerate(graph.constraints):
                _walk_semantic_record(constraint, out, g_path + ("constraints", index))
            _walk_semantic_record(graph.attributes, out, g_path + ("attributes",))
            _walk_generic(graph.provenance, out, g_path + ("provenance",), SymbolDomain.HUMAN_PROJECTION, in_semantic_core=False, reason="graph provenance")
            _walk_generic(graph.extensions, out, g_path + ("extensions",), SymbolDomain.EXTENSION_PAYLOAD, in_semantic_core=True, reason="graph extension-owned payload")

            for n_index, node in enumerate(graph.nodes):
                n_path = g_path + ("nodes", n_index)
                _occ(out, n_path + ("id",), node.id, SymbolDomain.STRUCTURAL_IDENTITY, reason="node projection label")
                _occ(out, n_path + ("kind",), node.kind, SymbolDomain.SEMANTIC_ATOM, reason="operator semantic atom")
                for field_name, values in (("inputs", node.inputs), ("outputs", node.outputs)):
                    for index, value in enumerate(values):
                        _occ(out, n_path + (field_name, index), str(value), SymbolDomain.STRUCTURAL_IDENTITY, reason="node value identity label")
                for field_name, value in (("value_type", node.value_type), ("shape_type", node.shape_type)):
                    if value is not None:
                        _walk_semantic_record(value, out, n_path + (field_name,))
                if isinstance(node.effect_type, str):
                    _occ(out, n_path + ("effect_type",), node.effect_type, SymbolDomain.SEMANTIC_ATOM, reason="effect semantic atom")
                else:
                    _walk_semantic_record(node.effect_type, out, n_path + ("effect_type",))
                if isinstance(node.differentiation_type, str):
                    _occ(out, n_path + ("differentiation_type",), node.differentiation_type, SymbolDomain.SEMANTIC_ATOM, reason="differentiation semantic atom")
                else:
                    _walk_semantic_record(node.differentiation_type, out, n_path + ("differentiation_type",))
                for index, constraint in enumerate(node.constraints):
                    _walk_semantic_record(constraint, out, n_path + ("constraints", index))
                _walk_attributes(node, out, n_path + ("attributes",))
                _walk_generic(node.source_projection, out, n_path + ("source_projection",), SymbolDomain.HUMAN_PROJECTION, in_semantic_core=False, reason="source projection")
                _walk_generic(node.provenance, out, n_path + ("provenance",), SymbolDomain.HUMAN_PROJECTION, in_semantic_core=False, reason="node provenance")
                _walk_generic(node.extensions, out, n_path + ("extensions",), SymbolDomain.EXTENSION_PAYLOAD, in_semantic_core=True, reason="node extension-owned payload")

            for e_index, edge in enumerate(graph.edges):
                e_path = g_path + ("edges", e_index)
                _occ(out, e_path + ("source",), edge.source, SymbolDomain.STRUCTURAL_IDENTITY, reason="edge source node identity")
                _occ(out, e_path + ("target",), edge.target, SymbolDomain.STRUCTURAL_IDENTITY, reason="edge target node identity")
                _occ(out, e_path + ("kind",), edge.kind, SymbolDomain.SEMANTIC_ATOM, reason="edge semantic atom")
                for index, constraint in enumerate(edge.constraints):
                    _walk_semantic_record(constraint, out, e_path + ("constraints", index))
                _walk_semantic_record(edge.attributes, out, e_path + ("attributes",))
                _walk_generic(edge.provenance, out, e_path + ("provenance",), SymbolDomain.HUMAN_PROJECTION, in_semantic_core=False, reason="edge provenance")
                _walk_generic(edge.extensions, out, e_path + ("extensions",), SymbolDomain.EXTENSION_PAYLOAD, in_semantic_core=True, reason="edge extension-owned payload")

    for index, constraint in enumerate(project.constraints):
        _walk_semantic_record(constraint, out, ("constraints", index))
    _walk_semantic_record(project.attributes, out, ("attributes",))
    _walk_generic(project.artifacts, out, ("artifacts",), SymbolDomain.HUMAN_PROJECTION, in_semantic_core=False, reason="artifact projection")
    _walk_generic(project.provenance, out, ("provenance",), SymbolDomain.HUMAN_PROJECTION, in_semantic_core=False, reason="project provenance")
    _walk_generic(project.extensions, out, ("extensions",), SymbolDomain.EXTENSION_PAYLOAD, in_semantic_core=True, reason="project extension-owned payload")

    return SymbolDomainReport(tuple(out))


def domain_report_sidecar(project: Project) -> dict[str, Any]:
    report = classify_project_symbols(project)
    record = report.to_record()
    record["fingerprint"] = report.fingerprint
    return record


__all__ = [
    "DOMAIN_REVISION",
    "DomainDisposition",
    "DomainText",
    "SymbolDomain",
    "SymbolDomainReport",
    "SymbolOccurrence",
    "classify_project_symbols",
    "domain_code",
    "domain_from_code",
    "domain_report_sidecar",
]

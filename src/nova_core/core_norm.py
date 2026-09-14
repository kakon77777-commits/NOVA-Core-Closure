from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .canonical import project_record, semantic_hash
from .errors import ValidationError
from .model import Project
from .semantic_registry import global_code

CORE_NORM_REVISION = 1

_COMMUTATIVE_OPS = frozenset({"Add", "Multiply"})
_HUMAN_ONLY_FIELDS = frozenset({"reason", "source_projection", "provenance", "migration_history", "artifacts"})
_SEMANTIC_DOMAINS = {
    "dtype": "dtype",
    "layout": "layout",
    "device": "device",
    "effect_type": "effect_kind",
    "differentiation_type": "differentiation_kind",
    "proof_status": "proof_status",
    "relation": "relation",
    "required_relation": "relation",
}


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _stable_bytes(value: Any) -> bytes:
    return _stable_json(value).encode("utf-8")


def _hash(value: Any, tag: bytes) -> str:
    return "sha256:" + hashlib.sha256(tag + _stable_bytes(value)).hexdigest()


def _atom(domain: str, text: str) -> list[Any]:
    pair = global_code(domain, str(text))
    if pair is None:
        return ["x", domain, str(text)]
    return ["g", int(pair[0]), int(pair[1])]


def _operator(text: str) -> list[Any]:
    return _atom("operator", text)


def _edge_kind(text: str) -> list[Any]:
    return _atom("edge_kind", text)


def _record_kind(text: str) -> list[Any]:
    return _atom("record_kind", text)


def _contains_symbol_terms(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) == "terms" and isinstance(item, (list, tuple)):
                for term in item:
                    if isinstance(term, (list, tuple)) and term and isinstance(term[0], str):
                        return True
            if _contains_symbol_terms(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_symbol_terms(item) for item in value)
    return False


@dataclass(frozen=True)
class CoreNormProfile:
    revision: int = CORE_NORM_REVISION
    eliminate_trivial_identity: bool = True
    normalize_commutative_inputs: bool = True
    reject_calls: bool = True
    reject_cycles: bool = True
    reject_dead_nodes: bool = True
    reject_ambiguous_binders: bool = True

    def to_record(self) -> dict[str, Any]:
        return {
            "revision": self.revision,
            "eliminate_trivial_identity": self.eliminate_trivial_identity,
            "normalize_commutative_inputs": self.normalize_commutative_inputs,
            "reject_calls": self.reject_calls,
            "reject_cycles": self.reject_cycles,
            "reject_dead_nodes": self.reject_dead_nodes,
            "reject_ambiguous_binders": self.reject_ambiguous_binders,
        }


DEFAULT_CORE_NORM_PROFILE = CoreNormProfile()


@dataclass(frozen=True)
class CoreNormWitness:
    source_semantic_hash: str
    normalized_hash: str
    graph_count: int
    node_count: int
    identity_nodes_eliminated: int = 0
    commutative_nodes_reordered: int = 0
    scoped_binders_alpha_normalized: int = 0
    obligations: tuple[str, ...] = ()

    def to_record(self) -> dict[str, Any]:
        return {
            "source_semantic_hash": self.source_semantic_hash,
            "normalized_hash": self.normalized_hash,
            "graph_count": self.graph_count,
            "node_count": self.node_count,
            "identity_nodes_eliminated": self.identity_nodes_eliminated,
            "commutative_nodes_reordered": self.commutative_nodes_reordered,
            "scoped_binders_alpha_normalized": self.scoped_binders_alpha_normalized,
            "obligations": list(self.obligations),
        }


@dataclass(frozen=True)
class CoreNormResult:
    record: Mapping[str, Any]
    witness: CoreNormWitness

    @property
    def hash(self) -> str:
        return self.witness.normalized_hash

    def to_record(self) -> dict[str, Any]:
        return {"record": dict(self.record), "witness": self.witness.to_record()}


def _semantic_skeleton(value: Any) -> Any:
    if isinstance(value, str):
        return "<text>"
    if isinstance(value, Mapping):
        out = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text in _HUMAN_ONLY_FIELDS:
                continue
            if key_text == "terms" and isinstance(item, (list, tuple)):
                out[key_text] = [["<binder>", int(term[1])] if isinstance(term, (list, tuple)) and len(term) >= 2 and isinstance(term[0], str) else _semantic_skeleton(term) for term in item]
            else:
                out[key_text] = _semantic_skeleton(item)
        return out
    if isinstance(value, (list, tuple)):
        return [_semantic_skeleton(v) for v in value]
    return value


def _binder_occurrences(graph: Mapping[str, Any]) -> dict[str, list[list[Any]]]:
    out: dict[str, list[list[Any]]] = {}

    def walk(value: Any, path: list[Any]) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                key_text = str(key)
                if key_text in _HUMAN_ONLY_FIELDS:
                    continue
                if key_text == "terms" and isinstance(item, (list, tuple)):
                    for term in item:
                        if isinstance(term, (list, tuple)) and len(term) >= 2 and isinstance(term[0], str):
                            out.setdefault(str(term[0]), []).append(path + ["terms", int(term[1])])
                        else:
                            walk(term, path + ["terms"])
                    continue
                walk(item, path + [key_text])
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                walk(item, path + [index])

    for field_name in ("constraints", "attributes"):
        walk(graph.get(field_name), ["graph", field_name])

    node_contexts: list[tuple[str, Mapping[str, Any]]] = []
    for node in graph.get("nodes", ()) or ():
        n = dict(node)
        context = {
            "kind": n.get("kind"),
            "input_arity": len(n.get("inputs", ()) or ()),
            "output_arity": len(n.get("outputs", ()) or ()),
            "value_type": _semantic_skeleton(n.get("value_type")),
            "shape_type": _semantic_skeleton(n.get("shape_type")),
            "effect_type": _semantic_skeleton(n.get("effect_type")),
            "differentiation_type": _semantic_skeleton(n.get("differentiation_type")),
            "constraints": _semantic_skeleton(n.get("constraints", ())),
            "attributes": _semantic_skeleton(n.get("attributes", {})),
        }
        context_hash = hashlib.sha256(_stable_bytes(context)).hexdigest()
        node_contexts.append((context_hash, n))
    node_contexts.sort(key=lambda pair: pair[0])
    for context_hash, node in node_contexts:
        for field_name in ("value_type", "shape_type", "effect_type", "differentiation_type", "constraints", "attributes"):
            walk(node.get(field_name), ["node", context_hash, field_name])

    for edge in graph.get("edges", ()) or ():
        e = dict(edge)
        context = {
            "kind": e.get("kind"),
            "constraints": _semantic_skeleton(e.get("constraints", ())),
            "attributes": _semantic_skeleton(e.get("attributes", {})),
        }
        context_hash = hashlib.sha256(_stable_bytes(context)).hexdigest()
        for field_name in ("constraints", "attributes"):
            walk(e.get(field_name), ["edge", context_hash, field_name])
    return out


def _binder_map(graph: Mapping[str, Any], profile: CoreNormProfile) -> dict[str, int]:
    occurrences = _binder_occurrences(graph)
    if not occurrences:
        return {}
    signatures: list[tuple[str, str]] = []
    owner: dict[str, str] = {}
    for label, items in occurrences.items():
        signature = _hash(sorted(items, key=_stable_json), b"NOVA-CORENORM-BINDER-v0.7\0")
        other = owner.get(signature)
        if other is not None and other != label and profile.reject_ambiguous_binders:
            raise ValidationError(
                "CoreNorm cannot alpha-normalize structurally symmetric scoped binders",
                context={"labels": sorted([other, label]), "signature": signature},
            )
        owner[signature] = label
        signatures.append((signature, label))
    signatures.sort()
    return {label: index for index, (_, label) in enumerate(signatures)}


def _normalize_value(
    value: Any,
    *,
    binder_map: Mapping[str, int],
    field_name: str | None = None,
    record_kind: str | None = None,
) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        if field_name == "kind":
            if record_kind == "node":
                return _operator(value)
            if record_kind == "edge":
                return _edge_kind(value)
            return _record_kind(value)
        domain = _SEMANTIC_DOMAINS.get(field_name or "")
        if domain is not None:
            return _atom(domain, value)
        if field_name in {"nova_core_version", "schema_version"}:
            return ["version", value]
        if field_name == "feature_flags":
            return ["flag", value]
        return ["text", value]
    if isinstance(value, Mapping):
        kind_hint = record_kind
        if isinstance(value.get("kind"), str):
            kind_hint = "record"
        out: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text in _HUMAN_ONLY_FIELDS:
                continue
            if key_text == "terms" and isinstance(item, (list, tuple)):
                terms: list[list[Any]] = []
                for term in item:
                    if isinstance(term, (list, tuple)) and len(term) >= 2 and isinstance(term[0], str):
                        label = str(term[0])
                        if label not in binder_map:
                            raise ValidationError("CoreNorm encountered unbound scoped semantic symbol", context={"label": label})
                        terms.append([["b", int(binder_map[label])], int(term[1])])
                    else:
                        terms.append(_normalize_value(term, binder_map=binder_map))
                terms.sort(key=_stable_json)
                out[key_text] = terms
            else:
                out[key_text] = _normalize_value(item, binder_map=binder_map, field_name=key_text, record_kind=kind_hint)
        return out
    if isinstance(value, (list, tuple)):
        normalized = [_normalize_value(v, binder_map=binder_map, field_name=field_name, record_kind=record_kind) for v in value]
        if field_name in {"constraints", "feature_flags"}:
            normalized.sort(key=_stable_json)
        return normalized
    to_record = getattr(value, "to_record", None)
    if callable(to_record):
        return _normalize_value(to_record(), binder_map=binder_map, field_name=field_name, record_kind=record_kind)
    return ["opaque", type(value).__name__, repr(value)]


def _trivial_identity(node: Mapping[str, Any]) -> bool:
    if str(node.get("kind", "")) != "Identity":
        return False
    if len(node.get("inputs", ()) or ()) != 1 or len(node.get("outputs", ()) or ()) != 1:
        return False
    if node.get("constraints"):
        return False
    if node.get("attributes"):
        return False
    if node.get("value_type") is not None or node.get("shape_type") is not None:
        return False
    if node.get("effect_type") not in (None, "Pure"):
        return False
    if node.get("differentiation_type") not in (None,):
        return False
    return True


class _GraphNormalizer:
    def __init__(self, graph: Mapping[str, Any], profile: CoreNormProfile):
        self.graph = dict(graph)
        self.profile = profile
        self.binders = _binder_map(self.graph, profile)
        self.nodes = {str(n["id"]): dict(n) for n in self.graph.get("nodes", ()) or ()}
        self.input_pos = {str(name): i for i, name in enumerate(self.graph.get("inputs", ()) or ())}
        self.producer: dict[str, tuple[str, int]] = {}
        for node in self.nodes.values():
            for index, value in enumerate(node.get("outputs", ()) or ()):
                label = str(value)
                if label in self.producer or label in self.input_pos:
                    raise ValidationError("CoreNorm requires unique graph value producers", context={"value": label})
                self.producer[label] = (str(node["id"]), index)
        self.memo_node: dict[str, Any] = {}
        self.memo_value: dict[str, Any] = {}
        self.visiting: set[str] = set()
        self.reachable: set[str] = set()
        self.identity_eliminated = 0
        self.commutative_reordered = 0

    def value_expr(self, name: str) -> Any:
        name = str(name)
        if name in self.memo_value:
            return self.memo_value[name]
        if name in self.input_pos:
            result = ["arg", self.input_pos[name]]
            self.memo_value[name] = result
            return result
        try:
            node_id, output_index = self.producer[name]
        except KeyError as exc:
            raise ValidationError("CoreNorm unresolved value", context={"value": name}) from exc
        node = self.nodes[node_id]
        if self.profile.eliminate_trivial_identity and _trivial_identity(node):
            result = self.value_expr(str((node.get("inputs") or [""])[0]))
            self.identity_eliminated += 1
            self.reachable.add(node_id)
        else:
            signature = self.node_signature(node_id)
            result = ["out", signature, int(output_index)]
        self.memo_value[name] = result
        return result

    def node_signature(self, node_id: str) -> Any:
        node_id = str(node_id)
        if node_id in self.memo_node:
            return self.memo_node[node_id]
        if node_id in self.visiting:
            if self.profile.reject_cycles:
                raise ValidationError("CoreNorm v0.7 bounded profile rejects cyclic graphs", context={"node": node_id})
            return ["cycle"]
        node = self.nodes[node_id]
        kind = str(node.get("kind", ""))
        if kind == "Call" and self.profile.reject_calls:
            raise ValidationError("CoreNorm v0.7 bounded profile does not normalize Call nodes")
        self.visiting.add(node_id)
        inputs = [self.value_expr(str(v)) for v in node.get("inputs", ()) or ()]
        if kind in _COMMUTATIVE_OPS and self.profile.normalize_commutative_inputs:
            before = list(inputs)
            inputs.sort(key=_stable_json)
            if inputs != before:
                self.commutative_reordered += 1
        semantic = {
            "op": _operator(kind),
            "inputs": inputs,
            "output_arity": len(node.get("outputs", ()) or ()),
            "value_type": _normalize_value(node.get("value_type"), binder_map=self.binders, field_name="value_type"),
            "shape_type": _normalize_value(node.get("shape_type"), binder_map=self.binders, field_name="shape_type"),
            "effect_type": _normalize_value(node.get("effect_type"), binder_map=self.binders, field_name="effect_type"),
            "differentiation_type": _normalize_value(node.get("differentiation_type"), binder_map=self.binders, field_name="differentiation_type"),
            "constraints": _normalize_value(node.get("constraints", ()), binder_map=self.binders, field_name="constraints"),
            "attributes": _normalize_value(node.get("attributes", {}), binder_map=self.binders, field_name="attributes"),
        }
        signature = ["node", semantic]
        self.memo_node[node_id] = signature
        self.visiting.remove(node_id)
        self.reachable.add(node_id)
        return signature

    def normalize(self) -> tuple[dict[str, Any], dict[str, int]]:
        if self.profile.eliminate_trivial_identity and self.graph.get("edges"):
            identity_ids = {node_id for node_id, node in self.nodes.items() if _trivial_identity(node)}
            for edge in self.graph.get("edges", ()) or ():
                if str(edge.get("source", "")) in identity_ids or str(edge.get("target", "")) in identity_ids:
                    raise ValidationError("CoreNorm v0.7 does not guess explicit-edge rewiring across eliminated Identity nodes")
        outputs = [self.value_expr(str(v)) for v in self.graph.get("outputs", ()) or ()]
        reachable_from_outputs = set(self.reachable)
        if self.profile.reject_dead_nodes:
            dead = sorted(
                node_id for node_id, node in self.nodes.items()
                if node_id not in reachable_from_outputs and not (self.profile.eliminate_trivial_identity and _trivial_identity(node))
            )
            if dead:
                raise ValidationError("CoreNorm v0.7 bounded profile rejects dead nodes", context={"nodes": dead})

        edges = []
        for edge in self.graph.get("edges", ()) or ():
            source = str(edge.get("source", "")); target = str(edge.get("target", ""))
            if source not in self.nodes or target not in self.nodes:
                raise ValidationError("CoreNorm edge endpoint does not exist", context={"source": source, "target": target})
            edges.append({
                "source": self.node_signature(source),
                "target": self.node_signature(target),
                "kind": _edge_kind(str(edge.get("kind", "value"))),
                "constraints": _normalize_value(edge.get("constraints", ()), binder_map=self.binders, field_name="constraints"),
                "attributes": _normalize_value(edge.get("attributes", {}), binder_map=self.binders, field_name="attributes"),
            })
        edges.sort(key=_stable_json)

        non_identity_nodes = [
            self.node_signature(node_id)
            for node_id, node in self.nodes.items()
            if not (self.profile.eliminate_trivial_identity and _trivial_identity(node))
        ]
        non_identity_nodes.sort(key=_stable_json)
        record = {
            "input_arity": len(self.graph.get("inputs", ()) or ()),
            "outputs": outputs,
            "nodes": non_identity_nodes,
            "edges": edges,
            "constraints": _normalize_value(self.graph.get("constraints", ()), binder_map=self.binders, field_name="constraints"),
            "attributes": _normalize_value(self.graph.get("attributes", {}), binder_map=self.binders, field_name="attributes"),
            "binder_count": len(self.binders),
        }
        stats = {
            "node_count": len(self.nodes),
            "identity_eliminated": self.identity_eliminated,
            "commutative_reordered": self.commutative_reordered,
            "binders": len(self.binders),
        }
        return record, stats


def core_norm_project(project: Project, *, profile: CoreNormProfile = DEFAULT_CORE_NORM_PROFILE) -> CoreNormResult:
    raw = project_record(project, semantic=True)
    if _contains_symbol_terms(raw.get("constraints")) or _contains_symbol_terms(raw.get("attributes")):
        raise ValidationError("CoreNorm v0.7 requires scoped semantic symbols to be graph-local")

    modules_out = []
    graph_count = 0
    node_count = 0
    identity_eliminated = 0
    commutative_reordered = 0
    binders = 0

    for module in raw.get("modules", ()) or ():
        if _contains_symbol_terms(module.get("attributes", {})):
            raise ValidationError("CoreNorm v0.7 requires scoped semantic symbols to be graph-local")
        graphs_out = []
        for graph in module.get("graphs", ()) or ():
            normalizer = _GraphNormalizer(graph, profile)
            graph_record_norm, stats = normalizer.normalize()
            graphs_out.append(graph_record_norm)
            graph_count += 1
            node_count += stats["node_count"]
            identity_eliminated += stats["identity_eliminated"]
            commutative_reordered += stats["commutative_reordered"]
            binders += stats["binders"]
        graphs_out.sort(key=_stable_json)
        modules_out.append({
            "imports": sorted([["external", str(v)] for v in module.get("imports", ()) or ()], key=_stable_json),
            "exports": sorted([["external", str(v)] for v in module.get("exports", ()) or ()], key=_stable_json),
            "graphs": graphs_out,
            "attributes": _normalize_value(module.get("attributes", {}), binder_map={}, field_name="attributes"),
        })
    modules_out.sort(key=_stable_json)

    header = raw.get("header", {}) or {}
    record = {
        "format": "nova.corenorm/0.7",
        "revision": CORE_NORM_REVISION,
        "profile": profile.to_record(),
        "header": {
            "nova_core_version": ["version", str(header.get("nova_core_version", ""))],
            "schema_version": ["version", str(header.get("schema_version", ""))],
            "feature_flags": sorted([["flag", str(v)] for v in header.get("feature_flags", ()) or ()], key=_stable_json),
        },
        "modules": modules_out,
        "constraints": _normalize_value(raw.get("constraints", ()), binder_map={}, field_name="constraints"),
        "attributes": _normalize_value(raw.get("attributes", {}), binder_map={}, field_name="attributes"),
    }
    normalized_hash = _hash(record, b"NOVA-CORENORM-HASH-v0.7\0")
    witness = CoreNormWitness(
        source_semantic_hash=semantic_hash(project),
        normalized_hash=normalized_hash,
        graph_count=graph_count,
        node_count=node_count,
        identity_nodes_eliminated=identity_eliminated,
        commutative_nodes_reordered=commutative_reordered,
        scoped_binders_alpha_normalized=binders,
        obligations=(),
    )
    return CoreNormResult(record, witness)


def core_norm_hash(project: Project, *, profile: CoreNormProfile = DEFAULT_CORE_NORM_PROFILE) -> str:
    return core_norm_project(project, profile=profile).hash


def core_norm_equivalent(left: Project, right: Project, *, profile: CoreNormProfile = DEFAULT_CORE_NORM_PROFILE) -> bool:
    return core_norm_hash(left, profile=profile) == core_norm_hash(right, profile=profile)


def core_norm_bytes(project: Project, *, profile: CoreNormProfile = DEFAULT_CORE_NORM_PROFILE) -> bytes:
    return _stable_bytes(core_norm_project(project, profile=profile).record)


__all__ = [
    "CORE_NORM_REVISION",
    "CoreNormProfile",
    "CoreNormResult",
    "CoreNormWitness",
    "DEFAULT_CORE_NORM_PROFILE",
    "core_norm_bytes",
    "core_norm_equivalent",
    "core_norm_hash",
    "core_norm_project",
]

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
import hashlib
import json
from types import MappingProxyType
from typing import Any

from .errors import ISQLCodecError


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


def _require_nonempty(name: str, value: str) -> str:
    out = str(value)
    if not out:
        raise ValueError(f"{name} must not be empty")
    return out


@dataclass(frozen=True)
class SemanticDimension:
    name: str
    value: Any
    weight: float = 1.0
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _require_nonempty("dimension name", self.name))
        weight = float(self.weight)
        if weight <= 0:
            raise ValueError("dimension weight must be positive")
        object.__setattr__(self, "weight", weight)
        object.__setattr__(self, "value", _freeze(self.value))
        object.__setattr__(self, "extensions", _freeze(dict(self.extensions or {})))


@dataclass(frozen=True)
class SemanticField:
    name: str
    value: Any
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _require_nonempty("semantic field name", self.name))
        object.__setattr__(self, "value", _freeze(self.value))
        object.__setattr__(self, "extensions", _freeze(dict(self.extensions or {})))


@dataclass(frozen=True)
class SemanticTopology:
    kind: str
    properties: Mapping[str, Any] = field(default_factory=dict)
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _require_nonempty("topology kind", self.kind))
        object.__setattr__(self, "properties", _freeze(dict(self.properties or {})))
        object.__setattr__(self, "extensions", _freeze(dict(self.extensions or {})))


@dataclass(frozen=True)
class SemanticRelation:
    source: str
    predicate: str
    target: str
    confidence: float = 1.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", _require_nonempty("relation source", self.source))
        object.__setattr__(self, "predicate", _require_nonempty("relation predicate", self.predicate))
        object.__setattr__(self, "target", _require_nonempty("relation target", self.target))
        confidence = float(self.confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("relation confidence must be in [0,1]")
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))


@dataclass(frozen=True)
class SemanticProvenance:
    protocol_version: str
    registry_id: str
    registry_version: str
    domain: str
    decoder_contract: str
    registry_hash: str | None = None
    encoder_version: str | None = None
    model_id: str | None = None
    resolution: str | None = None
    context_policy: str | None = None
    source_id: str | None = None
    parent_tensor_hash: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "protocol_version", _require_nonempty("protocol version", self.protocol_version))
        object.__setattr__(self, "registry_id", _require_nonempty("registry id", self.registry_id))
        object.__setattr__(self, "registry_version", _require_nonempty("registry version", self.registry_version))
        object.__setattr__(self, "domain", _require_nonempty("domain", self.domain))
        object.__setattr__(self, "decoder_contract", _require_nonempty("decoder contract", self.decoder_contract))
        for name in (
            "registry_hash",
            "encoder_version",
            "model_id",
            "resolution",
            "context_policy",
            "source_id",
            "parent_tensor_hash",
        ):
            value = getattr(self, name)
            object.__setattr__(self, name, None if value is None else str(value))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))


@dataclass(frozen=True)
class SemanticTensor:
    dimensions: tuple[SemanticDimension, ...]
    phase: SemanticField | None
    spectrum: tuple[SemanticField, ...]
    topology: SemanticTopology
    relations: tuple[SemanticRelation, ...]
    confidence: float
    provenance: SemanticProvenance
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        dims = tuple(sorted(tuple(self.dimensions), key=lambda d: d.name))
        spectrum = tuple(sorted(tuple(self.spectrum), key=lambda f: f.name))
        confidence = float(self.confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be in [0,1]")
        names = [d.name for d in dims]
        if len(names) != len(set(names)):
            raise ValueError("semantic dimension names must be unique")
        field_names = [f.name for f in spectrum]
        if len(field_names) != len(set(field_names)):
            raise ValueError("semantic spectrum field names must be unique")
        object.__setattr__(self, "dimensions", dims)
        object.__setattr__(self, "spectrum", spectrum)
        object.__setattr__(self, "relations", tuple(self.relations))
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "extensions", _freeze(dict(self.extensions or {})))


def _dimension_record(value: SemanticDimension) -> dict[str, Any]:
    return {
        "name": value.name,
        "value": _thaw(value.value),
        "weight": value.weight,
        "extensions": _thaw(value.extensions),
    }


def _field_record(value: SemanticField) -> dict[str, Any]:
    return {"name": value.name, "value": _thaw(value.value), "extensions": _thaw(value.extensions)}


def _topology_record(value: SemanticTopology) -> dict[str, Any]:
    return {"kind": value.kind, "properties": _thaw(value.properties), "extensions": _thaw(value.extensions)}


def _relation_record(value: SemanticRelation) -> dict[str, Any]:
    return {
        "source": value.source,
        "predicate": value.predicate,
        "target": value.target,
        "confidence": value.confidence,
        "metadata": _thaw(value.metadata),
    }


def _provenance_record(value: SemanticProvenance) -> dict[str, Any]:
    return {
        "protocol_version": value.protocol_version,
        "registry_id": value.registry_id,
        "registry_version": value.registry_version,
        "domain": value.domain,
        "decoder_contract": value.decoder_contract,
        "registry_hash": value.registry_hash,
        "encoder_version": value.encoder_version,
        "model_id": value.model_id,
        "resolution": value.resolution,
        "context_policy": value.context_policy,
        "source_id": value.source_id,
        "parent_tensor_hash": value.parent_tensor_hash,
        "metadata": _thaw(value.metadata),
    }


def semantic_tensor_record(tensor: SemanticTensor) -> dict[str, Any]:
    return {
        "kind": "semantic_tensor",
        "schema_version": "0.1.0",
        "dimensions": [_dimension_record(v) for v in tensor.dimensions],
        "phase": None if tensor.phase is None else _field_record(tensor.phase),
        "spectrum": [_field_record(v) for v in tensor.spectrum],
        "topology": _topology_record(tensor.topology),
        "relations": [_relation_record(v) for v in tensor.relations],
        "confidence": tensor.confidence,
        "provenance": _provenance_record(tensor.provenance),
        "extensions": _thaw(tensor.extensions),
    }


def encode_semantic_tensor(tensor: SemanticTensor) -> str:
    try:
        return json.dumps(
            semantic_tensor_record(tensor),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ISQLCodecError(f"semantic tensor is not JSON serializable: {exc}") from exc


def semantic_tensor_hash(tensor: SemanticTensor) -> str:
    return "sha256:" + hashlib.sha256(encode_semantic_tensor(tensor).encode("utf-8")).hexdigest()


def _decode_dimension(value: Mapping[str, Any]) -> SemanticDimension:
    return SemanticDimension(
        name=str(value.get("name", "")),
        value=value.get("value"),
        weight=float(value.get("weight", 1.0)),
        extensions=dict(value.get("extensions") or {}),
    )


def _decode_field(value: Mapping[str, Any]) -> SemanticField:
    return SemanticField(
        name=str(value.get("name", "")),
        value=value.get("value"),
        extensions=dict(value.get("extensions") or {}),
    )


def _decode_topology(value: Mapping[str, Any]) -> SemanticTopology:
    return SemanticTopology(
        kind=str(value.get("kind", "")),
        properties=dict(value.get("properties") or {}),
        extensions=dict(value.get("extensions") or {}),
    )


def _decode_relation(value: Mapping[str, Any]) -> SemanticRelation:
    return SemanticRelation(
        source=str(value.get("source", "")),
        predicate=str(value.get("predicate", "")),
        target=str(value.get("target", "")),
        confidence=float(value.get("confidence", 1.0)),
        metadata=dict(value.get("metadata") or {}),
    )


def _decode_provenance(value: Mapping[str, Any]) -> SemanticProvenance:
    def optional(name: str) -> str | None:
        raw = value.get(name)
        return None if raw is None else str(raw)

    return SemanticProvenance(
        protocol_version=str(value.get("protocol_version", "")),
        registry_id=str(value.get("registry_id", "")),
        registry_version=str(value.get("registry_version", "")),
        domain=str(value.get("domain", "")),
        decoder_contract=str(value.get("decoder_contract", "")),
        registry_hash=optional("registry_hash"),
        encoder_version=optional("encoder_version"),
        model_id=optional("model_id"),
        resolution=optional("resolution"),
        context_policy=optional("context_policy"),
        source_id=optional("source_id"),
        parent_tensor_hash=optional("parent_tensor_hash"),
        metadata=dict(value.get("metadata") or {}),
    )


def decode_semantic_tensor(value: str | bytes | Mapping[str, Any]) -> SemanticTensor:
    try:
        if isinstance(value, bytes):
            raw = json.loads(value.decode("utf-8"))
        elif isinstance(value, str):
            raw = json.loads(value)
        else:
            raw = dict(value)
        if not isinstance(raw, Mapping):
            raise ISQLCodecError("semantic tensor must decode to an object")
        if raw.get("kind") != "semantic_tensor":
            raise ISQLCodecError("semantic tensor kind is invalid")
        phase_raw = raw.get("phase")
        return SemanticTensor(
            dimensions=tuple(_decode_dimension(v) for v in raw.get("dimensions", ())),
            phase=None if phase_raw is None else _decode_field(phase_raw),
            spectrum=tuple(_decode_field(v) for v in raw.get("spectrum", ())),
            topology=_decode_topology(raw.get("topology") or {}),
            relations=tuple(_decode_relation(v) for v in raw.get("relations", ())),
            confidence=float(raw.get("confidence", 0.0)),
            provenance=_decode_provenance(raw.get("provenance") or {}),
            extensions=dict(raw.get("extensions") or {}),
        )
    except ISQLCodecError:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError, KeyError) as exc:
        raise ISQLCodecError(f"failed to decode semantic tensor: {exc}") from exc


@dataclass(frozen=True)
class DimensionPredicate:
    name: str
    expected: Any
    required: bool = True
    weight: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _require_nonempty("dimension predicate name", self.name))
        weight = float(self.weight)
        if weight <= 0:
            raise ValueError("dimension predicate weight must be positive")
        object.__setattr__(self, "expected", _freeze(self.expected))
        object.__setattr__(self, "weight", weight)


@dataclass(frozen=True)
class RelationPredicate:
    source: str
    predicate: str
    target: str
    required: bool = True
    weight: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", _require_nonempty("relation predicate source", self.source))
        object.__setattr__(self, "predicate", _require_nonempty("relation predicate", self.predicate))
        object.__setattr__(self, "target", _require_nonempty("relation predicate target", self.target))
        weight = float(self.weight)
        if weight <= 0:
            raise ValueError("relation predicate weight must be positive")
        object.__setattr__(self, "weight", weight)

    @property
    def key(self) -> str:
        return f"{self.source}:{self.predicate}:{self.target}"


@dataclass(frozen=True)
class SemanticBridgeTemplate:
    template_id: str
    version: str
    request: Any
    dimension_predicates: tuple[DimensionPredicate, ...] = ()
    relation_predicates: tuple[RelationPredicate, ...] = ()
    unresolved_obligations: tuple[str, ...] = ()
    support_weight: float = 1.0
    rationale: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "template_id", _require_nonempty("template id", self.template_id))
        object.__setattr__(self, "version", _require_nonempty("template version", self.version))
        object.__setattr__(self, "dimension_predicates", tuple(self.dimension_predicates))
        object.__setattr__(self, "relation_predicates", tuple(self.relation_predicates))
        object.__setattr__(self, "unresolved_obligations", tuple(str(v) for v in self.unresolved_obligations if str(v)))
        support = float(self.support_weight)
        if not 0.0 <= support <= 1.0:
            raise ValueError("template support_weight must be in [0,1]")
        object.__setattr__(self, "support_weight", support)
        object.__setattr__(self, "rationale", str(self.rationale))


def _dimension_predicate_record(value: DimensionPredicate) -> dict[str, Any]:
    return {
        "name": value.name,
        "expected": _thaw(value.expected),
        "required": value.required,
        "weight": value.weight,
    }


def _relation_predicate_record(value: RelationPredicate) -> dict[str, Any]:
    return {
        "source": value.source,
        "predicate": value.predicate,
        "target": value.target,
        "required": value.required,
        "weight": value.weight,
    }


def semantic_bridge_template_record(value: SemanticBridgeTemplate) -> dict[str, Any]:
    from .ai_build import encode_ai_build_request

    return {
        "template_id": value.template_id,
        "version": value.version,
        "request": json.loads(encode_ai_build_request(value.request)),
        "dimension_predicates": [_dimension_predicate_record(item) for item in value.dimension_predicates],
        "relation_predicates": [_relation_predicate_record(item) for item in value.relation_predicates],
        "unresolved_obligations": list(value.unresolved_obligations),
        "support_weight": value.support_weight,
        "rationale": value.rationale,
    }


def encode_semantic_bridge_templates(values: tuple[SemanticBridgeTemplate, ...] | list[SemanticBridgeTemplate]) -> str:
    ordered = tuple(sorted(tuple(values), key=lambda item: (item.template_id, item.version)))
    record = {
        "kind": "semantic_bridge_templates",
        "schema_version": "0.1.0",
        "templates": [semantic_bridge_template_record(item) for item in ordered],
    }
    try:
        return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ISQLCodecError(f"semantic bridge templates are not JSON serializable: {exc}") from exc


def decode_semantic_bridge_templates(value: str | bytes | Mapping[str, Any]) -> tuple[SemanticBridgeTemplate, ...]:
    from .ai_build import decode_ai_build_request

    try:
        if isinstance(value, bytes):
            raw = json.loads(value.decode("utf-8"))
        elif isinstance(value, str):
            raw = json.loads(value)
        else:
            raw = dict(value)
        if not isinstance(raw, Mapping) or raw.get("kind") != "semantic_bridge_templates":
            raise ISQLCodecError("semantic bridge template set kind is invalid")
        result: list[SemanticBridgeTemplate] = []
        for item in raw.get("templates", ()):
            if not isinstance(item, Mapping):
                raise ISQLCodecError("semantic bridge template must be an object")
            result.append(
                SemanticBridgeTemplate(
                    template_id=str(item.get("template_id", "")),
                    version=str(item.get("version", "")),
                    request=decode_ai_build_request(item.get("request") or {}),
                    dimension_predicates=tuple(
                        DimensionPredicate(
                            name=str(p.get("name", "")),
                            expected=p.get("expected"),
                            required=bool(p.get("required", True)),
                            weight=float(p.get("weight", 1.0)),
                        )
                        for p in item.get("dimension_predicates", ())
                    ),
                    relation_predicates=tuple(
                        RelationPredicate(
                            source=str(p.get("source", "")),
                            predicate=str(p.get("predicate", "")),
                            target=str(p.get("target", "")),
                            required=bool(p.get("required", True)),
                            weight=float(p.get("weight", 1.0)),
                        )
                        for p in item.get("relation_predicates", ())
                    ),
                    unresolved_obligations=tuple(str(v) for v in item.get("unresolved_obligations", ())),
                    support_weight=float(item.get("support_weight", 1.0)),
                    rationale=str(item.get("rationale", "")),
                )
            )
        return tuple(sorted(result, key=lambda item: (item.template_id, item.version)))
    except ISQLCodecError:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError, KeyError) as exc:
        raise ISQLCodecError(f"failed to decode semantic bridge templates: {exc}") from exc


@dataclass(frozen=True)
class SemanticAmbiguity:
    kind: str
    subject: str
    message: str
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _require_nonempty("ambiguity kind", self.kind))
        object.__setattr__(self, "subject", str(self.subject))
        object.__setattr__(self, "message", str(self.message))
        object.__setattr__(self, "evidence", _freeze(dict(self.evidence or {})))


@dataclass(frozen=True)
class SemanticObligation:
    kind: str
    subject: str
    message: str = ""
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _require_nonempty("obligation kind", self.kind))
        object.__setattr__(self, "subject", str(self.subject))
        object.__setattr__(self, "message", str(self.message))
        object.__setattr__(self, "evidence", _freeze(dict(self.evidence or {})))


@dataclass(frozen=True)
class BridgeConfidenceBreakdown:
    source_confidence: float
    dimension_coverage: float
    relation_coverage: float
    template_support: float
    obligation_penalty: float
    validation_factor: float

    @property
    def score(self) -> float:
        raw = (
            self.source_confidence
            * self.dimension_coverage
            * self.relation_coverage
            * self.template_support
            * self.obligation_penalty
            * self.validation_factor
        )
        return max(0.0, min(1.0, float(raw)))


@dataclass(frozen=True)
class SemanticGraphCandidate:
    candidate_id: str
    template_id: str
    template_version: str
    source_tensor_hash: str
    request_hash: str
    validation_status: str
    candidate_project: Any
    candidate_semantic_hash: str | None
    candidate_record_hash: str | None
    bridge_confidence: float
    confidence_breakdown: BridgeConfidenceBreakdown
    matched_dimensions: tuple[str, ...] = ()
    unmatched_dimensions: tuple[str, ...] = ()
    matched_relations: tuple[str, ...] = ()
    unmatched_relations: tuple[str, ...] = ()
    ambiguities: tuple[SemanticAmbiguity, ...] = ()
    obligations: tuple[SemanticObligation, ...] = ()
    diff: Any = None
    g4_candidate: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "matched_dimensions", tuple(sorted(self.matched_dimensions)))
        object.__setattr__(self, "unmatched_dimensions", tuple(sorted(self.unmatched_dimensions)))
        object.__setattr__(self, "matched_relations", tuple(sorted(self.matched_relations)))
        object.__setattr__(self, "unmatched_relations", tuple(sorted(self.unmatched_relations)))
        object.__setattr__(self, "ambiguities", tuple(self.ambiguities))
        object.__setattr__(self, "obligations", tuple(self.obligations))
        score = float(self.bridge_confidence)
        if not 0.0 <= score <= 1.0:
            raise ValueError("bridge confidence must be in [0,1]")
        object.__setattr__(self, "bridge_confidence", score)


@dataclass(frozen=True)
class SemanticCandidateSet:
    source_tensor_hash: str
    base_project_semantic_hash: str
    base_project_record_hash: str
    candidates: tuple[SemanticGraphCandidate, ...]
    ambiguities: tuple[SemanticAmbiguity, ...] = ()
    candidate_set_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidates", tuple(self.candidates))
        object.__setattr__(self, "ambiguities", tuple(self.ambiguities))
        if not self.candidate_set_hash:
            object.__setattr__(self, "candidate_set_hash", _candidate_set_hash(self))


def _semantic_equal(left: Any, right: Any) -> bool:
    return _thaw(left) == _thaw(right)


def _candidate_record(candidate: SemanticGraphCandidate) -> dict[str, Any]:
    return {
        "candidate_id": candidate.candidate_id,
        "template_id": candidate.template_id,
        "template_version": candidate.template_version,
        "source_tensor_hash": candidate.source_tensor_hash,
        "request_hash": candidate.request_hash,
        "validation_status": candidate.validation_status,
        "candidate_semantic_hash": candidate.candidate_semantic_hash,
        "candidate_record_hash": candidate.candidate_record_hash,
        "bridge_confidence": candidate.bridge_confidence,
        "confidence_breakdown": {
            "source_confidence": candidate.confidence_breakdown.source_confidence,
            "dimension_coverage": candidate.confidence_breakdown.dimension_coverage,
            "relation_coverage": candidate.confidence_breakdown.relation_coverage,
            "template_support": candidate.confidence_breakdown.template_support,
            "obligation_penalty": candidate.confidence_breakdown.obligation_penalty,
            "validation_factor": candidate.confidence_breakdown.validation_factor,
        },
        "matched_dimensions": list(candidate.matched_dimensions),
        "unmatched_dimensions": list(candidate.unmatched_dimensions),
        "matched_relations": list(candidate.matched_relations),
        "unmatched_relations": list(candidate.unmatched_relations),
        "ambiguities": [
            {"kind": a.kind, "subject": a.subject, "message": a.message, "evidence": _thaw(a.evidence)}
            for a in candidate.ambiguities
        ],
        "obligations": [
            {"kind": o.kind, "subject": o.subject, "message": o.message, "evidence": _thaw(o.evidence)}
            for o in candidate.obligations
        ],
    }


def semantic_candidate_set_record(value: SemanticCandidateSet) -> dict[str, Any]:
    return {
        "kind": "semantic_candidate_set",
        "schema_version": "0.1.0",
        "source_tensor_hash": value.source_tensor_hash,
        "base_project_semantic_hash": value.base_project_semantic_hash,
        "base_project_record_hash": value.base_project_record_hash,
        "candidates": [_candidate_record(c) for c in value.candidates],
        "ambiguities": [
            {"kind": a.kind, "subject": a.subject, "message": a.message, "evidence": _thaw(a.evidence)}
            for a in value.ambiguities
        ],
    }


def _candidate_set_hash(value: SemanticCandidateSet) -> str:
    payload = json.dumps(
        semantic_candidate_set_record(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def bridge_semantic_tensor(project: Any, tensor: SemanticTensor, templates: tuple[SemanticBridgeTemplate, ...] | list[SemanticBridgeTemplate]) -> SemanticCandidateSet:
    from .ai_build import BuildStatus, preview_ai_build
    from .canonical import record_hash, semantic_hash

    ordered_templates = tuple(sorted(tuple(templates), key=lambda t: (t.template_id, t.version)))
    template_ids = [t.template_id for t in ordered_templates]
    if len(template_ids) != len(set(template_ids)):
        raise ValueError("semantic bridge template ids must be unique")

    dimensions = {d.name: d for d in tensor.dimensions}
    relation_keys = {f"{r.source}:{r.predicate}:{r.target}" for r in tensor.relations}
    tensor_hash = semantic_tensor_hash(tensor)
    candidates: list[SemanticGraphCandidate] = []

    for template in ordered_templates:
        hard_fail = False
        matched_dims: list[str] = []
        unmatched_dims: list[str] = []
        matched_dim_weight = 0.0
        total_dim_weight = sum(p.weight for p in template.dimension_predicates) or 1.0
        ambiguities: list[SemanticAmbiguity] = []
        obligations: list[SemanticObligation] = []

        for predicate in template.dimension_predicates:
            observed = dimensions.get(predicate.name)
            if observed is None:
                if predicate.required:
                    hard_fail = True
                    break
                unmatched_dims.append(predicate.name)
                ambiguities.append(
                    SemanticAmbiguity(
                        kind="missing_dimension",
                        subject=predicate.name,
                        message="optional bridge dimension is not present",
                        evidence={"expected": _thaw(predicate.expected)},
                    )
                )
                obligations.append(
                    SemanticObligation(
                        kind="resolve_dimension",
                        subject=predicate.name,
                        message="provide or confirm the missing semantic dimension",
                        evidence={"expected": _thaw(predicate.expected)},
                    )
                )
                continue
            if _semantic_equal(observed.value, predicate.expected):
                matched_dims.append(predicate.name)
                matched_dim_weight += predicate.weight
            elif predicate.required:
                hard_fail = True
                break
            else:
                unmatched_dims.append(predicate.name)
                ambiguities.append(
                    SemanticAmbiguity(
                        kind="dimension_conflict",
                        subject=predicate.name,
                        message="optional bridge dimension differs from template preference",
                        evidence={"expected": _thaw(predicate.expected), "observed": _thaw(observed.value)},
                    )
                )
                obligations.append(
                    SemanticObligation(
                        kind="resolve_dimension",
                        subject=predicate.name,
                        message="resolve the semantic dimension conflict",
                        evidence={"expected": _thaw(predicate.expected), "observed": _thaw(observed.value)},
                    )
                )
        if hard_fail:
            continue

        matched_relations: list[str] = []
        unmatched_relations: list[str] = []
        matched_rel_weight = 0.0
        total_rel_weight = sum(p.weight for p in template.relation_predicates) or 1.0
        for predicate in template.relation_predicates:
            if predicate.key in relation_keys:
                matched_relations.append(predicate.key)
                matched_rel_weight += predicate.weight
            elif predicate.required:
                hard_fail = True
                break
            else:
                unmatched_relations.append(predicate.key)
                ambiguities.append(
                    SemanticAmbiguity(
                        kind="missing_relation",
                        subject=predicate.key,
                        message="optional semantic relation is not present",
                    )
                )
                obligations.append(
                    SemanticObligation(
                        kind="resolve_relation",
                        subject=predicate.key,
                        message="provide or confirm the missing semantic relation",
                    )
                )
        if hard_fail:
            continue

        for item in template.unresolved_obligations:
            obligations.append(
                SemanticObligation(
                    kind="template_obligation",
                    subject=item,
                    message="bridge template requires explicit follow-up evidence",
                )
            )

        preview = preview_ai_build(project, template.request)
        validation_factor = 1.0 if preview.status is BuildStatus.READY else 0.0
        dimension_coverage = matched_dim_weight / total_dim_weight
        relation_coverage = matched_rel_weight / total_rel_weight if template.relation_predicates else 1.0
        obligation_penalty = 1.0 / (1.0 + len(obligations))
        breakdown = BridgeConfidenceBreakdown(
            source_confidence=tensor.confidence,
            dimension_coverage=dimension_coverage,
            relation_coverage=relation_coverage,
            template_support=template.support_weight,
            obligation_penalty=obligation_penalty,
            validation_factor=validation_factor,
        )
        candidates.append(
            SemanticGraphCandidate(
                candidate_id=template.template_id,
                template_id=template.template_id,
                template_version=template.version,
                source_tensor_hash=tensor_hash,
                request_hash=preview.request_hash,
                validation_status=preview.status.value,
                candidate_project=preview.candidate_project,
                candidate_semantic_hash=preview.candidate_semantic_hash,
                candidate_record_hash=preview.candidate_record_hash,
                bridge_confidence=breakdown.score,
                confidence_breakdown=breakdown,
                matched_dimensions=tuple(matched_dims),
                unmatched_dimensions=tuple(unmatched_dims),
                matched_relations=tuple(matched_relations),
                unmatched_relations=tuple(unmatched_relations),
                ambiguities=tuple(ambiguities),
                obligations=tuple(obligations),
                diff=preview.diff,
                g4_candidate=preview,
            )
        )

    candidates.sort(
        key=lambda c: (
            0 if c.validation_status == BuildStatus.READY.value else 1,
            -c.bridge_confidence,
            len(c.obligations),
            c.candidate_id,
        )
    )
    set_ambiguities: list[SemanticAmbiguity] = []
    ready_count = sum(c.validation_status == BuildStatus.READY.value for c in candidates)
    if ready_count > 1:
        set_ambiguities.append(
            SemanticAmbiguity(
                kind="multiple_template_match",
                subject="candidate_set",
                message="multiple validated NOVA candidates match the same semantic intent",
                evidence={"candidate_ids": [c.candidate_id for c in candidates if c.validation_status == BuildStatus.READY.value]},
            )
        )
    if not candidates:
        set_ambiguities.append(
            SemanticAmbiguity(
                kind="no_template_match",
                subject="candidate_set",
                message="no bridge template satisfied all required semantic predicates",
            )
        )

    return SemanticCandidateSet(
        source_tensor_hash=tensor_hash,
        base_project_semantic_hash=semantic_hash(project),
        base_project_record_hash=record_hash(project),
        candidates=tuple(candidates),
        ambiguities=tuple(set_ambiguities),
    )


_ALLOWED_CORRECTION_ACTIONS = {
    "select_candidate",
    "reject_candidate",
    "set_dimension",
    "add_relation",
    "resolve_obligation",
}


@dataclass(frozen=True)
class SemanticCorrection:
    correction_id: str
    actor_id: str
    source_tensor_hash: str
    action: str
    subject: str = ""
    value: Any = None
    candidate_id: str | None = None
    rationale: str = ""
    parent_correction_id: str | None = None
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "correction_id", _require_nonempty("correction id", self.correction_id))
        object.__setattr__(self, "actor_id", _require_nonempty("correction actor id", self.actor_id))
        object.__setattr__(self, "source_tensor_hash", _require_nonempty("source tensor hash", self.source_tensor_hash))
        action = str(self.action)
        if action not in _ALLOWED_CORRECTION_ACTIONS:
            raise ValueError(f"unsupported semantic correction action: {action}")
        object.__setattr__(self, "action", action)
        object.__setattr__(self, "subject", str(self.subject))
        object.__setattr__(self, "value", _freeze(self.value))
        object.__setattr__(self, "candidate_id", None if self.candidate_id is None else str(self.candidate_id))
        object.__setattr__(self, "rationale", str(self.rationale))
        object.__setattr__(self, "parent_correction_id", None if self.parent_correction_id is None else str(self.parent_correction_id))
        object.__setattr__(self, "evidence", _freeze(dict(self.evidence or {})))
        if action in {"select_candidate", "reject_candidate"} and not self.candidate_id:
            raise ValueError(f"{action} requires candidate_id")
        if action in {"set_dimension", "add_relation", "resolve_obligation"} and not self.subject:
            raise ValueError(f"{action} requires subject")


def semantic_correction_record(value: SemanticCorrection) -> dict[str, Any]:
    return {
        "kind": "semantic_correction",
        "schema_version": "0.1.0",
        "correction_id": value.correction_id,
        "actor_id": value.actor_id,
        "source_tensor_hash": value.source_tensor_hash,
        "action": value.action,
        "subject": value.subject,
        "value": _thaw(value.value),
        "candidate_id": value.candidate_id,
        "rationale": value.rationale,
        "parent_correction_id": value.parent_correction_id,
        "evidence": _thaw(value.evidence),
    }


def semantic_correction_hash(value: SemanticCorrection) -> str:
    try:
        payload = json.dumps(
            semantic_correction_record(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ISQLCodecError(f"semantic correction is not JSON serializable: {exc}") from exc
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def encode_semantic_correction(value: SemanticCorrection) -> str:
    try:
        return json.dumps(
            semantic_correction_record(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ISQLCodecError(f"semantic correction is not JSON serializable: {exc}") from exc


def decode_semantic_correction(value: str | bytes | Mapping[str, Any]) -> SemanticCorrection:
    try:
        if isinstance(value, bytes):
            raw = json.loads(value.decode("utf-8"))
        elif isinstance(value, str):
            raw = json.loads(value)
        else:
            raw = dict(value)
        if not isinstance(raw, Mapping) or raw.get("kind") != "semantic_correction":
            raise ISQLCodecError("semantic correction kind is invalid")
        return SemanticCorrection(
            correction_id=str(raw.get("correction_id", "")),
            actor_id=str(raw.get("actor_id", "")),
            source_tensor_hash=str(raw.get("source_tensor_hash", "")),
            action=str(raw.get("action", "")),
            subject=str(raw.get("subject", "")),
            value=raw.get("value"),
            candidate_id=None if raw.get("candidate_id") is None else str(raw.get("candidate_id")),
            rationale=str(raw.get("rationale", "")),
            parent_correction_id=None
            if raw.get("parent_correction_id") is None
            else str(raw.get("parent_correction_id")),
            evidence=dict(raw.get("evidence") or {}),
        )
    except ISQLCodecError:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError, KeyError) as exc:
        raise ISQLCodecError(f"failed to decode semantic correction: {exc}") from exc


def _derived_provenance(tensor: SemanticTensor, correction: SemanticCorrection) -> SemanticProvenance:
    metadata = dict(_thaw(tensor.provenance.metadata))
    metadata.update(
        {
            "last_correction_id": correction.correction_id,
            "last_correction_action": correction.action,
            "last_correction_hash": semantic_correction_hash(correction),
        }
    )
    p = tensor.provenance
    return SemanticProvenance(
        protocol_version=p.protocol_version,
        registry_id=p.registry_id,
        registry_version=p.registry_version,
        domain=p.domain,
        decoder_contract=p.decoder_contract,
        registry_hash=p.registry_hash,
        encoder_version=p.encoder_version,
        model_id=p.model_id,
        resolution=p.resolution,
        context_policy=p.context_policy,
        source_id=p.source_id,
        parent_tensor_hash=semantic_tensor_hash(tensor),
        metadata=metadata,
    )


def apply_semantic_correction(tensor: SemanticTensor, correction: SemanticCorrection) -> SemanticTensor:
    from .errors import ISQLResolutionError

    current_hash = semantic_tensor_hash(tensor)
    if correction.source_tensor_hash != current_hash:
        raise ISQLResolutionError(
            "semantic correction source tensor hash does not match current tensor",
            context={"expected": current_hash, "received": correction.source_tensor_hash},
        )
    if correction.action in {"select_candidate", "reject_candidate"}:
        raise ISQLResolutionError("candidate selection/rejection must use resolve_semantic_candidate")

    dimensions = list(tensor.dimensions)
    relations = list(tensor.relations)
    if correction.action == "set_dimension":
        existing = next((d for d in dimensions if d.name == correction.subject), None)
        weight = existing.weight if existing is not None else 1.0
        value = correction.value
        if isinstance(value, Mapping) and "value" in value:
            weight = float(value.get("weight", weight))
            value = value.get("value")
        replacement = SemanticDimension(correction.subject, value, weight=weight)
        dimensions = [d for d in dimensions if d.name != correction.subject] + [replacement]
    elif correction.action == "add_relation":
        value = _thaw(correction.value)
        if not isinstance(value, Mapping):
            raise ISQLResolutionError("add_relation correction value must be an object")
        relation = SemanticRelation(
            str(value.get("source", "")),
            str(value.get("predicate", "")),
            str(value.get("target", "")),
            confidence=float(value.get("confidence", 1.0)),
            metadata=dict(value.get("metadata") or {}),
        )
        key = (relation.source, relation.predicate, relation.target)
        existing_keys = {(r.source, r.predicate, r.target) for r in relations}
        if key not in existing_keys:
            relations.append(relation)
    elif correction.action == "resolve_obligation":
        # Resolution evidence lives in provenance; no semantic coordinate is silently invented.
        pass

    return SemanticTensor(
        dimensions=tuple(dimensions),
        phase=tensor.phase,
        spectrum=tensor.spectrum,
        topology=tensor.topology,
        relations=tuple(relations),
        confidence=tensor.confidence,
        provenance=_derived_provenance(tensor, correction),
        extensions=tensor.extensions,
    )


@dataclass(frozen=True)
class SemanticResolution:
    status: str
    source_tensor_hash: str
    candidate_set_hash: str
    correction_id: str
    selected_candidate_id: str
    selected_project: Any = None
    selected_semantic_hash: str | None = None
    selected_record_hash: str | None = None
    rationale: str = ""


def semantic_resolution_record(value: SemanticResolution) -> dict[str, Any]:
    return {
        "kind": "semantic_resolution",
        "schema_version": "0.1.0",
        "status": value.status,
        "source_tensor_hash": value.source_tensor_hash,
        "candidate_set_hash": value.candidate_set_hash,
        "correction_id": value.correction_id,
        "selected_candidate_id": value.selected_candidate_id,
        "selected_semantic_hash": value.selected_semantic_hash,
        "selected_record_hash": value.selected_record_hash,
        "rationale": value.rationale,
    }


def resolve_semantic_candidate(project: Any, candidate_set: SemanticCandidateSet, correction: SemanticCorrection) -> SemanticResolution:
    from .ai_build import BuildStatus
    from .canonical import record_hash, semantic_hash
    from .errors import ISQLResolutionError

    if correction.action not in {"select_candidate", "reject_candidate"}:
        raise ISQLResolutionError("semantic candidate resolution requires select_candidate or reject_candidate action")
    if correction.source_tensor_hash != candidate_set.source_tensor_hash:
        raise ISQLResolutionError("correction source tensor hash does not match candidate set")
    if semantic_hash(project) != candidate_set.base_project_semantic_hash or record_hash(project) != candidate_set.base_project_record_hash:
        raise ISQLResolutionError("base project has changed since semantic candidates were generated")
    candidate = next((c for c in candidate_set.candidates if c.candidate_id == correction.candidate_id), None)
    if candidate is None:
        raise ISQLResolutionError(f"semantic candidate not found: {correction.candidate_id}")
    if correction.action == "reject_candidate":
        return SemanticResolution(
            status="rejected",
            source_tensor_hash=candidate_set.source_tensor_hash,
            candidate_set_hash=candidate_set.candidate_set_hash,
            correction_id=correction.correction_id,
            selected_candidate_id=candidate.candidate_id,
            selected_project=None,
            rationale=correction.rationale,
        )
    if candidate.validation_status != BuildStatus.READY.value or candidate.candidate_project is None:
        raise ISQLResolutionError("only READY semantic candidates can be selected")
    return SemanticResolution(
        status="selected",
        source_tensor_hash=candidate_set.source_tensor_hash,
        candidate_set_hash=candidate_set.candidate_set_hash,
        correction_id=correction.correction_id,
        selected_candidate_id=candidate.candidate_id,
        selected_project=candidate.candidate_project,
        selected_semantic_hash=candidate.candidate_semantic_hash,
        selected_record_hash=candidate.candidate_record_hash,
        rationale=correction.rationale,
    )


@dataclass(frozen=True)
class SemanticFidelity:
    dimension_preservation_ratio: float
    relation_preservation_ratio: float
    unresolved_obligation_count: int
    correction_count: int
    provenance_complete: bool
    traceable: bool


@dataclass(frozen=True)
class SemanticBackProjection:
    source_tensor_hash: str
    candidate_id: str
    candidate_graph_hash: str | None
    preserved_dimensions: tuple[str, ...]
    unresolved_dimensions: tuple[str, ...]
    preserved_relations: tuple[str, ...]
    unresolved_relations: tuple[str, ...]
    fidelity: SemanticFidelity
    bridge_confidence: float
    request_hash: str
    correction_ids: tuple[str, ...] = ()
    diff_summary: Mapping[str, Any] = field(default_factory=dict)
    exact_reconstruction_claimed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "preserved_dimensions", tuple(sorted(self.preserved_dimensions)))
        object.__setattr__(self, "unresolved_dimensions", tuple(sorted(self.unresolved_dimensions)))
        object.__setattr__(self, "preserved_relations", tuple(sorted(self.preserved_relations)))
        object.__setattr__(self, "unresolved_relations", tuple(sorted(self.unresolved_relations)))
        object.__setattr__(self, "correction_ids", tuple(self.correction_ids))
        object.__setattr__(self, "diff_summary", _freeze(dict(self.diff_summary or {})))


def semantic_back_projection_record(value: SemanticBackProjection) -> dict[str, Any]:
    return {
        "kind": "semantic_back_projection",
        "schema_version": "0.1.0",
        "source_tensor_hash": value.source_tensor_hash,
        "candidate_id": value.candidate_id,
        "candidate_graph_hash": value.candidate_graph_hash,
        "preserved_dimensions": list(value.preserved_dimensions),
        "unresolved_dimensions": list(value.unresolved_dimensions),
        "preserved_relations": list(value.preserved_relations),
        "unresolved_relations": list(value.unresolved_relations),
        "fidelity": {
            "dimension_preservation_ratio": value.fidelity.dimension_preservation_ratio,
            "relation_preservation_ratio": value.fidelity.relation_preservation_ratio,
            "unresolved_obligation_count": value.fidelity.unresolved_obligation_count,
            "correction_count": value.fidelity.correction_count,
            "provenance_complete": value.fidelity.provenance_complete,
            "traceable": value.fidelity.traceable,
        },
        "bridge_confidence": value.bridge_confidence,
        "request_hash": value.request_hash,
        "correction_ids": list(value.correction_ids),
        "diff_summary": _thaw(value.diff_summary),
        "exact_reconstruction_claimed": value.exact_reconstruction_claimed,
    }


def back_project_semantics(
    tensor: SemanticTensor,
    candidate_set: SemanticCandidateSet,
    candidate_id: str,
    *,
    corrections: tuple[SemanticCorrection, ...] | list[SemanticCorrection] = (),
) -> SemanticBackProjection:
    from .errors import ISQLResolutionError

    tensor_hash = semantic_tensor_hash(tensor)
    if tensor_hash != candidate_set.source_tensor_hash:
        raise ISQLResolutionError("semantic tensor does not match candidate set source")
    candidate = next((c for c in candidate_set.candidates if c.candidate_id == candidate_id), None)
    if candidate is None:
        raise ISQLResolutionError(f"semantic candidate not found: {candidate_id}")

    preserved_dimensions = set(candidate.matched_dimensions)
    all_dimensions = {d.name: d for d in tensor.dimensions}
    unresolved_dimensions = set(all_dimensions) - preserved_dimensions
    total_weight = sum(d.weight for d in tensor.dimensions)
    preserved_weight = sum(d.weight for d in tensor.dimensions if d.name in preserved_dimensions)
    dimension_ratio = 1.0 if total_weight == 0 else preserved_weight / total_weight

    preserved_relations = set(candidate.matched_relations)
    all_relations = {f"{r.source}:{r.predicate}:{r.target}" for r in tensor.relations}
    unresolved_relations = all_relations - preserved_relations
    relation_ratio = 1.0 if not all_relations else len(preserved_relations & all_relations) / len(all_relations)

    p = tensor.provenance
    provenance_complete = all(
        bool(v)
        for v in (p.protocol_version, p.registry_id, p.registry_version, p.domain, p.decoder_contract)
    )
    traceable = bool(
        candidate.source_tensor_hash == tensor_hash
        and candidate.request_hash
        and candidate.candidate_semantic_hash
        and candidate.template_id
    )
    diff_summary: dict[str, Any] = {}
    if candidate.diff is not None:
        diff_summary = {
            "semantic_changed": bool(getattr(candidate.diff, "semantic_changed", False)),
            "before_semantic_hash": getattr(candidate.diff, "before_semantic_hash", None),
            "after_semantic_hash": getattr(candidate.diff, "after_semantic_hash", None),
        }
    correction_ids = tuple(c.correction_id for c in corrections)
    fidelity = SemanticFidelity(
        dimension_preservation_ratio=dimension_ratio,
        relation_preservation_ratio=relation_ratio,
        unresolved_obligation_count=len(candidate.obligations),
        correction_count=len(correction_ids),
        provenance_complete=provenance_complete,
        traceable=traceable,
    )
    return SemanticBackProjection(
        source_tensor_hash=tensor_hash,
        candidate_id=candidate.candidate_id,
        candidate_graph_hash=candidate.candidate_semantic_hash,
        preserved_dimensions=tuple(preserved_dimensions),
        unresolved_dimensions=tuple(unresolved_dimensions),
        preserved_relations=tuple(preserved_relations),
        unresolved_relations=tuple(unresolved_relations),
        fidelity=fidelity,
        bridge_confidence=candidate.bridge_confidence,
        request_hash=candidate.request_hash,
        correction_ids=correction_ids,
        diff_summary=diff_summary,
        exact_reconstruction_claimed=False,
    )

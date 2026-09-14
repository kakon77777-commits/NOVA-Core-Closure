from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
import copy
import hashlib
import json
from typing import Any, Mapping, Sequence

from .core_norm import DEFAULT_CORE_NORM_PROFILE, CoreNormProfile
from .core_norm_compare import core_norm_profile_hash
from .cross_reconstruction import (
    CrossRepresentationCertificate,
    certify_reconstructions,
    reconstruct_surface,
)
from .errors import ValidationError

PROGRAM_PEC_REVISION = 1
PROGRAM_PEC_FORMAT = "nova.program-pec/0.9"
PROGRAM_PEC_ENVELOPE_FORMAT = "nova.program-pec-envelope/0.9"
SUPPORTED_PEC_LEVEL = "DPEC"


def _stable_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _hash(tag: bytes, value: Any) -> str:
    return "sha256:" + hashlib.sha256(tag + _stable_bytes(value)).hexdigest()


def _sorted_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({str(v) for v in values}))


class PECLevel(str, Enum):
    LPEC = "LPEC"
    DPEC = "DPEC"
    RGPEC = "RGPEC"


class DebtSeverity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class DebtStatus(str, Enum):
    RESOLVED = "resolved"
    OPEN = "open"
    DEFERRED = "deferred"


class DebtScope(str, Enum):
    IN_CLAIM = "in_claim"
    FRONTIER = "frontier"


@dataclass(frozen=True)
class ProgramPECFrame:
    domain: str
    assumptions: tuple[str, ...]
    representation_family: tuple[str, ...]
    operator_family: tuple[str, ...]
    route_grammar: tuple[str, ...]
    validation_regime: tuple[str, ...]
    observer_conditions: tuple[str, ...]
    backend_family: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.domain:
            raise ValidationError("Program PEC frame domain must not be empty")
        for name in (
            "assumptions",
            "representation_family",
            "operator_family",
            "route_grammar",
            "validation_regime",
            "observer_conditions",
            "backend_family",
        ):
            object.__setattr__(self, name, _sorted_unique(getattr(self, name)))
        if not self.representation_family:
            raise ValidationError("Program PEC frame needs a representation family")
        if not self.validation_regime:
            raise ValidationError("Program PEC frame needs a validation regime")
        if not self.observer_conditions:
            raise ValidationError("Program PEC frame needs observer conditions")

    def to_record(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "assumptions": list(self.assumptions),
            "representation_family": list(self.representation_family),
            "operator_family": list(self.operator_family),
            "route_grammar": list(self.route_grammar),
            "validation_regime": list(self.validation_regime),
            "observer_conditions": list(self.observer_conditions),
            "backend_family": list(self.backend_family),
        }


@dataclass(frozen=True)
class ProgramResourceBudget:
    budget_id: str
    max_representation_routes: int
    max_modules_per_project: int
    max_graphs_per_module: int
    max_nodes_per_graph: int
    verification_case_budget: int
    reopening_challenge_budget: int
    tool_regime: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.budget_id:
            raise ValidationError("Program PEC budget_id must not be empty")
        for name in (
            "max_representation_routes",
            "max_modules_per_project",
            "max_graphs_per_module",
            "max_nodes_per_graph",
            "verification_case_budget",
            "reopening_challenge_budget",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValidationError(f"Program PEC {name} must be a positive integer")
        object.__setattr__(self, "tool_regime", _sorted_unique(self.tool_regime))

    def to_record(self) -> dict[str, Any]:
        return {
            "budget_id": self.budget_id,
            "max_representation_routes": self.max_representation_routes,
            "max_modules_per_project": self.max_modules_per_project,
            "max_graphs_per_module": self.max_graphs_per_module,
            "max_nodes_per_graph": self.max_nodes_per_graph,
            "verification_case_budget": self.verification_case_budget,
            "reopening_challenge_budget": self.reopening_challenge_budget,
            "tool_regime": list(self.tool_regime),
        }


@dataclass(frozen=True)
class DebtItem:
    debt_id: str
    category: str
    summary: str
    severity: DebtSeverity
    status: DebtStatus
    scope: DebtScope
    reopen_trigger: str

    def __post_init__(self) -> None:
        if not self.debt_id or not self.category or not self.summary or not self.reopen_trigger:
            raise ValidationError("Program PEC debt items require id/category/summary/reopen_trigger")

    def to_record(self) -> dict[str, Any]:
        return {
            "debt_id": self.debt_id,
            "category": self.category,
            "summary": self.summary,
            "severity": self.severity.value,
            "status": self.status.value,
            "scope": self.scope.value,
            "reopen_trigger": self.reopen_trigger,
        }


@dataclass(frozen=True)
class FrontierItem:
    frontier_id: str
    domain: str
    summary: str
    required_capability: str
    reopen_trigger: str

    def __post_init__(self) -> None:
        if not all((self.frontier_id, self.domain, self.summary, self.required_capability, self.reopen_trigger)):
            raise ValidationError("Program PEC frontier items must be fully explicit")

    def to_record(self) -> dict[str, Any]:
        return {
            "frontier_id": self.frontier_id,
            "domain": self.domain,
            "summary": self.summary,
            "required_capability": self.required_capability,
            "reopen_trigger": self.reopen_trigger,
        }


@dataclass(frozen=True)
class ReopenCondition:
    condition_id: str
    trigger: str
    action: str = "reopen_certificate"

    def __post_init__(self) -> None:
        if not self.condition_id or not self.trigger or not self.action:
            raise ValidationError("Program PEC reopening conditions must be explicit")

    def to_record(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "trigger": self.trigger,
            "action": self.action,
        }


@dataclass(frozen=True)
class ReopeningChallengeResult:
    challenge_id: str
    kind: str
    expected: str
    observed: str
    passed: bool
    evidence_hash: str

    def to_record(self) -> dict[str, Any]:
        return {
            "challenge_id": self.challenge_id,
            "kind": self.kind,
            "expected": self.expected,
            "observed": self.observed,
            "passed": self.passed,
            "evidence_hash": self.evidence_hash,
        }


@dataclass(frozen=True)
class ProgramVerificationEvidence:
    isolated_cases_passed: int
    isolated_cases_failed: int
    standalone_harness_passed: bool
    upstream_full_suite_fresh: bool = False
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("isolated_cases_passed", "isolated_cases_failed"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValidationError(f"Program PEC {name} must be a non-negative integer")
        object.__setattr__(self, "evidence_refs", _sorted_unique(self.evidence_refs))

    @property
    def total_cases(self) -> int:
        return self.isolated_cases_passed + self.isolated_cases_failed

    @property
    def passed(self) -> bool:
        return self.standalone_harness_passed and self.isolated_cases_passed > 0 and self.isolated_cases_failed == 0

    def to_record(self) -> dict[str, Any]:
        return {
            "isolated_cases_passed": self.isolated_cases_passed,
            "isolated_cases_failed": self.isolated_cases_failed,
            "standalone_harness_passed": self.standalone_harness_passed,
            "upstream_full_suite_fresh": self.upstream_full_suite_fresh,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class RouteCoverage:
    declared: tuple[str, ...]
    seen: tuple[str, ...]
    ratio: float

    def to_record(self) -> dict[str, Any]:
        return {"declared": list(self.declared), "seen": list(self.seen), "ratio": self.ratio}


@dataclass(frozen=True)
class NoveltyStats:
    core_norm_classes: int
    converged: bool
    obligations: int

    def to_record(self) -> dict[str, Any]:
        return {
            "core_norm_classes": self.core_norm_classes,
            "converged": self.converged,
            "obligations": self.obligations,
            "scope": "declared representation family only",
        }


@dataclass(frozen=True)
class ConditionAudit:
    name: str
    passed: bool
    score: float
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.score) <= 1.0:
            raise ValidationError("Program PEC condition score must be in [0,1]")
        object.__setattr__(self, "score", float(self.score))
        object.__setattr__(self, "evidence", tuple(str(v) for v in self.evidence))

    def to_record(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "score": self.score,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class ClosureConfidenceVector:
    reachability: float
    novelty_saturation: float
    debt_control: float
    frontier_audit: float
    verification_coverage: float
    reopening_robustness: float

    def to_record(self) -> dict[str, float]:
        return {
            "c_R": self.reachability,
            "c_N": self.novelty_saturation,
            "c_D": self.debt_control,
            "c_F": self.frontier_audit,
            "c_V": self.verification_coverage,
            "c_A": self.reopening_robustness,
        }


@dataclass(frozen=True)
class ProgramPECCertificate:
    revision: int
    level: PECLevel
    status: str
    claim_summary: str
    claim_boundary: str
    terminal_claim: bool
    frame: ProgramPECFrame
    budget: ProgramResourceBudget
    profile_hash: str
    reconstruction_certificate_hash: str
    state_ref: str | None
    manifest_ref: str
    route_coverage: RouteCoverage
    novelty_stats: NoveltyStats
    verification_summary: ProgramVerificationEvidence
    audits: tuple[ConditionAudit, ...]
    confidence: ClosureConfidenceVector
    debt_ledger: tuple[DebtItem, ...]
    frontier_map: tuple[FrontierItem, ...]
    reopen_conditions: tuple[ReopenCondition, ...]
    reopening_challenges: tuple[ReopeningChallengeResult, ...]
    false_closure_risk_flags: tuple[str, ...]

    @property
    def closed(self) -> bool:
        return self.status.endswith("_CLOSED")

    def to_record(self) -> dict[str, Any]:
        return {
            "format": PROGRAM_PEC_FORMAT,
            "revision": self.revision,
            "level": self.level.value,
            "status": self.status,
            "claim_summary": self.claim_summary,
            "claim_boundary": self.claim_boundary,
            "terminal_claim": self.terminal_claim,
            "frame": self.frame.to_record(),
            "budget": self.budget.to_record(),
            "profile_hash": self.profile_hash,
            "reconstruction_certificate_hash": self.reconstruction_certificate_hash,
            "state_ref": self.state_ref,
            "manifest_ref": self.manifest_ref,
            "route_coverage": self.route_coverage.to_record(),
            "novelty_stats": self.novelty_stats.to_record(),
            "verification_summary": self.verification_summary.to_record(),
            "audits": [item.to_record() for item in self.audits],
            "confidence": self.confidence.to_record(),
            "debt_ledger": [item.to_record() for item in self.debt_ledger],
            "frontier_map": [item.to_record() for item in self.frontier_map],
            "reopen_conditions": [item.to_record() for item in self.reopen_conditions],
            "reopening_challenges": [item.to_record() for item in self.reopening_challenges],
            "false_closure_risk_flags": list(self.false_closure_risk_flags),
        }

    @property
    def certificate_hash(self) -> str:
        return program_pec_hash(self)


def program_pec_hash(certificate: ProgramPECCertificate) -> str:
    return _hash(b"NOVA-PROGRAM-PEC-v0.9\0", certificate.to_record())


def cross_reconstruction_certificate_hash(certificate: CrossRepresentationCertificate) -> str:
    return _hash(b"NOVA-PROGRAM-PEC-XREC-v0.9\0", certificate.to_record())


def encode_program_pec(certificate: ProgramPECCertificate) -> str:
    envelope = {
        "format": PROGRAM_PEC_ENVELOPE_FORMAT,
        "certificate_hash": certificate.certificate_hash,
        "certificate": certificate.to_record(),
    }
    return json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _as_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValidationError(f"{label} must be an object")
    return value


def decode_program_pec(value: str | bytes | Mapping[str, Any]) -> ProgramPECCertificate:
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"invalid Program PEC JSON: {exc.msg}") from exc
    envelope = _as_mapping(value, "Program PEC envelope")
    if envelope.get("format") != PROGRAM_PEC_ENVELOPE_FORMAT:
        raise ValidationError("invalid Program PEC envelope format")
    expected_hash = str(envelope.get("certificate_hash", ""))
    data = _as_mapping(envelope.get("certificate"), "Program PEC certificate")
    if data.get("format") != PROGRAM_PEC_FORMAT:
        raise ValidationError("invalid Program PEC certificate format")
    if int(data.get("revision", 0)) != PROGRAM_PEC_REVISION:
        raise ValidationError("unsupported Program PEC revision")

    frame_data = _as_mapping(data.get("frame"), "Program PEC frame")
    frame = ProgramPECFrame(
        domain=str(frame_data.get("domain", "")),
        assumptions=tuple(frame_data.get("assumptions", ())),
        representation_family=tuple(frame_data.get("representation_family", ())),
        operator_family=tuple(frame_data.get("operator_family", ())),
        route_grammar=tuple(frame_data.get("route_grammar", ())),
        validation_regime=tuple(frame_data.get("validation_regime", ())),
        observer_conditions=tuple(frame_data.get("observer_conditions", ())),
        backend_family=tuple(frame_data.get("backend_family", ())),
    )
    budget_data = _as_mapping(data.get("budget"), "Program PEC budget")
    budget = ProgramResourceBudget(
        budget_id=str(budget_data.get("budget_id", "")),
        max_representation_routes=int(budget_data.get("max_representation_routes", 0)),
        max_modules_per_project=int(budget_data.get("max_modules_per_project", 0)),
        max_graphs_per_module=int(budget_data.get("max_graphs_per_module", 0)),
        max_nodes_per_graph=int(budget_data.get("max_nodes_per_graph", 0)),
        verification_case_budget=int(budget_data.get("verification_case_budget", 0)),
        reopening_challenge_budget=int(budget_data.get("reopening_challenge_budget", 0)),
        tool_regime=tuple(budget_data.get("tool_regime", ())),
    )
    route_data = _as_mapping(data.get("route_coverage"), "Program PEC route coverage")
    route_coverage = RouteCoverage(
        declared=tuple(route_data.get("declared", ())),
        seen=tuple(route_data.get("seen", ())),
        ratio=float(route_data.get("ratio", 0.0)),
    )
    novelty_data = _as_mapping(data.get("novelty_stats"), "Program PEC novelty stats")
    novelty_stats = NoveltyStats(
        core_norm_classes=int(novelty_data.get("core_norm_classes", 0)),
        converged=bool(novelty_data.get("converged", False)),
        obligations=int(novelty_data.get("obligations", 0)),
    )
    verify_data = _as_mapping(data.get("verification_summary"), "Program PEC verification summary")
    verification_summary = ProgramVerificationEvidence(
        isolated_cases_passed=int(verify_data.get("isolated_cases_passed", 0)),
        isolated_cases_failed=int(verify_data.get("isolated_cases_failed", 0)),
        standalone_harness_passed=bool(verify_data.get("standalone_harness_passed", False)),
        upstream_full_suite_fresh=bool(verify_data.get("upstream_full_suite_fresh", False)),
        evidence_refs=tuple(verify_data.get("evidence_refs", ())),
    )
    audits = tuple(
        ConditionAudit(
            name=str(item.get("name", "")),
            passed=bool(item.get("passed", False)),
            score=float(item.get("score", 0.0)),
            evidence=tuple(item.get("evidence", ())),
        )
        for item in data.get("audits", ())
        if isinstance(item, Mapping)
    )
    confidence_data = _as_mapping(data.get("confidence"), "Program PEC confidence")
    confidence = ClosureConfidenceVector(
        reachability=float(confidence_data.get("c_R", 0.0)),
        novelty_saturation=float(confidence_data.get("c_N", 0.0)),
        debt_control=float(confidence_data.get("c_D", 0.0)),
        frontier_audit=float(confidence_data.get("c_F", 0.0)),
        verification_coverage=float(confidence_data.get("c_V", 0.0)),
        reopening_robustness=float(confidence_data.get("c_A", 0.0)),
    )
    debts = tuple(
        DebtItem(
            debt_id=str(item.get("debt_id", "")),
            category=str(item.get("category", "")),
            summary=str(item.get("summary", "")),
            severity=DebtSeverity(str(item.get("severity", "minor"))),
            status=DebtStatus(str(item.get("status", "open"))),
            scope=DebtScope(str(item.get("scope", "frontier"))),
            reopen_trigger=str(item.get("reopen_trigger", "")),
        )
        for item in data.get("debt_ledger", ())
        if isinstance(item, Mapping)
    )
    frontier = tuple(
        FrontierItem(
            frontier_id=str(item.get("frontier_id", "")),
            domain=str(item.get("domain", "")),
            summary=str(item.get("summary", "")),
            required_capability=str(item.get("required_capability", "")),
            reopen_trigger=str(item.get("reopen_trigger", "")),
        )
        for item in data.get("frontier_map", ())
        if isinstance(item, Mapping)
    )
    reopens = tuple(
        ReopenCondition(
            condition_id=str(item.get("condition_id", "")),
            trigger=str(item.get("trigger", "")),
            action=str(item.get("action", "reopen_certificate")),
        )
        for item in data.get("reopen_conditions", ())
        if isinstance(item, Mapping)
    )
    challenges = tuple(
        ReopeningChallengeResult(
            challenge_id=str(item.get("challenge_id", "")),
            kind=str(item.get("kind", "")),
            expected=str(item.get("expected", "")),
            observed=str(item.get("observed", "")),
            passed=bool(item.get("passed", False)),
            evidence_hash=str(item.get("evidence_hash", "")),
        )
        for item in data.get("reopening_challenges", ())
        if isinstance(item, Mapping)
    )
    cert = ProgramPECCertificate(
        revision=int(data.get("revision", 0)),
        level=PECLevel(str(data.get("level", "DPEC"))),
        status=str(data.get("status", "")),
        claim_summary=str(data.get("claim_summary", "")),
        claim_boundary=str(data.get("claim_boundary", "")),
        terminal_claim=bool(data.get("terminal_claim", False)),
        frame=frame,
        budget=budget,
        profile_hash=str(data.get("profile_hash", "")),
        reconstruction_certificate_hash=str(data.get("reconstruction_certificate_hash", "")),
        state_ref=data.get("state_ref"),
        manifest_ref=str(data.get("manifest_ref", "")),
        route_coverage=route_coverage,
        novelty_stats=novelty_stats,
        verification_summary=verification_summary,
        audits=audits,
        confidence=confidence,
        debt_ledger=debts,
        frontier_map=frontier,
        reopen_conditions=reopens,
        reopening_challenges=challenges,
        false_closure_risk_flags=tuple(data.get("false_closure_risk_flags", ())),
    )
    if not expected_hash or cert.certificate_hash != expected_hash:
        raise ValidationError("Program PEC certificate hash mismatch")
    return cert


def _project_sizes(certificate: CrossRepresentationCertificate) -> tuple[int, int, int]:
    max_modules = 0
    max_graphs = 0
    max_nodes = 0
    for item in certificate.reconstructions:
        project = item.project
        max_modules = max(max_modules, len(project.modules))
        for module in project.modules:
            max_graphs = max(max_graphs, len(module.graphs))
            for graph in module.graphs:
                max_nodes = max(max_nodes, len(graph.nodes))
    return max_modules, max_graphs, max_nodes


def _validate_boundary(
    sources: Mapping[str, Any],
    frame: ProgramPECFrame,
    budget: ProgramResourceBudget,
    reconstruction: CrossRepresentationCertificate,
) -> None:
    declared = set(frame.representation_family)
    supplied = {str(key).lower() for key in sources}
    if len(declared) > budget.max_representation_routes:
        raise ValidationError(
            "Program PEC frame exceeds representation-route budget",
            context={"declared": len(declared), "budget": budget.max_representation_routes},
        )
    if supplied - declared:
        raise ValidationError(
            "Program PEC sources include undeclared representation routes",
            context={"undeclared": sorted(supplied - declared)},
        )
    max_modules, max_graphs, max_nodes = _project_sizes(reconstruction)
    if max_modules > budget.max_modules_per_project:
        raise ValidationError("Program PEC project exceeds module budget")
    if max_graphs > budget.max_graphs_per_module:
        raise ValidationError("Program PEC project exceeds graph budget")
    if max_nodes > budget.max_nodes_per_graph:
        raise ValidationError("Program PEC project exceeds node budget")


def _mutate_operator_source(kind: str, source: Any) -> Any | None:
    if kind == "ai" and isinstance(source, Mapping):
        candidate = copy.deepcopy(source)
        steps = candidate.get("steps")
        if isinstance(steps, list):
            for step in steps:
                if isinstance(step, dict) and step.get("operator") == "Add":
                    step["operator"] = "Subtract"
                    return candidate
    if kind == "graph" and isinstance(source, Mapping):
        candidate = copy.deepcopy(source)
        graph = candidate.get("graph")
        if isinstance(graph, dict) and isinstance(graph.get("nodes"), list):
            for node in graph["nodes"]:
                if isinstance(node, dict) and node.get("op") == "Add":
                    node["op"] = "Subtract"
                    return candidate
    if kind == "text" and isinstance(source, str) and "Add(" in source:
        return source.replace("Add(", "Subtract(", 1)
    return None


def _mutate_invalid_reference(kind: str, source: Any) -> Any | None:
    if kind == "ai" and isinstance(source, Mapping):
        candidate = copy.deepcopy(source)
        steps = candidate.get("steps")
        if isinstance(steps, list) and steps:
            last = steps[-1]
            if isinstance(last, dict):
                last["args"] = [{"value": "__pec_missing_binding__"}]
                return candidate
    if kind == "graph" and isinstance(source, Mapping):
        candidate = copy.deepcopy(source)
        graph = candidate.get("graph")
        if isinstance(graph, dict) and isinstance(graph.get("nodes"), list) and graph["nodes"]:
            node = graph["nodes"][0]
            if isinstance(node, dict):
                args = list(node.get("args", []))
                if args:
                    args[0] = "__pec_missing_binding__"
                    node["args"] = args
                    return candidate
    return None


def run_standard_reopening_challenges(
    sources: Mapping[str, Any],
    *,
    profile: CoreNormProfile = DEFAULT_CORE_NORM_PROFILE,
) -> tuple[ReopeningChallengeResult, ...]:
    results: list[ReopeningChallengeResult] = []

    mutated_sources = dict(sources)
    mutated_kind = None
    for kind in ("ai", "graph", "text"):
        if kind in sources:
            mutated = _mutate_operator_source(kind, sources[kind])
            if mutated is not None:
                mutated_sources[kind] = mutated
                mutated_kind = kind
                break
    if mutated_kind is None:
        results.append(ReopeningChallengeResult(
            challenge_id="ART-LITE-OPERATOR-01",
            kind="operator_mutation",
            expected="semantic mutation breaks convergence",
            observed="no admissible Add mutation route was available",
            passed=False,
            evidence_hash=_hash(b"NOVA-PEC-CHALLENGE-v0.9\0", {"kind": "operator_mutation", "available": False}),
        ))
    else:
        mutated_cert = certify_reconstructions(mutated_sources, profile=profile)
        passed = not mutated_cert.converged
        results.append(ReopeningChallengeResult(
            challenge_id="ART-LITE-OPERATOR-01",
            kind="operator_mutation",
            expected="semantic mutation breaks convergence",
            observed="convergence_broken" if passed else "convergence_survived",
            passed=passed,
            evidence_hash=cross_reconstruction_certificate_hash(mutated_cert),
        ))

    ref_kind = None
    ref_source = None
    for kind in ("ai", "graph"):
        if kind in sources:
            mutated = _mutate_invalid_reference(kind, sources[kind])
            if mutated is not None:
                ref_kind = kind
                ref_source = mutated
                break
    if ref_kind is None:
        results.append(ReopeningChallengeResult(
            challenge_id="ART-LITE-REFERENCE-01",
            kind="reference_integrity",
            expected="invalid structural reference is rejected",
            observed="no structured reference route was available",
            passed=False,
            evidence_hash=_hash(b"NOVA-PEC-CHALLENGE-v0.9\0", {"kind": "reference_integrity", "available": False}),
        ))
    else:
        try:
            reconstruct_surface(ref_kind, ref_source, profile=profile)
        except ValidationError as exc:
            category = getattr(getattr(exc, "detail", None), "category", type(exc).__name__)
            observed = f"rejected:{category}"
            passed = True
        else:
            observed = "accepted_invalid_reference"
            passed = False
        results.append(ReopeningChallengeResult(
            challenge_id="ART-LITE-REFERENCE-01",
            kind="reference_integrity",
            expected="invalid structural reference is rejected",
            observed=observed,
            passed=passed,
            evidence_hash=_hash(b"NOVA-PEC-CHALLENGE-v0.9\0", {"kind": ref_kind, "observed": observed}),
        ))

    if "text" in sources and isinstance(sources["text"], str):
        malicious = sources["text"] + "\n__pec_escape = __import__('os').system('echo no')\n"
        try:
            reconstruct_surface("text", malicious, profile=profile)
        except ValidationError as exc:
            category = getattr(getattr(exc, "detail", None), "category", type(exc).__name__)
            observed = f"rejected:{category}"
            passed = True
        else:
            observed = "accepted_host_escape"
            passed = False
    else:
        observed = "no_text_route"
        passed = False
    results.append(ReopeningChallengeResult(
        challenge_id="ART-LITE-SURFACE-01",
        kind="surface_escape",
        expected="unsupported host-language surface is rejected",
        observed=observed,
        passed=passed,
        evidence_hash=_hash(b"NOVA-PEC-CHALLENGE-v0.9\0", {"observed": observed}),
    ))

    return tuple(results)


def default_v09_frontier() -> tuple[FrontierItem, ...]:
    return (
        FrontierItem(
            "FRONTIER-REP-01",
            "representation",
            "Representation families outside text/graph/AI v0.8 adapters are not closed.",
            "new independently implemented adapter plus CoreNorm convergence evidence",
            "new representation adapter is admitted into the frame",
        ),
        FrontierItem(
            "FRONTIER-OP-01",
            "operators",
            "Effectful/control-flow/call equivalence remains outside the bounded CoreNorm profile.",
            "expanded CoreNorm profile with falsification suite",
            "operator family or CoreNorm rewrite family expands",
        ),
        FrontierItem(
            "FRONTIER-BACKEND-01",
            "backend",
            "Backend execution equivalence is not part of the v0.9 closure claim.",
            "backend replay and behavioral comparison evidence",
            "backend semantics are added to the claim",
        ),
        FrontierItem(
            "FRONTIER-VERIFY-01",
            "verification",
            "The historical upstream 215-test baseline was not freshly rerun in this container.",
            "fresh full upstream regression execution",
            "claim expands from isolated compatibility to upstream integration",
        ),
        FrontierItem(
            "FRONTIER-ART-01",
            "reopening",
            "Only ART-lite challenges are included; full ART/FDT belongs to the next experiment.",
            "versioned ART/FDT suite and Re-PEC replay",
            "full adversarial/future-dimension robustness is claimed",
        ),
    )


def default_v09_debts() -> tuple[DebtItem, ...]:
    return (
        DebtItem(
            "DEBT-UPSTREAM-01",
            "verification",
            "Fresh upstream full-suite integration evidence is absent.",
            DebtSeverity.MAJOR,
            DebtStatus.DEFERRED,
            DebtScope.FRONTIER,
            "reopen when upstream integration becomes part of the certificate scope",
        ),
        DebtItem(
            "DEBT-ART-01",
            "reopening",
            "Full ART/FDT coverage has not yet been executed.",
            DebtSeverity.MAJOR,
            DebtStatus.DEFERRED,
            DebtScope.FRONTIER,
            "reopen when stronger reopening robustness is claimed",
        ),
    )


def default_v09_reopen_conditions() -> tuple[ReopenCondition, ...]:
    return (
        ReopenCondition("REOPEN-REP", "representation_family changes or a new adapter is admitted"),
        ReopenCondition("REOPEN-OP", "operator_family or CoreNorm rewrite profile changes"),
        ReopenCondition("REOPEN-BACKEND", "backend behavior becomes part of the claim"),
        ReopenCondition("REOPEN-BUDGET", "resource budget expands beyond the certified envelope"),
        ReopenCondition("REOPEN-OBSERVER", "observer/equivalence condition changes"),
        ReopenCondition("REOPEN-DEBT", "a critical in-claim debt is discovered"),
        ReopenCondition("REOPEN-VERIFY", "certificate replay or source evidence verification fails"),
    )


def _audit_conditions(
    reconstruction: CrossRepresentationCertificate,
    frame: ProgramPECFrame,
    debt_ledger: tuple[DebtItem, ...],
    frontier_map: tuple[FrontierItem, ...],
    challenges: tuple[ReopeningChallengeResult, ...],
    reopen_conditions: tuple[ReopenCondition, ...],
    verification_summary: ProgramVerificationEvidence,
) -> tuple[tuple[ConditionAudit, ...], ClosureConfidenceVector, RouteCoverage, NoveltyStats]:
    declared = set(frame.representation_family)
    seen = {item.representation_kind for item in reconstruction.reconstructions}
    reach_score = len(declared & seen) / len(declared) if declared else 0.0
    reach_passed = seen == declared
    route_coverage = RouteCoverage(tuple(sorted(declared)), tuple(sorted(seen)), reach_score)
    reach = ConditionAudit(
        "Reach",
        reach_passed,
        reach_score,
        (f"declared={sorted(declared)}", f"seen={sorted(seen)}"),
    )

    unique_classes = {item.core_norm_hash for item in reconstruction.reconstructions}
    obligations = tuple(ob for item in reconstruction.reconstructions for ob in item.obligations)
    novelty_passed = reconstruction.converged and not obligations
    novelty_score = 1.0 if novelty_passed else (1.0 / max(1, len(unique_classes)))
    novelty_stats = NoveltyStats(len(unique_classes), reconstruction.converged, len(obligations))
    novelty = ConditionAudit(
        "Novel",
        novelty_passed,
        novelty_score,
        (
            f"core_norm_classes={len(unique_classes)}",
            f"obligations={len(obligations)}",
            "scope=declared representation family only",
        ),
    )

    blocking_debt = tuple(
        item.debt_id
        for item in debt_ledger
        if item.scope is DebtScope.IN_CLAIM
        and item.status is not DebtStatus.RESOLVED
        and item.severity is DebtSeverity.CRITICAL
    )
    debt_passed = not blocking_debt
    in_claim = [item for item in debt_ledger if item.scope is DebtScope.IN_CLAIM]
    resolved_in_claim = [item for item in in_claim if item.status is DebtStatus.RESOLVED]
    debt_score = 1.0 if not in_claim else len(resolved_in_claim) / len(in_claim)
    debt = ConditionAudit(
        "Debt",
        debt_passed,
        debt_score if debt_passed else min(debt_score, 0.99),
        (f"blocking_critical={list(blocking_debt)}", f"ledger_items={len(debt_ledger)}"),
    )

    frontier_passed = bool(frontier_map) and all(item.reopen_trigger and item.required_capability for item in frontier_map)
    frontier_score = 1.0 if frontier_passed else 0.0
    frontier = ConditionAudit(
        "Frontier",
        frontier_passed,
        frontier_score,
        (f"frontier_items={len(frontier_map)}", "all items require explicit reopen trigger/capability"),
    )

    recon_valid = all(
        item.source_hash.startswith("sha256:")
        and item.lowered_semantic_hash.startswith("sha256:")
        and item.core_norm_hash.startswith("sha256:")
        for item in reconstruction.reconstructions
    )
    verify_checks = (
        recon_valid,
        reconstruction.converged,
        bool(reconstruction.profile_hash),
        verification_summary.passed,
    )
    verification_score = sum(1 for ok in verify_checks if ok) / len(verify_checks)
    verification = ConditionAudit(
        "Verify",
        all(verify_checks),
        verification_score,
        (
            f"reconstruction_evidence={recon_valid}",
            f"converged={reconstruction.converged}",
            f"profile_hash={bool(reconstruction.profile_hash)}",
            f"isolated_cases={verification_summary.isolated_cases_passed}/{verification_summary.total_cases}",
            f"standalone_harness={verification_summary.standalone_harness_passed}",
        ),
    )

    reopening_score = (
        sum(1 for item in challenges if item.passed) / len(challenges)
        if challenges
        else 0.0
    )
    reopen_passed = bool(challenges) and bool(reopen_conditions) and all(item.passed for item in challenges)
    if not reopen_conditions:
        reopening_score = 0.0
    reopening = ConditionAudit(
        "Reopen",
        reopen_passed,
        reopening_score,
        tuple(f"{item.challenge_id}:{'PASS' if item.passed else 'FAIL'}" for item in challenges)
        + (f"declared_reopen_conditions={len(reopen_conditions)}",),
    )

    audits = (reach, novelty, debt, frontier, verification, reopening)
    confidence = ClosureConfidenceVector(
        reach.score,
        novelty.score,
        debt.score,
        frontier.score,
        verification.score,
        reopening_score,
    )
    return audits, confidence, route_coverage, novelty_stats


def build_program_pec_certificate(
    sources: Mapping[str, Any],
    *,
    frame: ProgramPECFrame,
    budget: ProgramResourceBudget,
    debt_ledger: Sequence[DebtItem] = (),
    frontier_map: Sequence[FrontierItem] = (),
    reopen_conditions: Sequence[ReopenCondition] = (),
    level: PECLevel = PECLevel.DPEC,
    claim_summary: str = (
        "Declared text-like, graph-native, and AI-native reconstruction routes converge "
        "to one bounded CoreNorm class under the certified frame."
    ),
    profile: CoreNormProfile = DEFAULT_CORE_NORM_PROFILE,
    verification_summary: ProgramVerificationEvidence | None = None,
    run_reopening_challenges: bool = True,
) -> ProgramPECCertificate:
    if level.value != SUPPORTED_PEC_LEVEL:
        raise ValidationError(
            "v0.9 builder only certifies domain-level Program DPEC",
            context={"requested_level": level.value},
        )
    reconstruction = certify_reconstructions(sources, profile=profile)
    _validate_boundary(sources, frame, budget, reconstruction)
    verification_summary = verification_summary or ProgramVerificationEvidence(0, 0, False)
    if verification_summary.total_cases > budget.verification_case_budget:
        raise ValidationError("Program PEC verification evidence exceeds verification budget")

    challenges = (
        run_standard_reopening_challenges(sources, profile=profile)
        if run_reopening_challenges
        else ()
    )
    if len(challenges) > budget.reopening_challenge_budget:
        raise ValidationError("Program PEC challenge suite exceeds reopening budget")

    debts = tuple(sorted(debt_ledger, key=lambda item: item.debt_id))
    frontier = tuple(sorted(frontier_map, key=lambda item: item.frontier_id))
    reopens = tuple(sorted(reopen_conditions, key=lambda item: item.condition_id))
    audits, confidence, route_coverage, novelty_stats = _audit_conditions(
        reconstruction, frame, debts, frontier, challenges, reopens, verification_summary
    )
    closed = all(item.passed for item in audits)

    xrec_hash = cross_reconstruction_certificate_hash(reconstruction)
    frame_budget_manifest = {
        "frame": frame.to_record(),
        "budget": budget.to_record(),
        "profile_hash": core_norm_profile_hash(profile),
    }
    risk_flags = (
        "bounded_representation_family",
        "bounded_operator_family",
        "bounded_corenorm_profile",
        "backend_behavior_not_claimed",
        "fresh_upstream_full_suite_not_in_scope",
        "full_art_fdt_not_yet_claimed",
    )
    return ProgramPECCertificate(
        revision=PROGRAM_PEC_REVISION,
        level=level,
        status=f"{level.value}_{'CLOSED' if closed else 'OPEN'}",
        claim_summary=claim_summary,
        claim_boundary=(
            "relative domain closure under the declared frame/budget; "
            "not RGPEC, not terminal completeness, and not a proof of global program equivalence"
        ),
        terminal_claim=False,
        frame=frame,
        budget=budget,
        profile_hash=core_norm_profile_hash(profile),
        reconstruction_certificate_hash=xrec_hash,
        state_ref=reconstruction.common_core_norm_hash,
        manifest_ref=_hash(b"NOVA-PROGRAM-PEC-MANIFEST-v0.9\0", frame_budget_manifest),
        route_coverage=route_coverage,
        novelty_stats=novelty_stats,
        verification_summary=verification_summary,
        audits=audits,
        confidence=confidence,
        debt_ledger=debts,
        frontier_map=frontier,
        reopen_conditions=reopens,
        reopening_challenges=challenges,
        false_closure_risk_flags=risk_flags,
    )


def replay_program_pec_certificate(
    certificate: ProgramPECCertificate,
    sources: Mapping[str, Any],
    *,
    profile: CoreNormProfile = DEFAULT_CORE_NORM_PROFILE,
) -> tuple[bool, tuple[str, ...]]:
    errors: list[str] = []
    if certificate.level is not PECLevel.DPEC:
        errors.append("v0.9 replay only supports DPEC")
    if certificate.terminal_claim:
        errors.append("v0.9 certificate must not make a terminal claim")
    if certificate.profile_hash != core_norm_profile_hash(profile):
        errors.append("profile hash mismatch")

    try:
        rebuilt = build_program_pec_certificate(
            sources,
            frame=certificate.frame,
            budget=certificate.budget,
            debt_ledger=certificate.debt_ledger,
            frontier_map=certificate.frontier_map,
            reopen_conditions=certificate.reopen_conditions,
            level=certificate.level,
            claim_summary=certificate.claim_summary,
            profile=profile,
            verification_summary=certificate.verification_summary,
            run_reopening_challenges=bool(certificate.reopening_challenges),
        )
    except ValidationError as exc:
        message = getattr(getattr(exc, "detail", None), "message", str(exc))
        return False, tuple(errors + [f"replay validation failed:{message}"])

    fields = (
        "status",
        "profile_hash",
        "reconstruction_certificate_hash",
        "state_ref",
        "manifest_ref",
        "route_coverage",
        "novelty_stats",
        "verification_summary",
        "audits",
        "confidence",
        "reopening_challenges",
        "false_closure_risk_flags",
    )
    for name in fields:
        if getattr(certificate, name) != getattr(rebuilt, name):
            errors.append(f"certificate field mismatch:{name}")
    if certificate.certificate_hash != rebuilt.certificate_hash:
        errors.append("certificate hash mismatch")
    return not errors, tuple(errors)


def default_v09_frame() -> ProgramPECFrame:
    return ProgramPECFrame(
        domain="cross_representation_reconstruction",
        assumptions=(
            "bounded_pure_dag_corenorm",
            "single_graph_examples",
            "typed_tensor_annotations",
            "no_backend_behavior_claim",
        ),
        representation_family=("text", "graph", "ai"),
        operator_family=("Add", "Identity", "Input"),
        route_grammar=("surface_adapter->NOVA_Project->CoreNorm_v0.7",),
        validation_regime=(
            "v0.8 independent adapters",
            "v0.7 bounded CoreNorm",
            "isolated deterministic replay",
        ),
        observer_conditions=(
            "CoreNorm record/hash equality",
            "adapter rejection on invalid structural references",
        ),
        backend_family=(),
    )


def default_v09_budget(*, verification_case_budget: int = 80) -> ProgramResourceBudget:
    return ProgramResourceBudget(
        budget_id="v0.9-isolated-reference-envelope",
        max_representation_routes=3,
        max_modules_per_project=1,
        max_graphs_per_module=1,
        max_nodes_per_graph=16,
        verification_case_budget=verification_case_budget,
        reopening_challenge_budget=4,
        tool_regime=("python-reference", "pytest-isolated"),
    )


__all__ = [
    "PROGRAM_PEC_FORMAT",
    "PROGRAM_PEC_ENVELOPE_FORMAT",
    "PROGRAM_PEC_REVISION",
    "PECLevel",
    "DebtSeverity",
    "DebtStatus",
    "DebtScope",
    "ProgramPECFrame",
    "ProgramResourceBudget",
    "DebtItem",
    "FrontierItem",
    "ReopenCondition",
    "ReopeningChallengeResult",
    "ProgramVerificationEvidence",
    "RouteCoverage",
    "NoveltyStats",
    "ConditionAudit",
    "ClosureConfidenceVector",
    "ProgramPECCertificate",
    "build_program_pec_certificate",
    "encode_program_pec",
    "decode_program_pec",
    "cross_reconstruction_certificate_hash",
    "default_v09_budget",
    "default_v09_debts",
    "default_v09_frame",
    "default_v09_frontier",
    "default_v09_reopen_conditions",
    "program_pec_hash",
    "replay_program_pec_certificate",
    "run_standard_reopening_challenges",
]

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .paradigm import (
    FillMode,
    ParadigmClassification,
    ParadigmTag,
    PlannerProfile,
    StrategyRegion,
    classify_region,
    paradigm_for,
)


@dataclass(frozen=True)
class CostBreakdown:
    online_work: float = 0.0
    random_access: float = 0.0
    parallel_sync: float = 0.0
    precompute: float = 0.0
    storage: float = 0.0
    maintenance: float = 0.0
    space_conversion: float = 0.0
    risk_penalty: float = 0.0

    @property
    def total(self) -> float:
        return float(
            self.online_work
            + self.random_access
            + self.parallel_sync
            + self.precompute
            + self.storage
            + self.maintenance
            + self.space_conversion
            + self.risk_penalty
        )

    def to_record(self) -> dict[str, float]:
        return {
            "online_work": self.online_work,
            "random_access": self.random_access,
            "parallel_sync": self.parallel_sync,
            "precompute": self.precompute,
            "storage": self.storage,
            "maintenance": self.maintenance,
            "space_conversion": self.space_conversion,
            "risk_penalty": self.risk_penalty,
            "total": self.total,
        }


@dataclass(frozen=True)
class ExecutionStrategyCandidate:
    region_id: str
    tag: ParadigmTag
    preconditions: tuple[str, ...]
    evidence: tuple[str, ...]
    cost: CostBreakdown
    fallback_tag: ParadigmTag
    confidence: str

    def to_record(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "tag": self.tag.to_record(),
            "preconditions": list(self.preconditions),
            "evidence": list(self.evidence),
            "cost": self.cost.to_record(),
            "fallback_tag": self.fallback_tag.to_record(),
            "confidence": self.confidence,
        }


def _cost_for(fill: FillMode, profile: PlannerProfile) -> CostBreakdown:
    if fill is FillMode.SEQUENTIAL:
        return CostBreakdown(online_work=100.0)
    if fill is FillMode.JUMP:
        return CostBreakdown(
            online_work=35.0,
            random_access=10.0 * profile.random_access_weight,
            risk_penalty=2.0 * profile.risk_weight,
        )
    if fill is FillMode.PARALLEL:
        return CostBreakdown(
            online_work=100.0 / float(profile.parallelism),
            parallel_sync=8.0 * profile.synchronization_weight,
            risk_penalty=2.0 * profile.risk_weight,
        )
    if fill is FillMode.RECOGNITION:
        return CostBreakdown(
            online_work=0.0,
            precompute=4.0 * profile.precompute_weight,
            storage=4.0 * profile.storage_weight,
            maintenance=4.0 * profile.maintenance_weight,
            risk_penalty=1.0 * profile.risk_weight,
        )
    raise AssertionError(fill)


def _preconditions(classification: ParadigmClassification) -> tuple[str, ...]:
    fill = classification.tag.fill
    if fill is FillMode.SEQUENTIAL:
        return ()
    if fill is FillMode.JUMP:
        return ("selective_access_evidence",)
    if fill is FillMode.PARALLEL:
        return ("independence_evidence", "no_ordering_effect_conflict")
    if fill is FillMode.RECOGNITION:
        return ("stable_recognition_evidence", "precomputed_structure_available")
    return ()


def candidate_strategies(
    region: StrategyRegion,
    profile: PlannerProfile | None = None,
) -> tuple[ExecutionStrategyCandidate, ...]:
    profile = profile or PlannerProfile()
    classifications = classify_region(region, profile)
    fallback = paradigm_for(region.base, FillMode.SEQUENTIAL, region.observation)
    candidates = [
        ExecutionStrategyCandidate(
            region_id=region.region_id,
            tag=item.tag,
            preconditions=_preconditions(item),
            evidence=tuple(f"{ev.category}:{ev.detail}" for ev in item.evidence),
            cost=_cost_for(item.tag.fill, profile),
            fallback_tag=fallback,
            confidence=item.confidence,
        )
        for item in classifications
    ]
    return tuple(candidates)


def rank_candidates(
    region: StrategyRegion,
    profile: PlannerProfile | None = None,
) -> tuple[ExecutionStrategyCandidate, ...]:
    candidates = candidate_strategies(region, profile)
    confidence_rank = {"proven": 0, "supported": 1, "fallback": 2}
    return tuple(
        sorted(
            candidates,
            key=lambda item: (
                item.cost.total,
                confidence_rank.get(item.confidence, 9),
                item.tag.index,
            ),
        )
    )

from dataclasses import field
import hashlib
import json

from .canonical import semantic_hash
from .model import Graph
from .paradigm import BaseSpace, ObservationMode, extract_strategy_regions


@dataclass(frozen=True)
class BondViolation:
    rule: str
    transition_index: int
    message: str
    from_code: str
    to_code: str

    def to_record(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "transition_index": self.transition_index,
            "message": self.message,
            "from_code": self.from_code,
            "to_code": self.to_code,
        }


@dataclass(frozen=True)
class BondObligation:
    kind: str
    transition_index: int
    message: str
    cost: float = 0.0

    def to_record(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "transition_index": self.transition_index,
            "message": self.message,
            "cost": self.cost,
        }


@dataclass(frozen=True)
class BondDecision:
    legal: bool
    violations: tuple[BondViolation, ...] = ()
    obligations: tuple[BondObligation, ...] = ()
    conversion_cost: float = 0.0

    def to_record(self) -> dict[str, Any]:
        return {
            "legal": self.legal,
            "violations": [item.to_record() for item in self.violations],
            "obligations": [item.to_record() for item in self.obligations],
            "conversion_cost": self.conversion_cost,
        }


_FILL_RANK = {
    FillMode.SEQUENTIAL: 3,
    FillMode.JUMP: 2,
    FillMode.PARALLEL: 1,
    FillMode.RECOGNITION: 0,
}


def validate_bonds(
    tags: tuple[ParadigmTag, ...] | list[ParadigmTag],
    *,
    stability_resets: tuple[int, ...] | list[int] = (),
    conversion_weight: float = 1.0,
) -> BondDecision:
    tags = tuple(tags)
    resets = {int(i) for i in stability_resets}
    violations: list[BondViolation] = []
    obligations: list[BondObligation] = []
    conversion_cost = 0.0

    for index, (left, right) in enumerate(zip(tags, tags[1:])):
        reset = index in resets
        if reset:
            obligations.append(
                BondObligation(
                    kind="stability_reset",
                    transition_index=index,
                    message="stability collapse explicitly starts a new paradigm-chain segment",
                    cost=0.0,
                )
            )
        else:
            if left.fill is FillMode.RECOGNITION:
                violations.append(
                    BondViolation(
                        rule="recognition_terminal",
                        transition_index=index,
                        message="R is terminal while the recognition structure remains stable",
                        from_code=left.code,
                        to_code=right.code,
                    )
                )
            if _FILL_RANK[right.fill] > _FILL_RANK[left.fill]:
                violations.append(
                    BondViolation(
                        rule="fill_monotonicity",
                        transition_index=index,
                        message="fill complexity may only stay level or descend C→J→P→R",
                        from_code=left.code,
                        to_code=right.code,
                    )
                )

        if left.base is BaseSpace.CONTINUOUS and right.base is BaseSpace.DISCRETE:
            cost = 1.0 * conversion_weight
            conversion_cost += cost
            obligations.append(
                BondObligation(
                    kind="discretization_loss",
                    transition_index=index,
                    message="continuous-to-discrete conversion is relatively cheap but potentially lossy",
                    cost=cost,
                )
            )
        elif left.base is BaseSpace.DISCRETE and right.base is BaseSpace.CONTINUOUS:
            cost = 10.0 * conversion_weight
            conversion_cost += cost
            obligations.append(
                BondObligation(
                    kind="reconstruction_assumption",
                    transition_index=index,
                    message="discrete-to-continuous reconstruction is expensive and requires interpolation assumptions",
                    cost=cost,
                )
            )

    return BondDecision(
        legal=not violations,
        violations=tuple(violations),
        obligations=tuple(obligations),
        conversion_cost=conversion_cost,
    )


def _profile_record(profile: PlannerProfile) -> dict[str, Any]:
    return {
        "parallelism": profile.parallelism,
        "recognition_enabled": profile.recognition_enabled,
        "stable_cache": profile.stable_cache,
        "random_access_weight": profile.random_access_weight,
        "synchronization_weight": profile.synchronization_weight,
        "precompute_weight": profile.precompute_weight,
        "storage_weight": profile.storage_weight,
        "maintenance_weight": profile.maintenance_weight,
        "conversion_weight": profile.conversion_weight,
        "risk_weight": profile.risk_weight,
    }


@dataclass(frozen=True)
class ExecutionStrategyPlan:
    graph_hash: str
    selected: tuple[ExecutionStrategyCandidate, ...]
    candidate_matrix: tuple[tuple[ExecutionStrategyCandidate, ...], ...]
    bond_decision: BondDecision
    fallback_used: bool
    rejected_bond_decision: BondDecision | None
    profile: PlannerProfile

    @property
    def total_cost(self) -> float:
        return sum(item.cost.total for item in self.selected) + self.bond_decision.conversion_cost

    def to_record(self) -> dict[str, Any]:
        return {
            "graph_hash": self.graph_hash,
            "selected": [item.to_record() for item in self.selected],
            "candidate_matrix": [[item.to_record() for item in row] for row in self.candidate_matrix],
            "bond_decision": self.bond_decision.to_record(),
            "fallback_used": self.fallback_used,
            "rejected_bond_decision": None if self.rejected_bond_decision is None else self.rejected_bond_decision.to_record(),
            "profile": _profile_record(self.profile),
            "total_cost": self.total_cost,
        }


def _fallback_candidate(region: StrategyRegion, profile: PlannerProfile) -> ExecutionStrategyCandidate:
    candidate = next(
        item for item in candidate_strategies(region, profile)
        if item.tag.fill is FillMode.SEQUENTIAL
    )
    return candidate


def plan_graph(
    graph: Graph,
    profile: PlannerProfile | None = None,
    *,
    stability_resets: tuple[int, ...] | list[int] = (),
) -> ExecutionStrategyPlan:
    profile = profile or PlannerProfile()
    regions = extract_strategy_regions(graph)
    matrix = tuple(rank_candidates(region, profile) for region in regions)
    selected = tuple(row[0] for row in matrix)
    initial_bond = validate_bonds(
        tuple(item.tag for item in selected),
        stability_resets=stability_resets,
        conversion_weight=profile.conversion_weight,
    )
    fallback_used = False
    rejected: BondDecision | None = None
    bond = initial_bond
    if not initial_bond.legal:
        rejected = initial_bond
        selected = tuple(_fallback_candidate(region, profile) for region in regions)
        bond = validate_bonds(
            tuple(item.tag for item in selected),
            stability_resets=stability_resets,
            conversion_weight=profile.conversion_weight,
        )
        fallback_used = True
    return ExecutionStrategyPlan(
        graph_hash=semantic_hash(graph),
        selected=selected,
        candidate_matrix=matrix,
        bond_decision=bond,
        fallback_used=fallback_used,
        rejected_bond_decision=rejected,
        profile=profile,
    )


def plan_hash(plan: ExecutionStrategyPlan) -> str:
    payload = json.dumps(plan.to_record(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()

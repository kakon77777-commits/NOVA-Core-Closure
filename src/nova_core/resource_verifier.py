from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .canonical import semantic_hash
from .errors import ResourceVerificationError
from .model import Graph
from .types import TensorType
from .resources import (
    BufferBinding,
    MemoryPlan,
    ResourceObligation,
    ValueLifetime,
    _allocatable_values,
    _peak_reserved_bytes,
    _required_transfers,
    analyze_resources,
    conservative_memory_plan,
    memory_plan_hash,
)


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


class VerificationStatus(str, Enum):
    SAFE = "safe"
    CONDITIONALLY_SAFE = "conditionally_safe"
    UNSAFE = "unsafe"


@dataclass(frozen=True)
class PlanViolation:
    kind: str
    message: str
    context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "context", _freeze_mapping(self.context))

    def to_record(self) -> dict[str, Any]:
        return {"kind": self.kind, "message": self.message, "context": dict(self.context)}


@dataclass(frozen=True)
class MemoryPlanVerification:
    status: VerificationStatus
    plan_hash: str
    graph_semantic_hash: str
    violations: tuple[PlanViolation, ...] = ()
    obligations: tuple[ResourceObligation, ...] = ()
    recomputed_peak_reserved_bytes: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "violations", tuple(self.violations))
        object.__setattr__(self, "obligations", tuple(self.obligations))

    def to_record(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "plan_hash": self.plan_hash,
            "graph_semantic_hash": self.graph_semantic_hash,
            "violations": [v.to_record() for v in self.violations],
            "obligations": [o.to_record() for o in self.obligations],
            "recomputed_peak_reserved_bytes": self.recomputed_peak_reserved_bytes,
        }


@dataclass(frozen=True)
class PlanSelection:
    selected: MemoryPlan
    candidate_verification: MemoryPlanVerification
    selected_verification: MemoryPlanVerification
    fallback_used: bool
    rejected_candidate_hash: str | None = None
    rejected_violations: tuple[PlanViolation, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "rejected_violations", tuple(self.rejected_violations))

    def to_record(self) -> dict[str, Any]:
        return {
            "selected_plan_hash": memory_plan_hash(self.selected),
            "candidate_verification": self.candidate_verification.to_record(),
            "selected_verification": self.selected_verification.to_record(),
            "fallback_used": self.fallback_used,
            "rejected_candidate_hash": self.rejected_candidate_hash,
            "rejected_violations": [v.to_record() for v in self.rejected_violations],
        }


def _lifetime_map(values: tuple[ValueLifetime, ...]) -> dict[str, ValueLifetime]:
    return {value.symbol: value for value in values}


def _obligation_key(obligation: ResourceObligation) -> tuple[Any, ...]:
    return (
        obligation.kind,
        obligation.symbol,
        obligation.message,
        obligation.runtime_guard,
        tuple(sorted((str(k), repr(v)) for k, v in obligation.context.items())),
    )


def _transfer_key(transfer) -> tuple[str, str, str, str]:
    return (transfer.symbol, transfer.source_device, transfer.target_device, transfer.before_node)


def _value_record(value: ValueLifetime) -> dict[str, Any]:
    return value.to_record()


def verify_memory_plan(
    graph: Graph,
    plan: MemoryPlan,
    symbol_types: Mapping[str, TensorType] | None = None,
) -> MemoryPlanVerification:
    analysis = analyze_resources(graph, symbol_types)
    violations: list[PlanViolation] = []

    expected_graph_hash = semantic_hash(graph)
    if plan.graph_semantic_hash != expected_graph_hash:
        violations.append(
            PlanViolation(
                "graph_hash_mismatch",
                "memory plan targets a different graph semantic identity",
                {"expected": expected_graph_hash, "received": plan.graph_semantic_hash},
            )
        )

    if tuple(plan.schedule) != tuple(analysis.schedule):
        violations.append(
            PlanViolation(
                "schedule_mismatch",
                "candidate schedule differs from deterministic graph schedule",
                {"expected": list(analysis.schedule), "received": list(plan.schedule)},
            )
        )

    expected_lifetimes = dict(analysis.values)
    candidate_lifetimes = _lifetime_map(plan.lifetimes)
    for symbol in sorted(set(expected_lifetimes) | set(candidate_lifetimes)):
        expected = expected_lifetimes.get(symbol)
        received = candidate_lifetimes.get(symbol)
        if expected is None or received is None or _value_record(expected) != _value_record(received):
            violations.append(
                PlanViolation(
                    "lifetime_mismatch",
                    "candidate lifetime facts do not match independent analysis",
                    {
                        "symbol": symbol,
                        "expected": expected.to_record() if expected is not None else None,
                        "received": received.to_record() if received is not None else None,
                    },
                )
            )

    expected_allocatable = {value.symbol: value for value in _allocatable_values(analysis)}
    bound: dict[str, list[BufferBinding]] = {}
    for buffer in plan.buffers:
        if not buffer.symbols:
            violations.append(PlanViolation("empty_buffer", "physical buffer has no bound symbols", {"buffer_id": buffer.buffer_id}))
            continue
        for symbol in buffer.symbols:
            bound.setdefault(symbol, []).append(buffer)

        expected_in_buffer = [expected_allocatable.get(symbol) for symbol in buffer.symbols]
        known_values = [value for value in expected_in_buffer if value is not None]
        if len(known_values) != len(buffer.symbols):
            extras = [symbol for symbol, value in zip(buffer.symbols, expected_in_buffer) if value is None]
            violations.append(
                PlanViolation(
                    "unexpected_allocation",
                    "buffer binds a symbol that the independent analysis does not allocate",
                    {"buffer_id": buffer.buffer_id, "symbols": extras},
                )
            )

        if known_values:
            first_step = min(value.first_step for value in known_values)
            last_step = max(value.last_step for value in known_values)
            if buffer.first_step != first_step or buffer.last_step != last_step:
                violations.append(
                    PlanViolation(
                        "buffer_lifetime_mismatch",
                        "buffer lifetime bounds are inconsistent with bound values",
                        {
                            "buffer_id": buffer.buffer_id,
                            "expected_first": first_step,
                            "expected_last": last_step,
                            "received_first": buffer.first_step,
                            "received_last": buffer.last_step,
                        },
                    )
                )

            for value in known_values:
                tensor_type = value.tensor_type
                if tensor_type is not None:
                    if buffer.dtype != tensor_type.dtype or buffer.layout != value.layout or buffer.device != value.device:
                        violations.append(
                            PlanViolation(
                                "buffer_type_mismatch",
                                "physical buffer dtype/layout/device does not match tensor contract",
                                {
                                    "buffer_id": buffer.buffer_id,
                                    "symbol": value.symbol,
                                    "expected": {
                                        "dtype": tensor_type.dtype,
                                        "layout": value.layout,
                                        "device": value.device,
                                    },
                                    "received": {
                                        "dtype": buffer.dtype,
                                        "layout": buffer.layout,
                                        "device": buffer.device,
                                    },
                                },
                            )
                        )
                if value.size_bytes is not None:
                    if buffer.capacity_bytes is None or buffer.capacity_bytes < value.size_bytes:
                        violations.append(
                            PlanViolation(
                                "insufficient_capacity",
                                "physical buffer capacity is smaller than the required tensor bytes",
                                {
                                    "buffer_id": buffer.buffer_id,
                                    "symbol": value.symbol,
                                    "required": value.size_bytes,
                                    "capacity": buffer.capacity_bytes,
                                },
                            )
                        )
                elif len(buffer.symbols) > 1:
                    violations.append(
                        PlanViolation(
                            "unknown_size_alias",
                            "unknown-size tensors may not share a physical buffer",
                            {"buffer_id": buffer.buffer_id, "symbol": value.symbol},
                        )
                    )

            ordered = sorted(known_values, key=lambda value: (value.first_step, value.symbol))
            for previous, current in zip(ordered, ordered[1:]):
                if not previous.reusable or previous.last_step >= current.first_step:
                    violations.append(
                        PlanViolation(
                            "overlapping_lifetime",
                            "physical buffer is reused before the prior value is provably dead",
                            {
                                "buffer_id": buffer.buffer_id,
                                "previous": previous.symbol,
                                "previous_last": previous.last_step,
                                "current": current.symbol,
                                "current_first": current.first_step,
                                "previous_reusable": previous.reusable,
                            },
                        )
                    )

    for symbol in sorted(expected_allocatable):
        buffers = bound.get(symbol, [])
        if not buffers:
            violations.append(
                PlanViolation("missing_allocation", "allocatable symbol has no physical buffer", {"symbol": symbol})
            )
        elif len(buffers) > 1:
            violations.append(
                PlanViolation(
                    "duplicate_allocation",
                    "symbol is bound to multiple physical buffers",
                    {"symbol": symbol, "buffers": [buffer.buffer_id for buffer in buffers]},
                )
            )

    required_transfers, transfer_obligations = _required_transfers(graph, analysis)
    expected_transfer_keys = {_transfer_key(t) for t in required_transfers}
    received_transfer_keys = {_transfer_key(t) for t in plan.transfers}
    for key in sorted(expected_transfer_keys - received_transfer_keys):
        violations.append(
            PlanViolation(
                "missing_transfer",
                "required device transfer is missing",
                {"symbol": key[0], "source_device": key[1], "target_device": key[2], "before_node": key[3]},
            )
        )
    for key in sorted(received_transfer_keys - expected_transfer_keys):
        violations.append(
            PlanViolation(
                "redundant_transfer",
                "candidate contains a device transfer not required by independent analysis",
                {"symbol": key[0], "source_device": key[1], "target_device": key[2], "before_node": key[3]},
            )
        )

    obligations = tuple(analysis.obligations) + tuple(transfer_obligations)
    expected_obligation_keys = {_obligation_key(o) for o in obligations}
    received_obligation_keys = {_obligation_key(o) for o in plan.obligations}
    if expected_obligation_keys != received_obligation_keys:
        violations.append(
            PlanViolation(
                "obligation_mismatch",
                "candidate obligations differ from independently recomputed obligations",
                {
                    "missing_count": len(expected_obligation_keys - received_obligation_keys),
                    "extra_count": len(received_obligation_keys - expected_obligation_keys),
                },
            )
        )

    recomputed_peak = _peak_reserved_bytes(plan.buffers)
    if plan.peak_reserved_bytes != recomputed_peak:
        violations.append(
            PlanViolation(
                "peak_mismatch",
                "candidate peak reserved bytes do not match physical buffer capacities",
                {"expected": recomputed_peak, "received": plan.peak_reserved_bytes},
            )
        )

    if violations:
        status = VerificationStatus.UNSAFE
    elif obligations:
        status = VerificationStatus.CONDITIONALLY_SAFE
    else:
        status = VerificationStatus.SAFE

    return MemoryPlanVerification(
        status=status,
        plan_hash=memory_plan_hash(plan),
        graph_semantic_hash=expected_graph_hash,
        violations=tuple(violations),
        obligations=obligations,
        recomputed_peak_reserved_bytes=recomputed_peak,
    )


def select_memory_plan(
    graph: Graph,
    candidate: MemoryPlan,
    symbol_types: Mapping[str, TensorType] | None = None,
) -> PlanSelection:
    candidate_verification = verify_memory_plan(graph, candidate, symbol_types)
    if candidate_verification.status is not VerificationStatus.UNSAFE:
        return PlanSelection(
            selected=candidate,
            candidate_verification=candidate_verification,
            selected_verification=candidate_verification,
            fallback_used=False,
        )

    fallback = conservative_memory_plan(graph, symbol_types)
    fallback_verification = verify_memory_plan(graph, fallback, symbol_types)
    if fallback_verification.status is VerificationStatus.UNSAFE:
        raise ResourceVerificationError(
            "independently generated conservative memory plan failed verification",
            context={"violations": [v.to_record() for v in fallback_verification.violations]},
        )
    return PlanSelection(
        selected=fallback,
        candidate_verification=candidate_verification,
        selected_verification=fallback_verification,
        fallback_used=True,
        rejected_candidate_hash=memory_plan_hash(candidate),
        rejected_violations=candidate_verification.violations,
    )

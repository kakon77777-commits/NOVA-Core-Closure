from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable

from .errors import OperatorDescriptorError


def _sorted_unique_strings(values: Iterable[str], *, field: str, allow_empty: bool = True) -> tuple[str, ...]:
    normalized = tuple(sorted({str(v) for v in values}))
    if not allow_empty and not normalized:
        raise OperatorDescriptorError(f"{field} must not be empty")
    if any(not value for value in normalized):
        raise OperatorDescriptorError(f"{field} contains an empty string")
    return normalized


@dataclass(frozen=True)
class SemanticSlot:
    states: tuple[str, ...]
    transition: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        states = _sorted_unique_strings(self.states, field="states", allow_empty=False)
        raw = tuple((str(src), str(dst)) for src, dst in self.transition)
        keys = [src for src, _ in raw]
        if len(set(keys)) != len(keys):
            raise OperatorDescriptorError("semantic transition has duplicate source states")
        mapping = dict(raw)
        if set(mapping) != set(states):
            raise OperatorDescriptorError("semantic slot requires a total transition over its state space")
        outside = sorted({dst for dst in mapping.values() if dst not in set(states)})
        if outside:
            raise OperatorDescriptorError(
                "semantic transition targets outside state space",
                context={"targets": outside},
            )
        object.__setattr__(self, "states", states)
        object.__setattr__(self, "transition", tuple(sorted(mapping.items())))

    @property
    def transition_map(self) -> dict[str, str]:
        return dict(self.transition)

    def to_record(self) -> dict:
        return {
            "states": list(self.states),
            "transition": {src: dst for src, dst in self.transition},
        }


@dataclass(frozen=True)
class CompositionSlot:
    contexts: tuple[str, ...]
    input_arity: int = 1
    output_arity: int = 1

    def __post_init__(self) -> None:
        contexts = _sorted_unique_strings(self.contexts, field="contexts", allow_empty=False)
        if int(self.input_arity) < 1:
            raise OperatorDescriptorError("input_arity must be at least 1")
        if int(self.output_arity) < 1:
            raise OperatorDescriptorError("output_arity must be at least 1")
        object.__setattr__(self, "contexts", contexts)
        object.__setattr__(self, "input_arity", int(self.input_arity))
        object.__setattr__(self, "output_arity", int(self.output_arity))

    def to_record(self) -> dict:
        return {
            "contexts": list(self.contexts),
            "input_arity": self.input_arity,
            "output_arity": self.output_arity,
        }


@dataclass(frozen=True)
class ProjectionSlot:
    canonical_kind: str
    connected: bool = True
    orientation: str = "forward"
    scale: float = 1.0

    def __post_init__(self) -> None:
        canonical_kind = str(self.canonical_kind)
        if not canonical_kind:
            raise OperatorDescriptorError("canonical_kind must not be empty")
        orientation = str(self.orientation)
        if orientation not in {"forward", "reverse", "neutral"}:
            raise OperatorDescriptorError("projection orientation must be forward, reverse, or neutral")
        scale = float(self.scale)
        if not math.isfinite(scale) or scale <= 0.0:
            raise OperatorDescriptorError("projection scale must be finite and positive")
        object.__setattr__(self, "canonical_kind", canonical_kind)
        object.__setattr__(self, "connected", bool(self.connected))
        object.__setattr__(self, "orientation", orientation)
        object.__setattr__(self, "scale", scale)

    def to_record(self) -> dict:
        return {
            "canonical_kind": self.canonical_kind,
            "connected": self.connected,
            "orientation": self.orientation,
            "scale": self.scale,
        }


@dataclass(frozen=True)
class OperatorDescriptor:
    operator_id: str
    nova_kind: str
    semantic_slot: SemanticSlot
    composition_slot: CompositionSlot
    projection_slot: ProjectionSlot
    state_schema: tuple[str, ...] = ()
    effect_schema: tuple[str, ...] = ()
    version: str = "0.11.0"

    def __post_init__(self) -> None:
        operator_id = str(self.operator_id)
        nova_kind = str(self.nova_kind)
        version = str(self.version)
        if not operator_id:
            raise OperatorDescriptorError("operator_id must not be empty")
        if not nova_kind:
            raise OperatorDescriptorError("nova_kind must not be empty")
        if not version:
            raise OperatorDescriptorError("version must not be empty")
        object.__setattr__(self, "operator_id", operator_id)
        object.__setattr__(self, "nova_kind", nova_kind)
        object.__setattr__(self, "state_schema", _sorted_unique_strings(self.state_schema, field="state_schema"))
        object.__setattr__(self, "effect_schema", _sorted_unique_strings(self.effect_schema, field="effect_schema"))
        object.__setattr__(self, "version", version)

    def to_record(self) -> dict:
        return descriptor_record(self)


@dataclass(frozen=True)
class OperatorRegistry:
    descriptors: tuple[OperatorDescriptor, ...]

    def __post_init__(self) -> None:
        descriptors = tuple(sorted(self.descriptors, key=lambda item: item.operator_id))
        ids = [item.operator_id for item in descriptors]
        if len(set(ids)) != len(ids):
            raise OperatorDescriptorError("duplicate operator_id in registry")
        object.__setattr__(self, "descriptors", descriptors)

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(item.operator_id for item in self.descriptors)

    def get(self, operator_id: str) -> OperatorDescriptor:
        for descriptor in self.descriptors:
            if descriptor.operator_id == operator_id:
                return descriptor
        raise OperatorDescriptorError("operator not found", context={"operator_id": operator_id})


def descriptor_record(descriptor: OperatorDescriptor) -> dict:
    return {
        "operator_id": descriptor.operator_id,
        "nova_kind": descriptor.nova_kind,
        "semantic_slot": descriptor.semantic_slot.to_record(),
        "composition_slot": descriptor.composition_slot.to_record(),
        "projection_slot": descriptor.projection_slot.to_record(),
        "state_schema": list(descriptor.state_schema),
        "effect_schema": list(descriptor.effect_schema),
        "version": descriptor.version,
    }


def descriptor_hash(descriptor: OperatorDescriptor) -> str:
    payload = json.dumps(
        descriptor_record(descriptor),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _stable_unary(operator_id: str, nova_kind: str) -> OperatorDescriptor:
    return OperatorDescriptor(
        operator_id=operator_id,
        nova_kind=nova_kind,
        semantic_slot=SemanticSlot(states=("stable",), transition=(("stable", "stable"),)),
        composition_slot=CompositionSlot(
            contexts=("differentiable", "pure", "tensor"),
            input_arity=1,
            output_arity=1,
        ),
        projection_slot=ProjectionSlot(
            canonical_kind=nova_kind,
            connected=True,
            orientation="forward",
            scale=1.0,
        ),
        state_schema=("stateless",),
        effect_schema=(),
        version="0.11.0",
    )


def basic_operator_registry() -> OperatorRegistry:
    return OperatorRegistry(
        (
            _stable_unary("identity", "Identity"),
            _stable_unary("negate", "Negate"),
            _stable_unary("relu", "Relu"),
            _stable_unary("sigmoid", "Sigmoid"),
            _stable_unary("softmax", "Softmax"),
            _stable_unary("tanh", "Tanh"),
        )
    )

from enum import Enum

from .errors import CompCollapseError, EffectCompositionError, GIncoherenceError, SemDivergenceError


class CompositionStatus(Enum):
    SAFE = "safe"
    UNSAFE = "unsafe"
    CONDITIONALLY_SAFE = "conditionally_safe"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CompositionContext:
    k_s: int = 256
    max_depth: int = 32
    max_scale: float = 1024.0
    allowed_effects: tuple[str, ...] | None = None
    forbidden_effect_pairs: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        k_s = int(self.k_s)
        max_depth = int(self.max_depth)
        max_scale = float(self.max_scale)
        if k_s < 1:
            raise OperatorDescriptorError("k_s must be at least 1")
        if max_depth < 1:
            raise OperatorDescriptorError("max_depth must be at least 1")
        if not math.isfinite(max_scale) or max_scale <= 0:
            raise OperatorDescriptorError("max_scale must be finite and positive")
        allowed = None
        if self.allowed_effects is not None:
            allowed = _sorted_unique_strings(self.allowed_effects, field="allowed_effects")
        pairs: set[tuple[str, str]] = set()
        for raw in self.forbidden_effect_pairs:
            if len(raw) != 2:
                raise OperatorDescriptorError("forbidden effect pair must contain exactly two effects")
            a, b = str(raw[0]), str(raw[1])
            if not a or not b:
                raise OperatorDescriptorError("forbidden effect pair contains an empty effect")
            pairs.add(tuple(sorted((a, b))))
        object.__setattr__(self, "k_s", k_s)
        object.__setattr__(self, "max_depth", max_depth)
        object.__setattr__(self, "max_scale", max_scale)
        object.__setattr__(self, "allowed_effects", allowed)
        object.__setattr__(self, "forbidden_effect_pairs", tuple(sorted(pairs)))


@dataclass(frozen=True)
class RVPCheck:
    stage: str
    passed: bool
    message: str
    evidence: dict

    def to_record(self) -> dict:
        return {
            "stage": self.stage,
            "passed": self.passed,
            "message": self.message,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class CompositionReport:
    status: CompositionStatus
    left_id: str
    right_id: str
    checks: tuple[RVPCheck, ...]
    error: Exception | None = None
    comp_contexts: tuple[str, ...] = ()
    semantic_slot: SemanticSlot | None = None
    semantic_iterations: int = 0
    projection_slot: ProjectionSlot | None = None
    effect_schema: tuple[str, ...] = ()

    @property
    def safe(self) -> bool:
        return self.status is CompositionStatus.SAFE

    def to_record(self) -> dict:
        error_payload = None
        if self.error is not None:
            to_dict = getattr(self.error, "to_dict", None)
            error_payload = to_dict() if callable(to_dict) else {"category": type(self.error).__name__, "message": str(self.error)}
        return {
            "status": self.status.value,
            "left_id": self.left_id,
            "right_id": self.right_id,
            "checks": [check.to_record() for check in self.checks],
            "error": error_payload,
            "comp_contexts": list(self.comp_contexts),
            "semantic_slot": None if self.semantic_slot is None else self.semantic_slot.to_record(),
            "semantic_iterations": self.semantic_iterations,
            "projection_slot": None if self.projection_slot is None else self.projection_slot.to_record(),
            "effect_schema": list(self.effect_schema),
        }


def _unsafe_report(
    left: OperatorDescriptor,
    right: OperatorDescriptor,
    checks: list[RVPCheck],
    error: Exception,
    *,
    comp_contexts: tuple[str, ...] = (),
    semantic_slot: SemanticSlot | None = None,
    semantic_iterations: int = 0,
    projection_slot: ProjectionSlot | None = None,
    effect_schema: tuple[str, ...] = (),
) -> CompositionReport:
    return CompositionReport(
        status=CompositionStatus.UNSAFE,
        left_id=left.operator_id,
        right_id=right.operator_id,
        checks=tuple(checks),
        error=error,
        comp_contexts=comp_contexts,
        semantic_slot=semantic_slot,
        semantic_iterations=semantic_iterations,
        projection_slot=projection_slot,
        effect_schema=effect_schema,
    )


def _compose_transition_maps(a: dict[str, str], b: dict[str, str]) -> dict[str, str]:
    # Source convention: Sem_A o Sem_B, so A is applied after B.
    return {state: a[b[state]] for state in b}


def _semantic_fixed_point(left: SemanticSlot, right: SemanticSlot, k_s: int) -> tuple[SemanticSlot | None, int, str | None]:
    if left.states != right.states:
        return None, 0, "state_space_mismatch"
    f = _compose_transition_maps(left.transition_map, right.transition_map)
    power = dict(f)
    for iteration in range(1, k_s + 1):
        next_power = _compose_transition_maps(f, power)
        if next_power == power:
            return SemanticSlot(states=left.states, transition=tuple(power.items())), iteration, None
        power = next_power
    return None, k_s, "fixed_point_not_reached"


def _projection_composition(
    left: OperatorDescriptor,
    right: OperatorDescriptor,
    context: CompositionContext,
) -> tuple[ProjectionSlot | None, str | None, dict]:
    lp = left.projection_slot
    rp = right.projection_slot
    if lp.canonical_kind != left.nova_kind:
        return None, "left_canonical_kind_mismatch", {"expected": left.nova_kind, "observed": lp.canonical_kind}
    if rp.canonical_kind != right.nova_kind:
        return None, "right_canonical_kind_mismatch", {"expected": right.nova_kind, "observed": rp.canonical_kind}
    if not lp.connected or not rp.connected:
        return None, "connectivity", {"left_connected": lp.connected, "right_connected": rp.connected}
    non_neutral = {value for value in (lp.orientation, rp.orientation) if value != "neutral"}
    if len(non_neutral) > 1:
        return None, "orientation_inconsistency", {"left": lp.orientation, "right": rp.orientation}
    scale = lp.scale * rp.scale
    if not math.isfinite(scale) or scale <= 0 or scale > context.max_scale:
        return None, "scale_unbounded", {"scale": scale, "max_scale": context.max_scale}
    orientation = next(iter(non_neutral)) if non_neutral else "neutral"
    return (
        ProjectionSlot(
            canonical_kind=f"{lp.canonical_kind}∘{rp.canonical_kind}",
            connected=True,
            orientation=orientation,
            scale=scale,
        ),
        None,
        {"scale": scale, "orientation": orientation},
    )


def _effect_failure(
    effects: tuple[str, ...],
    left_effects: tuple[str, ...],
    right_effects: tuple[str, ...],
    context: CompositionContext,
) -> tuple[EffectCompositionError | None, dict]:
    if context.allowed_effects is not None:
        disallowed = sorted(set(effects) - set(context.allowed_effects))
        if disallowed:
            return EffectCompositionError(
                "operator composition uses effects outside the allowed context",
                context={"disallowed_effects": disallowed, "allowed_effects": list(context.allowed_effects)},
            ), {"disallowed_effects": disallowed}
    forbidden = set(context.forbidden_effect_pairs)
    for left_effect in left_effects:
        for right_effect in right_effects:
            pair = tuple(sorted((left_effect, right_effect)))
            if pair in forbidden:
                return EffectCompositionError(
                    "operator effects conflict under the composition context",
                    context={"forbidden_pair": list(pair)},
                ), {"forbidden_pair": list(pair)}
    return None, {"effects": list(effects)}


def validate_composition(
    left: OperatorDescriptor,
    right: OperatorDescriptor,
    *,
    context: CompositionContext | None = None,
) -> CompositionReport:
    context = context or CompositionContext()
    checks: list[RVPCheck] = []

    # C — Comp safety.
    comp_contexts = tuple(sorted(set(left.composition_slot.contexts) & set(right.composition_slot.contexts)))
    # Mathematical composition left o right executes right first, so right outputs feed left inputs.
    arity_ok = right.composition_slot.output_arity == left.composition_slot.input_arity
    c_passed = bool(comp_contexts) and arity_ok
    checks.append(
        RVPCheck(
            stage="C",
            passed=c_passed,
            message="Comp intersection and arity are compatible" if c_passed else "Comp intersection collapsed or arity is incompatible",
            evidence={
                "intersection": list(comp_contexts),
                "left_input_arity": left.composition_slot.input_arity,
                "right_output_arity": right.composition_slot.output_arity,
            },
        )
    )
    if not c_passed:
        error = CompCollapseError(
            "Comp slot collapsed during composition",
            context={
                "left": left.operator_id,
                "right": right.operator_id,
                "intersection": list(comp_contexts),
                "left_input_arity": left.composition_slot.input_arity,
                "right_output_arity": right.composition_slot.output_arity,
            },
        )
        return _unsafe_report(left, right, checks, error, comp_contexts=comp_contexts)

    # G — minimum geometry/projection consistency invariants.
    projection_slot, g_reason, g_evidence = _projection_composition(left, right, context)
    g_passed = projection_slot is not None
    checks.append(
        RVPCheck(
            stage="G",
            passed=g_passed,
            message="minimum projection/GCI invariants hold" if g_passed else "projection/GCI invariant failed",
            evidence={"reason": g_reason, **g_evidence},
        )
    )
    if not g_passed:
        error = GIncoherenceError(
            "projection/G slot is incoherent under composition",
            context={"reason": g_reason, **g_evidence},
        )
        return _unsafe_report(
            left,
            right,
            checks,
            error,
            comp_contexts=comp_contexts,
        )

    # S — bounded whole-map fixed-point validation.
    semantic_slot, iterations, s_reason = _semantic_fixed_point(left.semantic_slot, right.semantic_slot, context.k_s)
    s_passed = semantic_slot is not None
    checks.append(
        RVPCheck(
            stage="S",
            passed=s_passed,
            message="semantic composition reached a bounded fixed point" if s_passed else "semantic composition did not reach a bounded fixed point",
            evidence={"iterations": iterations, "k_s": context.k_s, "reason": s_reason},
        )
    )
    if not s_passed:
        error = SemDivergenceError(
            "semantic composition failed bounded RVP fixed-point validation",
            context={"reason": s_reason, "iterations": iterations, "k_s": context.k_s},
        )
        return _unsafe_report(
            left,
            right,
            checks,
            error,
            comp_contexts=comp_contexts,
            semantic_iterations=iterations,
            projection_slot=projection_slot,
        )

    # NOVA integration effect policy. This is deliberately after the source C→G→S core RVP.
    effects = tuple(sorted(set(left.effect_schema) | set(right.effect_schema)))
    effect_error, effect_evidence = _effect_failure(effects, left.effect_schema, right.effect_schema, context)
    checks.append(
        RVPCheck(
            stage="EFFECT",
            passed=effect_error is None,
            message="effect policy permits composition" if effect_error is None else "effect policy rejects composition",
            evidence=effect_evidence,
        )
    )
    if effect_error is not None:
        return _unsafe_report(
            left,
            right,
            checks,
            effect_error,
            comp_contexts=comp_contexts,
            semantic_slot=semantic_slot,
            semantic_iterations=iterations,
            projection_slot=projection_slot,
            effect_schema=effects,
        )

    return CompositionReport(
        status=CompositionStatus.SAFE,
        left_id=left.operator_id,
        right_id=right.operator_id,
        checks=tuple(checks),
        error=None,
        comp_contexts=comp_contexts,
        semantic_slot=semantic_slot,
        semantic_iterations=iterations,
        projection_slot=projection_slot,
        effect_schema=effects,
    )

from .errors import BrokenOperatorPropagationError, CompositionDepthError, CompositionError


@dataclass(frozen=True)
class OperatorClosure:
    members: tuple[OperatorDescriptor, ...]
    semantic_slot: SemanticSlot
    composition_slot: CompositionSlot
    projection_slot: ProjectionSlot
    state_schema: tuple[str, ...]
    effect_schema: tuple[str, ...]
    reports: tuple[CompositionReport, ...]
    version: str = "0.11.0"

    def __post_init__(self) -> None:
        if len(self.members) < 2:
            raise OperatorDescriptorError("OperatorClosure requires at least two members")
        object.__setattr__(self, "members", tuple(self.members))
        object.__setattr__(self, "state_schema", _sorted_unique_strings(self.state_schema, field="state_schema"))
        object.__setattr__(self, "effect_schema", _sorted_unique_strings(self.effect_schema, field="effect_schema"))
        object.__setattr__(self, "reports", tuple(self.reports))

    @property
    def member_ids(self) -> tuple[str, ...]:
        return tuple(member.operator_id for member in self.members)

    @property
    def depth(self) -> int:
        return len(self.members)

    def as_descriptor(self) -> OperatorDescriptor:
        # A closure is not a primitive NOVA kind. For further SOS composition, its
        # projection identity is used as the descriptor kind while lowering still
        # expands the original primitive members.
        return OperatorDescriptor(
            operator_id="closure:" + "∘".join(self.member_ids),
            nova_kind=self.projection_slot.canonical_kind,
            semantic_slot=self.semantic_slot,
            composition_slot=self.composition_slot,
            projection_slot=self.projection_slot,
            state_schema=self.state_schema,
            effect_schema=self.effect_schema,
            version=self.version,
        )

    def to_record(self) -> dict:
        return {
            "member_ids": list(self.member_ids),
            "member_hashes": [descriptor_hash(member) for member in self.members],
            "depth": self.depth,
            "semantic_slot": self.semantic_slot.to_record(),
            "composition_slot": self.composition_slot.to_record(),
            "projection_slot": self.projection_slot.to_record(),
            "state_schema": list(self.state_schema),
            "effect_schema": list(self.effect_schema),
            "reports": [report.to_record() for report in self.reports],
            "version": self.version,
        }


@dataclass(frozen=True)
class BrokenOperator:
    member_ids: tuple[str, ...]
    report: CompositionReport

    @property
    def error_category(self) -> str:
        error = self.report.error
        if error is None:
            return "CompositionError"
        return getattr(error, "category", type(error).__name__)

    def to_record(self) -> dict:
        return {
            "broken": True,
            "member_ids": list(self.member_ids),
            "error_category": self.error_category,
            "report": self.report.to_record(),
        }


def closure_hash(closure: OperatorClosure) -> str:
    payload = json.dumps(
        closure.to_record(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _operand_members(value: OperatorDescriptor | OperatorClosure) -> tuple[OperatorDescriptor, ...]:
    if isinstance(value, OperatorDescriptor):
        return (value,)
    if isinstance(value, OperatorClosure):
        return value.members
    raise TypeError(type(value).__name__)


def _operand_descriptor(value: OperatorDescriptor | OperatorClosure) -> OperatorDescriptor:
    if isinstance(value, OperatorDescriptor):
        return value
    if isinstance(value, OperatorClosure):
        return value.as_descriptor()
    raise TypeError(type(value).__name__)


def _operand_reports(value: OperatorDescriptor | OperatorClosure) -> tuple[CompositionReport, ...]:
    return value.reports if isinstance(value, OperatorClosure) else ()


def _depth_report(member_ids: tuple[str, ...], context: CompositionContext) -> CompositionReport:
    error = CompositionDepthError(
        "operator composition exceeds the configured depth limit",
        context={"depth": len(member_ids), "max_depth": context.max_depth, "member_ids": list(member_ids)},
    )
    return CompositionReport(
        status=CompositionStatus.UNSAFE,
        left_id=member_ids[0] if member_ids else "",
        right_id=member_ids[-1] if member_ids else "",
        checks=(
            RVPCheck(
                stage="DEPTH",
                passed=False,
                message="composition depth limit exceeded",
                evidence={"depth": len(member_ids), "max_depth": context.max_depth},
            ),
        ),
        error=error,
    )


def compose(
    left: OperatorDescriptor | OperatorClosure | BrokenOperator,
    right: OperatorDescriptor | OperatorClosure | BrokenOperator,
    *,
    context: CompositionContext | None = None,
    strict: bool = True,
) -> OperatorClosure | BrokenOperator:
    context = context or CompositionContext()

    broken = left if isinstance(left, BrokenOperator) else right if isinstance(right, BrokenOperator) else None
    if broken is not None:
        if not strict:
            return broken
        raise BrokenOperatorPropagationError(
            "BrokenOperator cannot participate in further composition",
            context={
                "original_error_category": broken.error_category,
                "member_ids": list(broken.member_ids),
            },
        )

    assert isinstance(left, (OperatorDescriptor, OperatorClosure))
    assert isinstance(right, (OperatorDescriptor, OperatorClosure))
    members = _operand_members(left) + _operand_members(right)
    member_ids = tuple(member.operator_id for member in members)
    if len(members) > context.max_depth:
        report = _depth_report(member_ids, context)
        if strict:
            assert isinstance(report.error, CompositionDepthError)
            raise report.error
        return BrokenOperator(member_ids=member_ids, report=report)

    left_descriptor = _operand_descriptor(left)
    right_descriptor = _operand_descriptor(right)
    report = validate_composition(left_descriptor, right_descriptor, context=context)
    if not report.safe:
        if strict:
            assert isinstance(report.error, CompositionError)
            raise report.error
        return BrokenOperator(member_ids=member_ids, report=report)

    assert report.semantic_slot is not None
    assert report.projection_slot is not None
    state_schema = tuple(sorted(set(left_descriptor.state_schema) | set(right_descriptor.state_schema)))
    # Mathematical left o right: input contract comes from right; output contract from left.
    comp_slot = CompositionSlot(
        contexts=report.comp_contexts,
        input_arity=right_descriptor.composition_slot.input_arity,
        output_arity=left_descriptor.composition_slot.output_arity,
    )
    reports = _operand_reports(left) + _operand_reports(right) + (report,)
    return OperatorClosure(
        members=members,
        semantic_slot=report.semantic_slot,
        composition_slot=comp_slot,
        projection_slot=report.projection_slot,
        state_schema=state_schema,
        effect_schema=report.effect_schema,
        reports=reports,
        version="0.11.0",
    )


def compose_chain(
    operators: Iterable[OperatorDescriptor | OperatorClosure | BrokenOperator],
    *,
    context: CompositionContext | None = None,
    strict: bool = True,
) -> OperatorClosure | BrokenOperator:
    values = tuple(operators)
    if len(values) < 2:
        raise OperatorDescriptorError("compose_chain requires at least two operators")
    current = compose(values[0], values[1], context=context, strict=strict)
    for value in values[2:]:
        current = compose(current, value, context=context, strict=strict)
    return current

from dataclasses import replace

from nova_core import (
    CompositionContext,
    CompositionSlot,
    CompositionStatus,
    CompCollapseError,
    EffectCompositionError,
    GIncoherenceError,
    OperatorDescriptor,
    ProjectionSlot,
    SemanticSlot,
    SemDivergenceError,
    basic_operator_registry,
    validate_composition,
)


def descriptor(
    operator_id,
    *,
    contexts=("pure", "tensor"),
    states=("s",),
    transition=(("s", "s"),),
    connected=True,
    orientation="forward",
    scale=1.0,
    canonical_kind=None,
    effects=(),
):
    nova_kind = operator_id.title()
    return OperatorDescriptor(
        operator_id=operator_id,
        nova_kind=nova_kind,
        semantic_slot=SemanticSlot(states=states, transition=transition),
        composition_slot=CompositionSlot(contexts=contexts, input_arity=1, output_arity=1),
        projection_slot=ProjectionSlot(
            canonical_kind=canonical_kind or nova_kind,
            connected=connected,
            orientation=orientation,
            scale=scale,
        ),
        effect_schema=effects,
        version="0.11.0",
    )


def test_safe_rvp_runs_core_checks_in_exact_c_g_s_order_then_effect_integration():
    registry = basic_operator_registry()
    report = validate_composition(registry.get("relu"), registry.get("tanh"))
    assert report.status is CompositionStatus.SAFE
    assert tuple(check.stage for check in report.checks) == ("C", "G", "S", "EFFECT")
    assert all(check.passed for check in report.checks)
    assert report.comp_contexts == ("differentiable", "pure", "tensor")
    assert report.semantic_iterations == 1
    assert report.semantic_slot is not None
    assert report.error is None


def test_comp_collapse_fails_fast_before_g_or_s():
    left = descriptor("left", contexts=("left-only",))
    right = descriptor("right", contexts=("right-only",))
    report = validate_composition(left, right)
    assert report.status is CompositionStatus.UNSAFE
    assert tuple(check.stage for check in report.checks) == ("C",)
    assert isinstance(report.error, CompCollapseError)


def test_gci_rejects_connectivity_orientation_scale_and_canonical_kind_inconsistency():
    base = descriptor("relu")
    cases = (
        descriptor("bad-connected", connected=False),
        descriptor("bad-orientation", orientation="reverse"),
        descriptor("bad-scale", scale=100.0),
        descriptor("bad-kind", canonical_kind="NotBadKind"),
    )
    contexts = (
        CompositionContext(),
        CompositionContext(),
        CompositionContext(max_scale=10.0),
        CompositionContext(),
    )
    for right, context in zip(cases, contexts):
        report = validate_composition(base, right, context=context)
        assert report.status is CompositionStatus.UNSAFE
        assert tuple(check.stage for check in report.checks) == ("C", "G")
        assert isinstance(report.error, GIncoherenceError)
        assert report.error.detail.context["reason"]


def test_sem_rvp_compares_whole_map_powers_and_detects_toggle_cycle():
    stable = descriptor(
        "stable",
        states=("a", "b"),
        transition=(("a", "a"), ("b", "b")),
    )
    toggle = descriptor(
        "toggle",
        states=("a", "b"),
        transition=(("a", "b"), ("b", "a")),
    )
    report = validate_composition(stable, toggle, context=CompositionContext(k_s=8))
    assert report.status is CompositionStatus.UNSAFE
    assert tuple(check.stage for check in report.checks) == ("C", "G", "S")
    assert isinstance(report.error, SemDivergenceError)
    assert report.semantic_iterations == 8


def test_sem_rvp_rejects_incompatible_state_spaces_as_sem_failure():
    left = descriptor("left", states=("a",), transition=(("a", "a"),))
    right = descriptor("right", states=("b",), transition=(("b", "b"),))
    report = validate_composition(left, right)
    assert isinstance(report.error, SemDivergenceError)
    assert report.error.detail.context["reason"] == "state_space_mismatch"


def test_effect_conflict_is_a_nova_integration_check_after_core_rvp():
    left = descriptor("left", effects=("State",))
    right = descriptor("right", effects=("Network",))
    context = CompositionContext(forbidden_effect_pairs=(("Network", "State"),))
    report = validate_composition(left, right, context=context)
    assert report.status is CompositionStatus.UNSAFE
    assert tuple(check.stage for check in report.checks) == ("C", "G", "S", "EFFECT")
    assert isinstance(report.error, EffectCompositionError)


def test_allowed_effect_policy_rejects_effects_outside_context():
    left = descriptor("left", effects=("IO",))
    right = descriptor("right", effects=())
    report = validate_composition(left, right, context=CompositionContext(allowed_effects=("State",)))
    assert isinstance(report.error, EffectCompositionError)
    assert "IO" in report.error.detail.context["disallowed_effects"]


def test_neutral_projection_orientation_composes_with_forward():
    left = descriptor("left", orientation="neutral")
    right = descriptor("right", orientation="forward")
    report = validate_composition(left, right)
    assert report.status is CompositionStatus.SAFE
    assert report.projection_slot is not None
    assert report.projection_slot.orientation == "forward"


def test_comp_arity_uses_mathematical_composition_direction_right_output_to_left_input():
    base = descriptor("base")
    binary_left = OperatorDescriptor(
        operator_id="binary-left",
        nova_kind="Add",
        semantic_slot=base.semantic_slot,
        composition_slot=CompositionSlot(contexts=("pure", "tensor"), input_arity=2, output_arity=1),
        projection_slot=ProjectionSlot(canonical_kind="Add", connected=True, orientation="forward", scale=1.0),
        version="0.11.0",
    )
    unary_right = descriptor("unary-right")
    report = validate_composition(binary_left, unary_right)
    assert report.status is CompositionStatus.UNSAFE
    assert isinstance(report.error, CompCollapseError)
    assert report.error.detail.context["left_input_arity"] == 2
    assert report.error.detail.context["right_output_arity"] == 1

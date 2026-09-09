from dataclasses import replace

import pytest

from nova_core import (
    BrokenOperator,
    BrokenOperatorPropagationError,
    CompositionContext,
    CompositionDepthError,
    CompCollapseError,
    CompositionSlot,
    OperatorClosure,
    OperatorDescriptor,
    ProjectionSlot,
    SemanticSlot,
    basic_operator_registry,
    compose,
    compose_chain,
    closure_hash,
)


def incompatible_pair():
    base = basic_operator_registry().get("relu")
    left = replace(base, operator_id="left", composition_slot=CompositionSlot(contexts=("a",), input_arity=1, output_arity=1))
    right = replace(base, operator_id="right", composition_slot=CompositionSlot(contexts=("b",), input_arity=1, output_arity=1))
    return left, right


def test_strict_compose_raises_first_typed_rvp_failure():
    left, right = incompatible_pair()
    with pytest.raises(CompCollapseError):
        compose(left, right, strict=True)


def test_diagnostic_compose_returns_explicit_broken_operator():
    left, right = incompatible_pair()
    broken = compose(left, right, strict=False)
    assert isinstance(broken, BrokenOperator)
    assert broken.report.error is not None
    assert broken.error_category == "CompCollapseError"
    assert broken.member_ids == ("left", "right")


def test_broken_operator_isolated_from_downstream_composition():
    left, right = incompatible_pair()
    broken = compose(left, right, strict=False)
    relu = basic_operator_registry().get("relu")

    again = compose(broken, relu, strict=False)
    assert again is broken

    with pytest.raises(BrokenOperatorPropagationError) as exc:
        compose(broken, relu, strict=True)
    assert exc.value.detail.context["original_error_category"] == "CompCollapseError"


def test_safe_compose_returns_deterministic_closure():
    registry = basic_operator_registry()
    relu = registry.get("relu")
    tanh = registry.get("tanh")
    a = compose(relu, tanh)
    b = compose(relu, tanh)
    assert isinstance(a, OperatorClosure)
    assert a.member_ids == ("relu", "tanh")
    assert a.depth == 2
    assert a.effect_schema == ()
    assert closure_hash(a) == closure_hash(b)
    assert closure_hash(a).startswith("sha256:")


def test_compose_chain_builds_mathematical_composition_order_and_depth():
    registry = basic_operator_registry()
    closure = compose_chain((registry.get("relu"), registry.get("tanh"), registry.get("negate")))
    assert isinstance(closure, OperatorClosure)
    assert closure.member_ids == ("relu", "tanh", "negate")
    assert closure.depth == 3
    assert len(closure.reports) == 2


def test_depth_limit_rejects_before_deep_damage_can_propagate():
    registry = basic_operator_registry()
    with pytest.raises(CompositionDepthError):
        compose_chain(
            (registry.get("relu"), registry.get("tanh"), registry.get("negate")),
            context=CompositionContext(max_depth=2),
        )


def test_depth_limit_diagnostic_mode_returns_broken_operator():
    registry = basic_operator_registry()
    result = compose_chain(
        (registry.get("relu"), registry.get("tanh"), registry.get("negate")),
        context=CompositionContext(max_depth=2),
        strict=False,
    )
    assert isinstance(result, BrokenOperator)
    assert result.error_category == "CompositionDepthError"

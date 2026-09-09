import pytest

from nova_core import (
    CompositionSlot,
    OperatorDescriptor,
    OperatorDescriptorError,
    OperatorRegistry,
    ProjectionSlot,
    SemanticSlot,
    basic_operator_registry,
    descriptor_hash,
    descriptor_record,
)


def make_descriptor(*, operator_id="relu", nova_kind="Relu", transition=(("s", "s"),)):
    return OperatorDescriptor(
        operator_id=operator_id,
        nova_kind=nova_kind,
        semantic_slot=SemanticSlot(states=("s",), transition=transition),
        composition_slot=CompositionSlot(contexts=("pure", "tensor"), input_arity=1, output_arity=1),
        projection_slot=ProjectionSlot(canonical_kind=nova_kind, connected=True, orientation="forward", scale=1.0),
        state_schema=("stateless",),
        effect_schema=(),
        version="0.11.0",
    )


def test_semantic_slot_normalizes_order_and_requires_total_closed_transition():
    a = SemanticSlot(states=("b", "a"), transition=(("b", "b"), ("a", "a")))
    b = SemanticSlot(states=("a", "b"), transition=(("a", "a"), ("b", "b")))
    assert a == b
    assert a.states == ("a", "b")
    assert a.transition == (("a", "a"), ("b", "b"))

    with pytest.raises(OperatorDescriptorError, match="total transition"):
        SemanticSlot(states=("a", "b"), transition=(("a", "a"),))
    with pytest.raises(OperatorDescriptorError, match="outside state space"):
        SemanticSlot(states=("a",), transition=(("a", "b"),))


def test_composition_slot_normalizes_contexts_and_validates_arity():
    slot = CompositionSlot(contexts=("tensor", "pure", "tensor"), input_arity=1, output_arity=1)
    assert slot.contexts == ("pure", "tensor")
    with pytest.raises(OperatorDescriptorError, match="input_arity"):
        CompositionSlot(contexts=("pure",), input_arity=0, output_arity=1)
    with pytest.raises(OperatorDescriptorError, match="contexts"):
        CompositionSlot(contexts=(), input_arity=1, output_arity=1)


def test_projection_slot_rejects_invalid_orientation_or_scale():
    with pytest.raises(OperatorDescriptorError, match="orientation"):
        ProjectionSlot(canonical_kind="Relu", connected=True, orientation="sideways", scale=1.0)
    with pytest.raises(OperatorDescriptorError, match="scale"):
        ProjectionSlot(canonical_kind="Relu", connected=True, orientation="forward", scale=0.0)


def test_descriptor_record_and_hash_are_deterministic():
    a = make_descriptor()
    b = OperatorDescriptor(
        operator_id="relu",
        nova_kind="Relu",
        semantic_slot=SemanticSlot(states=("s",), transition=(("s", "s"),)),
        composition_slot=CompositionSlot(contexts=("tensor", "pure"), input_arity=1, output_arity=1),
        projection_slot=ProjectionSlot(canonical_kind="Relu", connected=True, orientation="forward", scale=1),
        state_schema=("stateless", "stateless"),
        effect_schema=(),
        version="0.11.0",
    )
    assert descriptor_record(a) == descriptor_record(b)
    assert descriptor_hash(a) == descriptor_hash(b)
    assert descriptor_hash(a).startswith("sha256:")


def test_operator_registry_rejects_duplicates_and_supports_lookup():
    d = make_descriptor()
    registry = OperatorRegistry((d,))
    assert registry.get("relu") == d
    assert registry.ids == ("relu",)
    with pytest.raises(OperatorDescriptorError, match="duplicate operator_id"):
        OperatorRegistry((d, d))
    with pytest.raises(OperatorDescriptorError, match="operator not found"):
        registry.get("missing")


def test_basic_operator_library_is_small_pure_unary_nova_mapped_set():
    registry = basic_operator_registry()
    assert registry.ids == ("identity", "negate", "relu", "sigmoid", "softmax", "tanh")
    expected = {
        "identity": "Identity",
        "negate": "Negate",
        "relu": "Relu",
        "sigmoid": "Sigmoid",
        "softmax": "Softmax",
        "tanh": "Tanh",
    }
    for operator_id, nova_kind in expected.items():
        descriptor = registry.get(operator_id)
        assert descriptor.nova_kind == nova_kind
        assert descriptor.composition_slot.input_arity == 1
        assert descriptor.composition_slot.output_arity == 1
        assert descriptor.effect_schema == ()
        assert descriptor.projection_slot.canonical_kind == nova_kind
        assert descriptor.version == "0.11.0"

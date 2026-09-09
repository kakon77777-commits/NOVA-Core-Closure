import numpy as np
import pytest

from nova_core import (
    CompositionSlot,
    Interpreter,
    NumPyBackend,
    OperatorDescriptor,
    OperatorDescriptorError,
    ProjectionSlot,
    SemanticSlot,
    basic_operator_registry,
    compose,
    lower_closure_to_project,
    validate_project,
)


def test_safe_unary_closure_lowers_to_ordinary_nova_graph_and_executes_equivalently():
    registry = basic_operator_registry()
    # Mathematical composition relu o tanh executes tanh first, then relu.
    closure = compose(registry.get("relu"), registry.get("tanh"))
    project = lower_closure_to_project(closure, input_symbol="x", output_symbol="y")
    validate_project(project)
    graph = project.modules[0].graphs[0]
    assert [node.kind for node in graph.nodes] == ["Tanh", "Relu"]
    assert graph.inputs == ("x",)
    assert graph.outputs == ("y",)
    x = np.array([-2.0, -0.25, 0.5, 2.0], dtype=np.float32)
    expected = np.maximum(np.tanh(x), 0)
    i = Interpreter().run_graph(graph, {"x": x}).outputs["y"]
    n = NumPyBackend().run_graph(graph, {"x": x}).outputs["y"]
    np.testing.assert_allclose(i, expected)
    np.testing.assert_allclose(n, expected)
    np.testing.assert_allclose(i, n)


def test_lowered_nodes_are_normal_existing_nova_kinds_not_sos_runtime_magic():
    registry = basic_operator_registry()
    closure = compose(registry.get("sigmoid"), registry.get("negate"))
    project = lower_closure_to_project(closure)
    kinds = [node.kind for node in project.modules[0].graphs[0].nodes]
    assert kinds == ["Negate", "Sigmoid"]
    assert "SOSClosure" not in kinds


def test_lowering_rejects_unsupported_multi_input_descriptor_instead_of_guessing_topology():
    base = basic_operator_registry().get("relu")
    binary = OperatorDescriptor(
        operator_id="binary",
        nova_kind="Add",
        semantic_slot=base.semantic_slot,
        composition_slot=CompositionSlot(contexts=("pure", "tensor"), input_arity=2, output_arity=1),
        projection_slot=ProjectionSlot(canonical_kind="Add", connected=True, orientation="forward", scale=1.0),
        version="0.11.0",
    )
    closure = compose(binary, base, strict=False)
    # Arity mismatch is already rejected by Cl-safe C and must not reach lowering.
    from nova_core import BrokenOperator
    assert isinstance(closure, BrokenOperator)
    with pytest.raises(OperatorDescriptorError, match="safe OperatorClosure"):
        lower_closure_to_project(closure)

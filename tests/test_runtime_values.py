import numpy as np
import pytest

from nova_core import Node, Shape, TensorType
from nova_core.errors import MissingInputError, RuntimeShapeError
from nova_core.runtime import ExecutionEnvironment, ExecutionTrace, validate_runtime_value


def test_environment_resolves_inputs_and_parameters_without_mutation():
    inputs = {"X": np.ones((2, 3), dtype=np.float32)}
    params = {"W": np.ones((3, 4), dtype=np.float32)}
    env = ExecutionEnvironment(inputs=inputs, parameters=params)

    assert env.resolve("X") is inputs["X"]
    assert env.resolve("W") is params["W"]
    with pytest.raises(TypeError):
        env.inputs["Y"] = 1


def test_environment_missing_value_is_typed_error():
    env = ExecutionEnvironment(inputs={})
    with pytest.raises(MissingInputError) as exc:
        env.resolve("missing")
    assert exc.value.to_dict()["category"] == "MissingInputError"
    assert exc.value.to_dict()["context"]["name"] == "missing"


def test_runtime_tensor_validation_binds_symbolic_dimensions():
    typ = TensorType("f32", Shape.of("B", 3))
    env = ExecutionEnvironment(inputs={})
    value = np.zeros((5, 3), dtype=np.float32)

    validated = validate_runtime_value(value, typ, solver=env.shape_solver, source="X")

    assert validated is value
    assert env.shape_solver.bindings["B"] == 5


def test_runtime_tensor_validation_rejects_concrete_mismatch():
    typ = TensorType("f32", Shape.of(2, 3))
    value = np.zeros((2, 4), dtype=np.float32)
    with pytest.raises(RuntimeShapeError) as exc:
        validate_runtime_value(value, typ, source="X")
    detail = exc.value.to_dict()
    assert detail["category"] == "RuntimeShapeError"
    assert detail["context"]["expected"] == [2, 3]
    assert detail["context"]["observed"] == [2, 4]


def test_runtime_tensor_validation_rejects_rank_mismatch():
    typ = TensorType("f32", Shape.of("B", 3))
    with pytest.raises(RuntimeShapeError):
        validate_runtime_value(np.zeros((3,), dtype=np.float32), typ, source="X")


def test_execution_trace_records_are_immutable_snapshots():
    trace = ExecutionTrace()
    trace = trace.append(
        node_id="n1",
        kind="Add",
        inputs=("a", "b"),
        outputs=("c",),
        result=np.ones((2, 2)),
    )
    assert len(trace.records) == 1
    assert trace.records[0].result_shape == (2, 2)
    with pytest.raises(AttributeError):
        trace.records = ()

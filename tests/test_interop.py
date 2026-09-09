import numpy as np
import pytest

from nova_core.canonical import semantic_hash
from nova_core.errors import DTypeInteropError, InteropError, RuntimeShapeError
from nova_core.model import Graph, Node
from nova_core.shape import Shape
from nova_core.types import TensorType
from nova_core.interop import from_numpy, to_numpy, to_python


def test_to_numpy_accepts_python_sequence_and_matches_expected_tensor_type():
    expected = TensorType(dtype="f32", shape=Shape.of(2, 2))
    value = to_numpy([[1, 2], [3, 4]], expected=expected)
    assert isinstance(value, np.ndarray)
    assert value.dtype == np.float32
    assert value.shape == (2, 2)


def test_to_numpy_safe_policy_rejects_narrowing_float_cast():
    expected = TensorType(dtype="f32", shape=Shape.of(2))
    with pytest.raises(DTypeInteropError):
        to_numpy(np.array([1.0, 2.0], dtype=np.float64), expected=expected, dtype_policy="safe")


def test_to_numpy_exact_policy_requires_exact_dtype():
    expected = TensorType(dtype="f64", shape=Shape.of(2))
    with pytest.raises(DTypeInteropError):
        to_numpy(np.array([1, 2], dtype=np.int64), expected=expected, dtype_policy="exact")


def test_to_numpy_rejects_shape_mismatch():
    expected = TensorType(dtype="f32", shape=Shape.of(2, 2))
    with pytest.raises(RuntimeShapeError):
        to_numpy(np.zeros((4,), dtype=np.float32), expected=expected)


def test_to_numpy_rejects_non_cpu_device_contract():
    expected = TensorType(dtype="f32", shape=Shape.of(2), device="gpu:0")
    with pytest.raises(InteropError):
        to_numpy([1, 2], expected=expected)


def test_from_numpy_copy_policy_is_explicit():
    source = np.arange(4, dtype=np.float32)
    view = from_numpy(source, copy=False)
    clone = from_numpy(source, copy=True)
    assert np.shares_memory(source, view)
    assert not np.shares_memory(source, clone)
    np.testing.assert_array_equal(source, clone)


def test_to_python_returns_plain_python_values():
    source = np.array([[1, 2], [3, 4]], dtype=np.int64)
    assert to_python(source) == [[1, 2], [3, 4]]
    scalar = to_python(np.array(3.5, dtype=np.float32))
    assert isinstance(scalar, float)
    assert scalar == pytest.approx(3.5)


def test_interop_does_not_mutate_canonical_graph_identity():
    graph = Graph(
        id="g",
        inputs=("X",),
        outputs=("Y",),
        nodes=(
            Node(id="x", kind="Input", outputs=("X",), value_type=TensorType(dtype="f32", shape=Shape.of(2))),
            Node(id="y", kind="Identity", inputs=("X",), outputs=("Y",), value_type=TensorType(dtype="f32", shape=Shape.of(2))),
        ),
    )
    before = semantic_hash(graph)
    _ = to_numpy([1.0, 2.0], expected=TensorType(dtype="f32", shape=Shape.of(2)))
    assert semantic_hash(graph) == before

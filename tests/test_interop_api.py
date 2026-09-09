import numpy as np

from nova_core.api import interop_from_dlpack, interop_to_dlpack, interop_to_numpy
from nova_core.shape import Shape
from nova_core.types import TensorType


def test_api_numpy_and_dlpack_wrappers_use_same_contract():
    expected = TensorType(dtype="f32", shape=Shape.of(2, 2))
    array = interop_to_numpy([[1, 2], [3, 4]], expected=expected)
    capsule = interop_to_dlpack(array)
    restored = interop_from_dlpack(capsule, expected=expected)
    np.testing.assert_array_equal(restored, array)
    assert np.shares_memory(restored, array)

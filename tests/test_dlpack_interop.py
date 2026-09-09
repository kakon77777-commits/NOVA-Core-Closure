import numpy as np
import pytest

from nova_core.errors import DLPackInteropError, RuntimeShapeError
from nova_core.interop import dlpack_device, from_dlpack, to_dlpack
from nova_core.shape import Shape
from nova_core.types import TensorType


def test_numpy_provider_dlpack_roundtrip_is_zero_copy_and_read_only_view():
    source = np.arange(6, dtype=np.float32).reshape(2, 3)
    imported = from_dlpack(source, expected=TensorType(dtype="f32", shape=Shape.of(2, 3)))
    np.testing.assert_array_equal(imported, source)
    assert np.shares_memory(imported, source)
    assert imported.flags.owndata is False


def test_raw_capsule_can_be_bridged_once():
    source = np.arange(4, dtype=np.float32)
    capsule = to_dlpack(source)
    imported = from_dlpack(capsule)
    np.testing.assert_array_equal(imported, source)
    assert np.shares_memory(imported, source)
    with pytest.raises(DLPackInteropError):
        from_dlpack(capsule)


def test_dlpack_device_reports_numpy_cpu_device():
    source = np.arange(2, dtype=np.float32)
    assert dlpack_device(source) == (1, 0)


def test_from_dlpack_validates_expected_shape():
    source = np.arange(6, dtype=np.float32).reshape(2, 3)
    with pytest.raises(RuntimeShapeError):
        from_dlpack(source, expected=TensorType(dtype="f32", shape=Shape.of(3, 2)))


def test_from_dlpack_rejects_non_cpu_provider_before_import():
    class FakeCudaProvider:
        def __dlpack_device__(self):
            return (2, 0)

        def __dlpack__(self, stream=None):
            raise AssertionError("must not consume unsupported device provider")

    with pytest.raises(DLPackInteropError):
        from_dlpack(FakeCudaProvider())


def test_dlpack_rejects_object_without_protocol():
    with pytest.raises(DLPackInteropError):
        to_dlpack([1, 2, 3])
    with pytest.raises(DLPackInteropError):
        from_dlpack(object())

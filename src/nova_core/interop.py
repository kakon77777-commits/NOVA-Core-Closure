from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from .errors import DLPackInteropError, DTypeInteropError, InteropError
from .runtime import validate_runtime_value
from .types import TensorType

_DTYPE_ALIASES: dict[str, np.dtype[Any]] = {
    "bool": np.dtype(np.bool_),
    "i8": np.dtype(np.int8),
    "i16": np.dtype(np.int16),
    "i32": np.dtype(np.int32),
    "i64": np.dtype(np.int64),
    "u8": np.dtype(np.uint8),
    "u16": np.dtype(np.uint16),
    "u32": np.dtype(np.uint32),
    "u64": np.dtype(np.uint64),
    "f16": np.dtype(np.float16),
    "f32": np.dtype(np.float32),
    "f64": np.dtype(np.float64),
    "c64": np.dtype(np.complex64),
    "c128": np.dtype(np.complex128),
    "float16": np.dtype(np.float16),
    "float32": np.dtype(np.float32),
    "float64": np.dtype(np.float64),
    "int8": np.dtype(np.int8),
    "int16": np.dtype(np.int16),
    "int32": np.dtype(np.int32),
    "int64": np.dtype(np.int64),
    "uint8": np.dtype(np.uint8),
    "uint16": np.dtype(np.uint16),
    "uint32": np.dtype(np.uint32),
    "uint64": np.dtype(np.uint64),
    "complex64": np.dtype(np.complex64),
    "complex128": np.dtype(np.complex128),
}


def numpy_dtype(dtype: str) -> np.dtype[Any]:
    normalized = str(dtype).strip().lower()
    try:
        return _DTYPE_ALIASES[normalized]
    except KeyError as exc:
        raise DTypeInteropError(
            "unsupported NOVA dtype for NumPy interop",
            context={"dtype": dtype},
        ) from exc


def _validate_cpu_contract(expected: TensorType | None) -> None:
    if expected is None:
        return
    if expected.device not in {"cpu", "cpu:0"}:
        raise InteropError(
            "NumPy reference interop only realizes CPU tensor contracts",
            context={"device": expected.device},
        )
    if expected.layout not in {"dense", "row_major", "row-major", "c"}:
        raise InteropError(
            "NumPy reference interop does not realize this tensor layout",
            context={"layout": expected.layout},
        )


def to_numpy(
    value: Any,
    expected: TensorType | None = None,
    *,
    dtype_policy: str = "safe",
    copy: bool = False,
) -> np.ndarray:
    if dtype_policy not in {"safe", "exact"}:
        raise InteropError(
            "unknown dtype interop policy",
            context={"dtype_policy": dtype_policy},
        )
    _validate_cpu_contract(expected)
    target = numpy_dtype(expected.dtype) if expected is not None else None

    if isinstance(value, np.ndarray):
        array = value
        if target is not None:
            if dtype_policy == "exact" and array.dtype != target:
                raise DTypeInteropError(
                    "NumPy dtype does not exactly match NOVA tensor dtype",
                    context={"observed": str(array.dtype), "expected": str(target)},
                )
            if dtype_policy == "safe" and array.dtype != target:
                if not np.can_cast(array.dtype, target, casting="safe"):
                    raise DTypeInteropError(
                        "NumPy dtype cannot be safely cast to NOVA tensor dtype",
                        context={"observed": str(array.dtype), "expected": str(target)},
                    )
                array = array.astype(target, copy=False)
        if copy:
            array = np.array(array, copy=True)
    else:
        # Python scalars/sequences do not carry an external ndarray dtype contract.
        array = np.asarray(value, dtype=target)
        if copy:
            array = np.array(array, copy=True)

    validate_runtime_value(array, expected, source="interop")
    return array


def from_numpy(array: np.ndarray, *, copy: bool = False) -> np.ndarray:
    if not isinstance(array, np.ndarray):
        raise InteropError(
            "from_numpy requires a NumPy ndarray",
            context={"type": type(array).__name__},
        )
    return np.array(array, copy=True) if copy else np.asarray(array)


def to_python(value: Any, *, copy: bool = True) -> Any:
    if not copy and isinstance(value, (str, bytes, bool, int, float, complex, list, tuple, dict)):
        return value
    array = np.array(value, copy=True) if copy else np.asarray(value)
    if array.shape == ():
        return array.item()
    return array.tolist()

class _RawCapsuleProvider:
    def __init__(self, capsule: Any) -> None:
        self._capsule = capsule

    def __dlpack__(self, stream: Any = None) -> Any:
        return self._capsule

    def __dlpack_device__(self) -> tuple[int, int]:
        # Round 06 raw-capsule bridge is only exposed through the CPU NumPy
        # reference runtime. Non-CPU raw capsules are rejected by NumPy.
        return (1, 0)


def _is_raw_dlpack_capsule(value: Any) -> bool:
    return type(value).__name__ == "PyCapsule"


def dlpack_device(value: Any) -> tuple[int, int]:
    method = getattr(value, "__dlpack_device__", None)
    if method is None:
        raise DLPackInteropError(
            "object does not expose DLPack device metadata",
            context={"type": type(value).__name__},
        )
    try:
        raw = method()
    except Exception as exc:
        raise DLPackInteropError(
            "failed to query DLPack device metadata",
            context={"type": type(value).__name__},
        ) from exc
    if not isinstance(raw, tuple) or len(raw) != 2:
        raise DLPackInteropError(
            "invalid DLPack device metadata",
            context={"device": repr(raw)},
        )
    return (int(raw[0]), int(raw[1]))


def to_dlpack(value: Any) -> Any:
    method = getattr(value, "__dlpack__", None)
    if method is None:
        raise DLPackInteropError(
            "object does not implement the DLPack export protocol",
            context={"type": type(value).__name__},
        )
    try:
        return method()
    except Exception as exc:
        raise DLPackInteropError(
            "DLPack export failed",
            context={"type": type(value).__name__},
        ) from exc


def from_dlpack(value: Any, expected: TensorType | None = None) -> np.ndarray:
    provider: Any
    if _is_raw_dlpack_capsule(value):
        provider = _RawCapsuleProvider(value)
    else:
        if not hasattr(value, "__dlpack__"):
            raise DLPackInteropError(
                "object does not implement the DLPack import protocol",
                context={"type": type(value).__name__},
            )
        if hasattr(value, "__dlpack_device__"):
            device = dlpack_device(value)
            if device[0] != 1:
                raise DLPackInteropError(
                    "NumPy reference DLPack import only supports CPU providers",
                    context={"device_type": device[0], "device_id": device[1]},
                )
        provider = value
    try:
        array = np.from_dlpack(provider)
    except Exception as exc:
        raise DLPackInteropError(
            "DLPack import failed or capsule was already consumed",
            context={"type": type(value).__name__},
        ) from exc
    validate_runtime_value(array, expected, source="dlpack")
    if expected is not None:
        target = numpy_dtype(expected.dtype)
        if array.dtype != target:
            raise DTypeInteropError(
                "DLPack dtype does not exactly match NOVA tensor dtype",
                context={"observed": str(array.dtype), "expected": str(target)},
            )
    return array

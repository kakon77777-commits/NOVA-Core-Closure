from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np

from .errors import RuntimeShapeError


def _normalize_axes(axis: Any, ndim: int) -> tuple[int, ...]:
    if axis is None:
        return tuple(range(ndim))
    if isinstance(axis, Iterable) and not isinstance(axis, (str, bytes)):
        raw = tuple(int(v) for v in axis)
    else:
        raw = (int(axis),)
    normalized: list[int] = []
    for value in raw:
        actual = value + ndim if value < 0 else value
        if actual < 0 or actual >= ndim:
            raise RuntimeShapeError(
                "AD reduction axis is outside runtime rank",
                context={"axis": value, "rank": ndim},
            )
        if actual not in normalized:
            normalized.append(actual)
    return tuple(sorted(normalized))


def reduce_to_shape(gradient: Any, reference: Any) -> Any:
    grad = np.asarray(gradient)
    ref = np.asarray(reference)
    target = ref.shape

    while grad.ndim > len(target):
        grad = np.sum(grad, axis=0)
    if grad.ndim < len(target):
        raise RuntimeShapeError(
            "cotangent rank is smaller than the referenced primal rank",
            context={"gradient_shape": list(grad.shape), "reference_shape": list(target)},
        )

    for axis, (grad_dim, ref_dim) in enumerate(zip(grad.shape, target)):
        if ref_dim == grad_dim:
            continue
        if ref_dim == 1:
            grad = np.sum(grad, axis=axis, keepdims=True)
            continue
        raise RuntimeShapeError(
            "cotangent cannot be reduced to referenced primal shape",
            context={"gradient_shape": list(grad.shape), "reference_shape": list(target)},
        )

    if grad.shape != target:
        grad = np.reshape(grad, target)
    return grad


def broadcast_like(gradient: Any, reference: Any, *, axis: Any = None, keepdims: bool = False) -> Any:
    grad = np.asarray(gradient)
    ref = np.asarray(reference)
    axes = _normalize_axes(axis, ref.ndim)
    if not keepdims:
        for current_axis in axes:
            grad = np.expand_dims(grad, axis=current_axis)
    try:
        return np.broadcast_to(grad, ref.shape)
    except ValueError as exc:
        raise RuntimeShapeError(
            "cotangent cannot be broadcast to referenced primal shape",
            context={
                "gradient_shape": list(np.asarray(gradient).shape),
                "reference_shape": list(ref.shape),
                "axis": list(axes),
                "keepdims": bool(keepdims),
            },
        ) from exc


def reshape_like(gradient: Any, reference: Any) -> Any:
    grad = np.asarray(gradient)
    ref = np.asarray(reference)
    try:
        return np.reshape(grad, ref.shape)
    except ValueError as exc:
        raise RuntimeShapeError(
            "cotangent cannot be reshaped to referenced primal shape",
            context={"gradient_shape": list(grad.shape), "reference_shape": list(ref.shape)},
        ) from exc


def transpose_last2(value: Any) -> Any:
    array = np.asarray(value)
    if array.ndim < 2:
        raise RuntimeShapeError(
            "ADTransposeLast2 requires rank >= 2",
            context={"shape": list(array.shape)},
        )
    return np.swapaxes(array, -1, -2)


def mean_grad(gradient: Any, reference: Any, *, axis: Any = None, keepdims: bool = False) -> Any:
    ref = np.asarray(reference)
    axes = _normalize_axes(axis, ref.ndim)
    count = 1
    for current_axis in axes:
        count *= ref.shape[current_axis]
    if count == 0:
        raise RuntimeShapeError("mean gradient is undefined for an empty reduction")
    return broadcast_like(gradient, reference, axis=axes, keepdims=keepdims) / count


def relu_grad(gradient: Any, primal: Any) -> Any:
    return np.asarray(gradient) * (np.asarray(primal) > 0)


def zero_like(reference: Any) -> Any:
    return np.zeros_like(np.asarray(reference))

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from .errors import ValidationError
from .shape import Shape


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


@dataclass(frozen=True)
class TensorType:
    dtype: str
    shape: Shape = Shape(())
    layout: str = "dense"
    device: str = "cpu"
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.dtype):
            raise ValidationError("tensor dtype must not be empty")
        if not isinstance(self.shape, Shape):
            object.__setattr__(self, "shape", Shape(tuple(self.shape)))
        if not str(self.layout):
            raise ValidationError("tensor layout must not be empty")
        if not str(self.device):
            raise ValidationError("tensor device must not be empty")
        object.__setattr__(self, "extensions", _freeze(dict(self.extensions or {})))

    @classmethod
    def scalar(cls, dtype: str, *, layout: str = "dense", device: str = "cpu") -> "TensorType":
        return cls(dtype=dtype, shape=Shape(()), layout=layout, device=device)

    @property
    def rank(self) -> int:
        return self.shape.rank

    def to_record(self) -> dict[str, object]:
        record: dict[str, object] = {
            "kind": "tensor_type",
            "dtype": self.dtype,
            "shape": self.shape.to_record(),
            "layout": self.layout,
            "device": self.device,
        }
        for key, value in sorted(self.extensions.items()):
            if key not in record:
                record[key] = _thaw(value)
        return record

    @classmethod
    def from_record(cls, value: Mapping[str, object]) -> "TensorType":
        if value.get("kind") != "tensor_type":
            raise ValidationError("invalid tensor type record")
        known = {"kind", "dtype", "shape", "layout", "device", "extensions"}
        ext = dict(value.get("extensions", {}) or {}) if isinstance(value.get("extensions", {}), Mapping) else {}
        ext.update({str(k): v for k, v in value.items() if k not in known})
        raw_shape = value.get("shape", {"kind": "shape", "dims": []})
        if not isinstance(raw_shape, Mapping):
            raise ValidationError("tensor shape must be an object")
        return cls(
            dtype=str(value.get("dtype", "")),
            shape=Shape.from_record(raw_shape),
            layout=str(value.get("layout", "dense")),
            device=str(value.get("device", "cpu")),
            extensions=ext,
        )

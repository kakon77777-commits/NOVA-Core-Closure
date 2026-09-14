from __future__ import annotations

from typing import Any

from .domain_wire import _decode, _encode, _prepare
from .errors import DecodeError
from .human_projection import PURIFICATION_REVISION, contains_human_projection
from .semantic_registry import REGISTRY_REVISION
from .symbol_domains import DOMAIN_REVISION
from .symbol_minimal import _read_uvarint, _uvarint


_MAGIC = b"NSM5"


def encode_purified_record(record: Any) -> bytes:
    if contains_human_projection(record):
        raise TypeError("NSM5 refuses Human Projection inside canonical semantic payload")
    prepared = _prepare(record)
    body = _encode(prepared)
    return (
        _MAGIC
        + _uvarint(REGISTRY_REVISION)
        + _uvarint(DOMAIN_REVISION)
        + _uvarint(PURIFICATION_REVISION)
        + body
    )


def decode_purified_record(blob: bytes | bytearray | memoryview) -> Any:
    data = memoryview(blob)
    if len(data) < 4 or bytes(data[:4]) != _MAGIC:
        raise DecodeError("invalid NSM5 magic")
    offset = 4
    registry_revision, offset = _read_uvarint(data, offset)
    if registry_revision > REGISTRY_REVISION:
        raise DecodeError("NSM5 registry revision is newer than supported")
    domain_revision, offset = _read_uvarint(data, offset)
    if domain_revision != DOMAIN_REVISION:
        raise DecodeError("unsupported NSM5 symbol-domain revision")
    purification_revision, offset = _read_uvarint(data, offset)
    if purification_revision != PURIFICATION_REVISION:
        raise DecodeError("unsupported NSM5 purification revision")
    value, offset = _decode(data, offset)
    if offset != len(data):
        raise DecodeError("trailing bytes after NSM5 record")
    if contains_human_projection(value):
        raise DecodeError("NSM5 payload contains forbidden Human Projection")
    return value


__all__ = ["decode_purified_record", "encode_purified_record"]

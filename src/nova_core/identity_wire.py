from __future__ import annotations

from typing import Any

from .errors import DecodeError
from .semantic_registry import REGISTRY_REVISION
from .symbol_minimal import (
    _decode_value,
    _encode_value,
    _intern,
    _read_uvarint,
    _restore,
    _symbol_table,
    _uvarint,
)


_MAGIC = b"NSM3"


def encode_identity_record(record: Any) -> bytes:
    """Encode an identity-normalized mapping using the NSM3 envelope."""

    table = _symbol_table(record, use_global_registry=True)
    indices = {symbol: index for index, symbol in enumerate(table)}
    body = _encode_value(_intern(record, indices, use_global_registry=True))

    out = bytearray(_MAGIC)
    out.extend(_uvarint(REGISTRY_REVISION))
    out.extend(_uvarint(len(table)))
    for symbol in table:
        raw = symbol.encode("utf-8")
        out.extend(_uvarint(len(raw)))
        out.extend(raw)
    out.extend(body)
    return bytes(out)


def decode_identity_record(blob: bytes | bytearray | memoryview) -> Any:
    data = memoryview(blob)
    if len(data) < 4 or bytes(data[:4]) != _MAGIC:
        raise DecodeError("invalid NSM3 magic")

    offset = 4
    revision, offset = _read_uvarint(data, offset)
    if revision > REGISTRY_REVISION:
        raise DecodeError(
            f"NSM registry revision {revision} is newer than supported {REGISTRY_REVISION}"
        )
    if revision <= 0:
        raise DecodeError("invalid NSM registry revision")

    count, offset = _read_uvarint(data, offset)
    symbols: list[str] = []
    for _ in range(count):
        length, offset = _read_uvarint(data, offset)
        end = offset + length
        if end > len(data):
            raise DecodeError("truncated NSM3 symbol table")
        try:
            symbols.append(bytes(data[offset:end]).decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise DecodeError("invalid UTF-8 in NSM3 symbol table") from exc
        offset = end

    compact, offset = _decode_value(data, offset, allow_global=True)
    if offset != len(data):
        raise DecodeError("trailing bytes after NSM3 record")
    return _restore(compact, tuple(symbols))


__all__ = ["decode_identity_record", "encode_identity_record"]

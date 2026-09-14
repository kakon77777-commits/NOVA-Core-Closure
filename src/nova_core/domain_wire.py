from __future__ import annotations

import math
import struct
from typing import Any, Mapping

from .errors import DecodeError
from .semantic_registry import REGISTRY_REVISION, resolve_global
from .symbol_domains import DOMAIN_REVISION, DomainText, domain_from_code
from .symbol_minimal import _global_ref, _read_uvarint, _uvarint, _zigzag_decode, _zigzag_encode


_MAGIC = b"NSM4"

# NSM1/2 field codes stay stable; v0.4 appends common operator attribute keys
# without modifying the frozen v0.2 module.
_FIELD_NAMES = (
    "header", "nova_core_version", "schema_version", "feature_flags", "modules",
    "constraints", "attributes", "id", "imports", "exports", "graphs", "inputs",
    "outputs", "nodes", "edges", "kind", "value_type", "shape_type", "effect_type",
    "differentiation_type", "source", "target", "dtype", "shape", "layout", "device",
    "dims", "const", "terms", "relation", "reason", "required_relation", "proof_status",
    "runtime_guard",
    # v0.4 append-only field codes
    "name", "value", "axes", "axis", "keepdims", "callee", "trip_count", "body_kind",
)
_FIELD_TO_CODE = {name: index + 1 for index, name in enumerate(_FIELD_NAMES)}
_CODE_TO_FIELD = {code: name for name, code in _FIELD_TO_CODE.items()}

_T_NULL = 0x00
_T_FALSE = 0x01
_T_TRUE = 0x02
_T_INT = 0x03
_T_FLOAT64 = 0x04
_T_BYTES = 0x05
_T_ARRAY = 0x06
_T_MAP = 0x07
_T_FIELD = 0x09
_T_GLOBAL = 0x0A
_T_DOMAIN_TEXT = 0x0B


class _FieldRef:
    __slots__ = ("code",)
    def __init__(self, code: int): self.code = int(code)
    def __hash__(self): return hash(("field", self.code))
    def __eq__(self, other): return isinstance(other, _FieldRef) and self.code == other.code


class _GlobalRef:
    __slots__ = ("domain", "code")
    def __init__(self, domain: int, code: int): self.domain, self.code = int(domain), int(code)
    def __hash__(self): return hash(("global", self.domain, self.code))
    def __eq__(self, other): return isinstance(other, _GlobalRef) and (self.domain, self.code) == (other.domain, other.code)


def _prepare(
    value: Any,
    *,
    as_key: bool = False,
    field_name: str | None = None,
    container: Mapping[Any, Any] | None = None,
) -> Any:
    if value is None or isinstance(value, (bool, int, float, bytes, DomainText)):
        return value
    if isinstance(value, str):
        if as_key and value in _FIELD_TO_CODE:
            return _FieldRef(_FIELD_TO_CODE[value])
        if not as_key:
            ref = _global_ref(value, field_name=field_name, container=container if isinstance(container, Mapping) else None)
            if ref is not None:
                return _GlobalRef(ref.domain, ref.code)
        raise TypeError(f"NSM4 refuses unclassified text: {value!r} at field {field_name!r}")
    if isinstance(value, Mapping):
        out: dict[Any, Any] = {}
        for key, item in value.items():
            prepared_key = _prepare(key, as_key=True, container=value)
            key_name = key if isinstance(key, str) else None
            prepared_value = _prepare(item, field_name=key_name, container=value)
            out[prepared_key] = prepared_value
        return out
    if isinstance(value, (list, tuple)):
        return [_prepare(item, field_name=field_name, container=container) for item in value]
    raise TypeError(f"unsupported NSM4 value type: {type(value).__name__}")


def _encode(value: Any) -> bytes:
    if value is None: return bytes((_T_NULL,))
    if value is False: return bytes((_T_FALSE,))
    if value is True: return bytes((_T_TRUE,))
    if isinstance(value, int) and not isinstance(value, bool):
        return bytes((_T_INT,)) + _uvarint(_zigzag_encode(value))
    if isinstance(value, float):
        if not math.isfinite(value): raise ValueError("NSM4 rejects NaN and Infinity")
        return bytes((_T_FLOAT64,)) + struct.pack(">d", value)
    if isinstance(value, bytes):
        return bytes((_T_BYTES,)) + _uvarint(len(value)) + value
    if isinstance(value, DomainText):
        raw = value.text.encode("utf-8")
        return bytes((_T_DOMAIN_TEXT,)) + _uvarint(value.code) + _uvarint(len(raw)) + raw
    if isinstance(value, _FieldRef):
        return bytes((_T_FIELD,)) + _uvarint(value.code)
    if isinstance(value, _GlobalRef):
        return bytes((_T_GLOBAL,)) + _uvarint(value.domain) + _uvarint(value.code)
    if isinstance(value, list):
        return bytes((_T_ARRAY,)) + _uvarint(len(value)) + b"".join(_encode(item) for item in value)
    if isinstance(value, Mapping):
        pairs = [(_encode(key), _encode(item)) for key, item in value.items()]
        pairs.sort(key=lambda pair: pair[0])
        out = bytearray((_T_MAP,)); out.extend(_uvarint(len(pairs)))
        for key_blob, value_blob in pairs:
            out.extend(key_blob); out.extend(value_blob)
        return bytes(out)
    raise TypeError(f"unsupported NSM4 prepared type: {type(value).__name__}")


def _decode(data: memoryview, offset: int) -> tuple[Any, int]:
    if offset >= len(data): raise DecodeError("truncated NSM4 value")
    tag = int(data[offset]); offset += 1
    if tag == _T_NULL: return None, offset
    if tag == _T_FALSE: return False, offset
    if tag == _T_TRUE: return True, offset
    if tag == _T_INT:
        raw, offset = _read_uvarint(data, offset); return _zigzag_decode(raw), offset
    if tag == _T_FLOAT64:
        end = offset + 8
        if end > len(data): raise DecodeError("truncated NSM4 float")
        return struct.unpack(">d", data[offset:end])[0], end
    if tag == _T_BYTES:
        length, offset = _read_uvarint(data, offset); end = offset + length
        if end > len(data): raise DecodeError("truncated NSM4 bytes")
        return bytes(data[offset:end]), end
    if tag == _T_FIELD:
        code, offset = _read_uvarint(data, offset)
        try: return _CODE_TO_FIELD[code], offset
        except KeyError as exc: raise DecodeError(f"unknown NSM4 field code: {code}") from exc
    if tag == _T_GLOBAL:
        domain, offset = _read_uvarint(data, offset); code, offset = _read_uvarint(data, offset)
        try: return resolve_global(domain, code), offset
        except KeyError as exc: raise DecodeError(str(exc)) from exc
    if tag == _T_DOMAIN_TEXT:
        domain_code, offset = _read_uvarint(data, offset); length, offset = _read_uvarint(data, offset)
        end = offset + length
        if end > len(data): raise DecodeError("truncated NSM4 domain text")
        try: text = bytes(data[offset:end]).decode("utf-8")
        except UnicodeDecodeError as exc: raise DecodeError("invalid UTF-8 in NSM4 domain text") from exc
        try: domain = domain_from_code(domain_code)
        except KeyError as exc: raise DecodeError(str(exc)) from exc
        return DomainText(domain, text), end
    if tag == _T_ARRAY:
        length, offset = _read_uvarint(data, offset); items=[]
        for _ in range(length):
            item, offset = _decode(data, offset); items.append(item)
        return items, offset
    if tag == _T_MAP:
        length, offset = _read_uvarint(data, offset); items={}
        for _ in range(length):
            key, offset = _decode(data, offset); item, offset = _decode(data, offset)
            if key in items: raise DecodeError("duplicate NSM4 map key")
            items[key] = item
        return items, offset
    raise DecodeError(f"unknown NSM4 tag: {tag}")


def encode_domain_record(record: Any) -> bytes:
    prepared = _prepare(record)
    body = _encode(prepared)
    return _MAGIC + _uvarint(REGISTRY_REVISION) + _uvarint(DOMAIN_REVISION) + body


def decode_domain_record(blob: bytes | bytearray | memoryview) -> Any:
    data = memoryview(blob)
    if len(data) < 4 or bytes(data[:4]) != _MAGIC: raise DecodeError("invalid NSM4 magic")
    offset = 4
    registry_revision, offset = _read_uvarint(data, offset)
    if registry_revision > REGISTRY_REVISION: raise DecodeError("NSM4 registry revision is newer than supported")
    domain_revision, offset = _read_uvarint(data, offset)
    if domain_revision != DOMAIN_REVISION: raise DecodeError("unsupported NSM4 symbol-domain revision")
    value, offset = _decode(data, offset)
    if offset != len(data): raise DecodeError("trailing bytes after NSM4 record")
    return value


__all__ = ["decode_domain_record", "encode_domain_record"]

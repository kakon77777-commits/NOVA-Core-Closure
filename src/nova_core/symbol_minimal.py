from __future__ import annotations

from dataclasses import dataclass
import math
import struct
from typing import Any, Mapping

from .canonical import project_record, semantic_hash
from .codec import decode_project
from .errors import DecodeError
from .model import Project

_MAGIC = b"NSM1"

_FIELD_NAMES = (
    "header",
    "nova_core_version",
    "schema_version",
    "feature_flags",
    "modules",
    "constraints",
    "attributes",
    "id",
    "imports",
    "exports",
    "graphs",
    "inputs",
    "outputs",
    "nodes",
    "edges",
    "kind",
    "value_type",
    "shape_type",
    "effect_type",
    "differentiation_type",
    "source",
    "target",
    "dtype",
    "shape",
    "layout",
    "device",
    "dims",
    "const",
    "terms",
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
_T_SYMBOL = 0x08
_T_FIELD = 0x09


@dataclass(frozen=True)
class _SymbolRef:
    index: int


@dataclass(frozen=True)
class _FieldRef:
    code: int


def _uvarint(value: int) -> bytes:
    if value < 0:
        raise ValueError("uvarint requires a non-negative integer")
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _read_uvarint(data: memoryview, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise DecodeError("truncated NSM varint")
        byte = int(data[offset])
        offset += 1
        value |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return value, offset
        shift += 7
        if shift > 126:
            raise DecodeError("NSM varint is too large")


def _zigzag_encode(value: int) -> int:
    return value * 2 if value >= 0 else (-value * 2) - 1


def _zigzag_decode(value: int) -> int:
    return value // 2 if value % 2 == 0 else -(value // 2) - 1


def _collect_symbols(value: Any, out: set[str], *, as_key: bool = False) -> None:
    if isinstance(value, str):
        if not (as_key and value in _FIELD_TO_CODE):
            out.add(value)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("NOVA canonical mappings must use string keys")
            _collect_symbols(key, out, as_key=True)
            _collect_symbols(item, out)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _collect_symbols(item, out)


def _symbol_table(value: Any) -> tuple[str, ...]:
    symbols: set[str] = set()
    _collect_symbols(value, symbols)
    return tuple(sorted(symbols, key=lambda item: item.encode("utf-8")))


def _intern(value: Any, symbols: Mapping[str, int], *, as_key: bool = False) -> Any:
    if value is None or isinstance(value, (bool, int, float, bytes)):
        return value
    if isinstance(value, str):
        if as_key and value in _FIELD_TO_CODE:
            return _FieldRef(_FIELD_TO_CODE[value])
        return _SymbolRef(symbols[value])
    if isinstance(value, Mapping):
        return {
            _intern(str(key), symbols, as_key=True): _intern(item, symbols)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_intern(item, symbols) for item in value]
    raise TypeError(f"unsupported NSM value type: {type(value).__name__}")


def _restore(value: Any, symbols: tuple[str, ...], *, as_key: bool = False) -> Any:
    if isinstance(value, _SymbolRef):
        try:
            return symbols[value.index]
        except IndexError as exc:
            raise DecodeError("NSM symbol reference is out of range") from exc
    if isinstance(value, _FieldRef):
        try:
            return _CODE_TO_FIELD[value.code]
        except KeyError as exc:
            raise DecodeError(f"unknown NSM field code: {value.code}") from exc
    if isinstance(value, Mapping):
        restored: dict[str, Any] = {}
        for key, item in value.items():
            decoded_key = _restore(key, symbols, as_key=True)
            if not isinstance(decoded_key, str):
                raise DecodeError("decoded NSM map key is not a string")
            restored[decoded_key] = _restore(item, symbols)
        return restored
    if isinstance(value, list):
        return [_restore(item, symbols) for item in value]
    return value


def _encode_value(value: Any) -> bytes:
    if value is None:
        return bytes((_T_NULL,))
    if value is False:
        return bytes((_T_FALSE,))
    if value is True:
        return bytes((_T_TRUE,))
    if isinstance(value, int) and not isinstance(value, bool):
        return bytes((_T_INT,)) + _uvarint(_zigzag_encode(value))
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("NSM canonical encoding rejects NaN and Infinity")
        return bytes((_T_FLOAT64,)) + struct.pack(">d", value)
    if isinstance(value, bytes):
        return bytes((_T_BYTES,)) + _uvarint(len(value)) + value
    if isinstance(value, _SymbolRef):
        return bytes((_T_SYMBOL,)) + _uvarint(value.index)
    if isinstance(value, _FieldRef):
        return bytes((_T_FIELD,)) + _uvarint(value.code)
    if isinstance(value, list):
        return bytes((_T_ARRAY,)) + _uvarint(len(value)) + b"".join(_encode_value(v) for v in value)
    if isinstance(value, Mapping):
        encoded_items = [(_encode_value(key), _encode_value(item)) for key, item in value.items()]
        encoded_items.sort(key=lambda pair: pair[0])
        body = bytearray((_T_MAP,))
        body.extend(_uvarint(len(encoded_items)))
        for key_blob, value_blob in encoded_items:
            body.extend(key_blob)
            body.extend(value_blob)
        return bytes(body)
    raise TypeError(f"unsupported NSM canonical value: {type(value).__name__}")


def _decode_value(data: memoryview, offset: int) -> tuple[Any, int]:
    if offset >= len(data):
        raise DecodeError("truncated NSM value")
    tag = int(data[offset])
    offset += 1

    if tag == _T_NULL:
        return None, offset
    if tag == _T_FALSE:
        return False, offset
    if tag == _T_TRUE:
        return True, offset
    if tag == _T_INT:
        raw, offset = _read_uvarint(data, offset)
        return _zigzag_decode(raw), offset
    if tag == _T_FLOAT64:
        end = offset + 8
        if end > len(data):
            raise DecodeError("truncated NSM float")
        return struct.unpack(">d", data[offset:end])[0], end
    if tag == _T_BYTES:
        length, offset = _read_uvarint(data, offset)
        end = offset + length
        if end > len(data):
            raise DecodeError("truncated NSM byte string")
        return bytes(data[offset:end]), end
    if tag == _T_SYMBOL:
        index, offset = _read_uvarint(data, offset)
        return _SymbolRef(index), offset
    if tag == _T_FIELD:
        code, offset = _read_uvarint(data, offset)
        return _FieldRef(code), offset
    if tag == _T_ARRAY:
        length, offset = _read_uvarint(data, offset)
        items: list[Any] = []
        for _ in range(length):
            item, offset = _decode_value(data, offset)
            items.append(item)
        return items, offset
    if tag == _T_MAP:
        length, offset = _read_uvarint(data, offset)
        items: dict[Any, Any] = {}
        for _ in range(length):
            key, offset = _decode_value(data, offset)
            item, offset = _decode_value(data, offset)
            if key in items:
                raise DecodeError("duplicate NSM map key")
            items[key] = item
        return items, offset
    raise DecodeError(f"unknown NSM type tag: {tag}")


def encode_semantic_core(project: Project) -> bytes:
    """Encode semantic NOVA Project state into deterministic symbol-minimal bytes."""
    record = project_record(project, semantic=True)
    table = _symbol_table(record)
    indices = {symbol: index for index, symbol in enumerate(table)}
    body = _encode_value(_intern(record, indices))

    out = bytearray(_MAGIC)
    out.extend(_uvarint(len(table)))
    for symbol in table:
        raw = symbol.encode("utf-8")
        out.extend(_uvarint(len(raw)))
        out.extend(raw)
    out.extend(body)
    return bytes(out)


def decode_semantic_core(blob: bytes | bytearray | memoryview) -> Project:
    data = memoryview(blob)
    if len(data) < len(_MAGIC) or bytes(data[:4]) != _MAGIC:
        raise DecodeError("invalid NSM magic")
    offset = 4
    count, offset = _read_uvarint(data, offset)
    symbols: list[str] = []
    for _ in range(count):
        length, offset = _read_uvarint(data, offset)
        end = offset + length
        if end > len(data):
            raise DecodeError("truncated NSM symbol table")
        try:
            symbols.append(bytes(data[offset:end]).decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise DecodeError("invalid UTF-8 in NSM symbol table") from exc
        offset = end

    compact, offset = _decode_value(data, offset)
    if offset != len(data):
        raise DecodeError("trailing bytes after NSM project")
    restored = _restore(compact, tuple(symbols))
    if not isinstance(restored, Mapping):
        raise DecodeError("NSM root must decode to a project mapping")
    return decode_project(restored)


def semantic_roundtrip_ok(project: Project) -> bool:
    restored = decode_semantic_core(encode_semantic_core(project))
    return semantic_hash(project) == semantic_hash(restored)


def annotation_sidecar(project: Project) -> dict[str, Any]:
    """Extract non-authoritative human/provenance surfaces by stable identity."""
    modules: dict[str, Any] = {}
    for module in project.modules:
        graphs: dict[str, Any] = {}
        for graph in module.graphs:
            nodes: dict[str, Any] = {}
            for node in graph.nodes:
                entry: dict[str, Any] = {}
                if node.source_projection is not None:
                    entry["source_projection"] = node.source_projection
                if node.provenance:
                    entry["provenance"] = dict(node.provenance)
                if entry:
                    nodes[node.id] = entry
            graph_entry: dict[str, Any] = {}
            if nodes:
                graph_entry["nodes"] = nodes
            if graph.provenance:
                graph_entry["provenance"] = dict(graph.provenance)
            if graph_entry:
                graphs[graph.id] = graph_entry

        module_entry: dict[str, Any] = {}
        if graphs:
            module_entry["graphs"] = graphs
        if module.provenance:
            module_entry["provenance"] = dict(module.provenance)
        if module_entry:
            modules[module.id] = module_entry

    sidecar: dict[str, Any] = {
        "format": "nova.annotation-sidecar/0.1",
        "semantic_hash": semantic_hash(project),
    }
    if project.header.migration_history:
        sidecar["migration_history"] = list(project.header.migration_history)
    if project.header.provenance:
        sidecar["header_provenance"] = dict(project.header.provenance)
    if modules:
        sidecar["modules"] = modules
    if project.artifacts:
        sidecar["artifacts"] = list(project.artifacts)
    if project.provenance:
        sidecar["project_provenance"] = dict(project.provenance)
    return sidecar

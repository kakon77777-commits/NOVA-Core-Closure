from __future__ import annotations

from dataclasses import dataclass
import math
import struct
from typing import Any, Mapping

from .canonical import project_record, semantic_hash
from .codec import decode_project
from .errors import DecodeError
from .model import Project
from .semantic_registry import REGISTRY_REVISION, global_code, resolve_global

_MAGIC_V1 = b"NSM1"
_MAGIC_V2 = b"NSM2"

# Structural field names are encoded as numeric field references rather than
# repeated UTF-8 labels in the canonical body. The mapping is append-only.
# The first 29 entries are frozen by NSM1 and MUST NOT be reordered.
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
    # NSM2 append-only field extensions.
    "relation",
    "reason",
    "required_relation",
    "proof_status",
    "runtime_guard",
)
_FIELD_TO_CODE = {name: index + 1 for index, name in enumerate(_FIELD_NAMES)}
_CODE_TO_FIELD = {code: name for name, code in _FIELD_TO_CODE.items()}

# Canonical binary value tags.
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
_T_GLOBAL = 0x0A


@dataclass(frozen=True)
class _SymbolRef:
    index: int


@dataclass(frozen=True)
class _FieldRef:
    code: int


@dataclass(frozen=True)
class _GlobalRef:
    domain: int
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
        if shift > 63 * 2:
            raise DecodeError("NSM varint is too large")


def _zigzag_encode(value: int) -> int:
    return value * 2 if value >= 0 else (-value * 2) - 1


def _zigzag_decode(value: int) -> int:
    return value // 2 if value % 2 == 0 else -(value // 2) - 1


def _kind_domain(container: Mapping[str, Any], value: str) -> str | None:
    # Edge records and Node records both use the field name "kind". Infer the
    # authoritative domain from structural shape rather than from spelling.
    if "source" in container and "target" in container:
        return "edge_kind"
    if "id" in container and "inputs" in container and "outputs" in container:
        return "operator"
    if global_code("record_kind", value) is not None:
        return "record_kind"
    return None


def _semantic_domain(
    *,
    field_name: str | None,
    container: Mapping[str, Any] | None,
    value: str,
) -> str | None:
    if field_name == "kind" and container is not None:
        return _kind_domain(container, value)
    if field_name == "dtype":
        return "dtype"
    if field_name == "device":
        return "device"
    if field_name == "layout":
        return "layout"
    if field_name == "effect_type":
        return "effect_kind"
    if field_name == "differentiation_type":
        return "differentiation_kind"
    if field_name == "proof_status":
        return "proof_status"
    if field_name in {"relation", "required_relation"}:
        return "relation"
    return None


def _global_ref(
    value: str,
    *,
    field_name: str | None,
    container: Mapping[str, Any] | None,
) -> _GlobalRef | None:
    domain = _semantic_domain(field_name=field_name, container=container, value=value)
    if domain is None:
        return None
    pair = global_code(domain, value)
    return None if pair is None else _GlobalRef(*pair)


def _collect_symbols(
    value: Any,
    out: set[str],
    *,
    as_key: bool = False,
    field_name: str | None = None,
    container: Mapping[str, Any] | None = None,
    use_global_registry: bool = True,
) -> None:
    if isinstance(value, str):
        if as_key and value in _FIELD_TO_CODE:
            return
        if use_global_registry and not as_key:
            if _global_ref(value, field_name=field_name, container=container) is not None:
                return
        out.add(value)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("NOVA canonical mappings must use string keys")
            _collect_symbols(
                key,
                out,
                as_key=True,
                container=value,
                use_global_registry=use_global_registry,
            )
            _collect_symbols(
                item,
                out,
                field_name=key,
                container=value,
                use_global_registry=use_global_registry,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _collect_symbols(
                item,
                out,
                field_name=field_name,
                container=container,
                use_global_registry=use_global_registry,
            )


def _symbol_table(value: Any, *, use_global_registry: bool) -> tuple[str, ...]:
    symbols: set[str] = set()
    _collect_symbols(value, symbols, use_global_registry=use_global_registry)
    return tuple(sorted(symbols, key=lambda item: item.encode("utf-8")))


def _intern(
    value: Any,
    symbols: Mapping[str, int],
    *,
    as_key: bool = False,
    field_name: str | None = None,
    container: Mapping[str, Any] | None = None,
    use_global_registry: bool = True,
) -> Any:
    if value is None or isinstance(value, (bool, int, float, bytes)):
        return value
    if isinstance(value, str):
        if as_key and value in _FIELD_TO_CODE:
            return _FieldRef(_FIELD_TO_CODE[value])
        if use_global_registry and not as_key:
            ref = _global_ref(value, field_name=field_name, container=container)
            if ref is not None:
                return ref
        return _SymbolRef(symbols[value])
    if isinstance(value, Mapping):
        return {
            _intern(
                str(key),
                symbols,
                as_key=True,
                container=value,
                use_global_registry=use_global_registry,
            ): _intern(
                item,
                symbols,
                field_name=str(key),
                container=value,
                use_global_registry=use_global_registry,
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            _intern(
                item,
                symbols,
                field_name=field_name,
                container=container,
                use_global_registry=use_global_registry,
            )
            for item in value
        ]
    raise TypeError(f"unsupported NSM value type: {type(value).__name__}")


def _restore(value: Any, symbols: tuple[str, ...]) -> Any:
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
    if isinstance(value, _GlobalRef):
        try:
            return resolve_global(value.domain, value.code)
        except KeyError as exc:
            raise DecodeError(str(exc)) from exc
    if isinstance(value, Mapping):
        restored: dict[str, Any] = {}
        for key, item in value.items():
            decoded_key = _restore(key, symbols)
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
    if isinstance(value, _GlobalRef):
        return bytes((_T_GLOBAL,)) + _uvarint(value.domain) + _uvarint(value.code)
    if isinstance(value, list):
        return bytes((_T_ARRAY,)) + _uvarint(len(value)) + b"".join(
            _encode_value(v) for v in value
        )
    if isinstance(value, Mapping):
        encoded_items = [
            (_encode_value(key), _encode_value(item)) for key, item in value.items()
        ]
        encoded_items.sort(key=lambda pair: pair[0])
        body = bytearray((_T_MAP,))
        body.extend(_uvarint(len(encoded_items)))
        for key_blob, value_blob in encoded_items:
            body.extend(key_blob)
            body.extend(value_blob)
        return bytes(body)
    raise TypeError(f"unsupported NSM canonical value: {type(value).__name__}")


def _decode_value(
    data: memoryview,
    offset: int,
    *,
    allow_global: bool,
) -> tuple[Any, int]:
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
    if tag == _T_GLOBAL:
        if not allow_global:
            raise DecodeError("NSM1 payload contains NSM2 global atom tag")
        domain, offset = _read_uvarint(data, offset)
        code, offset = _read_uvarint(data, offset)
        return _GlobalRef(domain, code), offset
    if tag == _T_ARRAY:
        length, offset = _read_uvarint(data, offset)
        items: list[Any] = []
        for _ in range(length):
            item, offset = _decode_value(data, offset, allow_global=allow_global)
            items.append(item)
        return items, offset
    if tag == _T_MAP:
        length, offset = _read_uvarint(data, offset)
        items: dict[Any, Any] = {}
        for _ in range(length):
            key, offset = _decode_value(data, offset, allow_global=allow_global)
            item, offset = _decode_value(data, offset, allow_global=allow_global)
            if key in items:
                raise DecodeError("duplicate NSM map key")
            items[key] = item
        return items, offset
    raise DecodeError(f"unknown NSM type tag: {tag}")


def _encode_record(record: Mapping[str, Any], *, version: int) -> bytes:
    if version not in {1, 2}:
        raise ValueError("NSM version must be 1 or 2")
    use_global = version >= 2
    table = _symbol_table(record, use_global_registry=use_global)
    indices = {symbol: index for index, symbol in enumerate(table)}
    body = _encode_value(_intern(record, indices, use_global_registry=use_global))

    out = bytearray(_MAGIC_V2 if version == 2 else _MAGIC_V1)
    if version == 2:
        out.extend(_uvarint(REGISTRY_REVISION))
    out.extend(_uvarint(len(table)))
    for symbol in table:
        raw = symbol.encode("utf-8")
        out.extend(_uvarint(len(raw)))
        out.extend(raw)
    out.extend(body)
    return bytes(out)


def _decode_record(blob: bytes | bytearray | memoryview) -> Mapping[str, Any]:
    data = memoryview(blob)
    if len(data) < 4:
        raise DecodeError("invalid NSM magic")
    magic = bytes(data[:4])
    if magic not in {_MAGIC_V1, _MAGIC_V2}:
        raise DecodeError("invalid NSM magic")

    offset = 4
    allow_global = magic == _MAGIC_V2
    if allow_global:
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
            raise DecodeError("truncated NSM symbol table")
        try:
            symbols.append(bytes(data[offset:end]).decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise DecodeError("invalid UTF-8 in NSM symbol table") from exc
        offset = end

    compact, offset = _decode_value(data, offset, allow_global=allow_global)
    if offset != len(data):
        raise DecodeError("trailing bytes after NSM project")
    restored = _restore(compact, tuple(symbols))
    if not isinstance(restored, Mapping):
        raise DecodeError("NSM root must decode to a project mapping")
    return restored


def encode_semantic_core(project: Project, *, version: int = 2) -> bytes:
    """Encode the semantic NOVA Project into deterministic symbol-minimal bytes.

    NSM2 is the default. Known semantic atoms use global numeric registries;
    unknown/extension atoms fall back to the deterministic local symbol table.
    NSM1 remains available for compatibility experiments.
    """

    return _encode_record(project_record(project, semantic=True), version=version)


def decode_semantic_core(blob: bytes | bytearray | memoryview) -> Project:
    return decode_project(_decode_record(blob))


def semantic_roundtrip_ok(project: Project, *, version: int = 2) -> bool:
    restored = decode_semantic_core(encode_semantic_core(project, version=version))
    return semantic_hash(project) == semantic_hash(restored)


def annotation_sidecar(project: Project) -> dict[str, Any]:
    """Extract non-authoritative human/provenance surfaces by stable identity.

    The sidecar is deliberately separate from the semantic-core blob. It is a
    view/documentation artifact, not program authority.
    """

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
        "format": "nova.annotation-sidecar/0.2",
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


__all__ = [
    "annotation_sidecar",
    "decode_semantic_core",
    "encode_semantic_core",
    "semantic_roundtrip_ok",
]

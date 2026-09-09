from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import prod
from types import MappingProxyType
from typing import Any, Mapping

from .canonical import semantic_hash
from .errors import ResourcePlanningError
from .model import Graph, Node
from .types import TensorType


class OwnershipState(str, Enum):
    OWNED = "owned"
    BORROWED_IMMUTABLE = "borrowed_immutable"
    BORROWED_MUTABLE = "borrowed_mutable"
    SHARED_IMMUTABLE = "shared_immutable"
    DEVICE_RESIDENT = "device_resident"
    MOVED = "moved"
    RELEASED = "released"
    EXTERNAL_UNMANAGED = "external_unmanaged"


_DTYPE_BYTES = {
    "bool": 1,
    "i8": 1,
    "int8": 1,
    "u8": 1,
    "uint8": 1,
    "i16": 2,
    "int16": 2,
    "u16": 2,
    "uint16": 2,
    "f16": 2,
    "float16": 2,
    "i32": 4,
    "int32": 4,
    "u32": 4,
    "uint32": 4,
    "f32": 4,
    "float32": 4,
    "i64": 8,
    "int64": 8,
    "u64": 8,
    "uint64": 8,
    "f64": 8,
    "float64": 8,
    "complex64": 8,
    "c64": 8,
    "complex128": 16,
    "c128": 16,
}


def dtype_nbytes(dtype: str) -> int:
    key = str(dtype).strip().lower()
    try:
        return _DTYPE_BYTES[key]
    except KeyError as exc:
        raise ResourcePlanningError(
            "unknown tensor dtype size",
            context={"dtype": str(dtype)},
        ) from exc


def tensor_nbytes(tensor_type: TensorType) -> int | None:
    dims: list[int] = []
    for dim in tensor_type.shape:
        if not dim.is_concrete:
            return None
        value = dim.concrete_value
        if value is None:
            return None
        dims.append(int(value))
    count = prod(dims) if dims else 1
    return int(count) * dtype_nbytes(tensor_type.dtype)


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


@dataclass(frozen=True)
class ResourceObligation:
    kind: str
    symbol: str
    message: str
    runtime_guard: bool = True
    context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "context", _freeze_mapping(self.context))

    def to_record(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "symbol": self.symbol,
            "message": self.message,
            "runtime_guard": self.runtime_guard,
            "context": dict(self.context),
        }


@dataclass(frozen=True)
class ValueLifetime:
    symbol: str
    producer_node: str | None
    first_step: int
    last_step: int
    ownership: OwnershipState
    tensor_type: TensorType | None
    size_bytes: int | None
    device: str
    layout: str
    external: bool = False
    graph_output: bool = False
    reusable: bool = False

    def to_record(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "producer_node": self.producer_node,
            "first_step": self.first_step,
            "last_step": self.last_step,
            "ownership": self.ownership.value,
            "tensor_type": self.tensor_type.to_record() if self.tensor_type is not None else None,
            "size_bytes": self.size_bytes,
            "device": self.device,
            "layout": self.layout,
            "external": self.external,
            "graph_output": self.graph_output,
            "reusable": self.reusable,
        }


@dataclass(frozen=True)
class ResourceAnalysis:
    graph_semantic_hash: str
    schedule: tuple[str, ...]
    exit_step: int
    values: Mapping[str, ValueLifetime]
    obligations: tuple[ResourceObligation, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))
        object.__setattr__(self, "obligations", tuple(self.obligations))

    def value(self, symbol: str) -> ValueLifetime:
        try:
            return self.values[str(symbol)]
        except KeyError as exc:
            raise ResourcePlanningError(
                "resource symbol not found",
                context={"symbol": str(symbol)},
            ) from exc

    def to_record(self) -> dict[str, Any]:
        return {
            "graph_semantic_hash": self.graph_semantic_hash,
            "schedule": list(self.schedule),
            "exit_step": self.exit_step,
            "values": [self.values[name].to_record() for name in sorted(self.values)],
            "obligations": [o.to_record() for o in self.obligations],
        }


def _deterministic_schedule(graph: Graph) -> tuple[Node, ...]:
    available = set(graph.inputs)
    pending = {node.id: node for node in graph.nodes}
    schedule: list[Node] = []

    while pending:
        progressed = False
        for node_id in sorted(tuple(pending)):
            node = pending[node_id]
            ready = node.kind in {"Parameter", "Constant", "Input"} or all(name in available for name in node.inputs)
            if not ready:
                continue
            schedule.append(node)
            available.update(node.outputs)
            del pending[node_id]
            progressed = True
        if not progressed:
            raise ResourcePlanningError(
                "resource analysis dependency cycle or unresolved dependency",
                context={
                    "unresolved": {
                        node.id: [name for name in node.inputs if name not in available]
                        for node in pending.values()
                    }
                },
            )
    return tuple(schedule)


def _ownership_for_node(node: Node, tensor_type: TensorType | None) -> OwnershipState:
    if node.kind in {"Input", "Parameter"}:
        return OwnershipState.BORROWED_IMMUTABLE
    if node.kind == "Constant":
        return OwnershipState.SHARED_IMMUTABLE
    if tensor_type is not None and tensor_type.device != "cpu":
        return OwnershipState.DEVICE_RESIDENT
    return OwnershipState.OWNED


def _is_effectful(node: Node) -> bool:
    value = node.effect_type
    if value is None:
        return False
    if isinstance(value, (tuple, list, set, dict)):
        return bool(value)
    return bool(str(value))


def analyze_resources(
    graph: Graph,
    symbol_types: Mapping[str, TensorType] | None = None,
) -> ResourceAnalysis:
    provided_types = {str(k): v for k, v in dict(symbol_types or {}).items()}
    schedule_nodes = _deterministic_schedule(graph)
    schedule = tuple(node.id for node in schedule_nodes)
    exit_step = len(schedule_nodes)

    producer: dict[str, str | None] = {name: None for name in graph.inputs}
    first: dict[str, int] = {name: -1 for name in graph.inputs}
    last: dict[str, int] = {name: -1 for name in graph.inputs}
    types: dict[str, TensorType | None] = {name: provided_types.get(name) for name in graph.inputs}
    ownership: dict[str, OwnershipState] = {
        name: OwnershipState.BORROWED_IMMUTABLE for name in graph.inputs
    }
    reusable: dict[str, bool] = {name: False for name in graph.inputs}

    for step, node in enumerate(schedule_nodes):
        node_type = node.value_type if isinstance(node.value_type, TensorType) else None
        for output in node.outputs:
            producer[output] = node.id
            first[output] = step
            last[output] = step
            output_type = provided_types.get(output, node_type)
            types[output] = output_type
            own = _ownership_for_node(node, output_type)
            ownership[output] = own
            reusable[output] = (
                own in {OwnershipState.OWNED, OwnershipState.DEVICE_RESIDENT}
                and output not in graph.outputs
                and not _is_effectful(node)
            )
        for input_name in node.inputs:
            if input_name in last:
                last[input_name] = max(last[input_name], step)

    for output in graph.outputs:
        if output in last:
            last[output] = max(last[output], exit_step)

    obligations: list[ResourceObligation] = []
    values: dict[str, ValueLifetime] = {}
    for symbol in sorted(first):
        tensor_type = types.get(symbol)
        size_bytes: int | None = None
        device = "unknown"
        layout = "unknown"
        if tensor_type is None:
            obligations.append(
                ResourceObligation(
                    kind="runtime_type",
                    symbol=symbol,
                    message="tensor type is not statically known",
                    runtime_guard=True,
                )
            )
        else:
            device = tensor_type.device
            layout = tensor_type.layout
            size_bytes = tensor_nbytes(tensor_type)
            if size_bytes is None:
                obligations.append(
                    ResourceObligation(
                        kind="runtime_size",
                        symbol=symbol,
                        message="tensor byte size depends on symbolic/runtime dimensions",
                        runtime_guard=True,
                        context={"shape": tensor_type.shape.to_record()},
                    )
                )
        values[symbol] = ValueLifetime(
            symbol=symbol,
            producer_node=producer.get(symbol),
            first_step=first[symbol],
            last_step=last[symbol],
            ownership=ownership[symbol],
            tensor_type=tensor_type,
            size_bytes=size_bytes,
            device=device,
            layout=layout,
            external=producer.get(symbol) is None or ownership[symbol] is OwnershipState.BORROWED_IMMUTABLE,
            graph_output=symbol in graph.outputs,
            reusable=reusable[symbol],
        )

    return ResourceAnalysis(
        graph_semantic_hash=semantic_hash(graph),
        schedule=schedule,
        exit_step=exit_step,
        values=values,
        obligations=tuple(obligations),
    )

import hashlib
import json


@dataclass(frozen=True)
class BufferBinding:
    buffer_id: str
    symbols: tuple[str, ...]
    dtype: str
    layout: str
    device: str
    capacity_bytes: int | None
    first_step: int
    last_step: int

    def to_record(self) -> dict[str, Any]:
        return {
            "buffer_id": self.buffer_id,
            "symbols": list(self.symbols),
            "dtype": self.dtype,
            "layout": self.layout,
            "device": self.device,
            "capacity_bytes": self.capacity_bytes,
            "first_step": self.first_step,
            "last_step": self.last_step,
        }


@dataclass(frozen=True)
class DeviceTransfer:
    symbol: str
    source_device: str
    target_device: str
    before_node: str
    reason: str = "device mismatch"

    def to_record(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "source_device": self.source_device,
            "target_device": self.target_device,
            "before_node": self.before_node,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class MemoryPlan:
    graph_semantic_hash: str
    schedule: tuple[str, ...]
    lifetimes: tuple[ValueLifetime, ...]
    buffers: tuple[BufferBinding, ...]
    transfers: tuple[DeviceTransfer, ...]
    obligations: tuple[ResourceObligation, ...]
    peak_reserved_bytes: int | None
    verification_mode: str
    proposer: str = "deterministic-planner"
    confidence: float | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.verification_mode not in {"optimized", "conservative", "external"}:
            raise ResourcePlanningError(
                "invalid memory-plan mode",
                context={"mode": self.verification_mode},
            )
        object.__setattr__(self, "schedule", tuple(self.schedule))
        object.__setattr__(self, "lifetimes", tuple(self.lifetimes))
        object.__setattr__(self, "buffers", tuple(self.buffers))
        object.__setattr__(self, "transfers", tuple(self.transfers))
        object.__setattr__(self, "obligations", tuple(self.obligations))
        object.__setattr__(self, "provenance", _freeze_mapping(self.provenance))
        if self.confidence is not None and not 0.0 <= float(self.confidence) <= 1.0:
            raise ResourcePlanningError("memory-plan confidence must be between 0 and 1")

    def buffer_for(self, symbol: str) -> str:
        for buffer in self.buffers:
            if str(symbol) in buffer.symbols:
                return buffer.buffer_id
        raise ResourcePlanningError(
            "symbol has no physical buffer binding",
            context={"symbol": str(symbol)},
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "kind": "memory_plan",
            "graph_semantic_hash": self.graph_semantic_hash,
            "schedule": list(self.schedule),
            "lifetimes": [value.to_record() for value in self.lifetimes],
            "buffers": [buffer.to_record() for buffer in self.buffers],
            "transfers": [transfer.to_record() for transfer in self.transfers],
            "obligations": [obligation.to_record() for obligation in self.obligations],
            "peak_reserved_bytes": self.peak_reserved_bytes,
            "verification_mode": self.verification_mode,
            "proposer": self.proposer,
            "confidence": self.confidence,
            "provenance": dict(self.provenance),
        }


def memory_plan_hash(plan: MemoryPlan) -> str:
    payload = json.dumps(plan.to_record(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _node_execution_device(node: Node) -> str:
    if isinstance(node.value_type, TensorType):
        return node.value_type.device
    if "device" in node.attributes:
        return str(node.attributes["device"])
    return "cpu"


def _required_transfers(
    graph: Graph,
    analysis: ResourceAnalysis,
) -> tuple[tuple[DeviceTransfer, ...], tuple[ResourceObligation, ...]]:
    nodes = {node.id: node for node in graph.nodes}
    transfers: list[DeviceTransfer] = []
    obligations: list[ResourceObligation] = []
    for node_id in analysis.schedule:
        node = nodes[node_id]
        target_device = _node_execution_device(node)
        for symbol in node.inputs:
            if symbol not in analysis.values:
                continue
            source_device = analysis.value(symbol).device
            if source_device == "unknown":
                obligations.append(
                    ResourceObligation(
                        kind="runtime_device",
                        symbol=symbol,
                        message="input device is not statically known",
                        runtime_guard=True,
                        context={"before_node": node_id, "target_device": target_device},
                    )
                )
                continue
            if source_device != target_device:
                transfers.append(
                    DeviceTransfer(
                        symbol=symbol,
                        source_device=source_device,
                        target_device=target_device,
                        before_node=node_id,
                    )
                )
    transfers.sort(key=lambda t: (analysis.schedule.index(t.before_node), t.symbol, t.source_device, t.target_device))
    return tuple(transfers), tuple(obligations)


def _allocatable_values(analysis: ResourceAnalysis) -> tuple[ValueLifetime, ...]:
    return tuple(
        sorted(
            (
                value
                for value in analysis.values.values()
                if value.producer_node is not None
                and value.ownership
                in {
                    OwnershipState.OWNED,
                    OwnershipState.DEVICE_RESIDENT,
                    OwnershipState.SHARED_IMMUTABLE,
                }
            ),
            key=lambda value: (value.first_step, value.symbol),
        )
    )


def _buffer_compatible(buffer: dict[str, Any], value: ValueLifetime) -> bool:
    if value.tensor_type is None or value.size_bytes is None:
        return False
    if buffer["capacity_bytes"] is None:
        return False
    return (
        buffer["last_reusable"]
        and int(buffer["last_step"]) < value.first_step
        and buffer["dtype"] == value.tensor_type.dtype
        and buffer["layout"] == value.layout
        and buffer["device"] == value.device
        and int(buffer["capacity_bytes"]) >= value.size_bytes
    )


def _plan_buffers(
    analysis: ResourceAnalysis,
    *,
    mode: str,
) -> tuple[BufferBinding, ...]:
    state: list[dict[str, Any]] = []
    for value in _allocatable_values(analysis):
        tensor_type = value.tensor_type
        dtype = tensor_type.dtype if tensor_type is not None else "unknown"
        selected: dict[str, Any] | None = None
        if mode == "optimized" and value.size_bytes is not None:
            candidates = [buffer for buffer in state if _buffer_compatible(buffer, value)]
            if candidates:
                selected = sorted(candidates, key=lambda b: (int(b["capacity_bytes"]), b["buffer_id"]))[0]
        if selected is None:
            selected = {
                "buffer_id": f"buf:{len(state):04d}",
                "symbols": [],
                "dtype": dtype,
                "layout": value.layout,
                "device": value.device,
                "capacity_bytes": value.size_bytes,
                "first_step": value.first_step,
                "last_step": value.last_step,
                "last_reusable": value.reusable,
            }
            state.append(selected)
        else:
            selected["last_step"] = max(int(selected["last_step"]), value.last_step)
            selected["last_reusable"] = value.reusable
        selected["symbols"].append(value.symbol)

    return tuple(
        BufferBinding(
            buffer_id=str(buffer["buffer_id"]),
            symbols=tuple(buffer["symbols"]),
            dtype=str(buffer["dtype"]),
            layout=str(buffer["layout"]),
            device=str(buffer["device"]),
            capacity_bytes=buffer["capacity_bytes"],
            first_step=int(buffer["first_step"]),
            last_step=int(buffer["last_step"]),
        )
        for buffer in state
    )


def _peak_reserved_bytes(buffers: tuple[BufferBinding, ...]) -> int | None:
    if any(buffer.capacity_bytes is None for buffer in buffers):
        return None
    return sum(int(buffer.capacity_bytes) for buffer in buffers if buffer.capacity_bytes is not None)


def plan_memory(
    graph: Graph,
    symbol_types: Mapping[str, TensorType] | None = None,
    *,
    mode: str = "optimized",
    proposer: str = "deterministic-planner",
    confidence: float | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> MemoryPlan:
    if mode not in {"optimized", "conservative"}:
        raise ResourcePlanningError("planner mode must be optimized or conservative", context={"mode": mode})
    analysis = analyze_resources(graph, symbol_types)
    buffers = _plan_buffers(analysis, mode=mode)
    transfers, transfer_obligations = _required_transfers(graph, analysis)
    return MemoryPlan(
        graph_semantic_hash=analysis.graph_semantic_hash,
        schedule=analysis.schedule,
        lifetimes=tuple(analysis.values[name] for name in sorted(analysis.values)),
        buffers=buffers,
        transfers=transfers,
        obligations=analysis.obligations + transfer_obligations,
        peak_reserved_bytes=_peak_reserved_bytes(buffers),
        verification_mode=mode,
        proposer=proposer,
        confidence=confidence,
        provenance=provenance or {},
    )


def conservative_memory_plan(
    graph: Graph,
    symbol_types: Mapping[str, TensorType] | None = None,
    *,
    proposer: str = "conservative-fallback",
) -> MemoryPlan:
    return plan_memory(graph, symbol_types, mode="conservative", proposer=proposer)


def encode_memory_plan(plan: MemoryPlan) -> str:
    return json.dumps(plan.to_record(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _decode_resource_obligation(value: Mapping[str, Any]) -> ResourceObligation:
    return ResourceObligation(
        kind=str(value.get("kind", "")),
        symbol=str(value.get("symbol", "")),
        message=str(value.get("message", "")),
        runtime_guard=bool(value.get("runtime_guard", True)),
        context=dict(value.get("context", {}) or {}),
    )


def _decode_value_lifetime(value: Mapping[str, Any]) -> ValueLifetime:
    raw_type = value.get("tensor_type")
    tensor_type = TensorType.from_record(raw_type) if isinstance(raw_type, Mapping) else None
    try:
        ownership = OwnershipState(str(value.get("ownership", "owned")))
    except ValueError as exc:
        raise ResourcePlanningError(
            "invalid ownership state in memory plan",
            context={"ownership": value.get("ownership")},
        ) from exc
    return ValueLifetime(
        symbol=str(value.get("symbol", "")),
        producer_node=None if value.get("producer_node") is None else str(value.get("producer_node")),
        first_step=int(value.get("first_step", 0)),
        last_step=int(value.get("last_step", 0)),
        ownership=ownership,
        tensor_type=tensor_type,
        size_bytes=None if value.get("size_bytes") is None else int(value.get("size_bytes")),
        device=str(value.get("device", "unknown")),
        layout=str(value.get("layout", "unknown")),
        external=bool(value.get("external", False)),
        graph_output=bool(value.get("graph_output", False)),
        reusable=bool(value.get("reusable", False)),
    )


def decode_memory_plan(source: str | bytes | Mapping[str, Any]) -> MemoryPlan:
    if isinstance(source, bytes):
        raw: Any = json.loads(source.decode("utf-8"))
    elif isinstance(source, str):
        raw = json.loads(source)
    elif isinstance(source, Mapping):
        raw = dict(source)
    else:
        raise ResourcePlanningError("unsupported memory-plan source type")
    if not isinstance(raw, Mapping) or raw.get("kind") != "memory_plan":
        raise ResourcePlanningError("invalid memory-plan record")

    buffers = tuple(
        BufferBinding(
            buffer_id=str(item.get("buffer_id", "")),
            symbols=tuple(str(v) for v in item.get("symbols", ())),
            dtype=str(item.get("dtype", "unknown")),
            layout=str(item.get("layout", "unknown")),
            device=str(item.get("device", "unknown")),
            capacity_bytes=None if item.get("capacity_bytes") is None else int(item.get("capacity_bytes")),
            first_step=int(item.get("first_step", 0)),
            last_step=int(item.get("last_step", 0)),
        )
        for item in raw.get("buffers", ())
        if isinstance(item, Mapping)
    )
    transfers = tuple(
        DeviceTransfer(
            symbol=str(item.get("symbol", "")),
            source_device=str(item.get("source_device", "unknown")),
            target_device=str(item.get("target_device", "unknown")),
            before_node=str(item.get("before_node", "")),
            reason=str(item.get("reason", "device mismatch")),
        )
        for item in raw.get("transfers", ())
        if isinstance(item, Mapping)
    )
    lifetimes = tuple(
        _decode_value_lifetime(item)
        for item in raw.get("lifetimes", ())
        if isinstance(item, Mapping)
    )
    obligations = tuple(
        _decode_resource_obligation(item)
        for item in raw.get("obligations", ())
        if isinstance(item, Mapping)
    )
    return MemoryPlan(
        graph_semantic_hash=str(raw.get("graph_semantic_hash", "")),
        schedule=tuple(str(v) for v in raw.get("schedule", ())),
        lifetimes=lifetimes,
        buffers=buffers,
        transfers=transfers,
        obligations=obligations,
        peak_reserved_bytes=None if raw.get("peak_reserved_bytes") is None else int(raw.get("peak_reserved_bytes")),
        verification_mode=str(raw.get("verification_mode", "external")),
        proposer=str(raw.get("proposer", "external")),
        confidence=None if raw.get("confidence") is None else float(raw.get("confidence")),
        provenance=dict(raw.get("provenance", {}) or {}),
    )


def decode_symbol_types(value: Mapping[str, Any]) -> dict[str, TensorType]:
    result: dict[str, TensorType] = {}
    for name, record in value.items():
        if not isinstance(record, Mapping) or record.get("kind") != "tensor_type":
            raise ResourcePlanningError(
                "symbol type record must be a tensor_type",
                context={"symbol": str(name)},
            )
        try:
            result[str(name)] = TensorType.from_record(record)
        except Exception as exc:
            if isinstance(exc, ResourcePlanningError):
                raise
            raise ResourcePlanningError(
                "failed to decode symbol tensor type",
                context={"symbol": str(name), "error": type(exc).__name__},
            ) from exc
    return result

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from .errors import MissingInputError, RuntimeShapeError
from .shape import ShapeSolver
from .types import TensorType


def _freeze_map(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


@dataclass(frozen=True)
class ExecutionEnvironment:
    inputs: Mapping[str, Any] = field(default_factory=dict)
    parameters: Mapping[str, Any] = field(default_factory=dict)
    shape_solver: ShapeSolver = field(default_factory=ShapeSolver, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "inputs", _freeze_map(self.inputs))
        object.__setattr__(self, "parameters", _freeze_map(self.parameters))

    def resolve(self, name: str) -> Any:
        if name in self.inputs:
            return self.inputs[name]
        if name in self.parameters:
            return self.parameters[name]
        raise MissingInputError(
            f"runtime value not found: {name}",
            context={"name": name},
        )


@dataclass(frozen=True)
class TraceRecord:
    node_id: str
    kind: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    result_shape: tuple[int, ...] | None
    result_type: str


@dataclass(frozen=True)
class ExecutionTrace:
    records: tuple[TraceRecord, ...] = ()

    def append(
        self,
        *,
        node_id: str,
        kind: str,
        inputs: tuple[str, ...],
        outputs: tuple[str, ...],
        result: Any,
    ) -> "ExecutionTrace":
        raw_shape = getattr(result, "shape", None)
        shape = tuple(int(v) for v in raw_shape) if raw_shape is not None else ()
        record = TraceRecord(
            node_id=node_id,
            kind=kind,
            inputs=tuple(inputs),
            outputs=tuple(outputs),
            result_shape=shape,
            result_type=type(result).__name__,
        )
        return ExecutionTrace(self.records + (record,))


@dataclass(frozen=True)
class ExecutionResult:
    outputs: Mapping[str, Any]
    trace: ExecutionTrace = ExecutionTrace()

    def __post_init__(self) -> None:
        object.__setattr__(self, "outputs", _freeze_map(self.outputs))


def validate_runtime_value(
    value: Any,
    expected: TensorType | None,
    *,
    solver: ShapeSolver | None = None,
    source: str = "",
) -> Any:
    if expected is None:
        return value
    solver = solver or ShapeSolver()
    raw_shape = getattr(value, "shape", None)
    observed = tuple(int(v) for v in raw_shape) if raw_shape is not None else ()
    if len(observed) != expected.rank:
        raise RuntimeShapeError(
            "runtime tensor rank mismatch",
            context={
                "source": source,
                "expected_rank": expected.rank,
                "observed_rank": len(observed),
                "expected": [dim.concrete_value if dim.is_concrete else dim.symbols[0] if len(dim.symbols) == 1 and dim.const == 0 else dim.to_record() for dim in expected.shape],
                "observed": list(observed),
            },
        )
    try:
        for dim, actual in zip(expected.shape, observed):
            solver.add_equal(dim, actual, reason=f"runtime shape guard for {source or '<value>'}")
    except Exception as exc:
        if isinstance(exc, RuntimeShapeError):
            raise
        raise RuntimeShapeError(
            "runtime tensor shape mismatch",
            context={
                "source": source,
                "expected": [dim.concrete_value if dim.is_concrete else dim.symbols[0] if len(dim.symbols) == 1 and dim.const == 0 else dim.to_record() for dim in expected.shape],
                "observed": list(observed),
            },
        ) from exc
    return value

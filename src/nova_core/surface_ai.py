from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .errors import ValidationError
from .model import Graph, Module, Node, Project, SchemaHeader

AI_SURFACE_FORMAT = "nova.ai-plan/0.8"


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValidationError(f"{label} must be a mapping")
    return value


def _tensor_type(raw: Any) -> Any:
    if raw is None:
        return None
    data = _mapping(raw, "AI tensor contract")
    dtype = str(data.get("dtype", ""))
    if not dtype:
        raise ValidationError("AI tensor dtype is required")
    raw_dims = data.get("dims", ())
    if not isinstance(raw_dims, (list, tuple)):
        raise ValidationError("AI tensor dims must be a sequence")
    dims = []
    for dim in raw_dims:
        if isinstance(dim, int) and not isinstance(dim, bool):
            dims.append({"kind": "affine_dim", "const": dim, "terms": []})
        elif isinstance(dim, Mapping) and "binder" in dim:
            dims.append({"kind": "affine_dim", "const": int(dim.get("const", 0)), "terms": [[str(dim["binder"]), int(dim.get("coefficient", 1))]]})
        else:
            raise ValidationError("AI tensor dimension is invalid", context={"dimension": dim})
    return {
        "kind": "tensor_type",
        "dtype": dtype,
        "shape": {"kind": "shape", "dims": dims},
        "layout": str(data.get("layout", "dense")),
        "device": str(data.get("device", "cpu")),
    }


def lower_ai_surface(source: str | Mapping[str, Any]) -> Project:
    """Lower an AI-native structured construction plan directly to NOVA.

    References are typed as either {input: <slot>} or {value: <binding>}.
    This path does not parse the text or graph surface grammars.
    """
    if isinstance(source, str):
        try:
            source = json.loads(source)
        except json.JSONDecodeError as exc:
            raise ValidationError("AI surface JSON is invalid", context={"message": exc.msg}) from exc
    data = _mapping(source, "AI surface")
    if data.get("format") != AI_SURFACE_FORMAT:
        raise ValidationError("unsupported AI surface format", context={"format": data.get("format")})

    raw_inputs = data.get("inputs", ())
    if not isinstance(raw_inputs, (list, tuple)):
        raise ValidationError("AI surface inputs must be a sequence")
    slots: dict[int, str] = {}
    ordered: list[tuple[int, str]] = []
    for raw in raw_inputs:
        entry = _mapping(raw, "AI input")
        slot = int(entry.get("slot", -1))
        label = str(entry.get("label", ""))
        if slot < 0 or not label or slot in slots:
            raise ValidationError("AI input slot/label is invalid", context={"entry": dict(entry)})
        slots[slot] = label
        ordered.append((slot, label))
    ordered.sort(key=lambda pair: pair[0])
    if [slot for slot, _ in ordered] != list(range(len(ordered))):
        raise ValidationError("AI input slots must be dense from zero")
    graph_inputs = tuple(label for _, label in ordered)

    bindings: dict[str, str] = {}
    nodes: list[Node] = []

    def resolve(ref: Any) -> str:
        entry = _mapping(ref, "AI value reference")
        if set(entry) == {"input"}:
            slot = int(entry["input"])
            if slot not in slots:
                raise ValidationError("AI plan references unknown input slot", context={"slot": slot})
            return slots[slot]
        if set(entry) == {"value"}:
            key = str(entry["value"])
            if key not in bindings:
                raise ValidationError("AI plan references unknown value binding", context={"value": key})
            return bindings[key]
        raise ValidationError("AI value reference must contain exactly input or value")

    raw_steps = data.get("steps", ())
    if not isinstance(raw_steps, (list, tuple)):
        raise ValidationError("AI surface steps must be a sequence")
    for index, raw in enumerate(raw_steps):
        step = _mapping(raw, "AI step")
        op = str(step.get("operator", ""))
        bind = str(step.get("bind", ""))
        step_id = str(step.get("step", f"ai_step_{index}"))
        if not op or not bind or bind in bindings:
            raise ValidationError("AI step operator/bind is invalid", context={"step": dict(step)})
        raw_args = step.get("args", ())
        if not isinstance(raw_args, (list, tuple)):
            raise ValidationError("AI step args must be a sequence")
        args = tuple(resolve(ref) for ref in raw_args)
        internal_value = f"ai_value_{index}"
        nodes.append(Node(id=step_id, kind=op, inputs=args, outputs=(internal_value,), value_type=_tensor_type(step.get("tensor"))))
        bindings[bind] = internal_value

    raw_outputs = data.get("outputs", ())
    if not isinstance(raw_outputs, (list, tuple)):
        raise ValidationError("AI surface outputs must be a sequence")
    graph_outputs = tuple(resolve(ref) for ref in raw_outputs)
    graph = Graph(
        id=str(data.get("graph", "ai_generated_graph")),
        inputs=graph_inputs,
        outputs=graph_outputs,
        nodes=tuple(nodes),
    )
    return Project(
        header=SchemaHeader(feature_flags=("cross-representation-v0.8",)),
        modules=(Module(id=str(data.get("module", "ai_surface_module")), graphs=(graph,)),),
    )


__all__ = ["AI_SURFACE_FORMAT", "lower_ai_surface"]

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .errors import ValidationError
from .model import Graph, Module, Node, Project, SchemaHeader

GRAPH_SURFACE_FORMAT = "nova.graph-surface/0.8"


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValidationError(f"{label} must be a mapping")
    return value


def _seq_str(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValidationError(f"{label} must be a sequence")
    result = tuple(str(v) for v in value)
    if any(not item for item in result):
        raise ValidationError(f"{label} contains empty value")
    return result


def _tensor_type(raw: Any) -> Any:
    if raw is None:
        return None
    data = _mapping(raw, "graph-surface tensor")
    dtype = str(data.get("dtype", ""))
    if not dtype:
        raise ValidationError("graph-surface tensor dtype is required")
    shape = data.get("shape", ())
    if not isinstance(shape, (list, tuple)):
        raise ValidationError("graph-surface tensor shape must be a sequence")
    dims = []
    for dim in shape:
        if isinstance(dim, int) and not isinstance(dim, bool):
            dims.append({"kind": "affine_dim", "const": dim, "terms": []})
        elif isinstance(dim, Mapping) and "symbol" in dim:
            dims.append({"kind": "affine_dim", "const": int(dim.get("const", 0)), "terms": [[str(dim["symbol"]), int(dim.get("coefficient", 1))]]})
        else:
            raise ValidationError("graph-surface tensor dimension is invalid", context={"dimension": dim})
    return {
        "kind": "tensor_type",
        "dtype": dtype,
        "shape": {"kind": "shape", "dims": dims},
        "layout": str(data.get("layout", "dense")),
        "device": str(data.get("device", "cpu")),
    }


def lower_graph_surface(source: str | Mapping[str, Any]) -> Project:
    """Lower a graph-native exchange object directly into a NOVA Project."""
    if isinstance(source, str):
        try:
            source = json.loads(source)
        except json.JSONDecodeError as exc:
            raise ValidationError("graph surface JSON is invalid", context={"message": exc.msg}) from exc
    data = _mapping(source, "graph surface")
    if data.get("format") != GRAPH_SURFACE_FORMAT:
        raise ValidationError("unsupported graph surface format", context={"format": data.get("format")})
    graph_data = _mapping(data.get("graph"), "graph surface graph")
    inputs = _seq_str(graph_data.get("inputs", ()), "graph inputs")
    outputs = _seq_str(graph_data.get("outputs", ()), "graph outputs")
    raw_nodes = graph_data.get("nodes", ())
    if not isinstance(raw_nodes, (list, tuple)):
        raise ValidationError("graph surface nodes must be a sequence")

    nodes: list[Node] = []
    ids: set[str] = set()
    produced = set(inputs)
    for raw in raw_nodes:
        node_data = _mapping(raw, "graph surface node")
        node_id = str(node_data.get("key", ""))
        op = str(node_data.get("op", ""))
        if not node_id or not op:
            raise ValidationError("graph surface node key/op are required")
        if node_id in ids:
            raise ValidationError("graph surface node key is duplicated", context={"key": node_id})
        ids.add(node_id)
        args = _seq_str(node_data.get("args", ()), "graph node args")
        binds = _seq_str(node_data.get("bind", ()), "graph node bind")
        if len(binds) != 1:
            raise ValidationError("v0.8 graph surface node must bind exactly one value")
        if binds[0] in produced:
            raise ValidationError("graph surface value producer is duplicated", context={"value": binds[0]})
        nodes.append(Node(id=node_id, kind=op, inputs=args, outputs=binds, value_type=_tensor_type(node_data.get("tensor"))))
        produced.add(binds[0])

    all_values = set(inputs)
    all_values.update(value for node in nodes for value in node.outputs)
    for node in nodes:
        missing = tuple(arg for arg in node.inputs if arg not in all_values)
        if missing:
            raise ValidationError("graph surface contains unresolved node argument", context={"node": node.id, "missing": missing})
    missing_outputs = tuple(value for value in outputs if value not in all_values)
    if missing_outputs:
        raise ValidationError("graph surface output is unresolved", context={"missing": missing_outputs})

    graph = Graph(
        id=str(graph_data.get("name", "graph_native")),
        inputs=inputs,
        outputs=outputs,
        nodes=tuple(nodes),
    )
    return Project(
        header=SchemaHeader(feature_flags=("cross-representation-v0.8",)),
        modules=(Module(id=str(data.get("module", "graph_surface_module")), graphs=(graph,)),),
    )


__all__ = ["GRAPH_SURFACE_FORMAT", "lower_graph_surface"]

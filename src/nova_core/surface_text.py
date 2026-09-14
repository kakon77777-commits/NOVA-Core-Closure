from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .errors import ValidationError
from .model import Graph, Module, Node, Project, SchemaHeader

TEXT_SURFACE_FORMAT = "nova.text-surface/0.8"

_IDENT = r"[A-Za-z_][A-Za-z0-9_]*"
_GRAPH_RE = re.compile(rf"^graph\s+({_IDENT})\s*\(([^)]*)\)\s*->\s*\(([^)]*)\)\s*$")
_STMT_RE = re.compile(rf"^({_IDENT})\s*=\s*({_IDENT})\s*\(([^)]*)\)\s*(?:::\s*({_IDENT})\s*\[([^]]*)\])?\s*$")


def _split_names(raw: str) -> tuple[str, ...]:
    if not raw.strip():
        return ()
    names = tuple(part.strip() for part in raw.split(","))
    if any(not re.fullmatch(_IDENT, name) for name in names):
        raise ValidationError("text surface contains invalid identifier", context={"value": raw})
    if len(set(names)) != len(names):
        raise ValidationError("text surface contains duplicate identifier", context={"value": raw})
    return names


def _tensor_type(dtype: str, dims_text: str) -> dict[str, Any]:
    dims: list[dict[str, Any]] = []
    for raw in [part.strip() for part in dims_text.split(",") if part.strip()]:
        if re.fullmatch(r"[0-9]+", raw):
            dims.append({"kind": "affine_dim", "const": int(raw), "terms": []})
        elif re.fullmatch(_IDENT, raw):
            dims.append({"kind": "affine_dim", "const": 0, "terms": [[raw, 1]]})
        else:
            raise ValidationError("text surface tensor dimension is outside v0.8 grammar", context={"dimension": raw})
    return {
        "kind": "tensor_type",
        "dtype": dtype,
        "shape": {"kind": "shape", "dims": dims},
        "layout": "dense",
        "device": "cpu",
    }


def lower_text_surface(source: str) -> Project:
    """Lower the bounded human text surface directly into a NOVA Project.

    This parser is intentionally not Python-like and never uses eval/exec. The
    accepted v0.8 grammar contains one graph declaration plus assignment lines.
    """
    if not isinstance(source, str) or not source.strip():
        raise ValidationError("text surface must be non-empty UTF-8 text")
    lines: list[str] = []
    for raw in source.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    if not lines:
        raise ValidationError("text surface has no program lines")

    header = _GRAPH_RE.fullmatch(lines[0])
    if header is None:
        raise ValidationError("text surface must start with graph <id>(...) -> (...)")
    graph_name, raw_inputs, raw_outputs = header.groups()
    graph_inputs = _split_names(raw_inputs)
    graph_outputs = _split_names(raw_outputs)

    available = set(graph_inputs)
    nodes: list[Node] = []
    produced: set[str] = set()
    for index, line in enumerate(lines[1:]):
        match = _STMT_RE.fullmatch(line)
        if match is None:
            raise ValidationError("text surface statement is outside v0.8 grammar", context={"line": line})
        output, operator, raw_args, dtype, dims = match.groups()
        args = _split_names(raw_args)
        missing = tuple(arg for arg in args if arg not in available)
        if missing:
            raise ValidationError("text surface references unresolved value", context={"line": line, "missing": missing})
        if output in available or output in produced:
            raise ValidationError("text surface output shadows existing value", context={"value": output})
        value_type = None if dtype is None else _tensor_type(dtype, dims or "")
        node = Node(
            id=f"text_step_{index}",
            kind=operator,
            inputs=args,
            outputs=(output,),
            value_type=value_type,
        )
        nodes.append(node)
        produced.add(output)
        available.add(output)

    missing_outputs = tuple(name for name in graph_outputs if name not in available)
    if missing_outputs:
        raise ValidationError("text surface graph output is unresolved", context={"missing": missing_outputs})

    graph = Graph(id=graph_name, inputs=graph_inputs, outputs=graph_outputs, nodes=tuple(nodes))
    return Project(
        header=SchemaHeader(feature_flags=("cross-representation-v0.8",)),
        modules=(Module(id="text_surface_module", graphs=(graph,)),),
    )


__all__ = ["TEXT_SURFACE_FORMAT", "lower_text_surface"]

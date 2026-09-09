from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping
import hashlib
import json

from .canonical import semantic_hash
from .errors import DiffError, ValidationError
from .model import Graph, Node, validate_graph
from .types import TensorType


@dataclass(frozen=True)
class DifferentiationRequest:
    target: str
    wrt: tuple[str, ...]
    seed_input: str | None = None
    derivative_graph_id: str | None = None

    def __post_init__(self) -> None:
        target = str(self.target)
        wrt = tuple(str(v) for v in self.wrt)
        if not target:
            raise ValidationError("differentiation target must not be empty")
        if not wrt or any(not value for value in wrt):
            raise ValidationError("differentiation wrt must contain at least one non-empty symbol")
        if len(set(wrt)) != len(wrt):
            raise ValidationError("differentiation wrt symbols must be unique")
        seed = None if self.seed_input is None else str(self.seed_input)
        if seed == "":
            raise ValidationError("seed_input must not be empty when provided")
        graph_id = None if self.derivative_graph_id is None else str(self.derivative_graph_id)
        if graph_id == "":
            raise ValidationError("derivative_graph_id must not be empty when provided")
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "wrt", wrt)
        object.__setattr__(self, "seed_input", seed)
        object.__setattr__(self, "derivative_graph_id", graph_id)


@dataclass(frozen=True)
class DerivativeGraphResult:
    graph: Graph
    target: str
    gradients: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "target", str(self.target))
        object.__setattr__(self, "gradients", MappingProxyType({str(k): str(v) for k, v in self.gradients.items()}))


def gradient_symbol(symbol: str) -> str:
    value = str(symbol)
    if not value:
        raise ValidationError("gradient source symbol must not be empty")
    return f"__nova_grad__{value}"


def derivative_graph_id(graph: Graph, request: DifferentiationRequest) -> str:
    if request.derivative_graph_id is not None:
        return request.derivative_graph_id
    payload = json.dumps(
        {
            "graph": graph.id,
            "target": request.target,
            "wrt": list(request.wrt),
            "seed_input": request.seed_input,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    suffix = hashlib.sha256(payload).hexdigest()[:12]
    return f"{graph.id}__rev__{request.target}__{suffix}"


def _topological_nodes(graph: Graph) -> tuple[Node, ...]:
    available = set(graph.inputs)
    pending = {node.id: node for node in graph.nodes}
    ordered: list[Node] = []
    while pending:
        ready = [node for node in pending.values() if all(name in available for name in node.inputs)]
        if not ready:
            raise DiffError(
                "cannot differentiate graph with cyclic or unresolved dependencies",
                source_nodes=tuple(sorted(pending)),
            )
        for node in sorted(ready, key=lambda item: item.id):
            ordered.append(node)
            available.update(node.outputs)
            del pending[node.id]
    return tuple(ordered)


class _ADBuilder:
    def __init__(self, graph: Graph) -> None:
        self.nodes: list[Node] = list(graph.nodes)
        self._node_ids = {node.id for node in graph.nodes}
        self._symbols = set(graph.inputs)
        for node in graph.nodes:
            self._symbols.update(node.outputs)
        self._counter = 0

    def _next(self, kind: str) -> tuple[str, str]:
        stem = "".join(ch.lower() if ch.isalnum() else "_" for ch in kind).strip("_") or "value"
        while True:
            index = self._counter
            self._counter += 1
            node_id = f"__ad__{index:04d}__{stem}"
            output = f"__ad_value__{index:04d}"
            if node_id not in self._node_ids and output not in self._symbols:
                self._node_ids.add(node_id)
                self._symbols.add(output)
                return node_id, output

    def emit(
        self,
        kind: str,
        inputs: tuple[str, ...] = (),
        *,
        attributes: Mapping[str, object] | None = None,
        output: str | None = None,
        value_type: object = None,
        differentiation_type: object = "Differentiable",
    ) -> str:
        node_id, generated_output = self._next(kind)
        if output is None:
            output = generated_output
        else:
            if output in self._symbols:
                raise DiffError(
                    "autodiff output symbol collides with primal graph",
                    context={"symbol": output},
                )
            self._symbols.remove(generated_output)
            self._symbols.add(output)
        self.nodes.append(
            Node(
                id=node_id,
                kind=kind,
                inputs=inputs,
                outputs=(output,),
                value_type=value_type,
                differentiation_type=differentiation_type,
                attributes=dict(attributes or {}),
                provenance={"generated_by": "nova_core.autodiff"},
            )
        )
        return output

    def accumulate(self, symbol: str, contributions: list[str]) -> str:
        if not contributions:
            raise DiffError("cannot accumulate an empty cotangent list", context={"symbol": symbol})
        current = contributions[0]
        for contribution in contributions[1:]:
            current = self.emit(
                "Add",
                (current, contribution),
                attributes={"ad_role": "accumulate", "symbol": symbol},
            )
        return current


def _reduce_to_shape(builder: _ADBuilder, grad: str, reference: str, *, source: str) -> str:
    return builder.emit(
        "ADReduceToShape",
        (grad, reference),
        attributes={"ad_role": "unbroadcast", "source_symbol": source},
    )


def _rule_identity(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    return [(node.inputs[0], gout)]


def _rule_add(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    return [
        (node.inputs[0], _reduce_to_shape(builder, gout, node.inputs[0], source=node.inputs[0])),
        (node.inputs[1], _reduce_to_shape(builder, gout, node.inputs[1], source=node.inputs[1])),
    ]


def _rule_subtract(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    right = builder.emit("Negate", (gout,), attributes={"ad_role": "vjp", "source_node": node.id})
    return [
        (node.inputs[0], _reduce_to_shape(builder, gout, node.inputs[0], source=node.inputs[0])),
        (node.inputs[1], _reduce_to_shape(builder, right, node.inputs[1], source=node.inputs[1])),
    ]


def _rule_multiply(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    left_raw = builder.emit("Multiply", (gout, node.inputs[1]), attributes={"ad_role": "vjp", "source_node": node.id})
    right_raw = builder.emit("Multiply", (gout, node.inputs[0]), attributes={"ad_role": "vjp", "source_node": node.id})
    return [
        (node.inputs[0], _reduce_to_shape(builder, left_raw, node.inputs[0], source=node.inputs[0])),
        (node.inputs[1], _reduce_to_shape(builder, right_raw, node.inputs[1], source=node.inputs[1])),
    ]


def _rule_divide(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    left_raw = builder.emit("Divide", (gout, node.inputs[1]), attributes={"ad_role": "vjp", "source_node": node.id})
    denom_sq = builder.emit("Multiply", (node.inputs[1], node.inputs[1]), attributes={"ad_role": "vjp", "source_node": node.id})
    numerator = builder.emit("Multiply", (gout, node.inputs[0]), attributes={"ad_role": "vjp", "source_node": node.id})
    quotient = builder.emit("Divide", (numerator, denom_sq), attributes={"ad_role": "vjp", "source_node": node.id})
    right_raw = builder.emit("Negate", (quotient,), attributes={"ad_role": "vjp", "source_node": node.id})
    return [
        (node.inputs[0], _reduce_to_shape(builder, left_raw, node.inputs[0], source=node.inputs[0])),
        (node.inputs[1], _reduce_to_shape(builder, right_raw, node.inputs[1], source=node.inputs[1])),
    ]


def _rule_negate(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    return [(node.inputs[0], builder.emit("Negate", (gout,), attributes={"ad_role": "vjp", "source_node": node.id}))]


def _rule_matmul(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    right_t = builder.emit("ADTransposeLast2", (node.inputs[1],), attributes={"ad_role": "vjp", "source_node": node.id})
    left_t = builder.emit("ADTransposeLast2", (node.inputs[0],), attributes={"ad_role": "vjp", "source_node": node.id})
    left_raw = builder.emit("MatMul", (gout, right_t), attributes={"ad_role": "vjp", "source_node": node.id})
    right_raw = builder.emit("MatMul", (left_t, gout), attributes={"ad_role": "vjp", "source_node": node.id})
    return [
        (node.inputs[0], _reduce_to_shape(builder, left_raw, node.inputs[0], source=node.inputs[0])),
        (node.inputs[1], _reduce_to_shape(builder, right_raw, node.inputs[1], source=node.inputs[1])),
    ]


def _rule_reshape(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    return [(node.inputs[0], builder.emit("ADReshapeLike", (gout, node.inputs[0]), attributes={"ad_role": "vjp", "source_node": node.id}))]


def _rule_transpose(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    axes = node.attributes.get("axes")
    inverse = None
    if axes is not None:
        try:
            axes_tuple = tuple(int(v) for v in axes)
        except Exception as exc:
            raise DiffError("Transpose axes are invalid for reverse-mode AD", source_nodes=(node.id,)) from exc
        if sorted(axes_tuple) != list(range(len(axes_tuple))):
            raise DiffError("Transpose axes must be a permutation", source_nodes=(node.id,), context={"axes": list(axes_tuple)})
        inv = [0] * len(axes_tuple)
        for index, axis in enumerate(axes_tuple):
            inv[axis] = index
        inverse = inv
    result = builder.emit("Transpose", (gout,), attributes={"axes": inverse, "ad_role": "vjp", "source_node": node.id})
    return [(node.inputs[0], result)]


def _rule_reduce_sum(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    result = builder.emit(
        "ADBroadcastLike",
        (gout, node.inputs[0]),
        attributes={
            "axis": node.attributes.get("axis"),
            "keepdims": bool(node.attributes.get("keepdims", False)),
            "ad_role": "vjp",
            "source_node": node.id,
        },
    )
    return [(node.inputs[0], result)]


def _rule_mean(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    result = builder.emit(
        "ADMeanGrad",
        (gout, node.inputs[0]),
        attributes={
            "axis": node.attributes.get("axis"),
            "keepdims": bool(node.attributes.get("keepdims", False)),
            "ad_role": "vjp",
            "source_node": node.id,
        },
    )
    return [(node.inputs[0], result)]


def _rule_relu(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    result = builder.emit("ADReluGrad", (gout, node.inputs[0]), attributes={"ad_role": "vjp", "source_node": node.id})
    return [(node.inputs[0], result)]


def _rule_sigmoid(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    y = node.outputs[0]
    one = builder.emit("Constant", (), attributes={"value": 1.0, "ad_role": "constant"})
    one_minus = builder.emit("Subtract", (one, y), attributes={"ad_role": "vjp", "source_node": node.id})
    local = builder.emit("Multiply", (y, one_minus), attributes={"ad_role": "vjp", "source_node": node.id})
    result = builder.emit("Multiply", (gout, local), attributes={"ad_role": "vjp", "source_node": node.id})
    return [(node.inputs[0], result)]


def _rule_tanh(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    y = node.outputs[0]
    y_sq = builder.emit("Multiply", (y, y), attributes={"ad_role": "vjp", "source_node": node.id})
    one = builder.emit("Constant", (), attributes={"value": 1.0, "ad_role": "constant"})
    local = builder.emit("Subtract", (one, y_sq), attributes={"ad_role": "vjp", "source_node": node.id})
    result = builder.emit("Multiply", (gout, local), attributes={"ad_role": "vjp", "source_node": node.id})
    return [(node.inputs[0], result)]


def _rule_softmax(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    y = node.outputs[0]
    axis = int(node.attributes.get("axis", -1))
    weighted = builder.emit("Multiply", (gout, y), attributes={"ad_role": "vjp", "source_node": node.id})
    reduced = builder.emit(
        "ReduceSum",
        (weighted,),
        attributes={"axis": axis, "keepdims": True, "ad_role": "vjp", "source_node": node.id},
    )
    centered = builder.emit("Subtract", (gout, reduced), attributes={"ad_role": "vjp", "source_node": node.id})
    result = builder.emit("Multiply", (y, centered), attributes={"ad_role": "vjp", "source_node": node.id})
    return [(node.inputs[0], result)]


def _rule_stop_gradient(builder: _ADBuilder, node: Node, gout: str) -> list[tuple[str, str]]:
    return []


VJPRule = Callable[[_ADBuilder, Node, str], list[tuple[str, str]]]
VJP_RULES: dict[str, VJPRule] = {
    "Identity": _rule_identity,
    "Add": _rule_add,
    "Subtract": _rule_subtract,
    "Multiply": _rule_multiply,
    "Divide": _rule_divide,
    "Negate": _rule_negate,
    "MatMul": _rule_matmul,
    "Reshape": _rule_reshape,
    "Transpose": _rule_transpose,
    "ReduceSum": _rule_reduce_sum,
    "Mean": _rule_mean,
    "Relu": _rule_relu,
    "Sigmoid": _rule_sigmoid,
    "Tanh": _rule_tanh,
    "Softmax": _rule_softmax,
    "StopGradient": _rule_stop_gradient,
}

_LEAF_KINDS = {"Input", "Parameter", "Constant"}


def _symbol_producers(graph: Graph) -> dict[str, Node]:
    out: dict[str, Node] = {}
    for node in graph.nodes:
        for symbol in node.outputs:
            out[symbol] = node
    return out


def _all_symbols(graph: Graph) -> set[str]:
    out = set(graph.inputs)
    for node in graph.nodes:
        out.update(node.outputs)
    return out


def _target_is_static_scalar(target: str, producers: Mapping[str, Node]) -> bool:
    node = producers.get(target)
    if node is None:
        return False
    if isinstance(node.value_type, TensorType):
        return node.value_type.rank == 0
    if node.kind == "Constant":
        value = node.attributes.get("value")
        return isinstance(value, (bool, int, float, complex))
    return False


def _check_active_node(node: Node) -> None:
    if node.kind == "StopGradient":
        return
    diff = "" if node.differentiation_type is None else str(node.differentiation_type)
    if diff in {"NonDifferentiable", "non_differentiable", "nondifferentiable"}:
        raise DiffError(
            "active reverse path contains a non-differentiable node",
            source_nodes=(node.id,),
            context={"kind": node.kind, "differentiation_type": diff},
            repair_candidates=("insert StopGradient", "provide a supported differentiable replacement"),
        )
    if diff in {"UnknownDifferentiability", "unknown", "unknown_differentiability"}:
        raise DiffError(
            "active reverse path has unknown differentiability",
            source_nodes=(node.id,),
            context={"kind": node.kind, "differentiation_type": diff},
            repair_candidates=("provide a differentiation rule", "insert StopGradient"),
        )


def differentiate_graph(graph: Graph, request: DifferentiationRequest) -> DerivativeGraphResult:
    validate_graph(graph)
    ordered = _topological_nodes(graph)
    producers = _symbol_producers(graph)
    symbols = _all_symbols(graph)

    if request.target not in symbols:
        raise DiffError("differentiation target does not exist in graph", context={"target": request.target})
    missing_wrt = [symbol for symbol in request.wrt if symbol not in symbols]
    if missing_wrt:
        raise DiffError("differentiation wrt symbol does not exist in graph", context={"missing_wrt": missing_wrt})

    derivative_inputs = list(graph.inputs)
    builder = _ADBuilder(graph)
    if request.seed_input is None:
        if not _target_is_static_scalar(request.target, producers):
            raise DiffError(
                "non-scalar or statically unknown target requires an explicit VJP seed input",
                context={"target": request.target},
                repair_candidates=("provide seed_input", "attach a scalar TensorType to the target"),
            )
        target_type = producers.get(request.target).value_type if producers.get(request.target) is not None else None
        seed = builder.emit(
            "Constant",
            (),
            attributes={"value": 1.0, "ad_role": "seed", "target": request.target},
            value_type=target_type,
        )
    else:
        seed = request.seed_input
        if seed not in derivative_inputs:
            if seed in symbols:
                raise DiffError(
                    "explicit VJP seed collides with a non-input primal symbol",
                    context={"seed_input": seed},
                )
            derivative_inputs.append(seed)

    contributions: dict[str, list[str]] = {request.target: [seed]}

    for node in reversed(ordered):
        active_outputs = [symbol for symbol in node.outputs if contributions.get(symbol)]
        if not active_outputs:
            continue
        if len(node.outputs) != 1 or len(active_outputs) != 1:
            raise DiffError(
                "Round 04 reverse-mode AD supports one active output per node",
                source_nodes=(node.id,),
                context={"outputs": list(node.outputs), "active_outputs": active_outputs},
            )
        output = active_outputs[0]
        gout = builder.accumulate(output, contributions[output])
        if node.kind in _LEAF_KINDS:
            continue
        _check_active_node(node)
        rule = VJP_RULES.get(node.kind)
        if rule is None:
            raise DiffError(
                "node kind has no Round 04 VJP rule",
                source_nodes=(node.id,),
                context={"kind": node.kind},
                repair_candidates=("register a VJP rule", "insert StopGradient"),
            )
        for input_symbol, cotangent in rule(builder, node, gout):
            contributions.setdefault(input_symbol, []).append(cotangent)

    gradient_outputs: dict[str, str] = {}
    for symbol in request.wrt:
        parts = contributions.get(symbol, [])
        if parts:
            gradient = builder.accumulate(symbol, parts)
        else:
            gradient = builder.emit(
                "ADZeroLike",
                (symbol,),
                attributes={"ad_role": "zero_gradient", "symbol": symbol},
            )
        public_symbol = gradient_symbol(symbol)
        builder.emit(
            "Identity",
            (gradient,),
            output=public_symbol,
            attributes={"ad_role": "gradient_output", "symbol": symbol},
        )
        gradient_outputs[symbol] = public_symbol

    attributes = dict(graph.attributes)
    attributes["autodiff"] = {
        "mode": "reverse",
        "primal_graph_id": graph.id,
        "primal_semantic_hash": semantic_hash(graph),
        "target": request.target,
        "wrt": list(request.wrt),
        "seed_input": request.seed_input,
    }
    provenance = dict(graph.provenance)
    provenance["autodiff_generated"] = True
    provenance["primal_semantic_hash"] = semantic_hash(graph)

    derivative = Graph(
        id=derivative_graph_id(graph, request),
        inputs=tuple(derivative_inputs),
        outputs=tuple(gradient_outputs[symbol] for symbol in request.wrt),
        nodes=tuple(builder.nodes),
        edges=graph.edges,
        constraints=graph.constraints,
        attributes=attributes,
        provenance=provenance,
        extensions=graph.extensions,
    )
    validate_graph(derivative)
    return DerivativeGraphResult(graph=derivative, target=request.target, gradients=gradient_outputs)

from __future__ import annotations

from .errors import ProjectionError
from .model import Graph, Node
from .shape import DimExpr
from .types import TensorType


def _ordered_nodes(graph: Graph) -> tuple[Node, ...]:
    available = set(graph.inputs)
    pending = {node.id: node for node in graph.nodes}
    ordered: list[Node] = []
    while pending:
        ready = [node for node in pending.values() if all(name in available for name in node.inputs)]
        if not ready:
            raise ProjectionError(
                "graph cannot be deterministically projected because dependencies are cyclic or unresolved",
                source_nodes=tuple(sorted(pending)),
            )
        for node in sorted(ready, key=lambda item: item.id):
            ordered.append(node)
            available.update(node.outputs)
            del pending[node.id]
    return tuple(ordered)


def _dim_text(dim: DimExpr) -> str:
    if dim.is_concrete:
        return str(dim.const)
    if dim.const == 0 and len(dim.terms) == 1 and dim.terms[0][1] == 1:
        return dim.terms[0][0]
    chunks: list[str] = []
    if dim.const:
        chunks.append(str(dim.const))
    for name, coeff in dim.terms:
        if coeff == 1:
            chunks.append(name)
        elif coeff == -1:
            chunks.append(f"-{name}")
        else:
            chunks.append(f"{coeff}*{name}")
    return "+".join(chunks).replace("+-", "-") or "0"


def _type_text(value_type: object) -> str:
    if not isinstance(value_type, TensorType):
        return ""
    dims = ",".join(_dim_text(dim) for dim in value_type.shape)
    return f"Tensor[{value_type.dtype}; {dims}]" if dims else f"Tensor[{value_type.dtype}; ]"


def _op_name(kind: str) -> str:
    mapping = {
        "Identity": "identity",
        "Add": "add",
        "Subtract": "subtract",
        "Multiply": "multiply",
        "Divide": "divide",
        "Negate": "negate",
        "MatMul": "matmul",
        "Reshape": "reshape",
        "Transpose": "transpose",
        "ReduceSum": "reduce_sum",
        "Mean": "mean",
        "Relu": "relu",
        "Sigmoid": "sigmoid",
        "Tanh": "tanh",
        "Softmax": "softmax",
        "If": "if",
        "BoundedLoop": "bounded_loop",
        "Call": "call",
        "StopGradient": "stop_gradient",
        "ADReduceToShape": "ad_reduce_to_shape",
        "ADBroadcastLike": "ad_broadcast_like",
        "ADReshapeLike": "ad_reshape_like",
        "ADTransposeLast2": "ad_transpose_last2",
        "ADMeanGrad": "ad_mean_grad",
        "ADReluGrad": "ad_relu_grad",
        "ADZeroLike": "ad_zero_like",
        "Constant": "constant",
        "Parameter": "parameter",
        "Input": "input",
    }
    return mapping.get(kind, kind.lower())


def project_text(graph: Graph) -> str:
    lines = [f"graph {graph.id}"]
    if graph.inputs:
        lines.append("inputs " + ", ".join(graph.inputs))
    for node in _ordered_nodes(graph):
        outputs = ", ".join(node.outputs) if node.outputs else "_"
        args = ", ".join(node.inputs)
        op = _op_name(node.kind)
        if node.kind == "Constant":
            call = f"constant({node.attributes.get('value')!r})"
        elif node.kind == "Parameter":
            call = f"parameter({node.attributes.get('name', outputs)!s})"
        elif node.kind == "Reshape":
            call = f"reshape({args}; shape={list(node.attributes.get('shape', []))})"
        elif node.kind == "Transpose":
            call = f"transpose({args}; axes={list(node.attributes.get('axes', []))})"
        elif node.kind in {"ReduceSum", "Mean", "Softmax"}:
            call = f"{op}({args}; axis={node.attributes.get('axis', -1)})"
        elif node.kind == "BoundedLoop":
            call = f"bounded_loop({args}; trip_count={node.attributes.get('trip_count')}; body={node.attributes.get('body_kind')})"
        elif node.kind in {"ADBroadcastLike", "ADMeanGrad"}:
            call = f"{op}({args}; axis={node.attributes.get('axis')}; keepdims={bool(node.attributes.get('keepdims', False))})"
        else:
            call = f"{op}({args})"
        type_suffix = _type_text(node.value_type)
        if type_suffix:
            lines.append(f"{outputs} = {call} : {type_suffix}")
        else:
            lines.append(f"{outputs} = {call}")
    if graph.outputs:
        lines.append("return " + ", ".join(graph.outputs))
    return "\n".join(lines)



def _formula_operand(expression: str) -> str:
    stripped = expression.strip()
    if stripped.replace("_", "").replace(":", "").isalnum():
        return stripped
    try:
        float(stripped)
        return stripped
    except ValueError:
        return f"({stripped})"

def project_formula(graph: Graph) -> str:
    expr: dict[str, str] = {name: name for name in graph.inputs}
    for node in _ordered_nodes(graph):
        if len(node.outputs) != 1:
            raise ProjectionError(
                "formula projection requires exactly one output per node",
                source_nodes=(node.id,),
            )
        args = [expr.get(name, name) for name in node.inputs]
        kind = node.kind
        if kind == "Identity":
            value = args[0]
        elif kind == "Add":
            value = f"{args[0]} + {args[1]}"
        elif kind == "Subtract":
            value = f"{_formula_operand(args[0])} - {_formula_operand(args[1])}"
        elif kind == "Multiply":
            value = f"{_formula_operand(args[0])} \\odot {_formula_operand(args[1])}"
        elif kind == "Divide":
            value = f"{_formula_operand(args[0])} / {_formula_operand(args[1])}"
        elif kind == "Negate":
            value = f"-{_formula_operand(args[0])}"
        elif kind == "MatMul":
            value = f"({_formula_operand(args[0])} \\cdot {_formula_operand(args[1])})"
        elif kind == "Relu":
            value = f"\\operatorname{{ReLU}}({args[0]})"
        elif kind == "Sigmoid":
            value = f"\\sigma({args[0]})"
        elif kind == "Tanh":
            value = f"\\tanh({args[0]})"
        elif kind == "Softmax":
            value = f"\\operatorname{{softmax}}({args[0]})"
        elif kind == "ReduceSum":
            value = f"\\operatorname{{sum}}_{{{node.attributes.get('axis')}}}({args[0]})"
        elif kind == "Mean":
            value = f"\\operatorname{{mean}}_{{{node.attributes.get('axis')}}}({args[0]})"
        elif kind == "Reshape":
            value = f"\\operatorname{{reshape}}({args[0]})"
        elif kind == "Transpose":
            value = f"\\operatorname{{transpose}}({args[0]})"
        elif kind == "StopGradient":
            value = f"\\operatorname{{stopgrad}}({args[0]})"
        elif kind == "ADReduceToShape":
            value = f"\\operatorname{{reduceToShape}}({args[0]}, {args[1]})"
        elif kind == "ADBroadcastLike":
            value = f"\\operatorname{{broadcastLike}}({args[0]}, {args[1]})"
        elif kind == "ADReshapeLike":
            value = f"\\operatorname{{reshapeLike}}({args[0]}, {args[1]})"
        elif kind == "ADTransposeLast2":
            value = f"\\operatorname{{transposeLast2}}({args[0]})"
        elif kind == "ADMeanGrad":
            value = f"\\operatorname{{meanGrad}}({args[0]}, {args[1]})"
        elif kind == "ADReluGrad":
            value = f"\\operatorname{{reluGrad}}({args[0]}, {args[1]})"
        elif kind == "ADZeroLike":
            value = f"\\operatorname{{zeroLike}}({args[0]})"
        elif kind == "Constant":
            value = str(node.attributes.get("value"))
        elif kind == "Parameter":
            value = str(node.attributes.get("name", node.outputs[0]))
        else:
            raise ProjectionError(
                "node kind is outside the current formula projection subset",
                source_nodes=(node.id,),
                context={"kind": kind},
            )
        expr[node.outputs[0]] = value
    missing = [name for name in graph.outputs if name not in expr]
    if missing:
        raise ProjectionError("formula projection is missing graph outputs", context={"missing": missing})
    return "\n".join(f"{name} = {expr[name]}" for name in graph.outputs)

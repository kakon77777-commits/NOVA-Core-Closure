from __future__ import annotations

import ast
from dataclasses import dataclass, replace
from typing import Any

from .editing import ProjectionEditCandidate, build_projection_edit_candidate
from .errors import FormulaEditError
from .model import Graph, Node, Project
from .shape import Shape
from .types import TensorType


@dataclass(frozen=True)
class ParsedLocalFormula:
    output: str
    kind: str
    inputs: tuple[str, ...]
    attributes: dict[str, Any]


_BINOPS: dict[type[ast.operator], str] = {
    ast.Add: "Add",
    ast.Sub: "Subtract",
    ast.Mult: "Multiply",
    ast.Div: "Divide",
    ast.MatMult: "MatMul",
}

_CALLS: dict[str, str] = {
    "relu": "Relu",
    "sigmoid": "Sigmoid",
    "tanh": "Tanh",
    "softmax": "Softmax",
    "identity": "Identity",
}

_FAMILY: dict[str, str] = {
    "Identity": "unary",
    "Negate": "unary",
    "Relu": "unary",
    "Sigmoid": "unary",
    "Tanh": "unary",
    "Softmax": "unary",
    "Add": "elementwise_binary",
    "Subtract": "elementwise_binary",
    "Multiply": "elementwise_binary",
    "Divide": "elementwise_binary",
    "MatMul": "matmul",
}


def _name(node: ast.AST) -> str:
    if not isinstance(node, ast.Name):
        raise FormulaEditError("bounded formula operands must be existing symbol names")
    return node.id


def _parse_expr(node: ast.AST) -> tuple[str, tuple[str, ...], dict[str, Any]]:
    if isinstance(node, ast.Name):
        return "Identity", (node.id,), {}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return "Negate", (_name(node.operand),), {}
    if isinstance(node, ast.BinOp):
        kind = _BINOPS.get(type(node.op))
        if kind is None:
            raise FormulaEditError("binary operator is outside the bounded formula-edit subset")
        return kind, (_name(node.left), _name(node.right)), {}
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise FormulaEditError("formula calls must use a direct allowed function name")
        kind = _CALLS.get(node.func.id)
        if kind is None:
            raise FormulaEditError("formula function is outside the bounded formula-edit subset", context={"function": node.func.id})
        if len(node.args) != 1 or node.keywords:
            raise FormulaEditError("bounded formula functions require exactly one symbolic operand and no keywords")
        attrs = {"axis": -1} if kind == "Softmax" else {}
        return kind, (_name(node.args[0]),), attrs
    raise FormulaEditError("formula expression is outside the bounded local-edit subset")


def parse_local_formula(source: str) -> ParsedLocalFormula:
    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError as exc:
        raise FormulaEditError("local formula could not be parsed", context={"offset": exc.offset, "message": exc.msg}) from exc
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Assign):
        raise FormulaEditError("local formula must contain exactly one assignment")
    assignment = tree.body[0]
    if len(assignment.targets) != 1 or not isinstance(assignment.targets[0], ast.Name):
        raise FormulaEditError("formula assignment target must be one symbol")
    kind, inputs, attributes = _parse_expr(assignment.value)
    return ParsedLocalFormula(assignment.targets[0].id, kind, inputs, attributes)


def _find_graph(project: Project, module_id: str, graph_id: str) -> Graph:
    for module in project.modules:
        if module.id != module_id:
            continue
        for graph in module.graphs:
            if graph.id == graph_id:
                return graph
        break
    raise FormulaEditError("target graph not found", context={"module_id": module_id, "graph_id": graph_id})


def _find_node(graph: Graph, node_id: str) -> Node:
    for node in graph.nodes:
        if node.id == node_id:
            return node
    raise FormulaEditError("target node not found", source_nodes=(node_id,))


def _typed(node: Node) -> bool:
    return isinstance(node.value_type, TensorType) or isinstance(node.shape_type, Shape)


def _guard_shape_family(node: Node, new_kind: str) -> None:
    if not _typed(node):
        return
    old_family = _FAMILY.get(node.kind)
    new_family = _FAMILY.get(new_kind)
    if old_family is None or new_family is None or old_family != new_family:
        raise FormulaEditError(
            "typed local formula edit cannot cross shape families",
            source_nodes=(node.id,),
            context={"before_kind": node.kind, "after_kind": new_kind, "before_family": old_family, "after_family": new_family},
        )


def preview_formula_edit(
    project: Project,
    module_id: str,
    graph_id: str,
    node_id: str,
    formula: str,
    *,
    rationale: str = "",
    provenance: dict[str, Any] | None = None,
) -> ProjectionEditCandidate:
    graph = _find_graph(project, module_id, graph_id)
    target = _find_node(graph, node_id)
    if len(target.outputs) != 1:
        raise FormulaEditError("bounded local formula edit requires a target node with exactly one output", source_nodes=(node_id,))
    parsed = parse_local_formula(formula)
    if parsed.output != target.outputs[0]:
        raise FormulaEditError(
            "formula assignment output does not match target node output",
            source_nodes=(node_id,),
            context={"expected": target.outputs[0], "received": parsed.output},
        )
    _guard_shape_family(target, parsed.kind)
    if parsed.kind == target.kind:
        attrs = dict(target.attributes)
        if parsed.kind == "Softmax" and "axis" not in attrs:
            attrs["axis"] = -1
    else:
        attrs = dict(parsed.attributes)
    replacement = replace(target, kind=parsed.kind, inputs=parsed.inputs, attributes=attrs)
    nodes = tuple(replacement if node.id == node_id else node for node in graph.nodes)
    after = replace(graph, nodes=nodes)
    return build_projection_edit_candidate(
        project,
        module_id,
        graph_id,
        after,
        rationale=rationale,
        provenance=provenance,
    )

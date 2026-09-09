from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from .errors import DependencyError, MissingInputError, UnsupportedOperationError
from .model import Graph, Node
from .runtime import ExecutionEnvironment, ExecutionResult, ExecutionTrace, validate_runtime_value


def _single_output(node: Node, value: Any) -> dict[str, Any]:
    if len(node.outputs) != 1:
        raise UnsupportedOperationError(
            "Round 03 operation requires exactly one output",
            source_nodes=(node.id,),
            context={"kind": node.kind, "outputs": list(node.outputs)},
        )
    return {node.outputs[0]: value}


def _softmax(value: Any, axis: int = -1) -> Any:
    x = np.asarray(value)
    shifted = x - np.max(x, axis=axis, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.sum(exp, axis=axis, keepdims=True)


class Interpreter:
    """Reference executor for the Round 03 pure executable subset."""

    def run_graph(
        self,
        graph: Graph,
        inputs: Mapping[str, Any],
        *,
        parameters: Mapping[str, Any] | None = None,
        graph_lookup: Mapping[str, Graph] | None = None,
    ) -> ExecutionResult:
        env = ExecutionEnvironment(inputs=inputs, parameters=parameters or {})
        values: dict[str, Any] = {}
        for name in graph.inputs:
            values[name] = env.resolve(name)

        trace = ExecutionTrace()
        pending = {node.id: node for node in graph.nodes}

        while pending:
            progressed = False
            for node_id in sorted(tuple(pending)):
                node = pending[node_id]
                if node.kind not in {"Parameter", "Constant", "Input"} and any(name not in values for name in node.inputs):
                    continue
                produced = self._execute_node(
                    node,
                    values,
                    env=env,
                    graph_lookup=graph_lookup or {},
                )
                for name, value in produced.items():
                    validate_runtime_value(value, node.value_type if hasattr(node.value_type, "shape") else None, solver=env.shape_solver, source=name)
                    values[name] = value
                result_for_trace = next(iter(produced.values())) if produced else None
                trace = trace.append(
                    node_id=node.id,
                    kind=node.kind,
                    inputs=node.inputs,
                    outputs=node.outputs,
                    result=result_for_trace,
                )
                del pending[node_id]
                progressed = True
            if not progressed:
                unresolved = {
                    node.id: [name for name in node.inputs if name not in values]
                    for node in pending.values()
                }
                raise DependencyError(
                    "runtime dependency cycle or unresolved dependency",
                    source_nodes=tuple(sorted(pending)),
                    context={"unresolved": unresolved},
                )

        missing_outputs = [name for name in graph.outputs if name not in values]
        if missing_outputs:
            raise DependencyError(
                "graph completed without producing required outputs",
                context={"missing_outputs": missing_outputs},
            )
        return ExecutionResult(outputs={name: values[name] for name in graph.outputs}, trace=trace)

    def _execute_node(
        self,
        node: Node,
        values: Mapping[str, Any],
        *,
        env: ExecutionEnvironment,
        graph_lookup: Mapping[str, Graph],
    ) -> dict[str, Any]:
        kind = node.kind
        args = [values[name] for name in node.inputs if name in values]

        if kind == "Input":
            name = str(node.attributes.get("name", node.outputs[0] if node.outputs else ""))
            return _single_output(node, env.resolve(name))
        if kind == "Parameter":
            name = str(node.attributes.get("name", node.outputs[0] if node.outputs else ""))
            if name not in env.parameters:
                raise MissingInputError(
                    f"runtime parameter not found: {name}",
                    source_nodes=(node.id,),
                    context={"name": name, "kind": "parameter"},
                )
            return _single_output(node, env.parameters[name])
        if kind == "Constant":
            if "value" not in node.attributes:
                raise MissingInputError(
                    "constant node has no value",
                    source_nodes=(node.id,),
                    context={"name": node.id, "kind": "constant"},
                )
            return _single_output(node, node.attributes["value"])
        if kind == "Identity":
            return _single_output(node, args[0])
        if kind == "Add":
            return _single_output(node, args[0] + args[1])
        if kind == "Subtract":
            return _single_output(node, args[0] - args[1])
        if kind == "Multiply":
            return _single_output(node, args[0] * args[1])
        if kind == "Divide":
            return _single_output(node, args[0] / args[1])
        if kind == "Negate":
            return _single_output(node, -args[0])
        if kind == "MatMul":
            return _single_output(node, np.matmul(args[0], args[1]))
        if kind == "Reshape":
            raw_shape = node.attributes.get("shape")
            if raw_shape is None:
                raise UnsupportedOperationError("Reshape requires attributes.shape", source_nodes=(node.id,))
            return _single_output(node, np.reshape(args[0], tuple(int(v) for v in raw_shape)))
        if kind == "Transpose":
            axes = node.attributes.get("axes")
            return _single_output(node, np.transpose(args[0], axes=None if axes is None else tuple(int(v) for v in axes)))
        if kind == "ReduceSum":
            axis = node.attributes.get("axis")
            keepdims = bool(node.attributes.get("keepdims", False))
            return _single_output(node, np.sum(args[0], axis=axis, keepdims=keepdims))
        if kind == "Mean":
            axis = node.attributes.get("axis")
            keepdims = bool(node.attributes.get("keepdims", False))
            return _single_output(node, np.mean(args[0], axis=axis, keepdims=keepdims))
        if kind == "Relu":
            return _single_output(node, np.maximum(args[0], 0))
        if kind == "Sigmoid":
            return _single_output(node, 1.0 / (1.0 + np.exp(-np.asarray(args[0]))))
        if kind == "Tanh":
            return _single_output(node, np.tanh(args[0]))
        if kind == "Softmax":
            return _single_output(node, _softmax(args[0], int(node.attributes.get("axis", -1))))
        if kind == "If":
            if len(args) != 3:
                raise UnsupportedOperationError("If requires condition, then, else inputs", source_nodes=(node.id,))
            condition = args[0]
            if isinstance(condition, np.ndarray):
                if condition.shape != ():
                    raise UnsupportedOperationError("Round 03 If condition must be scalar", source_nodes=(node.id,))
                condition = condition.item()
            return _single_output(node, args[1] if bool(condition) else args[2])
        if kind == "BoundedLoop":
            return _single_output(node, self._run_bounded_loop(node, args))
        if kind == "Call":
            callee_id = str(node.attributes.get("callee", ""))
            callee = graph_lookup.get(callee_id)
            if callee is None:
                raise UnsupportedOperationError(
                    "Call callee graph is not available",
                    source_nodes=(node.id,),
                    context={"callee": callee_id},
                )
            if len(callee.inputs) != len(args):
                raise UnsupportedOperationError(
                    "Call input arity mismatch",
                    source_nodes=(node.id,),
                    context={"callee": callee_id},
                )
            child = self.run_graph(callee, dict(zip(callee.inputs, args)), parameters=env.parameters, graph_lookup=graph_lookup)
            if len(node.outputs) != len(callee.outputs):
                raise UnsupportedOperationError(
                    "Call output arity mismatch",
                    source_nodes=(node.id,),
                    context={"callee": callee_id},
                )
            return {dst: child.outputs[src] for dst, src in zip(node.outputs, callee.outputs)}

        raise UnsupportedOperationError(
            f"unsupported Round 03 node kind: {kind}",
            source_nodes=(node.id,),
            context={"kind": kind},
        )

    def _run_bounded_loop(self, node: Node, args: list[Any]) -> Any:
        trip_count = node.attributes.get("trip_count")
        if not isinstance(trip_count, int) or isinstance(trip_count, bool) or trip_count < 0:
            raise UnsupportedOperationError(
                "BoundedLoop requires a non-negative integer trip_count",
                source_nodes=(node.id,),
            )
        if trip_count > 1_000_000:
            raise UnsupportedOperationError(
                "BoundedLoop trip_count exceeds Round 03 safety bound",
                source_nodes=(node.id,),
                context={"trip_count": trip_count},
            )
        if not args:
            raise UnsupportedOperationError("BoundedLoop requires an accumulator input", source_nodes=(node.id,))
        body_kind = str(node.attributes.get("body_kind", "Identity"))
        accumulator = args[0]
        operand = args[1] if len(args) > 1 else None
        for _ in range(trip_count):
            if body_kind == "Identity":
                accumulator = accumulator
            elif body_kind == "Add":
                accumulator = accumulator + operand
            elif body_kind == "Subtract":
                accumulator = accumulator - operand
            elif body_kind == "Multiply":
                accumulator = accumulator * operand
            elif body_kind == "Divide":
                accumulator = accumulator / operand
            else:
                raise UnsupportedOperationError(
                    "BoundedLoop body_kind is unsupported",
                    source_nodes=(node.id,),
                    context={"body_kind": body_kind},
                )
        return accumulator

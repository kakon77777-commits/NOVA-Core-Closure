from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from ..errors import MissingInputError, UnsupportedOperationError
from ..interpreter import Interpreter, _single_output, _softmax
from ..model import Graph, Node
from ..runtime import ExecutionEnvironment


class NumPyBackend(Interpreter):
    """NumPy CPU implementation of the Round 03 executable subset.

    Scheduling, tracing, and runtime guards reuse the reference runtime contract;
    operation lowering is implemented here through NumPy primitives.
    """

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
                raise MissingInputError("constant node has no value", source_nodes=(node.id,))
            return _single_output(node, node.attributes["value"])
        if kind == "Identity":
            return _single_output(node, args[0])
        if kind == "Add":
            return _single_output(node, np.add(args[0], args[1]))
        if kind == "Subtract":
            return _single_output(node, np.subtract(args[0], args[1]))
        if kind == "Multiply":
            return _single_output(node, np.multiply(args[0], args[1]))
        if kind == "Divide":
            return _single_output(node, np.divide(args[0], args[1]))
        if kind == "Negate":
            return _single_output(node, np.negative(args[0]))
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
            return _single_output(node, np.sum(args[0], axis=node.attributes.get("axis"), keepdims=bool(node.attributes.get("keepdims", False))))
        if kind == "Mean":
            return _single_output(node, np.mean(args[0], axis=node.attributes.get("axis"), keepdims=bool(node.attributes.get("keepdims", False))))
        if kind == "Relu":
            return _single_output(node, np.maximum(args[0], 0))
        if kind == "Sigmoid":
            x = np.asarray(args[0])
            return _single_output(node, np.reciprocal(1.0 + np.exp(-x)))
        if kind == "Tanh":
            return _single_output(node, np.tanh(args[0]))
        if kind == "Softmax":
            return _single_output(node, _softmax(args[0], int(node.attributes.get("axis", -1))))
        if kind == "If":
            if len(args) != 3:
                raise UnsupportedOperationError("If requires condition, then, else inputs", source_nodes=(node.id,))
            condition = np.asarray(args[0])
            if condition.shape != ():
                raise UnsupportedOperationError("Round 03 If condition must be scalar", source_nodes=(node.id,))
            return _single_output(node, args[1] if bool(condition.item()) else args[2])
        if kind == "BoundedLoop":
            return _single_output(node, self._run_bounded_loop_numpy(node, args))
        if kind == "Call":
            return super()._execute_node(node, values, env=env, graph_lookup=graph_lookup)
        raise UnsupportedOperationError(
            f"unsupported Round 03 NumPy node kind: {kind}",
            source_nodes=(node.id,),
            context={"kind": kind, "backend": "numpy"},
        )

    def _run_bounded_loop_numpy(self, node: Node, args: list[Any]) -> Any:
        trip_count = node.attributes.get("trip_count")
        if not isinstance(trip_count, int) or isinstance(trip_count, bool) or trip_count < 0 or trip_count > 1_000_000:
            raise UnsupportedOperationError("invalid BoundedLoop trip_count", source_nodes=(node.id,))
        if not args:
            raise UnsupportedOperationError("BoundedLoop requires an accumulator input", source_nodes=(node.id,))
        body_kind = str(node.attributes.get("body_kind", "Identity"))
        accumulator = args[0]
        operand = args[1] if len(args) > 1 else None
        op = {
            "Identity": lambda a, b: a,
            "Add": np.add,
            "Subtract": np.subtract,
            "Multiply": np.multiply,
            "Divide": np.divide,
        }.get(body_kind)
        if op is None:
            raise UnsupportedOperationError(
                "BoundedLoop body_kind is unsupported",
                source_nodes=(node.id,),
                context={"body_kind": body_kind, "backend": "numpy"},
            )
        for _ in range(trip_count):
            accumulator = op(accumulator, operand)
        return accumulator

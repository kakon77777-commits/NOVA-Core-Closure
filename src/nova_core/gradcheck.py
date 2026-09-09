from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np

from .autodiff import DifferentiationRequest, differentiate_graph, gradient_symbol
from .backends.numpy_backend import NumPyBackend
from .errors import DiffError
from .model import Graph, Node


@dataclass(frozen=True)
class GradientCheckResult:
    analytic: Mapping[str, np.ndarray]
    numeric: Mapping[str, np.ndarray]
    max_abs_error: Mapping[str, float]
    max_rel_error: Mapping[str, float]
    passed: bool
    epsilon: float
    rtol: float
    atol: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "analytic", MappingProxyType({str(k): np.asarray(v) for k, v in self.analytic.items()}))
        object.__setattr__(self, "numeric", MappingProxyType({str(k): np.asarray(v) for k, v in self.numeric.items()}))
        object.__setattr__(self, "max_abs_error", MappingProxyType({str(k): float(v) for k, v in self.max_abs_error.items()}))
        object.__setattr__(self, "max_rel_error", MappingProxyType({str(k): float(v) for k, v in self.max_rel_error.items()}))


def _producer_for(graph: Graph, symbol: str) -> Node | None:
    for node in graph.nodes:
        if symbol in node.outputs:
            return node
    return None


def _runtime_scalar(result: Any, *, target: str) -> float:
    array = np.asarray(result)
    if array.shape != ():
        raise DiffError(
            "finite-difference gradient checking requires a scalar target",
            context={"target": target, "observed_shape": list(array.shape)},
        )
    return float(array.item())


def _execute_scalar(
    graph: Graph,
    inputs: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    target: str,
    backend: NumPyBackend,
) -> float:
    if target not in graph.outputs:
        raise DiffError(
            "finite-difference target must be a graph output",
            context={"target": target, "graph_outputs": list(graph.outputs)},
        )
    result = backend.run_graph(graph, inputs, parameters=parameters)
    return _runtime_scalar(result.outputs[target], target=target)


def finite_difference_gradient(
    graph: Graph,
    inputs: Mapping[str, Any],
    *,
    target: str,
    wrt: str,
    parameters: Mapping[str, Any] | None = None,
    epsilon: float = 1e-6,
    backend: NumPyBackend | None = None,
) -> np.ndarray:
    if epsilon <= 0:
        raise DiffError("finite-difference epsilon must be positive", context={"epsilon": epsilon})
    runtime = backend or NumPyBackend()
    base_inputs = dict(inputs)
    base_parameters = dict(parameters or {})

    if wrt in graph.inputs:
        if wrt not in base_inputs:
            raise DiffError("finite-difference input is missing", context={"wrt": wrt})
        location = "input"
        runtime_name = wrt
        original = base_inputs[wrt]
    else:
        producer = _producer_for(graph, wrt)
        if producer is None or producer.kind != "Parameter":
            raise DiffError(
                "finite differences can perturb only graph inputs or Parameter leaves",
                context={"wrt": wrt},
            )
        runtime_name = str(producer.attributes.get("name", wrt))
        if runtime_name not in base_parameters:
            raise DiffError(
                "finite-difference parameter is missing",
                source_nodes=(producer.id,),
                context={"wrt": wrt, "parameter": runtime_name},
            )
        location = "parameter"
        original = base_parameters[runtime_name]

    value = np.asarray(original, dtype=np.float64)
    numeric = np.empty(value.shape, dtype=np.float64)
    indices = list(np.ndindex(value.shape)) if value.shape else [()]

    for index in indices:
        plus_value = value.copy()
        minus_value = value.copy()
        plus_value[index] += epsilon
        minus_value[index] -= epsilon

        plus_inputs = dict(base_inputs)
        minus_inputs = dict(base_inputs)
        plus_parameters = dict(base_parameters)
        minus_parameters = dict(base_parameters)
        if location == "input":
            plus_inputs[runtime_name] = plus_value
            minus_inputs[runtime_name] = minus_value
        else:
            plus_parameters[runtime_name] = plus_value
            minus_parameters[runtime_name] = minus_value

        plus = _execute_scalar(graph, plus_inputs, plus_parameters, target=target, backend=runtime)
        minus = _execute_scalar(graph, minus_inputs, minus_parameters, target=target, backend=runtime)
        numeric[index] = (plus - minus) / (2.0 * epsilon)

    return numeric


def check_gradient(
    graph: Graph,
    inputs: Mapping[str, Any],
    request: DifferentiationRequest,
    *,
    parameters: Mapping[str, Any] | None = None,
    epsilon: float = 1e-6,
    rtol: float = 1e-5,
    atol: float = 1e-7,
    backend: NumPyBackend | None = None,
) -> GradientCheckResult:
    if request.seed_input is not None:
        raise DiffError(
            "finite-difference check currently validates scalar grad requests, not explicit-seed VJPs",
            context={"seed_input": request.seed_input},
        )
    runtime = backend or NumPyBackend()
    derivative = differentiate_graph(graph, request)
    analytic_outputs = runtime.run_graph(
        derivative.graph,
        inputs,
        parameters=dict(parameters or {}),
    ).outputs

    analytic: dict[str, np.ndarray] = {}
    numeric: dict[str, np.ndarray] = {}
    max_abs: dict[str, float] = {}
    max_rel: dict[str, float] = {}
    passed = True

    for symbol in request.wrt:
        analytic_value = np.asarray(analytic_outputs[gradient_symbol(symbol)], dtype=np.float64)
        numeric_value = finite_difference_gradient(
            graph,
            inputs,
            target=request.target,
            wrt=symbol,
            parameters=parameters,
            epsilon=epsilon,
            backend=runtime,
        )
        analytic[symbol] = analytic_value
        numeric[symbol] = numeric_value
        if analytic_value.shape != numeric_value.shape:
            passed = False
            max_abs[symbol] = float("inf")
            max_rel[symbol] = float("inf")
            continue
        difference = np.abs(analytic_value - numeric_value)
        max_abs[symbol] = float(np.max(difference)) if difference.size else float(difference)
        denominator = np.maximum(np.abs(numeric_value), atol)
        relative = difference / denominator
        max_rel[symbol] = float(np.max(relative)) if relative.size else float(relative)
        if not np.allclose(analytic_value, numeric_value, rtol=rtol, atol=atol):
            passed = False

    return GradientCheckResult(
        analytic=analytic,
        numeric=numeric,
        max_abs_error=max_abs,
        max_rel_error=max_rel,
        passed=passed,
        epsilon=float(epsilon),
        rtol=float(rtol),
        atol=float(atol),
    )

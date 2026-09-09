from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .autodiff import DerivativeGraphResult, DifferentiationRequest, differentiate_graph
from .backends import NumPyBackend
from .codec import decode_project
from .errors import ValidationError
from .interpreter import Interpreter
from .interop import from_dlpack as _interop_from_dlpack, to_dlpack as _interop_to_dlpack, to_numpy as _interop_to_numpy
from .types import TensorType
from .model import Graph, Project
from .runtime import ExecutionResult
from .training import TrainingConfig, TrainingResult, train_graph as _train_graph
from .diff import GraphDiff, diff_graphs
from .editing import ProjectionEditCandidate, interpret_structured_text_edit



@dataclass(frozen=True)
class GradientExecutionResult:
    derivative: DerivativeGraphResult
    execution: ExecutionResult

def load_project(source: Project | str | bytes | Mapping[str, Any] | Path) -> Project:
    if isinstance(source, Project):
        return source
    if isinstance(source, Path):
        return decode_project(source.read_text(encoding="utf-8"))
    if isinstance(source, str):
        stripped = source.lstrip()
        if stripped.startswith("{") or stripped.startswith("["):
            return decode_project(source)
        path = Path(source)
        try:
            if "\n" not in source and path.exists() and path.is_file():
                return decode_project(path.read_text(encoding="utf-8"))
        except OSError:
            pass
    return decode_project(source)


def _backend(name: str):
    if name == "interpreter":
        return Interpreter()
    if name == "numpy":
        return NumPyBackend()
    raise ValidationError("unknown execution backend", context={"backend": name})


def run_graph(
    graph: Graph,
    inputs: Mapping[str, Any],
    *,
    parameters: Mapping[str, Any] | None = None,
    backend: str = "interpreter",
    graph_lookup: Mapping[str, Graph] | None = None,
) -> ExecutionResult:
    return _backend(backend).run_graph(
        graph,
        inputs,
        parameters=parameters,
        graph_lookup=graph_lookup,
    )


def _find_graph(project: Project, module_id: str, graph_id: str) -> tuple[Graph, dict[str, Graph]]:
    module = next((item for item in project.modules if item.id == module_id), None)
    if module is None:
        raise ValidationError("module not found", context={"module_id": module_id})
    graph = next((item for item in module.graphs if item.id == graph_id), None)
    if graph is None:
        raise ValidationError(
            "graph not found",
            context={"module_id": module_id, "graph_id": graph_id},
        )
    lookup = {item.id: item for item in module.graphs}
    return graph, lookup


def run_project(
    project: Project | str | bytes | Mapping[str, Any] | Path,
    module_id: str,
    graph_id: str,
    inputs: Mapping[str, Any],
    *,
    parameters: Mapping[str, Any] | None = None,
    backend: str = "interpreter",
) -> ExecutionResult:
    loaded = load_project(project)
    graph, lookup = _find_graph(loaded, module_id, graph_id)
    return run_graph(
        graph,
        inputs,
        parameters=parameters,
        backend=backend,
        graph_lookup=lookup,
    )


def find_graph(project: Project, module_id: str, graph_id: str) -> Graph:
    graph, _ = _find_graph(project, module_id, graph_id)
    return graph

def differentiate_project(
    project: Project | str | bytes | Mapping[str, Any] | Path,
    module_id: str,
    graph_id: str,
    request: DifferentiationRequest,
) -> DerivativeGraphResult:
    loaded = load_project(project)
    graph, _ = _find_graph(loaded, module_id, graph_id)
    return differentiate_graph(graph, request)


def run_gradient(
    graph: Graph,
    inputs: Mapping[str, Any],
    request: DifferentiationRequest,
    *,
    parameters: Mapping[str, Any] | None = None,
    backend: str = "interpreter",
) -> GradientExecutionResult:
    derivative = differentiate_graph(graph, request)
    execution = run_graph(
        derivative.graph,
        inputs,
        parameters=parameters,
        backend=backend,
    )
    return GradientExecutionResult(derivative=derivative, execution=execution)


def run_project_gradient(
    project: Project | str | bytes | Mapping[str, Any] | Path,
    module_id: str,
    graph_id: str,
    inputs: Mapping[str, Any],
    request: DifferentiationRequest,
    *,
    parameters: Mapping[str, Any] | None = None,
    backend: str = "interpreter",
) -> GradientExecutionResult:
    loaded = load_project(project)
    graph, _ = _find_graph(loaded, module_id, graph_id)
    return run_gradient(
        graph,
        inputs,
        request,
        parameters=parameters,
        backend=backend,
    )



def train_project(
    project: Project | str | bytes | Mapping[str, Any] | Path,
    module_id: str,
    graph_id: str,
    inputs: Mapping[str, Any],
    initial_parameters: Mapping[str, Any],
    config: TrainingConfig,
) -> TrainingResult:
    loaded = load_project(project)
    graph, _ = _find_graph(loaded, module_id, graph_id)
    return _train_graph(graph, inputs, initial_parameters, config)


def interop_to_numpy(value: Any, expected: TensorType | None = None, *, dtype_policy: str = "safe", copy: bool = False):
    return _interop_to_numpy(value, expected=expected, dtype_policy=dtype_policy, copy=copy)


def interop_to_dlpack(value: Any):
    return _interop_to_dlpack(value)


def interop_from_dlpack(value: Any, expected: TensorType | None = None):
    return _interop_from_dlpack(value, expected=expected)


def diff_project_graphs(
    base: Project | str | bytes | Mapping[str, Any] | Path,
    target: Project | str | bytes | Mapping[str, Any] | Path,
    module_id: str,
    graph_id: str,
) -> GraphDiff:
    base_project = load_project(base)
    target_project = load_project(target)
    base_graph, _ = _find_graph(base_project, module_id, graph_id)
    target_graph, _ = _find_graph(target_project, module_id, graph_id)
    return diff_graphs(base_graph, target_graph)


def preview_structured_edit(
    project: Project | str | bytes | Mapping[str, Any] | Path,
    module_id: str,
    graph_id: str,
    edited_text: str,
    *,
    rationale: str = "",
    provenance: Mapping[str, Any] | None = None,
) -> ProjectionEditCandidate:
    loaded = load_project(project)
    return interpret_structured_text_edit(
        loaded,
        module_id,
        graph_id,
        edited_text,
        rationale=rationale,
        provenance=provenance,
    )

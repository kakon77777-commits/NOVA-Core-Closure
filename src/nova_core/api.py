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
from .interactive import NodeGraphEdit, preview_node_graph_edit as _preview_node_graph_edit
from .formula_editing import preview_formula_edit as _preview_formula_edit
from .notebook import Notebook, NotebookResult, run_notebook as _run_notebook
from .paradigm import PlannerProfile
from .paradigm_planner import ExecutionStrategyPlan, plan_graph as _plan_graph



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

def preview_node_graph_edit_project(
    project: Project | str | bytes | Mapping[str, Any] | Path,
    module_id: str,
    graph_id: str,
    operations: tuple[NodeGraphEdit, ...] | list[NodeGraphEdit],
    *,
    rationale: str = "",
    provenance: Mapping[str, Any] | None = None,
) -> ProjectionEditCandidate:
    loaded = load_project(project)
    return _preview_node_graph_edit(
        loaded, module_id, graph_id, operations, rationale=rationale, provenance=provenance
    )


def preview_formula_edit_project(
    project: Project | str | bytes | Mapping[str, Any] | Path,
    module_id: str,
    graph_id: str,
    node_id: str,
    formula: str,
    *,
    rationale: str = "",
    provenance: Mapping[str, Any] | None = None,
) -> ProjectionEditCandidate:
    loaded = load_project(project)
    return _preview_formula_edit(
        loaded, module_id, graph_id, node_id, formula, rationale=rationale, provenance=dict(provenance or {})
    )


def run_project_notebook(
    project: Project | str | bytes | Mapping[str, Any] | Path,
    notebook: Notebook,
    external_inputs: Mapping[str, Any],
    *,
    backend: str = "interpreter",
    parameters: Mapping[str, Any] | None = None,
) -> NotebookResult:
    loaded = load_project(project)
    return _run_notebook(loaded, notebook, external_inputs, backend=backend, parameters=parameters)



def plan_project_memory(
    project: Project | str | bytes | Mapping[str, Any] | Path,
    module_id: str,
    graph_id: str,
    symbol_types: Mapping[str, TensorType] | None = None,
    *,
    mode: str = "optimized",
    proposer: str = "deterministic-planner",
    confidence: float | None = None,
):
    from .resources import plan_memory

    loaded = load_project(project)
    graph, _ = _find_graph(loaded, module_id, graph_id)
    return plan_memory(
        graph,
        symbol_types,
        mode=mode,
        proposer=proposer,
        confidence=confidence,
    )


def verify_project_memory_plan(
    project: Project | str | bytes | Mapping[str, Any] | Path,
    module_id: str,
    graph_id: str,
    plan,
    symbol_types: Mapping[str, TensorType] | None = None,
):
    from .resource_verifier import verify_memory_plan

    loaded = load_project(project)
    graph, _ = _find_graph(loaded, module_id, graph_id)
    return verify_memory_plan(graph, plan, symbol_types)


def select_project_memory_plan(
    project: Project | str | bytes | Mapping[str, Any] | Path,
    module_id: str,
    graph_id: str,
    candidate,
    symbol_types: Mapping[str, TensorType] | None = None,
):
    from .resource_verifier import select_memory_plan

    loaded = load_project(project)
    graph, _ = _find_graph(loaded, module_id, graph_id)
    return select_memory_plan(graph, candidate, symbol_types)


def load_ai_build_request(source):
    from .ai_build import AIBuildRequest, decode_ai_build_request

    if isinstance(source, AIBuildRequest):
        return source
    if isinstance(source, Path):
        return decode_ai_build_request(source.read_text(encoding="utf-8"))
    if isinstance(source, str):
        stripped = source.lstrip()
        if stripped.startswith("{"):
            return decode_ai_build_request(source)
        path = Path(source)
        try:
            if "\n" not in source and path.exists() and path.is_file():
                return decode_ai_build_request(path.read_text(encoding="utf-8"))
        except OSError:
            pass
    return decode_ai_build_request(source)


def preview_project_ai_build(project, request):
    from .ai_build import preview_ai_build

    loaded = load_project(project)
    loaded_request = load_ai_build_request(request)
    return preview_ai_build(loaded, loaded_request)


def audit_project_ai_build(project, request):
    from .audit import project_ai_build_audit

    return project_ai_build_audit(preview_project_ai_build(project, request))


def commit_project_ai_build(project, request):
    from .ai_build import AIBuildTransaction

    loaded = load_project(project)
    loaded_request = load_ai_build_request(request)
    tx = AIBuildTransaction(loaded)
    candidate = tx.preview(loaded_request)
    return tx.commit(candidate)


def list_operator_descriptors():
    from .sos import basic_operator_registry

    return basic_operator_registry().descriptors


def compose_operator_ids(operator_ids, *, context=None, strict=True):
    from .sos import basic_operator_registry, compose_chain

    ids = tuple(str(value) for value in operator_ids)
    registry = basic_operator_registry()
    descriptors = tuple(registry.get(operator_id) for operator_id in ids)
    return compose_chain(descriptors, context=context, strict=strict)


def validate_operator_ids(operator_ids, *, context=None):
    from .sos import BrokenOperator, closure_hash

    result = compose_operator_ids(operator_ids, context=context, strict=False)
    if isinstance(result, BrokenOperator):
        error = result.report.error
        to_dict = getattr(error, "to_dict", None) if error is not None else None
        return {
            "status": "unsafe",
            "member_ids": list(result.member_ids),
            "error": to_dict() if callable(to_dict) else None,
            "reports": [result.report.to_record()],
        }
    return {
        "status": "safe",
        "member_ids": list(result.member_ids),
        "closure_hash": closure_hash(result),
        "reports": [report.to_record() for report in result.reports],
    }


def lower_operator_ids(operator_ids, *, context=None, module_id="app", graph_id="main", input_symbol="x", output_symbol="y"):
    from .sos import BrokenOperator
    from .sos_lowering import lower_closure_to_project

    closure = compose_operator_ids(operator_ids, context=context, strict=True)
    if isinstance(closure, BrokenOperator):
        raise AssertionError("strict SOS composition returned BrokenOperator")
    return lower_closure_to_project(
        closure,
        module_id=module_id,
        graph_id=graph_id,
        input_symbol=input_symbol,
        output_symbol=output_symbol,
    )


def plan_project_paradigms(
    project: Project | str | bytes | Mapping[str, Any] | Path,
    module_id: str,
    graph_id: str,
    profile: PlannerProfile | None = None,
    *,
    stability_resets: tuple[int, ...] | list[int] = (),
) -> ExecutionStrategyPlan:
    loaded = load_project(project)
    graph, _ = _find_graph(loaded, module_id, graph_id)
    return _plan_graph(graph, profile, stability_resets=stability_resets)

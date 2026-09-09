from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
import json
from types import MappingProxyType
from typing import Any, TypeAlias

import numpy as np

from .backends import NumPyBackend
from .errors import NotebookError
from .interpreter import Interpreter
from .model import Graph, Module, Project
from .canonical import semantic_hash


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class ExternalInput:
    name: str

    def __post_init__(self) -> None:
        if not self.name:
            raise NotebookError("external input binding name must not be empty")


@dataclass(frozen=True)
class CellOutput:
    cell_id: str
    output: str

    def __post_init__(self) -> None:
        if not self.cell_id or not self.output:
            raise NotebookError("cell output binding requires cell_id and output")


NotebookBinding: TypeAlias = ExternalInput | CellOutput


@dataclass(frozen=True)
class NotebookCell:
    id: str
    module_id: str
    graph_id: str
    bindings: Mapping[str, NotebookBinding] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.module_id or not self.graph_id:
            raise NotebookError("notebook cell requires id, module_id, and graph_id")
        normalized: dict[str, NotebookBinding] = {}
        for name, binding in self.bindings.items():
            if not isinstance(binding, (ExternalInput, CellOutput)):
                raise NotebookError("notebook binding has unsupported type", context={"cell_id": self.id, "input": str(name)})
            normalized[str(name)] = binding
        object.__setattr__(self, "bindings", MappingProxyType(normalized))


@dataclass(frozen=True)
class Notebook:
    cells: tuple[NotebookCell, ...]
    version: str = "0.1"

    def __post_init__(self) -> None:
        cells = tuple(self.cells)
        object.__setattr__(self, "cells", cells)
        seen: set[str] = set()
        for cell in cells:
            if cell.id in seen:
                raise NotebookError("duplicate notebook cell id", context={"cell_id": cell.id})
            for binding in cell.bindings.values():
                if isinstance(binding, CellOutput) and binding.cell_id not in seen:
                    raise NotebookError(
                        "notebook cell output binding must reference an earlier cell",
                        context={"cell_id": cell.id, "dependency": binding.cell_id},
                    )
            seen.add(cell.id)


@dataclass(frozen=True)
class NotebookCellResult:
    cell_id: str
    module_id: str
    graph_id: str
    graph_semantic_hash: str
    dependency_cells: tuple[str, ...]
    backend: str
    outputs: Mapping[str, Any]
    output_digest: str
    output_summaries: Mapping[str, Mapping[str, Any]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "outputs", MappingProxyType(dict(self.outputs)))
        object.__setattr__(
            self,
            "output_summaries",
            MappingProxyType({name: MappingProxyType(dict(summary)) for name, summary in self.output_summaries.items()}),
        )


@dataclass(frozen=True)
class NotebookResult:
    notebook_hash: str
    cells: tuple[NotebookCellResult, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))


def notebook_record(notebook: Notebook) -> dict[str, Any]:
    cells: list[dict[str, Any]] = []
    for cell in notebook.cells:
        bindings: dict[str, Any] = {}
        for name in sorted(cell.bindings):
            binding = cell.bindings[name]
            if isinstance(binding, ExternalInput):
                bindings[name] = {"kind": "external", "name": binding.name}
            else:
                bindings[name] = {"kind": "cell_output", "cell_id": binding.cell_id, "output": binding.output}
        cells.append(
            {
                "id": cell.id,
                "module_id": cell.module_id,
                "graph_id": cell.graph_id,
                "bindings": bindings,
            }
        )
    return {"version": notebook.version, "cells": cells}


def notebook_hash(notebook: Notebook) -> str:
    payload = json.dumps(notebook_record(notebook), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise NotebookError(f"{label} must be an object")
    return value


def decode_notebook(value: str | bytes | Mapping[str, Any]) -> Notebook:
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise NotebookError("invalid notebook JSON", context={"message": exc.msg}) from exc
    data = _mapping(value, "notebook")
    raw_cells = data.get("cells", ())
    if not isinstance(raw_cells, list):
        raise NotebookError("notebook cells must be an array")
    cells: list[NotebookCell] = []
    for index, raw_cell in enumerate(raw_cells):
        cell = _mapping(raw_cell, f"cell[{index}]")
        raw_bindings = _mapping(cell.get("bindings", {}), f"cell[{index}].bindings")
        bindings: dict[str, NotebookBinding] = {}
        for input_name, raw_binding in raw_bindings.items():
            binding = _mapping(raw_binding, f"cell[{index}].bindings.{input_name}")
            kind = binding.get("kind")
            if kind == "external":
                bindings[str(input_name)] = ExternalInput(str(binding.get("name", "")))
            elif kind == "cell_output":
                bindings[str(input_name)] = CellOutput(str(binding.get("cell_id", "")), str(binding.get("output", "")))
            else:
                raise NotebookError("unknown notebook binding kind", context={"kind": kind, "cell_index": index, "input": str(input_name)})
        try:
            cells.append(
                NotebookCell(
                    id=str(cell["id"]),
                    module_id=str(cell["module_id"]),
                    graph_id=str(cell["graph_id"]),
                    bindings=bindings,
                )
            )
        except KeyError as exc:
            raise NotebookError("notebook cell is missing a required field", context={"field": str(exc), "cell_index": index}) from exc
    return Notebook(cells=tuple(cells), version=str(data.get("version", "0.1")))


def _find_module(project: Project, module_id: str) -> Module:
    for module in project.modules:
        if module.id == module_id:
            return module
    raise NotebookError("notebook cell module not found", context={"module_id": module_id})


def _find_graph(module: Module, graph_id: str) -> Graph:
    for graph in module.graphs:
        if graph.id == graph_id:
            return graph
    raise NotebookError("notebook cell graph not found", context={"module_id": module.id, "graph_id": graph_id})


def _backend(name: str):
    if name == "interpreter":
        return Interpreter()
    if name == "numpy":
        return NumPyBackend()
    raise NotebookError("unknown notebook execution backend", context={"backend": name})


def _freeze_output(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        out = np.array(value, copy=True)
        out.setflags(write=False)
        return out
    if isinstance(value, list):
        return tuple(_freeze_output(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze_output(v) for v in value)
    return value


def _value_digest(value: Any) -> tuple[str, dict[str, Any]]:
    arr = np.asarray(value)
    header = json.dumps({"dtype": str(arr.dtype), "shape": list(arr.shape)}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if arr.dtype.hasobject:
        body = json.dumps(arr.tolist(), ensure_ascii=False, sort_keys=True, default=repr, separators=(",", ":")).encode("utf-8")
    else:
        body = np.ascontiguousarray(arr).tobytes(order="C")
    digest = "sha256:" + hashlib.sha256(header + b"\0" + body).hexdigest()
    return digest, {"dtype": str(arr.dtype), "shape": list(arr.shape), "digest": digest}


def _output_evidence(outputs: Mapping[str, Any]) -> tuple[str, dict[str, dict[str, Any]]]:
    summaries: dict[str, dict[str, Any]] = {}
    combined = hashlib.sha256()
    for name in sorted(outputs):
        digest, summary = _value_digest(outputs[name])
        summaries[name] = summary
        combined.update(name.encode("utf-8") + b"\0" + digest.encode("ascii") + b"\0")
    return "sha256:" + combined.hexdigest(), summaries


def run_notebook(
    project: Project,
    notebook: Notebook,
    external_inputs: Mapping[str, Any],
    *,
    backend: str = "interpreter",
    parameters: Mapping[str, Any] | None = None,
) -> NotebookResult:
    runner = _backend(backend)
    completed: dict[str, NotebookCellResult] = {}
    results: list[NotebookCellResult] = []

    for cell in notebook.cells:
        module = _find_module(project, cell.module_id)
        graph = _find_graph(module, cell.graph_id)
        expected = set(graph.inputs)
        provided = set(cell.bindings)
        if provided != expected:
            raise NotebookError(
                "notebook cell bindings must exactly cover graph inputs",
                context={"cell_id": cell.id, "missing": sorted(expected - provided), "extra": sorted(provided - expected)},
            )
        resolved: dict[str, Any] = {}
        dependencies: list[str] = []
        for input_name in graph.inputs:
            binding = cell.bindings[input_name]
            if isinstance(binding, ExternalInput):
                if binding.name not in external_inputs:
                    raise NotebookError(
                        "notebook external input not provided",
                        context={"cell_id": cell.id, "graph_input": input_name, "external_name": binding.name},
                    )
                resolved[input_name] = external_inputs[binding.name]
            else:
                source = completed.get(binding.cell_id)
                if source is None:
                    raise NotebookError("notebook dependency cell has not completed", context={"cell_id": cell.id, "dependency": binding.cell_id})
                if binding.output not in source.outputs:
                    raise NotebookError(
                        "notebook dependency output not found",
                        context={"cell_id": cell.id, "dependency": binding.cell_id, "output": binding.output},
                    )
                resolved[input_name] = source.outputs[binding.output]
                if binding.cell_id not in dependencies:
                    dependencies.append(binding.cell_id)
        lookup = {item.id: item for item in module.graphs}
        execution = runner.run_graph(graph, resolved, parameters=parameters, graph_lookup=lookup)
        frozen_outputs = {name: _freeze_output(value) for name, value in execution.outputs.items()}
        digest, summaries = _output_evidence(frozen_outputs)
        cell_result = NotebookCellResult(
            cell_id=cell.id,
            module_id=cell.module_id,
            graph_id=cell.graph_id,
            graph_semantic_hash=semantic_hash(graph),
            dependency_cells=tuple(dependencies),
            backend=backend,
            outputs=frozen_outputs,
            output_digest=digest,
            output_summaries=summaries,
        )
        completed[cell.id] = cell_result
        results.append(cell_result)
    return NotebookResult(notebook_hash=notebook_hash(notebook), cells=tuple(results))

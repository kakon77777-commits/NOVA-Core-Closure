from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from .api import audit_project_ai_build, commit_project_ai_build, diff_project_graphs, find_graph, load_project, preview_formula_edit_project, preview_node_graph_edit_project, preview_project_ai_build, preview_structured_edit, run_project, run_project_gradient, run_project_notebook, train_project, plan_project_memory, verify_project_memory_plan, select_project_memory_plan, list_operator_descriptors, compose_operator_ids, lower_operator_ids
from .autodiff import DifferentiationRequest, gradient_symbol
from .canonical import semantic_hash
from .errors import AIBuildError, InteropError, NovaError, ProjectionEditError, ResourcePlanningError
from .gradcheck import check_gradient
from .interop import dlpack_device, from_dlpack, to_dlpack
from .interactive import decode_node_graph_edits
from .notebook import decode_notebook
from .projection import project_editable_text, project_formula, project_graph_view, project_text
from .training import TrainingConfig
from .resources import decode_memory_plan, decode_symbol_types, memory_plan_hash
from .audit import project_audit_view
from .codec import encode_project
from .sos import CompositionContext, closure_hash


def _runtime_value(value: Any) -> Any:
    if isinstance(value, list):
        return np.asarray(value)
    if isinstance(value, dict):
        return {str(k): _runtime_value(v) for k, v in value.items()}
    return value


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(v) for v in value]
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nova")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("check", "hash"):
        cmd = sub.add_parser(name)
        cmd.add_argument("program")

    run = sub.add_parser("run")
    run.add_argument("program")
    run.add_argument("--module", default="app")
    run.add_argument("--graph", default="main")
    run.add_argument("--inputs", required=True)
    run.add_argument("--parameters")
    run.add_argument("--backend", choices=("interpreter", "numpy"), default="interpreter")

    project = sub.add_parser("project")
    project.add_argument("program")
    project.add_argument("--module", default="app")
    project.add_argument("--graph", default="main")
    project.add_argument("--view", choices=("text", "formula", "graph", "editable"), required=True)

    grad = sub.add_parser("grad")
    grad.add_argument("program")
    grad.add_argument("--module", default="app")
    grad.add_argument("--graph", default="main")
    grad.add_argument("--target", required=True)
    grad.add_argument("--wrt", action="append", required=True)
    grad.add_argument("--seed-input")
    grad.add_argument("--inputs", required=True)
    grad.add_argument("--parameters")
    grad.add_argument("--backend", choices=("interpreter", "numpy"), default="numpy")
    grad.add_argument("--check", action="store_true")

    train = sub.add_parser("train")
    train.add_argument("program")
    train.add_argument("--module", default="app")
    train.add_argument("--graph", default="main")
    train.add_argument("--target", required=True)
    train.add_argument("--wrt", action="append", required=True)
    train.add_argument("--inputs", required=True)
    train.add_argument("--parameters", required=True)
    train.add_argument("--steps", type=int, required=True)
    train.add_argument("--learning-rate", type=float, required=True)
    train.add_argument("--backend", choices=("interpreter", "numpy"), default="numpy")


    diff_cmd = sub.add_parser("diff")
    diff_cmd.add_argument("base_program")
    diff_cmd.add_argument("target_program")
    diff_cmd.add_argument("--module", default="app")
    diff_cmd.add_argument("--graph", default="main")

    preview = sub.add_parser("edit-preview")
    preview.add_argument("program")
    preview.add_argument("--edited", required=True)
    preview.add_argument("--module", default="app")
    preview.add_argument("--graph", default="main")
    preview.add_argument("--rationale", default="")

    commit = sub.add_parser("edit-commit")
    commit.add_argument("program")
    commit.add_argument("--edited", required=True)
    commit.add_argument("--output", required=True)
    commit.add_argument("--module", default="app")
    commit.add_argument("--graph", default="main")
    commit.add_argument("--rationale", default="")

    node_preview = sub.add_parser("node-edit-preview")
    node_preview.add_argument("program")
    node_preview.add_argument("--ops", required=True)
    node_preview.add_argument("--module", default="app")
    node_preview.add_argument("--graph", default="main")
    node_preview.add_argument("--rationale", default="")

    node_commit = sub.add_parser("node-edit-commit")
    node_commit.add_argument("program")
    node_commit.add_argument("--ops", required=True)
    node_commit.add_argument("--output", required=True)
    node_commit.add_argument("--module", default="app")
    node_commit.add_argument("--graph", default="main")
    node_commit.add_argument("--rationale", default="")

    formula_preview = sub.add_parser("formula-edit-preview")
    formula_preview.add_argument("program")
    formula_preview.add_argument("--node", required=True)
    formula_preview.add_argument("--formula", required=True)
    formula_preview.add_argument("--module", default="app")
    formula_preview.add_argument("--graph", default="main")
    formula_preview.add_argument("--rationale", default="")

    formula_commit = sub.add_parser("formula-edit-commit")
    formula_commit.add_argument("program")
    formula_commit.add_argument("--node", required=True)
    formula_commit.add_argument("--formula", required=True)
    formula_commit.add_argument("--output", required=True)
    formula_commit.add_argument("--module", default="app")
    formula_commit.add_argument("--graph", default="main")
    formula_commit.add_argument("--rationale", default="")

    notebook_run = sub.add_parser("notebook-run")
    notebook_run.add_argument("program")
    notebook_run.add_argument("--notebook", required=True)
    notebook_run.add_argument("--inputs", required=True)
    notebook_run.add_argument("--parameters")
    notebook_run.add_argument("--backend", choices=("interpreter", "numpy"), default="numpy")

    resource_plan = sub.add_parser("resource-plan")
    resource_plan.add_argument("program")
    resource_plan.add_argument("--module", default="app")
    resource_plan.add_argument("--graph", default="main")
    resource_plan.add_argument("--types")
    resource_plan.add_argument("--mode", choices=("optimized", "conservative"), default="optimized")

    resource_verify = sub.add_parser("resource-verify")
    resource_verify.add_argument("program")
    resource_verify.add_argument("plan")
    resource_verify.add_argument("--module", default="app")
    resource_verify.add_argument("--graph", default="main")
    resource_verify.add_argument("--types")

    resource_select = sub.add_parser("resource-select")
    resource_select.add_argument("program")
    resource_select.add_argument("plan")
    resource_select.add_argument("--module", default="app")
    resource_select.add_argument("--graph", default="main")
    resource_select.add_argument("--types")

    ai_preview = sub.add_parser("ai-build-preview")
    ai_preview.add_argument("program")
    ai_preview.add_argument("request")

    ai_audit = sub.add_parser("ai-build-audit")
    ai_audit.add_argument("program")
    ai_audit.add_argument("request")

    ai_commit = sub.add_parser("ai-build-commit")
    ai_commit.add_argument("program")
    ai_commit.add_argument("request")
    ai_commit.add_argument("--output", required=True)

    sos = sub.add_parser("sos")
    sos_sub = sos.add_subparsers(dest="sos_command", required=True)
    sos_sub.add_parser("list")
    for name in ("validate", "compose", "lower"):
        cmd = sos_sub.add_parser(name)
        cmd.add_argument("operator_ids", nargs="+")
        cmd.add_argument("--max-depth", type=int, default=32)
        cmd.add_argument("--k-s", type=int, default=256)
        if name == "lower":
            cmd.add_argument("--output", required=True)

    interop = sub.add_parser("interop")
    interop_sub = interop.add_subparsers(dest="interop_command", required=True)
    for name in ("inspect", "roundtrip"):
        cmd = interop_sub.add_parser(name)
        cmd.add_argument("npy_file")
    return parser



def _load_symbol_types(path: str | None):
    if not path:
        return {}
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ResourcePlanningError("symbol type file must contain a JSON object")
    return decode_symbol_types(raw)


def _load_npy(path: str) -> np.ndarray:
    try:
        value = np.load(Path(path), allow_pickle=False)
    except Exception as exc:
        raise InteropError(
            "failed to load NumPy .npy interop input",
            context={"path": path, "error": type(exc).__name__},
        ) from exc
    if not isinstance(value, np.ndarray):
        raise InteropError("NumPy interop input is not an ndarray", context={"path": path})
    return value



def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return left.absolute() == right.absolute()


def _write_candidate_project(input_path: Path, output_path: Path, candidate, *, label: str) -> dict[str, Any]:
    if _same_path(input_path, output_path):
        raise ProjectionEditError(f"{label} refuses to overwrite the input project")
    output_path.write_text(encode_project(candidate.candidate_project), encoding="utf-8")
    return {
        "ok": True,
        "output": str(output_path),
        "before_semantic_hash": candidate.before_semantic_hash,
        "candidate_semantic_hash": candidate.candidate_semantic_hash,
        "before_record_hash": candidate.before_record_hash,
        "candidate_record_hash": candidate.candidate_record_hash,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "sos":
            if args.sos_command == "list":
                descriptors = list_operator_descriptors()
                print(json.dumps({
                    "ok": True,
                    "operator_ids": [item.operator_id for item in descriptors],
                    "descriptors": [item.to_record() for item in descriptors],
                }, ensure_ascii=False, sort_keys=True))
                return 0
            context = CompositionContext(k_s=args.k_s, max_depth=args.max_depth)
            closure = compose_operator_ids(tuple(args.operator_ids), context=context, strict=True)
            if args.sos_command == "validate":
                print(json.dumps({
                    "ok": True,
                    "status": "safe",
                    "member_ids": list(closure.member_ids),
                    "closure_hash": closure_hash(closure),
                    "reports": [report.to_record() for report in closure.reports],
                }, ensure_ascii=False, sort_keys=True))
                return 0
            if args.sos_command == "compose":
                print(json.dumps({
                    "ok": True,
                    "member_ids": list(closure.member_ids),
                    "closure_hash": closure_hash(closure),
                    "closure": closure.to_record(),
                }, ensure_ascii=False, sort_keys=True))
                return 0
            project = lower_operator_ids(tuple(args.operator_ids), context=context)
            output_path = Path(args.output)
            output_path.write_text(encode_project(project), encoding="utf-8")
            print(json.dumps({
                "ok": True,
                "output": str(output_path),
                "member_ids": list(closure.member_ids),
                "closure_hash": closure_hash(closure),
            }, ensure_ascii=False, sort_keys=True))
            return 0

        if args.command in {"ai-build-preview", "ai-build-audit", "ai-build-commit"}:
            input_path = Path(args.program)
            request_path = Path(args.request)
            candidate = preview_project_ai_build(input_path, request_path)
            if args.command == "ai-build-preview":
                payload = {
                    "status": candidate.status.value,
                    "request_hash": candidate.request_hash,
                    "before_semantic_hash": candidate.before_semantic_hash,
                    "before_record_hash": candidate.before_record_hash,
                    "candidate_semantic_hash": candidate.candidate_semantic_hash,
                    "candidate_record_hash": candidate.candidate_record_hash,
                    "sandbox_passed": candidate.sandbox.passed,
                    "error": None if candidate.error is None else dict(candidate.error),
                }
                print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
                return 0
            if args.command == "ai-build-audit":
                print(json.dumps(audit_project_ai_build(input_path, request_path), ensure_ascii=False, sort_keys=True))
                return 0
            output_path = Path(args.output)
            if _same_path(input_path, output_path):
                raise AIBuildError("ai-build-commit refuses to overwrite the input project")
            result = commit_project_ai_build(input_path, request_path)
            output_path.write_text(encode_project(result.project), encoding="utf-8")
            print(json.dumps({
                "ok": True,
                "output": str(output_path),
                "request_id": result.request_id,
                "request_hash": result.request_hash,
                "before_semantic_hash": result.before_semantic_hash,
                "after_semantic_hash": result.after_semantic_hash,
                "before_record_hash": result.before_record_hash,
                "after_record_hash": result.after_record_hash,
            }, ensure_ascii=False, sort_keys=True))
            return 0

        if args.command == "interop":
            source = _load_npy(args.npy_file)
            if args.interop_command == "inspect":
                payload = {
                    "ok": True,
                    "dtype": str(source.dtype),
                    "shape": list(source.shape),
                    "device": list(dlpack_device(source)),
                }
                print(json.dumps(payload, sort_keys=True))
                return 0
            capsule = to_dlpack(source)
            restored = from_dlpack(capsule)
            payload = {
                "ok": True,
                "dtype": str(restored.dtype),
                "shape": list(restored.shape),
                "shared_memory": bool(np.shares_memory(source, restored)),
                "equal": bool(np.array_equal(source, restored)),
            }
            print(json.dumps(payload, sort_keys=True))
            return 0

        if args.command == "resource-plan":
            types = _load_symbol_types(args.types)
            plan = plan_project_memory(
                Path(args.program), args.module, args.graph, types, mode=args.mode
            )
            payload = {"ok": True, "plan_hash": memory_plan_hash(plan), "plan": plan.to_record()}
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            return 0

        if args.command in {"resource-verify", "resource-select"}:
            types = _load_symbol_types(args.types)
            plan = decode_memory_plan(Path(args.plan).read_text(encoding="utf-8"))
            if args.command == "resource-verify":
                report = verify_project_memory_plan(
                    Path(args.program), args.module, args.graph, plan, types
                )
                print(json.dumps({"ok": report.status.value != "unsafe", "verification": report.to_record()}, ensure_ascii=False, sort_keys=True))
                return 0
            selection = select_project_memory_plan(
                Path(args.program), args.module, args.graph, plan, types
            )
            print(json.dumps({"ok": True, "selection": selection.to_record(), "selected_plan": selection.selected.to_record()}, ensure_ascii=False, sort_keys=True))
            return 0

        if args.command == "diff":
            diff = diff_project_graphs(Path(args.base_program), Path(args.target_program), args.module, args.graph)
            print(json.dumps(diff.to_dict(), ensure_ascii=False, sort_keys=True))
            return 0

        if args.command in {"node-edit-preview", "node-edit-commit"}:
            input_path = Path(args.program)
            raw_ops = json.loads(Path(args.ops).read_text(encoding="utf-8"))
            operations = decode_node_graph_edits(raw_ops)
            candidate = preview_node_graph_edit_project(
                input_path, args.module, args.graph, operations, rationale=args.rationale
            )
            if args.command == "node-edit-preview":
                print(json.dumps(project_audit_view(candidate), ensure_ascii=False, sort_keys=True))
                return 0
            payload = _write_candidate_project(input_path, Path(args.output), candidate, label="node-edit-commit")
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            return 0

        if args.command in {"formula-edit-preview", "formula-edit-commit"}:
            input_path = Path(args.program)
            candidate = preview_formula_edit_project(
                input_path, args.module, args.graph, args.node, args.formula, rationale=args.rationale
            )
            if args.command == "formula-edit-preview":
                print(json.dumps(project_audit_view(candidate), ensure_ascii=False, sort_keys=True))
                return 0
            payload = _write_candidate_project(input_path, Path(args.output), candidate, label="formula-edit-commit")
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            return 0

        if args.command == "notebook-run":
            notebook_value = decode_notebook(Path(args.notebook).read_text(encoding="utf-8"))
            raw_inputs = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
            raw_parameters = {}
            if args.parameters:
                raw_parameters = json.loads(Path(args.parameters).read_text(encoding="utf-8"))
            result = run_project_notebook(
                Path(args.program),
                notebook_value,
                {str(k): _runtime_value(v) for k, v in raw_inputs.items()},
                parameters={str(k): _runtime_value(v) for k, v in raw_parameters.items()},
                backend=args.backend,
            )
            payload = {
                "ok": True,
                "notebook_hash": result.notebook_hash,
                "cells": [
                    {
                        "id": cell.cell_id,
                        "module_id": cell.module_id,
                        "graph_id": cell.graph_id,
                        "graph_semantic_hash": cell.graph_semantic_hash,
                        "dependency_cells": list(cell.dependency_cells),
                        "backend": cell.backend,
                        "outputs": _jsonable(dict(cell.outputs)),
                        "output_digest": cell.output_digest,
                        "output_summaries": {name: dict(summary) for name, summary in cell.output_summaries.items()},
                    }
                    for cell in result.cells
                ],
            }
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            return 0

        if args.command in {"edit-preview", "edit-commit"}:
            input_path = Path(args.program)
            edited_text = Path(args.edited).read_text(encoding="utf-8")
            candidate = preview_structured_edit(
                input_path, args.module, args.graph, edited_text, rationale=args.rationale
            )
            if args.command == "edit-preview":
                print(json.dumps(project_audit_view(candidate), ensure_ascii=False, sort_keys=True))
                return 0
            output_path = Path(args.output)
            try:
                same_target = input_path.resolve() == output_path.resolve()
            except OSError:
                same_target = input_path.absolute() == output_path.absolute()
            if same_target:
                raise ProjectionEditError("edit-commit refuses to overwrite the input project")
            output_path.write_text(encode_project(candidate.candidate_project), encoding="utf-8")
            print(json.dumps({
                "ok": True,
                "output": str(output_path),
                "before_semantic_hash": candidate.before_semantic_hash,
                "candidate_semantic_hash": candidate.candidate_semantic_hash,
                "before_record_hash": candidate.before_record_hash,
                "candidate_record_hash": candidate.candidate_record_hash,
            }, ensure_ascii=False, sort_keys=True))
            return 0

        project = load_project(Path(args.program))
        if args.command == "check":
            print(json.dumps({"ok": True, "semantic_hash": semantic_hash(project)}, sort_keys=True))
            return 0
        if args.command == "hash":
            print(json.dumps({"semantic_hash": semantic_hash(project)}, sort_keys=True))
            return 0
        if args.command == "run":
            raw_inputs = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
            raw_parameters = {}
            if args.parameters:
                raw_parameters = json.loads(Path(args.parameters).read_text(encoding="utf-8"))
            result = run_project(
                project,
                args.module,
                args.graph,
                {str(k): _runtime_value(v) for k, v in raw_inputs.items()},
                parameters={str(k): _runtime_value(v) for k, v in raw_parameters.items()},
                backend=args.backend,
            )
            payload = {
                "ok": True,
                "outputs": _jsonable(dict(result.outputs)),
                "trace": [
                    {
                        "node_id": record.node_id,
                        "kind": record.kind,
                        "inputs": list(record.inputs),
                        "outputs": list(record.outputs),
                        "result_shape": list(record.result_shape) if record.result_shape is not None else None,
                        "result_type": record.result_type,
                    }
                    for record in result.trace.records
                ],
            }
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            return 0
        if args.command == "project":
            graph = find_graph(project, args.module, args.graph)
            if args.view == "text":
                print(project_text(graph))
            elif args.view == "formula":
                print(project_formula(graph))
            elif args.view == "graph":
                print(json.dumps(project_graph_view(graph), ensure_ascii=False, sort_keys=True))
            else:
                print(project_editable_text(graph), end="")
            return 0
        if args.command == "train":
            raw_inputs = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
            raw_parameters = json.loads(Path(args.parameters).read_text(encoding="utf-8"))
            config = TrainingConfig(
                target=args.target,
                wrt=tuple(args.wrt),
                steps=args.steps,
                learning_rate=args.learning_rate,
                backend=args.backend,
            )
            result = train_project(
                project,
                args.module,
                args.graph,
                {str(k): _runtime_value(v) for k, v in raw_inputs.items()},
                {str(k): _runtime_value(v) for k, v in raw_parameters.items()},
                config,
            )
            payload = {
                "ok": True,
                "target": config.target,
                "wrt": list(config.wrt),
                "steps": config.steps,
                "learning_rate": config.learning_rate,
                "initial_loss": result.initial_loss,
                "final_loss": result.final_loss,
                "loss_history": list(result.state.loss_history),
                "final_parameters": _jsonable(dict(result.state.parameters)),
                "parameter_state_hash": result.state.parameter_state_hash,
                "graph_semantic_hash": result.state.graph_semantic_hash,
                "derivative_graph_id": result.derivative_graph_id,
                "derivative_semantic_hash": result.derivative_semantic_hash,
            }
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            return 0

        if args.command == "grad":
            raw_inputs = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
            raw_parameters = {}
            if args.parameters:
                raw_parameters = json.loads(Path(args.parameters).read_text(encoding="utf-8"))
            inputs = {str(k): _runtime_value(v) for k, v in raw_inputs.items()}
            parameters = {str(k): _runtime_value(v) for k, v in raw_parameters.items()}
            request = DifferentiationRequest(
                target=args.target,
                wrt=tuple(args.wrt),
                seed_input=args.seed_input,
            )
            run = run_project_gradient(
                project,
                args.module,
                args.graph,
                inputs,
                request,
                parameters=parameters,
                backend=args.backend,
            )
            primal = find_graph(project, args.module, args.graph)
            check_payload = None
            if args.check:
                checked = check_gradient(
                    primal,
                    inputs,
                    request,
                    parameters=parameters,
                )
                check_payload = {
                    "passed": checked.passed,
                    "max_abs_error": dict(checked.max_abs_error),
                    "max_rel_error": dict(checked.max_rel_error),
                    "epsilon": checked.epsilon,
                    "rtol": checked.rtol,
                    "atol": checked.atol,
                }
            payload = {
                "ok": True,
                "target": request.target,
                "derivative_graph_id": run.derivative.graph.id,
                "primal_semantic_hash": semantic_hash(primal),
                "derivative_semantic_hash": semantic_hash(run.derivative.graph),
                "gradients": {
                    symbol: _jsonable(run.execution.outputs[gradient_symbol(symbol)])
                    for symbol in request.wrt
                },
                "check": check_payload,
            }
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            return 0
        return 2
    except NovaError as exc:
        print(json.dumps({"ok": False, "error": exc.to_dict()}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": {"category": type(exc).__name__, "message": str(exc)}}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

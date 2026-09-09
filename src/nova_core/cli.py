from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from .api import find_graph, load_project, run_project, run_project_gradient, train_project
from .autodiff import DifferentiationRequest, gradient_symbol
from .canonical import semantic_hash
from .errors import NovaError
from .gradcheck import check_gradient
from .projection import project_formula, project_text
from .training import TrainingConfig


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
    project.add_argument("--view", choices=("text", "formula"), required=True)

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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
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
            print(project_text(graph) if args.view == "text" else project_formula(graph))
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

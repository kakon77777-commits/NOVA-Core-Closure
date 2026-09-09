from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from .api import find_graph, load_project, run_project
from .canonical import semantic_hash
from .errors import NovaError
from .projection import project_formula, project_text


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
        return 2
    except NovaError as exc:
        print(json.dumps({"ok": False, "error": exc.to_dict()}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": {"category": type(exc).__name__, "message": str(exc)}}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

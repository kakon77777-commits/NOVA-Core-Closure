from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from nova_core import Graph, Module, Node, Project
from nova_core.codec import encode_project


def _run_cli(*args: str):
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    return subprocess.run([sys.executable, "-m", "nova_core.cli", *args], text=True, encoding="utf-8", capture_output=True, env=env, check=False)


def _dense_project():
    return Project(modules=(Module(id="app", graphs=(Graph(id="main", inputs=("x","w"), outputs=("y",), nodes=(
        Node(id="mm", kind="MatMul", inputs=("x","w"), outputs=("y",)),
    )),)),))


def test_python_api_plans_project_and_returns_parallel_for_dense():
    from nova_core import plan_project_paradigms
    plan = plan_project_paradigms(_dense_project(), "app", "main")
    assert plan.selected[0].tag.fill.value == "P"
    assert plan.graph_hash.startswith("sha256:")


def test_cli_paradigm_classify_and_plan(tmp_path: Path):
    program = tmp_path / "program.json"
    program.write_text(encode_project(_dense_project()), encoding="utf-8")
    classified = _run_cli("paradigm", "classify", str(program))
    assert classified.returncode == 0, classified.stderr
    cp = json.loads(classified.stdout)
    assert cp["ok"] is True
    assert cp["regions"][0]["candidates"][0]["tag"]["fill"] in {"C","P"}

    planned = _run_cli("paradigm", "plan", str(program))
    assert planned.returncode == 0, planned.stderr
    pp = json.loads(planned.stdout)
    assert pp["ok"] is True
    assert pp["selected"][0]["tag"]["fill"] == "P"
    assert pp["plan_hash"].startswith("sha256:")


def test_cli_validate_bonds_reports_illegal_r_after_stable_recognition():
    result = _run_cli("paradigm", "validate-bonds", "DRD", "DPD")
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert any(v["rule"] == "recognition_terminal" for v in payload["decision"]["violations"])


def test_cli_validate_bonds_accepts_explicit_reset():
    result = _run_cli("paradigm", "validate-bonds", "DRD", "DCD", "--reset-after", "0")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert any(o["kind"] == "stability_reset" for o in payload["decision"]["obligations"])

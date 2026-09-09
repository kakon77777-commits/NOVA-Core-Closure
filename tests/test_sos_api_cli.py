from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from nova_core import (
    Interpreter,
    compose_operator_ids,
    list_operator_descriptors,
    lower_operator_ids,
    validate_operator_ids,
)


def _run_cli(*args: str):
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    return subprocess.run(
        [sys.executable, "-m", "nova_core.cli", *args],
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=env,
        check=False,
    )


def test_python_sos_api_lists_validates_composes_and_lowers():
    descriptors = list_operator_descriptors()
    assert [d.operator_id for d in descriptors] == ["identity", "negate", "relu", "sigmoid", "softmax", "tanh"]

    validated = validate_operator_ids(("relu", "tanh"))
    assert validated["status"] == "safe"
    assert validated["member_ids"] == ["relu", "tanh"]

    closure = compose_operator_ids(("relu", "tanh"))
    assert closure.member_ids == ("relu", "tanh")

    project = lower_operator_ids(("relu", "tanh"))
    graph = project.modules[0].graphs[0]
    x = np.asarray([-1.0, 0.5])
    result = Interpreter().run_graph(graph, {"x": x})
    np.testing.assert_allclose(result.outputs["y"], np.maximum(np.tanh(x), 0))


def test_cli_sos_list_validate_compose_and_lower(tmp_path: Path):
    listed = _run_cli("sos", "list")
    assert listed.returncode == 0, listed.stderr
    listed_payload = json.loads(listed.stdout)
    assert listed_payload["ok"] is True
    assert listed_payload["operator_ids"] == ["identity", "negate", "relu", "sigmoid", "softmax", "tanh"]

    validated = _run_cli("sos", "validate", "relu", "tanh")
    assert validated.returncode == 0, validated.stderr
    vp = json.loads(validated.stdout)
    assert vp["status"] == "safe"
    assert [c["stage"] for c in vp["reports"][-1]["checks"]] == ["C", "G", "S", "EFFECT"]

    composed = _run_cli("sos", "compose", "relu", "tanh")
    assert composed.returncode == 0, composed.stderr
    cp = json.loads(composed.stdout)
    assert cp["ok"] is True
    assert cp["member_ids"] == ["relu", "tanh"]
    assert cp["closure_hash"].startswith("sha256:")

    out = tmp_path / "lowered.json"
    lowered = _run_cli("sos", "lower", "relu", "tanh", "--output", str(out))
    assert lowered.returncode == 0, lowered.stderr
    lp = json.loads(lowered.stdout)
    assert lp["ok"] is True
    assert out.exists()
    assert lp["output"] == str(out)


def test_cli_sos_depth_failure_is_structured_and_nonzero():
    result = _run_cli("sos", "validate", "relu", "tanh", "negate", "--max-depth", "2")
    assert result.returncode == 1
    payload = json.loads(result.stderr)
    assert payload["ok"] is False
    assert payload["error"]["category"] == "CompositionDepthError"

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from nova_core.api import find_graph, load_project, run_graph
from nova_core.autodiff import DifferentiationRequest
from nova_core.canonical import semantic_hash
from nova_core.gradcheck import check_gradient
from nova_core.training import TrainingConfig, train_graph


ROOT = Path(__file__).resolve().parents[1] / "examples"


def _runtime_map(path: Path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {key: np.asarray(value) for key, value in raw.items()}


def test_small_attention_closes_primal_ad_gradcheck_and_training_gate() -> None:
    project = load_project(ROOT / "training_attention.json")
    graph = find_graph(project, "app", "main")
    inputs = _runtime_map(ROOT / "training_attention_inputs.json")
    parameters = _runtime_map(ROOT / "training_attention_parameters.json")
    before = semantic_hash(graph)

    interp = run_graph(graph, inputs, parameters=parameters, backend="interpreter").outputs["loss"]
    numpy_loss = run_graph(graph, inputs, parameters=parameters, backend="numpy").outputs["loss"]
    np.testing.assert_allclose(interp, numpy_loss, rtol=0, atol=0)

    checked = check_gradient(
        graph,
        inputs,
        DifferentiationRequest(target="loss", wrt=("WQ", "WV")),
        parameters=parameters,
        epsilon=1e-6,
        rtol=1e-4,
        atol=1e-6,
    )
    assert checked.passed is True
    assert max(checked.max_abs_error.values()) < 1e-7

    trained = train_graph(
        graph,
        inputs,
        parameters,
        TrainingConfig(target="loss", wrt=("WQ", "WK", "WV", "WO"), steps=100, learning_rate=0.05),
    )
    assert trained.final_loss < trained.initial_loss * 0.02
    assert semantic_hash(graph) == before

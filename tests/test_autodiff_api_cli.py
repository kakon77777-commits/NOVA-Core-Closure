import json

import numpy as np

from nova_core import Graph, Module, Node, Project, TensorType
from nova_core.api import differentiate_project, run_project_gradient
from nova_core.autodiff import DifferentiationRequest, differentiate_graph, gradient_symbol
from nova_core.cli import main
from nova_core.codec import encode_project
from nova_core.projection import project_formula, project_text


def differentiable_project() -> Project:
    graph = Graph(
        id="main",
        inputs=("x",),
        outputs=("loss",),
        nodes=(
            Node(id="p", kind="Parameter", outputs=("w",), attributes={"name": "weight"}),
            Node(id="mul", kind="Multiply", inputs=("x", "w"), outputs=("y",)),
            Node(id="sq", kind="Multiply", inputs=("y", "y"), outputs=("sq",)),
            Node(id="mean", kind="Mean", inputs=("sq",), outputs=("loss",), attributes={"axis": None}, value_type=TensorType.scalar("f64")),
        ),
    )
    return Project(modules=(Module(id="app", graphs=(graph,)),))


def test_api_differentiates_and_runs_project_gradient():
    project = differentiable_project()
    request = DifferentiationRequest(target="loss", wrt=("w",))
    derivative = differentiate_project(project, "app", "main", request)
    assert derivative.graph.id.startswith("main__rev__loss__")

    run = run_project_gradient(
        project,
        "app",
        "main",
        {"x": np.array([1.0, 2.0])},
        request,
        parameters={"weight": np.array([3.0, 4.0])},
        backend="numpy",
    )
    np.testing.assert_allclose(run.execution.outputs[gradient_symbol("w")], np.array([3.0, 16.0]))
    assert run.derivative.graph.id == derivative.graph.id


def test_derivative_graph_has_text_and_formula_projections():
    graph = differentiable_project().modules[0].graphs[0]
    derivative = differentiate_graph(graph, DifferentiationRequest(target="loss", wrt=("w",))).graph
    text = project_text(derivative)
    formula = project_formula(derivative)
    assert "ad_mean_grad" in text
    assert gradient_symbol("w") in text
    assert gradient_symbol("w") in formula
    assert "reduceToShape" in formula or "meanGrad" in formula


def test_cli_grad_runs_derivative_graph_and_optional_check(tmp_path, capsys):
    program = tmp_path / "program.json"
    program.write_text(encode_project(differentiable_project()), encoding="utf-8")
    inputs = tmp_path / "inputs.json"
    inputs.write_text(json.dumps({"x": [1.0, 2.0]}), encoding="utf-8")
    parameters = tmp_path / "parameters.json"
    parameters.write_text(json.dumps({"weight": [3.0, 4.0]}), encoding="utf-8")

    rc = main([
        "grad",
        str(program),
        "--module", "app",
        "--graph", "main",
        "--target", "loss",
        "--wrt", "w",
        "--inputs", str(inputs),
        "--parameters", str(parameters),
        "--backend", "numpy",
        "--check",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["target"] == "loss"
    assert payload["gradients"]["w"] == [3.0, 16.0]
    assert payload["check"]["passed"] is True
    assert payload["derivative_semantic_hash"].startswith("sha256:")

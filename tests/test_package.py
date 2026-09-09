from pathlib import Path
import json

import nova_core
from nova_core import decode_project, run_project, semantic_hash

ROOT = Path(__file__).resolve().parents[1]


def test_round05_package_version():
    assert nova_core.__version__ == "0.5.0"


def test_readme_marks_round05_implemented_and_round06_next():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Round 05 — Model Closure & Training Validation" in text
    assert "**Implemented.**" in text
    assert "Round 06" in text


def test_pyproject_version_dependency_and_cli_entrypoint():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.0"' in text
    assert 'numpy>=' in text
    assert 'nova = "nova_core.cli:main"' in text


def test_executable_linear_example_runs():
    project = decode_project((ROOT / "examples" / "executable_linear.json").read_text(encoding="utf-8"))
    inputs = json.loads((ROOT / "examples" / "executable_inputs.json").read_text(encoding="utf-8"))
    result = run_project(project, "app", "main", inputs, backend="numpy")
    assert result.outputs["Y"].tolist() == [[8.5]]
    assert semantic_hash(project).startswith("sha256:")


def test_default_schema_header_tracks_round05_core_version_without_schema_break():
    assert nova_core.SchemaHeader().nova_core_version == "0.5.0"
    assert nova_core.SchemaHeader().schema_version == "0.1.0"


def test_differentiable_linear_example_and_parameter_files_exist():
    assert (ROOT / "examples" / "differentiable_linear.json").exists()
    assert (ROOT / "examples" / "differentiable_inputs.json").exists()
    assert (ROOT / "examples" / "differentiable_parameters.json").exists()


def test_differentiable_linear_example_runs_gradient_and_finite_difference_check():
    import numpy as np
    from nova_core import DifferentiationRequest, check_gradient, find_graph, gradient_symbol, run_project, run_project_gradient

    project = decode_project((ROOT / "examples" / "differentiable_linear.json").read_text(encoding="utf-8"))
    inputs = json.loads((ROOT / "examples" / "differentiable_inputs.json").read_text(encoding="utf-8"))
    parameters = json.loads((ROOT / "examples" / "differentiable_parameters.json").read_text(encoding="utf-8"))
    primal = run_project(project, "app", "main", inputs, parameters=parameters, backend="numpy")
    np.testing.assert_allclose(primal.outputs["loss"], 1.125)

    request = DifferentiationRequest(target="loss", wrt=("W", "b"))
    gradient_run = run_project_gradient(project, "app", "main", inputs, request, parameters=parameters, backend="numpy")
    np.testing.assert_allclose(gradient_run.execution.outputs[gradient_symbol("W")], np.array([[1.5], [3.0]]))
    np.testing.assert_allclose(gradient_run.execution.outputs[gradient_symbol("b")], np.array([1.5]))

    checked = check_gradient(find_graph(project, "app", "main"), inputs, request, parameters=parameters)
    assert checked.passed


def test_round05_training_examples_exist_and_decode():
    for name in ("linear", "mlp", "attention"):
        program = ROOT / "examples" / f"training_{name}.json"
        inputs = ROOT / "examples" / f"training_{name}_inputs.json"
        parameters = ROOT / "examples" / f"training_{name}_parameters.json"
        assert program.exists() and inputs.exists() and parameters.exists()
        project = decode_project(program.read_text(encoding="utf-8"))
        assert project.header.nova_core_version == "0.5.0"
        json.loads(inputs.read_text(encoding="utf-8"))
        json.loads(parameters.read_text(encoding="utf-8"))

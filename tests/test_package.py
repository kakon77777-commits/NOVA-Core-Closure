from pathlib import Path
import json

import nova_core
from nova_core import decode_project, run_project, semantic_hash

ROOT = Path(__file__).resolve().parents[1]


def test_round03_package_version():
    assert nova_core.__version__ == "0.3.0"


def test_readme_marks_round03_implemented_and_round04_next():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Round 03 — Executable Closure" in text
    assert "**Implemented.**" in text
    assert "Round 04 — Reverse-Mode Automatic Differentiation" in text


def test_pyproject_version_dependency_and_cli_entrypoint():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.3.0"' in text
    assert 'numpy>=' in text
    assert 'nova = "nova_core.cli:main"' in text


def test_executable_linear_example_runs():
    project = decode_project((ROOT / "examples" / "executable_linear.json").read_text(encoding="utf-8"))
    inputs = json.loads((ROOT / "examples" / "executable_inputs.json").read_text(encoding="utf-8"))
    result = run_project(project, "app", "main", inputs, backend="numpy")
    assert result.outputs["Y"].tolist() == [[8.5]]
    assert semantic_hash(project).startswith("sha256:")


def test_default_schema_header_tracks_round03_core_version_without_schema_break():
    assert nova_core.SchemaHeader().nova_core_version == "0.3.0"
    assert nova_core.SchemaHeader().schema_version == "0.1.0"

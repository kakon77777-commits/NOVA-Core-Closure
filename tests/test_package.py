from pathlib import Path

import nova_core
from nova_core import TensorType, decode_project, semantic_hash


ROOT = Path(__file__).resolve().parents[1]


def test_round02_package_version():
    assert nova_core.__version__ == "0.2.0"


def test_readme_marks_round02_implemented_and_round03_next():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Round 02 — Tensor / Shape Semantic Kernel" in text
    assert "**Implemented.**" in text
    assert "Round 03 — Executable Closure" in text


def test_pyproject_version_is_round02():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.2.0"' in text


def test_tensor_shape_example_is_decodable_and_typed():
    example = ROOT / "examples" / "tensor_shape_graph.json"
    project = decode_project(example.read_text(encoding="utf-8"))
    node = project.modules[0].graphs[0].nodes[0]
    assert isinstance(node.value_type, TensorType)
    assert semantic_hash(project).startswith("sha256:")


def test_default_schema_header_tracks_round02_core_version():
    assert nova_core.SchemaHeader().nova_core_version == "0.2.0"
    assert nova_core.SchemaHeader().schema_version == "0.1.0"

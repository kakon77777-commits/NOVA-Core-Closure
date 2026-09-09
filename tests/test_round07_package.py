from pathlib import Path
import tomllib

import nova_core

ROOT = Path(__file__).resolve().parents[1]


def test_round07_compatibility_floor_and_docs():
    assert tuple(map(int, nova_core.__version__.split("."))) >= (0, 7, 0)
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == nova_core.__version__
    assert (ROOT / "docs/rounds/ROUND_07_PROJECTION_INTEGRITY_STRUCTURED_EDITING.md").exists()
    assert (ROOT / "docs/G2_CORE_VERIFICATION_MATRIX.md").exists()


def test_round07_examples_exist():
    assert (ROOT / "examples/editing/base_project.json").exists()
    assert (ROOT / "examples/editing/edited_graph.json").exists()


def test_readme_marks_round07_and_next_g2_work():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Round 07" in text
    assert "Projection Integrity" in text
    assert "Candidate GraphPatch" in text
    assert "Round 08" in text

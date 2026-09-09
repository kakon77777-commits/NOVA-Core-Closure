import json
from pathlib import Path

import nova_core
from nova_core import SchemaHeader

ROOT = Path(__file__).resolve().parents[1]


def test_round08_version_and_schema_header_default():
    assert nova_core.__version__ == "0.8.0"
    header = SchemaHeader()
    assert header.nova_core_version == "0.8.0"
    assert header.schema_version == "0.1.0"


def test_round08_g2_final_seal_artifacts_exist_and_are_machine_readable():
    assert (ROOT / "docs/rounds/ROUND_08_INTERACTIVE_EDITING_NOTEBOOK_G2_FINAL_SEAL.md").exists()
    assert (ROOT / "docs/G2_VERIFICATION_MATRIX.md").exists()
    seal = json.loads((ROOT / "examples/g2_verification.json").read_text(encoding="utf-8"))
    assert seal["g2"]["status"] == "SEALED"
    assert seal["g2"]["projection_hash_invariance"] is True
    assert seal["g2"]["node_graph_editing"] is True
    assert seal["g2"]["formula_editing"] == "bounded-local"
    assert seal["g2"]["notebook"] == "graph-cell-prototype"
    assert seal["project"]["version"] == "0.8.0"


def test_readme_marks_g2_sealed_and_round09_g3_next():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Round 08" in text
    assert "G2" in text and "sealed" in text.lower()
    assert "Notebook" in text
    assert "Round 09" in text
    assert "G3" in text


def test_round08_examples_exist():
    for name in (
        "notebook_chain_program.json",
        "notebook_chain.json",
        "notebook_chain_inputs.json",
    ):
        assert (ROOT / "examples" / name).exists()

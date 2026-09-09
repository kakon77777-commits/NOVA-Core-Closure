from pathlib import Path
import json

import numpy as np
import nova_core

ROOT = Path(__file__).resolve().parents[1]


def test_round06_package_version_and_schema_header():
    assert nova_core.__version__ == "0.6.0"
    assert nova_core.SchemaHeader().nova_core_version == "0.6.0"
    assert nova_core.SchemaHeader().schema_version == "0.1.0"


def test_readme_marks_round06_implemented_and_round07_g2_next():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Round 06 — DLPack / Interop & G1 Final Seal" in text
    round06 = text.split("Round 06 — DLPack / Interop & G1 Final Seal", 1)[1]
    assert "**Implemented.**" in round06
    assert "Round 07" in round06
    assert "G2" in round06


def test_round06_docs_and_machine_readable_g1_matrix_exist():
    assert (ROOT / "docs" / "rounds" / "ROUND_06_DLPACK_INTEROP_G1_FINAL_SEAL.md").exists()
    assert (ROOT / "docs" / "G1_VERIFICATION_MATRIX.md").exists()
    matrix_path = ROOT / "examples" / "g1_verification.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert matrix["gate"] == "G1"
    assert matrix["status"] == "sealed"
    required = {
        "graph_schema",
        "tensor_shape",
        "interpreter",
        "numpy_cpu_backend",
        "reverse_mode_ad",
        "cli",
        "projections",
        "python_numpy_interop",
        "dlpack_interop",
        "linear_regression",
        "mlp",
        "small_attention",
        "deterministic_identity",
        "typed_failure",
    }
    assert required <= set(matrix["requirements"])
    assert all(matrix["requirements"][key]["status"] == "pass" for key in required)


def test_round06_dlpack_zero_copy_smoke():
    source = np.arange(8, dtype=np.float32).reshape(2, 4)
    capsule = nova_core.to_dlpack(source)
    restored = nova_core.from_dlpack(capsule)
    np.testing.assert_array_equal(restored, source)
    assert np.shares_memory(restored, source)


def test_pyproject_round06_version():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.0"' in text

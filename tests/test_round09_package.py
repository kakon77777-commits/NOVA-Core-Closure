import json
from pathlib import Path

import nova_core
from nova_core import SchemaHeader

ROOT = Path(__file__).resolve().parents[1]


def test_round09_version_and_schema_header_default():
    current = tuple(int(x) for x in nova_core.__version__.split("."))
    assert current >= (0, 9, 0)
    assert SchemaHeader().nova_core_version == nova_core.__version__
    assert SchemaHeader().schema_version == "0.1.0"


def test_round09_g3_final_seal_artifacts_exist_and_are_machine_readable():
    assert (ROOT / "docs/rounds/ROUND_09_G3_RESOURCE_PLANNING_FINAL_SEAL.md").exists()
    assert (ROOT / "docs/G3_VERIFICATION_MATRIX.md").exists()
    seal = json.loads((ROOT / "examples/g3_verification.json").read_text(encoding="utf-8"))
    assert seal["g3"]["status"] == "SEALED"
    assert seal["g3"]["deterministic_lifetime_analysis"] is True
    assert seal["g3"]["buffer_reuse_verified"] is True
    assert seal["g3"]["device_transfer_verified"] is True
    assert seal["g3"]["unsafe_candidate_fallback"] is True
    assert seal["project"]["version"] == "0.9.0"


def test_round09_resource_examples_exist():
    for name in (
        "static_reuse_project.json",
        "static_reuse_types.json",
        "device_transfer_project.json",
        "device_transfer_types.json",
    ):
        assert (ROOT / "examples/resource_planning" / name).exists()


def test_readme_marks_g3_sealed_and_round10_g4_next():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Round 09" in text
    assert "G3" in text and "sealed" in text.lower()
    assert "MemoryPlan" in text
    assert "Round 10" in text
    assert "G4" in text

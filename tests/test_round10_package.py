from __future__ import annotations

import json
from pathlib import Path

import nova_core
from nova_core import SchemaHeader


def version_tuple(value: str):
    return tuple(int(x) for x in value.split("."))


def test_round10_runtime_version_and_schema_compatibility():
    assert nova_core.__version__ == "0.10.0"
    assert SchemaHeader().nova_core_version == "0.10.0"
    assert SchemaHeader().schema_version == "0.1.0"
    assert version_tuple(nova_core.__version__) >= (0, 10, 0)


def test_round10_g4_seal_artifacts_exist_and_are_machine_readable():
    assert Path("docs/G4_VERIFICATION_MATRIX.md").exists()
    assert Path("docs/rounds/ROUND_10_G4_NOVA_A_FINAL_SEAL.md").exists()
    seal = json.loads(Path("examples/g4_verification.json").read_text(encoding="utf-8"))
    assert seal["gate"] == "G4"
    assert seal["status"] == "sealed"
    assert seal["runtime_version"] == "0.10.0"
    assert seal["schema_version"] == "0.1.0"
    assert seal["acceptance"]["add_layer"] is True
    assert seal["acceptance"]["differentiation_request"] is True
    assert seal["acceptance"]["sandbox_rejection"] is True
    assert seal["acceptance"]["rollback"] is True


def test_round10_examples_exist():
    for path in (
        "examples/ai_build/base_project.json",
        "examples/ai_build/add_relu_request.json",
        "examples/ai_build/typed_shape_request.json",
        "examples/ai_build/effectful_rejected_request.json",
    ):
        assert Path(path).exists(), path

from __future__ import annotations

import json
from pathlib import Path

import nova_core
from nova_core import SchemaHeader


def test_round11_runtime_version_and_schema_compatibility():
    assert nova_core.__version__ == "0.11.0"
    assert SchemaHeader().nova_core_version == "0.11.0"
    assert SchemaHeader().schema_version == "0.1.0"


def test_round11_g5_seal_artifacts_exist_and_are_machine_readable():
    assert Path("docs/G5_VERIFICATION_MATRIX.md").exists()
    assert Path("docs/rounds/ROUND_11_G5_SOS_CLSAFE_FINAL_SEAL.md").exists()
    seal = json.loads(Path("releases/rounds/round-11/G5_SEAL.json").read_text(encoding="utf-8"))
    assert seal["gate"] == "G5"
    assert seal["status"] == "sealed"
    assert seal["runtime_version"] == "0.11.0"
    assert seal["schema_version"] == "0.1.0"
    for key in (
        "legal_composition",
        "comp_collapse",
        "sem_divergence",
        "projection_incoherence",
        "effect_conflict",
        "broken_operator_isolation",
        "depth_limit",
        "nova_lowering",
    ):
        assert seal["acceptance"][key] is True


def test_round11_examples_exist():
    for path in (
        "examples/sos/legal_chain.json",
        "examples/sos/comp_collapse.json",
        "examples/sos/sem_divergence.json",
        "examples/sos/projection_incoherence.json",
        "examples/sos/effect_conflict.json",
    ):
        assert Path(path).exists(), path

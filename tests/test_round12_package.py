from __future__ import annotations

import json
from pathlib import Path

import nova_core
from nova_core import SchemaHeader


def version_tuple(value: str):
    return tuple(int(x) for x in value.split("."))


def test_round12_runtime_version_and_schema_compatibility():
    assert version_tuple(nova_core.__version__) >= (0, 12, 0)
    assert SchemaHeader().nova_core_version == nova_core.__version__
    assert SchemaHeader().schema_version == "0.1.0"


def test_round12_g6_seal_artifacts_exist_and_are_machine_readable():
    assert Path("docs/G6_VERIFICATION_MATRIX.md").exists()
    assert Path("docs/rounds/ROUND_12_G6_PARADIGM_PLANNER_FINAL_SEAL.md").exists()
    seal = json.loads(Path("releases/rounds/round-12/G6_SEAL.json").read_text(encoding="utf-8"))
    assert seal["gate"] == "G6"
    assert seal["status"] == "sealed"
    assert seal["runtime_version"] == "0.12.0"
    assert seal["schema_version"] == "0.1.0"
    for key in ("dense_parallel", "sparse_jump", "sequential", "stable_recognition", "bonding", "fallback"):
        assert seal["acceptance"][key] is True


def test_round12_examples_exist():
    for path in (
        "examples/paradigm/dense_parallel.json",
        "examples/paradigm/sparse_jump.json",
        "examples/paradigm/sequential_loop.json",
        "examples/paradigm/stable_recognition.json",
    ):
        assert Path(path).exists(), path

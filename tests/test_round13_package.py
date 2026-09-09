from __future__ import annotations

import json
from pathlib import Path

import nova_core
from nova_core import SchemaHeader


def test_round13_runtime_version_and_schema_contract():
    assert nova_core.__version__ == "0.13.0"
    assert SchemaHeader().nova_core_version == "0.13.0"
    assert SchemaHeader().schema_version == "0.1.0"


def test_round13_release_artifacts_exist_and_seal_is_machine_readable():
    root = Path(__file__).resolve().parents[1]
    expected = [
        root / "docs" / "G7_VERIFICATION_MATRIX.md",
        root / "docs" / "rounds" / "ROUND_13_G7_ISQL_FINAL_SEAL.md",
        root / "examples" / "isql" / "activation_tensor.json",
        root / "examples" / "isql" / "activation_templates.json",
        root / "examples" / "isql" / "activation_selection.json",
        root / "releases" / "rounds" / "round-13" / "G7_SEAL.json",
    ]
    assert all(path.exists() for path in expected)
    seal = json.loads(expected[-1].read_text(encoding="utf-8"))
    assert seal["runtime_version"] == "0.13.0"
    assert seal["graph_schema_version"] == "0.1.0"
    acceptance = seal["acceptance"]
    required = {
        "multi_candidate", "distinct_graph_hashes", "visible_ambiguity", "visible_obligations",
        "deterministic_confidence", "no_auto_unique_selection", "human_selection",
        "parent_linked_refinement", "rejected_or_stale_selection", "semantic_back_projection",
        "source_identity_invariance",
    }
    assert required <= set(acceptance)
    assert all(acceptance[name] is True for name in required)
    assert seal["comparative_natural_language_superiority_claimed"] is False

from __future__ import annotations

import copy
import pytest

from nova_core.cross_reconstruction import certify_triad, reconstruct_surface
from nova_core.errors import ValidationError

TEXT_SOURCE = r'''
# Human authoring surface; comments/whitespace are surface-only.
graph calculation(left, right) -> (answer)
temporary = Add(right, left) :: f32[Batch,8]
answer = Identity(temporary)
'''

GRAPH_SOURCE = {
    "format": "nova.graph-surface/0.8",
    "module": "graph_world",
    "graph": {
        "name": "native_graph",
        "inputs": ["x", "y"],
        "outputs": ["sum"],
        "nodes": [{
            "key": "g_add",
            "op": "Add",
            "args": ["x", "y"],
            "bind": ["sum"],
            "tensor": {"dtype": "f32", "shape": [{"symbol": "B"}, 8], "layout": "dense", "device": "cpu"},
        }],
    },
}

AI_SOURCE = {
    "format": "nova.ai-plan/0.8",
    "module": "ai_constructed_module",
    "graph": "machine_plan",
    "inputs": [{"slot": 0, "label": "lhs"}, {"slot": 1, "label": "rhs"}],
    "steps": [
        {
            "step": "reasoning_step_7",
            "operator": "Add",
            "args": [{"input": 1}, {"input": 0}],
            "bind": "work",
            "tensor": {"dtype": "f32", "dims": [{"binder": "Rows"}, 8], "layout": "dense", "device": "cpu"},
        },
        {
            "step": "presentation_alias",
            "operator": "Identity",
            "args": [{"value": "work"}],
            "bind": "final",
        },
    ],
    "outputs": [{"value": "final"}],
}


def test_three_independent_surfaces_converge_to_same_corenorm() -> None:
    cert = certify_triad(TEXT_SOURCE, GRAPH_SOURCE, AI_SOURCE)
    assert cert.converged
    assert cert.common_core_norm_hash
    assert len({item.core_norm_hash for item in cert.reconstructions}) == 1


def test_lowered_legacy_semantic_hashes_can_all_differ() -> None:
    cert = certify_triad(TEXT_SOURCE, GRAPH_SOURCE, AI_SOURCE)
    assert len({item.lowered_semantic_hash for item in cert.reconstructions}) == 3


def test_corenorm_bytes_match_across_all_three_surfaces() -> None:
    from nova_core.core_norm import core_norm_bytes
    results = [reconstruct_surface("text", TEXT_SOURCE), reconstruct_surface("graph", GRAPH_SOURCE), reconstruct_surface("ai", AI_SOURCE)]
    blobs = [core_norm_bytes(result.project) for result in results]
    assert blobs[0] == blobs[1] == blobs[2]


def test_text_whitespace_and_comment_change_surface_hash_but_not_corenorm() -> None:
    changed = "\n# another comment\n" + TEXT_SOURCE.replace("temporary =", "temporary    =")
    left = reconstruct_surface("text", TEXT_SOURCE)
    right = reconstruct_surface("text", changed)
    assert left.source_hash != right.source_hash
    assert left.lowered_semantic_hash == right.lowered_semantic_hash
    assert left.core_norm_hash == right.core_norm_hash


def test_graph_node_order_is_surface_order_not_corenorm_identity() -> None:
    extended = copy.deepcopy(GRAPH_SOURCE)
    extended["graph"]["outputs"] = ["answer"]
    extended["graph"]["nodes"] = [{"key": "alias", "op": "Identity", "args": ["sum"], "bind": ["answer"]}, extended["graph"]["nodes"][0]]
    left = reconstruct_surface("graph", GRAPH_SOURCE)
    right = reconstruct_surface("graph", extended)
    assert left.lowered_semantic_hash != right.lowered_semantic_hash
    assert left.core_norm_hash == right.core_norm_hash


def test_semantic_operator_mutation_breaks_convergence() -> None:
    bad_ai = copy.deepcopy(AI_SOURCE)
    bad_ai["steps"][0]["operator"] = "Subtract"
    cert = certify_triad(TEXT_SOURCE, GRAPH_SOURCE, bad_ai)
    assert not cert.converged
    assert cert.common_core_norm_hash is None


def test_ai_reference_must_be_resolvable() -> None:
    bad = copy.deepcopy(AI_SOURCE)
    bad["steps"][1]["args"] = [{"value": "never_bound"}]
    with pytest.raises(ValidationError, match="unknown value binding"):
        reconstruct_surface("ai", bad)


def test_text_surface_is_not_general_code_execution() -> None:
    bad = "graph g(x)->(y)\ny = __import__('os').system(x)"
    with pytest.raises(ValidationError, match="outside v0.8 grammar"):
        reconstruct_surface("text", bad)


def test_graph_surface_rejects_unresolved_argument() -> None:
    bad = copy.deepcopy(GRAPH_SOURCE)
    bad["graph"]["nodes"][0]["args"] = ["missing", "y"]
    with pytest.raises(ValidationError, match="unresolved node argument"):
        reconstruct_surface("graph", bad)


def test_certificate_preserves_bounded_claim() -> None:
    cert = certify_triad(TEXT_SOURCE, GRAPH_SOURCE, AI_SOURCE)
    record = cert.to_record()
    assert record["converged"]
    assert "not global language or behavioral equivalence" in record["claim_boundary"]
    assert len({entry["source_hash"] for entry in record["reconstructions"]}) == 3


def test_reconstruction_source_kind_is_explicit() -> None:
    with pytest.raises(ValidationError, match="unknown reconstruction surface kind"):
        reconstruct_surface("mystery", {})

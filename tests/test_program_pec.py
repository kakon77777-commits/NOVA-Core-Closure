from __future__ import annotations

from dataclasses import replace
import copy
import pytest

from nova_core.errors import ValidationError
from nova_core.program_pec import (
    DebtItem,
    DebtScope,
    DebtSeverity,
    DebtStatus,
    PECLevel,
    ProgramResourceBudget,
    ProgramVerificationEvidence,
    build_program_pec_certificate,
    decode_program_pec,
    encode_program_pec,
    default_v09_budget,
    default_v09_debts,
    default_v09_frame,
    default_v09_frontier,
    default_v09_reopen_conditions,
    replay_program_pec_certificate,
)


TEXT_SOURCE = r'''
# text route
# human comment should not define authority
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
        "nodes": [
            {
                "key": "g_add",
                "op": "Add",
                "args": ["x", "y"],
                "bind": ["sum"],
                "tensor": {"dtype": "f32", "shape": [{"symbol": "B"}, 8], "layout": "dense", "device": "cpu"},
            }
        ],
    },
}

AI_SOURCE = {
    "format": "nova.ai-plan/0.8",
    "module": "ai_constructed_module",
    "graph": "machine_plan",
    "inputs": [
        {"slot": 0, "label": "lhs"},
        {"slot": 1, "label": "rhs"},
    ],
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


def sources():
    return {"text": TEXT_SOURCE, "graph": copy.deepcopy(GRAPH_SOURCE), "ai": copy.deepcopy(AI_SOURCE)}


def verification(cases: int = 62):
    return ProgramVerificationEvidence(
        isolated_cases_passed=cases,
        isolated_cases_failed=0,
        standalone_harness_passed=True,
        upstream_full_suite_fresh=False,
        evidence_refs=("isolated-pytest", "standalone-harness"),
    )


def closed_certificate():
    return build_program_pec_certificate(
        sources(),
        frame=default_v09_frame(),
        budget=default_v09_budget(verification_case_budget=62),
        verification_summary=verification(62),
        debt_ledger=default_v09_debts(),
        frontier_map=default_v09_frontier(),
        reopen_conditions=default_v09_reopen_conditions(),
    )


def audit(cert, name):
    return next(item for item in cert.audits if item.name == name)


def test_declared_v09_domain_closes_as_dpec() -> None:
    cert = closed_certificate()
    assert cert.level is PECLevel.DPEC
    assert cert.status == "DPEC_CLOSED"
    assert cert.closed
    assert not cert.terminal_claim
    assert all(item.passed for item in cert.audits)


def test_confidence_vector_is_not_a_scalar_completion_claim() -> None:
    cert = closed_certificate()
    record = cert.confidence.to_record()
    assert set(record) == {"c_R", "c_N", "c_D", "c_F", "c_V", "c_A"}
    assert all(value == 1.0 for value in record.values())
    assert "not RGPEC" in cert.claim_boundary
    assert "not terminal completeness" in cert.claim_boundary


def test_certificate_is_deterministic_and_source_order_independent() -> None:
    left = closed_certificate()
    unordered = {"ai": copy.deepcopy(AI_SOURCE), "text": TEXT_SOURCE, "graph": copy.deepcopy(GRAPH_SOURCE)}
    right = build_program_pec_certificate(
        unordered,
        frame=default_v09_frame(),
        budget=default_v09_budget(verification_case_budget=62),
        verification_summary=verification(62),
        debt_ledger=default_v09_debts(),
        frontier_map=default_v09_frontier(),
        reopen_conditions=default_v09_reopen_conditions(),
    )
    assert left.to_record() == right.to_record()
    assert left.certificate_hash == right.certificate_hash


def test_missing_declared_route_reopens_reachability() -> None:
    cert = build_program_pec_certificate(
        {"text": TEXT_SOURCE, "graph": copy.deepcopy(GRAPH_SOURCE)},
        frame=default_v09_frame(),
        budget=default_v09_budget(),
        verification_summary=verification(62),
        debt_ledger=default_v09_debts(),
        frontier_map=default_v09_frontier(),
        reopen_conditions=default_v09_reopen_conditions(),
    )
    assert cert.status == "DPEC_OPEN"
    assert not audit(cert, "Reach").passed
    assert audit(cert, "Reach").score == pytest.approx(2 / 3)


def test_semantic_mutation_reopens_novelty_and_verification() -> None:
    bad = sources()
    bad["ai"]["steps"][0]["operator"] = "Subtract"
    cert = build_program_pec_certificate(
        bad,
        frame=default_v09_frame(),
        budget=default_v09_budget(),
        verification_summary=verification(62),
        debt_ledger=default_v09_debts(),
        frontier_map=default_v09_frontier(),
        reopen_conditions=default_v09_reopen_conditions(),
    )
    assert cert.status == "DPEC_OPEN"
    assert not audit(cert, "Novel").passed
    assert not audit(cert, "Verify").passed


def test_critical_in_claim_debt_blocks_closure() -> None:
    blocking = DebtItem(
        "DEBT-CRITICAL-TEST",
        "semantic",
        "A critical in-claim ambiguity remains unresolved.",
        DebtSeverity.CRITICAL,
        DebtStatus.OPEN,
        DebtScope.IN_CLAIM,
        "resolve the ambiguity and replay the certificate",
    )
    cert = build_program_pec_certificate(
        sources(),
        frame=default_v09_frame(),
        budget=default_v09_budget(),
        verification_summary=verification(62),
        debt_ledger=default_v09_debts() + (blocking,),
        frontier_map=default_v09_frontier(),
        reopen_conditions=default_v09_reopen_conditions(),
    )
    assert cert.status == "DPEC_OPEN"
    assert not audit(cert, "Debt").passed


def test_frontier_debt_can_remain_explicit_without_false_completion() -> None:
    cert = closed_certificate()
    assert any(item.status is DebtStatus.DEFERRED for item in cert.debt_ledger)
    assert all(item.scope is DebtScope.FRONTIER for item in cert.debt_ledger)
    assert audit(cert, "Debt").passed
    assert len(cert.frontier_map) >= 5
    assert "fresh_upstream_full_suite_not_in_scope" in cert.false_closure_risk_flags


def test_no_frontier_map_means_no_mature_pec() -> None:
    cert = build_program_pec_certificate(
        sources(),
        frame=default_v09_frame(),
        budget=default_v09_budget(),
        verification_summary=verification(62),
        debt_ledger=default_v09_debts(),
        frontier_map=(),
        reopen_conditions=default_v09_reopen_conditions(),
    )
    assert cert.status == "DPEC_OPEN"
    assert not audit(cert, "Frontier").passed


def test_no_reopen_conditions_means_no_closure_even_if_challenges_pass() -> None:
    cert = build_program_pec_certificate(
        sources(),
        frame=default_v09_frame(),
        budget=default_v09_budget(),
        verification_summary=verification(62),
        debt_ledger=default_v09_debts(),
        frontier_map=default_v09_frontier(),
        reopen_conditions=(),
    )
    assert cert.status == "DPEC_OPEN"
    assert not audit(cert, "Reopen").passed
    assert all(item.passed for item in cert.reopening_challenges)


def test_standard_reopening_challenges_are_real_fail_open_checks() -> None:
    cert = closed_certificate()
    assert {item.kind for item in cert.reopening_challenges} == {
        "operator_mutation",
        "reference_integrity",
        "surface_escape",
    }
    assert all(item.passed for item in cert.reopening_challenges)


def test_budget_boundary_is_part_of_certificate_scope() -> None:
    too_small = ProgramResourceBudget(
        budget_id="too-small",
        max_representation_routes=2,
        max_modules_per_project=1,
        max_graphs_per_module=1,
        max_nodes_per_graph=16,
        verification_case_budget=62,
        reopening_challenge_budget=4,
        tool_regime=("python-reference",),
    )
    with pytest.raises(ValidationError, match="representation-route budget"):
        build_program_pec_certificate(
            sources(),
            frame=default_v09_frame(),
            budget=too_small,
            verification_summary=verification(62),
            debt_ledger=default_v09_debts(),
            frontier_map=default_v09_frontier(),
            reopen_conditions=default_v09_reopen_conditions(),
        )


def test_v09_builder_refuses_rgpec_overclaim() -> None:
    with pytest.raises(ValidationError, match="only certifies domain-level"):
        build_program_pec_certificate(
            sources(),
            frame=default_v09_frame(),
            budget=default_v09_budget(),
            verification_summary=verification(62),
            debt_ledger=default_v09_debts(),
            frontier_map=default_v09_frontier(),
            reopen_conditions=default_v09_reopen_conditions(),
            level=PECLevel.RGPEC,
        )


def test_certificate_replay_verifies_evidence_and_detects_tamper() -> None:
    cert = closed_certificate()
    ok, errors = replay_program_pec_certificate(cert, sources())
    assert ok, errors
    tampered = replace(cert, state_ref="sha256:" + "0" * 64)
    ok, errors = replay_program_pec_certificate(tampered, sources())
    assert not ok
    assert any("state_ref" in item or "certificate hash" in item for item in errors)


def test_certificate_hash_changes_when_frame_changes() -> None:
    cert = closed_certificate()
    frame = replace(default_v09_frame(), assumptions=default_v09_frame().assumptions + ("new_assumption",))
    changed = build_program_pec_certificate(
        sources(),
        frame=frame,
        budget=default_v09_budget(),
        verification_summary=verification(62),
        debt_ledger=default_v09_debts(),
        frontier_map=default_v09_frontier(),
        reopen_conditions=default_v09_reopen_conditions(),
    )
    assert cert.certificate_hash != changed.certificate_hash
    assert cert.manifest_ref != changed.manifest_ref


def test_certificate_record_has_f04_style_closure_artifact_fields() -> None:
    record = closed_certificate().to_record()
    for key in (
        "claim_summary",
        "debt_ledger",
        "frontier_map",
        "reopen_conditions",
        "manifest_ref",
        "state_ref",
        "confidence",
        "false_closure_risk_flags",
    ):
        assert key in record
    assert record["terminal_claim"] is False


def test_program_pec_codec_roundtrips_and_preserves_hash() -> None:
    cert = closed_certificate()
    encoded = encode_program_pec(cert)
    decoded = decode_program_pec(encoded)
    assert decoded == cert
    assert decoded.certificate_hash == cert.certificate_hash


def test_program_pec_codec_rejects_tampered_certificate() -> None:
    import json
    cert = closed_certificate()
    envelope = json.loads(encode_program_pec(cert))
    envelope["certificate"]["status"] = "DPEC_OPEN"
    with pytest.raises(ValidationError, match="hash mismatch"):
        decode_program_pec(envelope)


def test_explicit_verification_evidence_is_required_for_closed_status() -> None:
    cert = build_program_pec_certificate(
        sources(),
        frame=default_v09_frame(),
        budget=default_v09_budget(),
        debt_ledger=default_v09_debts(),
        frontier_map=default_v09_frontier(),
        reopen_conditions=default_v09_reopen_conditions(),
    )
    assert cert.status == "DPEC_OPEN"
    assert not audit(cert, "Verify").passed

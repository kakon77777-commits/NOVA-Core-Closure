# NOVA Competing Resolution Universes / Policy Governance v0.16 — Validation Record

**Date:** 2026-09-15  
**Status:** Experimental validation passed

## Canonical base

```text
raw rejected plan:
sha256:3c2275d8971cfe7cf1aec4056fa847dbde654856167070ba6de750b715674dc6

shared CoreNorm state:
sha256:2a02aae792b64e699caef73dd49efe10933e6642ec9bffbd695dd74605c4546e
```

## Competing valid resolution universes

```text
Universe A:
sha256:5d2481069a6492b6466113bd12e9029437b456f7550b7e87d0234eeeeb4dec34

Universe B:
sha256:c08ead93885a46b8c53a8adf2f0d34d376845cfe5b460699a836c5bd3760c140
```

Both universes are mechanically valid v0.15 conflict resolutions, use the same parent set, and were freshly Re-PEC certified with 264 cases under the same CoreNorm state/profile/frame/budget.

Their closure-knowledge normal forms differ:

```text
A knowledge:
sha256:01f59284ee1a3b2dae69cffd5ef6b1013e2ab4316baa812bbce94e88c8c171a8

B knowledge:
sha256:c616cff5e66823adca0acb8c68a0c2ffe28e80be1afbd4b6a287b974e0fe9b24
```

## Universe comparison

```text
verdict: GOVERNANCE_REQUIRED
comparison:
sha256:e697287a1614558f4961a42e4e8a993af874ba7805274aba3c16e18b9abbfd1f

knowledge differences: 3
```

The comparison is symmetric: reversing A/B produces the same comparison hash.

## Governance artifacts

### Preserve plurality

```text
status: PLURALITY_PRESERVED
sha256:c2fe6c045c05526c7a875ee497ef428df3afaf0e5de1ec00b2c27ef1695f78d6
```

Both universes remain operational and retained.

### Evidence-gated selection

```text
status: UNIVERSE_OPERATIONALLY_SELECTED
selected: Universe B
sha256:b516cf9d1410e56a13d6fd5fcf282a6d9056fa3359bae6a842c4eb1602b99a73
```

The policy binds explicit evidence plus a named governance authority. Universe A remains retained/replayable. This is an operational selection, not a truth claim.

### Request re-experiment

```text
status: REEXPERIMENT_REQUIRED
sha256:3911a82d04fdae01683ea7a08b61e36ef5376d8c60e2b7de5390b23b08be3c43
```

Both universes remain active and new discriminating verification is required.

## Equivalent-artifact control

Two different policy/proof/certificate paths were constructed with the same resolved closure knowledge.

```text
Universe EQ1:
sha256:4a77f8a0298fb56814fb8534628b6b81dfdeeb8bbc782f6e4631d0abd5d16224

Universe EQ2:
sha256:14674d4b9a098d1791a07fdcd0f978bc176d4190ba0325a5d5985f51b8c87658

shared knowledge normal form:
sha256:01f59284ee1a3b2dae69cffd5ef6b1013e2ab4316baa812bbce94e88c8c171a8

comparison verdict: EQUIVALENT
comparison:
sha256:37f68a74bdeb03b5c683402fef624826ce8ffa9520558f68c80db3e272c7d1e3
```

Auto reunification succeeds:

```text
sha256:08606a3e310987dc7cc98502e044166d81f185678f0068f0833cb65aa15a56fe
```

Both provenance universes remain retained.

## Context divergence probes

Governance is blocked for:

```text
PLAN_DIVERGENCE
PARENT_DIVERGENCE
STATE_DIVERGENCE
PROFILE_DIVERGENCE
FRAME_DIVERGENCE
BUDGET_DIVERGENCE
```

These are treated as different bounded questions rather than competing answers to one question.

## Executed tests

```text
new v0.16 tests: 31 passed
cumulative isolated compatibility suite: 264 passed / 0 failed
standalone v0.16 harness: PASS
```

The v0.16 tests cover universe construction, knowledge-equivalent artifact divergence, symmetric comparison, exact knowledge-difference reporting, context gates, all four governance policies, evidence/authority requirements, provenance retention, stale comparison rejection, deterministic replay, codec/hash roundtrips, tamper detection, and nonterminal/non-truth boundaries.

## Governance boundary

```text
universal_truth_adjudication_claim = false
majority_truth_claim = false
cross_state_governance_claim = false
governance_creates_pec_claim = false
terminal_claim = false
```

The historical upstream 215-test baseline was not freshly rerun in this execution container and is not counted as v0.16 evidence.

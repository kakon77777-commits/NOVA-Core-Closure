# NOVA N-Universe Adaptive Experiment Design v0.18 — Validation Record

**Date:** 2026-09-15  
**Status:** Experimental validation passed

## Canonical N-universe set

Eight mechanically valid closure universes were constructed under one shared context:

```text
adaptive-U000
adaptive-U001
adaptive-U010
adaptive-U011
adaptive-U100
adaptive-U101
adaptive-U110
adaptive-U111
```

They share the same rejected plan, parent set, CoreNorm state, CoreNorm profile, Program PEC frame, and Program PEC budget.

## Candidate probes and adaptive tree

```text
universe count:        8
candidate probes:      5
decision nodes:       15
unresolved leaves:     0
worst-case depth:      3
optimal depth:         3
information lower bound: 3
```

Canonical root probe:

```text
debt / DEBT-FDT-COMPLETE-01 / status
probe:
sha256:667e8f852f54cc83b7d99d731426dfbe3c00af71cc7d60311d200ded182ab26c
```

Canonical plan:

```text
sha256:97b0989c060c839f9a1fab8f96feaedfa723015764309ba1e1dc36c7ea468bef
```

Adaptive optimality certificate:

```text
sha256:a86d41f8a5ad19cb6700fe12a5d259d6db95d761444436c7fe90abadc207a0e4
```

The exact finite minimax planner reaches the information lower bound:

$$
8\rightarrow4\rightarrow2\rightarrow1.
$$

## Synthetic validation transcript

Canonical selected synthetic universe:

```text
adaptive-U101
sha256:d0ecb9464668f0c58fa1071f85b79e329e98d324026bbb397aa9ac478472a525
```

Synthetic evidence:

```text
sha256:e67200805699ac7be2d7a1cd8831646e47946c79faf8a8902b87abd49c32604c
```

Assessment:

```text
UNIQUE_MATCH
sha256:28b771c4d2ea9f55d28568cd4fc6333c92c9fc5ada4643fe95163f2cc472243a
```

This evidence is synthetic validation only. It is not an external measurement claim.

## Partial and failure-state validation

```text
1 observation -> 4 survivors -> INCOMPLETE_EVIDENCE
2 observations -> 2 survivors -> INCOMPLETE_EVIDENCE
UNKNOWN root  -> 8 survivors -> AMBIGUOUS_MATCH
out-of-model  -> NO_MATCH
```

Out-of-order observations and observations after tree termination are rejected.

## Experimental-track freeze

```text
status: EXPERIMENTAL_TRACK_FROZEN_FOR_PRACTICAL_TRANSITION
freeze certificate:
sha256:c73d3c7c3acacd28dcab439d6cc56b410efcc5ffb07d404d6d6952d3deb61299

frozen versions: v0.1 through v0.18
next track: NOVA Practical Language Track
```

The freeze remains explicitly reopenable and does not claim production readiness, language readiness, or terminal truth.

## Executed tests

```text
new v0.18 tests: 36 passed
cumulative isolated compatibility suite: 333 passed / 0 failed
standalone v0.18 harness: PASS
fresh-extract managed-file checksum before replay: 214 / 214 PASS
fresh-extract managed-file checksum after replay: 214 / 214 PASS
ZIP CRC: PASS
```

## Boundary

```text
synthetic_validation_only = true
external_measurement_claim = false
universal_experiment_optimality_claim = false
causal_identifiability_claim = false
production_ready_claim = false
language_ready_claim = false
terminal_claim = false
```

The historical upstream 215-test baseline was not freshly rerun in this execution container and is not counted as v0.18 evidence.

The next primary workstream is practical NOVA language engineering, not automatic continuation of the v0.x experimental proposition chain.

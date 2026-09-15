# NOVA N-Parent / Merge-of-Merge Coherence v0.14 — Validation Record

**Date:** 2026-09-15  
**Status:** Experimental validation passed

## Canonical base

```text
v0.10 hardened Program PEC:
sha256:d6378ad86f5e5ba40536e9ab4383517f905a58a70fb360c7deb276d1690eede4

CoreNorm state:
sha256:2a02aae792b64e699caef73dd49efe10933e6642ec9bffbd695dd74605c4546e
```

## Three-parent N-way plan

```text
status: N_PARENT_MERGE_READY_FOR_REPEC
plan hash:
sha256:1f2e83e4c4a57c4d1894d221e447669f41262f0831d7494c08da74a287c32959

knowledge normal form:
sha256:cc809a9cc1164544d9269cf7e3bc3e8e8ae14de94c80e7d01c82c23d2b179d21
```

All six permutations of the three parent branches produce the same plan/normal-form identity.

## Associativity / coherence

```text
status: KNOWLEDGE_COHERENT
coherence certificate:
sha256:8a383333b277dfd36b3314ec78376966a40ea57d55e9b33dcff807cf2ef4fe97

knowledge_associative: true
permutation_invariant: true
artifact_associativity_claim: false
```

The validated equality is:

$$
H_K((A\bowtie B)\bowtie C)
=
H_K(A\bowtie(B\bowtie C))
=
H_K(A\bowtie B\bowtie C).
$$

The claim applies to common-base closure-knowledge normal forms only.

## Fresh N-parent Re-PEC

```text
status: N_PARENT_REPEC_CLOSED
certificate:
sha256:e8706e5e91a86e58c823ca4424680a418cc666fb106c805bfd7a44f94a4d28d4

merged Program PEC:
sha256:90ef4acfe900d42ea0ea91bffb32467e0d5015e8796215e5e7d9ea5445b0466b
```

The merged child still certifies the original common CoreNorm state.

Fresh verification:

```text
203 passed
0 failed
standalone harness: PASS
```

Pre-merge evidence remains conservative:

```text
floor:   112
ceiling: 330
overlap_unknown: true
```

The value 330 is not treated as a certified union count.

## Merge-of-merge lineage

```text
status: MERGE_COHERENCE_LINEAGE_VALID
lineage hash:
sha256:7880681d4eab316e9f681eff8f68d1e26bcadfee216443c4494da4838ef7abea
```

The lineage records:

```text
A,B -> AB -> L
B,C -> BC -> R
A,B,C    -> D
```

and binds `L`, `R`, and `D` to the same final knowledge normal-form hash.

## Conflict / boundary probes

Validated rejection includes:

- incompatible edits to one logical debt;
- delete-vs-modify conflict;
- CoreNorm state divergence;
- Program PEC frame divergence;
- duplicate parent branches/tips;
- stale N-parent plan;
- insufficient fresh verification;
- lineage tamper;
- lineage cycle.

Identical parallel edits are accepted once, not duplicated.

A four-parent compatible plan was also validated to establish that the plan layer is not hard-coded to exactly three parents. The explicit associativity certificate in v0.14 remains three-parent/binary-grouping scoped.

## Executed tests

```text
new v0.14 tests: 34 passed
cumulative isolated compatibility suite: 203 passed / 0 failed
standalone v0.14 harness: PASS
```

## Boundary

```text
artifact_associativity_claim = false
cross_state_merge_claim = false
verification_disjointness_claim = false
universal_merge_algebra_claim = false
terminal_claim = false
```

The historical upstream 215-test baseline was not freshly rerun in this execution container and is not counted as v0.14 evidence.

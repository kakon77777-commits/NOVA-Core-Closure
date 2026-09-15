# NOVA Conflict Resolution Proof Objects / Policy Algebra v0.15 — Validation Record

**Date:** 2026-09-15  
**Status:** Experimental validation passed

## Canonical base

```text
CoreNorm state:
sha256:2a02aae792b64e699caef73dd49efe10933e6642ec9bffbd695dd74605c4546e
```

The v0.15 scenario uses three common-base parent branches and deliberately creates simultaneous debt, frontier, and reopening-condition conflicts.

## Raw conflict plan

```text
status: N_PARENT_MERGE_REJECTED
conflicts: 3
plan hash:
sha256:3c2275d8971cfe7cf1aec4056fa847dbde654856167070ba6de750b715674dc6
```

The three resolution policies are:

```text
debt     -> SELECT_PARENT
frontier -> FIELDWISE_JOIN
reopen   -> KEEP_BASE
```

## Policy bundle / policy algebra

```text
policy bundle:
sha256:4e1ccd9f569590cec27f39730e02bfb4c3a20971a29add928d0c389dd4539718

policy algebra certificate:
sha256:c07d72cbfa89eb3da804ed02735a8ed40fb1591939d38d613b35706889bbf8d5
```

Validated bounded properties:

```text
identity_law:          true
associative:           true
permutation_invariant: true
partial_algebra:       true
```

Different policies targeting the same logical conflict do not compose; they raise a policy-algebra conflict.

## Resolution proofs

```text
sha256:f038e97c16c79e755ece306f8e970d4ff31a10ef2cd8993bb0bef0f2ed2602b1
sha256:c642fb8d93b26ef46ee247a439d82bed29d5203457733045f5fe52a16199a5c4
sha256:428fc942a0949136f007228664bece21847ba8d412e2637305d9eb8b6ebaf191
```

Each proof binds the rejected-plan hash, exact conflict hash, parent alternative record hashes, policy hash, and resulting record.

## Resolution certificate

```text
status: ALL_CONFLICTS_RESOLVED
resolution hash:
sha256:484704cc0f9d2a370d1440f638a1847ff7a4e894a9d57c9c1762c28e0e0b6e19

resolved knowledge normal form:
sha256:2791704e8c18e3208bd114877b153110d8121d125b87a07a62e9391bd9ec4359
```

A deliberately partial policy bundle produces `PARTIAL_RESOLUTION` and is rejected by the Re-PEC builder.

## Fresh resolved Re-PEC

```text
status: RESOLVED_N_PARENT_REPEC_CLOSED
certificate:
sha256:8d921e3e754f88d25f383dd67e2d1b816926451a768fc0fdd3b7f82b6f432cc6

merged Program PEC:
sha256:9f453f037b27d4bcaf796c6e35d46262517923e6bc7537272a9fd36fcd973c30

shared CoreNorm state:
sha256:2a02aae792b64e699caef73dd49efe10933e6642ec9bffbd695dd74605c4546e
```

Fresh verification:

```text
233 passed
0 failed
standalone harness: PASS
```

The conflict-resolution proof does not replace fresh verification.

## Executed tests

```text
new v0.15 tests: 30 passed
cumulative isolated compatibility suite: 233 passed / 0 failed
standalone v0.15 harness: PASS
```

The v0.15 tests cover SELECT_PARENT exact-record binding, FIELDWISE_JOIN source-derived recombination, KEEP_BASE/DELETE, partial-resolution non-closure, policy-bundle algebra, proof replay, parent-tamper failure, codec/hash roundtrips, tamper detection, fresh verification floor enforcement, deterministic recertification, and explicit nonterminal/non-universal-policy boundaries.

## Boundary

```text
universal_policy_soundness_claim = false
cross_state_resolution_claim = false
arbitrary_literal_resolution_claim = false
challenge_conflict_resolution_claim = false
total_policy_algebra_claim = false
terminal_claim = false
```

The historical upstream 215-test baseline was not freshly rerun in this execution container and is not counted as v0.15 evidence.

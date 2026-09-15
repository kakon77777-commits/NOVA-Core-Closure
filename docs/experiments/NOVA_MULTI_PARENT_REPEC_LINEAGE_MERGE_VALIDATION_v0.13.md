# NOVA Multi-Parent Re-PEC / Lineage Merge v0.13 — Validation Record

**Date:** 2026-09-15  
**Status:** Experimental validation passed

## Parent artifacts

```text
v0.10 hardened base PEC:
sha256:d6378ad86f5e5ba40536e9ab4383517f905a58a70fb360c7deb276d1690eede4

v0.11 parent lineage graph:
sha256:f805642d33761270725e084c827be2ee492de436c37f4c0ffb28b39dd35e3e85

left branch tip:
sha256:9729a97dbd23bb8da7be9f16a1ba7ff5ad75cf7dfa68c82f902253cfa2cfa2f9

right branch tip:
sha256:d12bd944f4b8db2b0abd606d2e55c0d7959271baf78dcbe50965087a49c3d7b0

v0.12 comparison:
sha256:b1374a8aea4d11001a52880b84f6599f5778af8f025805a4354ea43574af1929

v0.12 knowledge merge:
sha256:9e602abb4bf82de1a6be5e57f99c554f74fd65560ba2fb5aa5f6b4734635e4be
```

## Multi-Parent Re-PEC

```text
status: MULTI_PARENT_REPEC_CLOSED
certificate hash:
sha256:e15f223fbb6e0ef0656d21db6d366bd3595cf067b23c6796f8364fdd073ac59a

merged Program PEC:
sha256:ac4bd06e9f5a80a7670b94af4e82bad0b406affc71396ee7481b614146c1b633

shared CoreNorm state:
sha256:2a02aae792b64e699caef73dd49efe10933e6642ec9bffbd695dd74605c4546e
```

The left parent, right parent, and merged child all certify the same CoreNorm state.

## Verification handling

Pre-merge v0.12 interval:

```text
floor:   112
ceiling: 222
overlap_unknown: true
```

Fresh v0.13 verification:

```text
169 cases passed
0 failed
standalone harness: PASS
```

The merged child records 169 fresh cases. It does not reinterpret 222 as a certified union count.

## Merged closure knowledge

```text
merged debts:              5
merged frontiers:           7
merged reopening conditions: 14
```

Route-oriented and observer-oriented branch knowledge is present in the merged Program PEC.

Parent-specific risk observations also survive recertification.

## Multi-parent lineage

```text
status: MULTI_PARENT_LINEAGE_VALID
graph hash:
sha256:ebda42a91c885d3940eecb2e178640eedbeaa6573f7cac75e3ade9f149a3b912

nodes:    7
edges:    14
episodes: 1
```

The episode contains exactly two `parent_of_multi_repec` edges and one merged child tip.

The v0.11 parent graph remains immutable and is referenced by hash.

## Executed tests

```text
new v0.13 tests: 25 passed
cumulative isolated compatibility suite: 169 passed / 0 failed
standalone v0.13 harness: PASS
```

The v0.13 tests cover:

- merge-ready v0.12 prerequisite;
- fresh multi-parent closure;
- exact two-parent identity;
- parent non-overwrite;
- shared state/profile preservation;
- merged debt/frontier/reopen materialization;
- conservative pre-merge verification interval preservation;
- fresh verification count separation;
- branch risk preservation;
- Re-PEC codec/hash roundtrip;
- Re-PEC tamper detection;
- insufficient verification rejection;
- stale comparison rejection;
- stale knowledge-merge rejection;
- parent-tamper replay failure;
- conflict-branch rejection;
- valid true two-parent lineage episode;
- exact two incoming parent edges;
- immutable parent-lineage reference;
- shared CoreNorm state node;
- lineage codec/hash roundtrip;
- lineage tamper detection;
- deterministic lineage replay;
- wrong parent context rejection;
- cycle guard;
- nonterminality;
- explicit evidence binding to both parents and v0.12 merge artifacts.

## Boundary

```text
cross_state_merge_claim = false
n_parent_general_merge_claim = false
verification_disjointness_claim = false
history_completeness_claim = false
future_branch_completeness_claim = false
terminal_claim = false
```

The historical upstream 215-test baseline was not freshly rerun in this execution container and is not counted as v0.13 evidence.

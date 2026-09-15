# NOVA Branch Comparison / Closure Knowledge Merge v0.12 — Validation Record

**Date:** 2026-09-15  
**Status:** Experimental validation passed

## Canonical base

```text
v0.10 hardened PEC:
sha256:d6378ad86f5e5ba40536e9ab4383517f905a58a70fb360c7deb276d1690eede4

v0.11 lineage graph:
sha256:f805642d33761270725e084c827be2ee492de436c37f4c0ffb28b39dd35e3e85
```

## Canonical branch heads

```text
Branch A tip:
sha256:9729a97dbd23bb8da7be9f16a1ba7ff5ad75cf7dfa68c82f902253cfa2cfa2f9

Branch B tip:
sha256:d12bd944f4b8db2b0abd606d2e55c0d7959271baf78dcbe50965087a49c3d7b0
```

The two branches share the same CoreNorm state, profile, Program PEC frame, budget, and lineage context.

Branch A adds route-oriented debt/frontier/reopening knowledge. Branch B adds observer-oriented debt/frontier/reopening knowledge.

## Comparison

```text
verdict: MERGEABLE
comparison hash:
sha256:b1374a8aea4d11001a52880b84f6599f5778af8f025805a4354ea43574af1929
```

Three-way merge semantics are base-aware; independent changes merge, identical parallel changes merge, incompatible concurrent changes conflict.

## Knowledge merge

```text
status: MERGE_READY_FOR_REPEC
merge hash:
sha256:9e602abb4bf82de1a6be5e57f99c554f74fd65560ba2fb5aa5f6b4734635e4be

merged debts: 5
merged frontiers: 7
merged reopening conditions: 14
```

Verification evidence is intentionally represented as a conservative interval:

```text
floor:   112
ceiling: 222
overlap_unknown: true
```

The artifact explicitly requires Re-PEC before a new closure tip may be claimed:

```text
requires_repec = true
terminal_claim = false
```

## Conflict probes

### Same logical debt changed incompatibly

```text
DEBT-CONFLICT-01
result: CONFLICT
```

### CoreNorm state divergence

```text
result: STATE_DIVERGENCE
```

Additional tests cover profile, frame, budget, base, and lineage-context divergence.

## Executed tests

```text
new v0.12 tests: 23 passed
cumulative isolated compatibility suite: 144 passed / 0 failed
standalone v0.12 harness: PASS
comparison codec/hash: PASS
comparison tamper detection: PASS
knowledge-merge codec/hash: PASS
knowledge-merge tamper detection: PASS
stale-comparison replay rejection: PASS
```

The v0.12 tests also verify:

- one-branch-only debt resolution merges safely when the other branch is unchanged;
- identical parallel discoveries merge safely;
- delete-vs-modify of the same logical item conflicts;
- branch IDs must be distinct;
- terminal branch heads are rejected;
- verification counts are not naively summed into a certified total.

## Boundary

```text
merged_pec_closed_claim = false
terminal_claim = false
verification_disjointness_claim = false
cross_state_merge_claim = false
```

The historical upstream 215-test baseline was not freshly rerun in this execution container and is not counted as v0.12 evidence.

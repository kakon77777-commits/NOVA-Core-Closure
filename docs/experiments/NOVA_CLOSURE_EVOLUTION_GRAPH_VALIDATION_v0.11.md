# NOVA Reopening Lineage / Closure Evolution Graph v0.11 — Validation Record

**Date:** 2026-09-15  
**Status:** Experimental validation passed

## Canonical parent artifacts

```text
v0.9 Program PEC:
sha256:2090f2e6db301b62b47e9006462451578f7b0eaddfe77711fdbe83273b570468

v0.10 ART/FDT report:
sha256:d27cdedc60121a20a24e57f0d293e2df65c093c158efb1b59b184cc31c915ef2

v0.10 Re-PEC:
sha256:0875d20efc7145f03697a5569a629f5d79d7ccc0b32a11e7ff1d07f090096f3d

v0.10 hardened PEC:
sha256:d6378ad86f5e5ba40536e9ab4383517f905a58a70fb360c7deb276d1690eede4
```

## Closure Evolution Graph

```text
status: LINEAGE_VALID
graph hash:
sha256:f805642d33761270725e084c827be2ee492de436c37f4c0ffb28b39dd35e3e85

nodes: 20
edges: 30
episodes: 1
```

Node kinds:

```text
PEC                 2
ART/FDT             1
Re-PEC              1
CoreNorm state      1
Debt snapshots      5
Frontier snapshots 10
```

The v0.9 PEC and v0.10 hardened PEC share the same CoreNorm state reference:

```text
sha256:2a02aae792b64e699caef73dd49efe10933e6642ec9bffbd695dd74605c4546e
```

Therefore this episode records closure-knowledge evolution without program-state evolution.

## Episode delta

```text
verification cases: 80 -> 98
state_changed: false
```

Added reopening conditions:

```text
REOPEN-FDT-FAMILY
REOPEN-PRIMITIVE
REOPEN-ROUTE
REOPEN-SEMANTIC
REOPEN-SUBSTRATE
```

Debt transitions:

```text
DEBT-ART-01           deferred -> resolved
DEBT-FDT-COMPLETE-01  introduced -> deferred
DEBT-UPSTREAM-01      deferred -> deferred
```

Frontier transitions:

```text
retired:    FRONTIER-ART-01
introduced: FRONTIER-FDT-COMPLETE-01
```

## Executed tests

```text
new v0.11 tests: 23 passed
cumulative isolated compatibility suite: 121 passed / 0 failed
standalone v0.11 lineage harness: PASS
```

The v0.11 tests cover deterministic graph construction, heterogeneous node inventory, causal spine validation, shared CoreNorm state reference, debt/frontier evolution, reopening-condition and verification deltas, branch-tip computation, codec/hash roundtrip, tamper detection, missing endpoint rejection, cycle guards, episode integrity, overwrite rejection, unique child-producer rule, deterministic replay, wrong-parent rejection, terminality guard, append-only extension, missing extension-parent rejection, and extended-graph codec roundtrip.

## Branch-capability validation

A synthetic second closure episode was appended to the canonical first episode using `extend_closure_evolution_graph()`.

The resulting graph remained valid, the old lineage remained unchanged, and the new child became the new branch tip.

This validates the append-only graph mechanism; it does not certify the synthetic episode as a real NOVA research result.

## Full-suite limitation

The historical upstream 215-test baseline was not freshly rerun in this execution container and is not counted as v0.11 evidence.

The current claim is limited to the packaged cumulative 121-test isolated suite, the standalone lineage harness, and the canonical v0.9/v0.10 artifacts.

## Boundary

```text
terminal_claim = false
history_completeness_claim = false
future_branch_completeness_claim = false
```

v0.11 certifies lineage integrity for the declared artifact history, not terminal or universal closure.

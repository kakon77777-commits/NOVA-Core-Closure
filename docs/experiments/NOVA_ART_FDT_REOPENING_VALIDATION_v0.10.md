# NOVA ART / FDT Reopening v0.10 — Validation Record

**Date:** 2026-09-15  
**Status:** Experimental validation passed

## Baseline

```text
Program DPEC v0.9:
sha256:2090f2e6db301b62b47e9006462451578f7b0eaddfe77711fdbe83273b570468
```

## ART/FDT report

```text
status: ART_FDT_REOPENED
report hash:
sha256:d27cdedc60121a20a24e57f0d293e2df65c093c158efb1b59b184cc31c915ef2

ART probes: 6
FDT probes: 7
controls: 3
```

All 13 attack probes observed reopening/boundary invalidation. All three controls survived without false reopening.

### Reopen gain vector

```text
[0.125, 0.25, 0.125, 0.125, 0.125, 0.125,
 0.125, 0.25, 0.25, 0.375, 0.125, 0.25, 0.25]
```

The vector is a bounded operational axis-change proxy, not an information-theoretic completeness claim.

## v0.9 hardening gaps exposed

```text
missing explicit REOPEN-ROUTE condition in v0.9
missing explicit REOPEN-SEMANTIC condition in v0.9
no dedicated REOPEN-SUBSTRATE condition in v0.9
no dedicated primitive-reframing reopen condition in v0.9
```

## Re-PEC

```text
status: REPEC_CLOSED
Re-PEC hash:
sha256:0875d20efc7145f03697a5569a629f5d79d7ccc0b32a11e7ff1d07f090096f3d

hardened Program PEC:
sha256:d6378ad86f5e5ba40536e9ab4383517f905a58a70fb360c7deb276d1690eede4
```

Added reopening conditions:

```text
REOPEN-FDT-FAMILY
REOPEN-PRIMITIVE
REOPEN-ROUTE
REOPEN-SEMANTIC
REOPEN-SUBSTRATE
```

Debt transition:

```text
DEBT-ART-01 = resolved
DEBT-FDT-COMPLETE-01 = deferred
```

New frontier:

```text
FRONTIER-FDT-COMPLETE-01
```

Lineage rule:

```text
SUPERSEDE_WITH_LINEAGE_NOT_OVERWRITE
```

The v0.9 parent certificate remains unchanged and replayable.

## Executed tests

```text
new v0.10 tests: 18 passed
cumulative isolated compatibility suite: 98 passed / 0 failed
standalone v0.10 harness: PASS
ART/FDT report codec/hash: PASS
ART/FDT tamper detection: PASS
Re-PEC codec/hash: PASS
Re-PEC tamper detection: PASS
Re-PEC deterministic replay: PASS
v0.9 parent replay after Re-PEC: PASS
```

## False-closure categories

```text
search          deferred
representation  checked
operator        checked
budget          checked
verification    checked
ambiguity       partial
compression     deferred
observer        checked
memory          deferred
consensus       deferred
```

## Boundary

```text
test_family_completeness_claim = false
terminal_claim = false
```

Passing this bounded suite raises reopening robustness confidence only. It does not imply that all possible future dimensions have been tested.

The historical upstream 215-test baseline was not freshly rerun in this execution container and is not counted as v0.10 evidence.

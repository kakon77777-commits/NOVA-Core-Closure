# NOVA Discriminating Experiment Objects / Universe Separation v0.17 — Validation Record

**Date:** 2026-09-15  
**Status:** Experimental validation passed

## Canonical v0.16 comparison

```text
comparison:
sha256:e697287a1614558f4961a42e4e8a993af874ba7805274aba3c16e18b9abbfd1f
verdict: GOVERNANCE_REQUIRED
```

Source governance:

```text
REEXPERIMENT_REQUIRED
sha256:8a5b675f7d8d6d1612deb6a10a0addcd77b665836d05e905016693e8b66ba4c2
```

## Minimal discriminator

The comparison expands to five atomic candidates. The deterministic minimal experiment selects:

```text
probe: debt / DEBT-FDT-COMPLETE-01 / status
probe hash:
sha256:c009fc8dc4e08f7205c8d36921b0499196249b40a2835794a9d7ee117670929f

Universe A prediction: deferred
Universe B prediction: resolved
```

Experiment:

```text
sha256:31f95687c96e0ed50a75b92bb96a1ffdd2d62e88fa726464c4e31b9e83c94d70
```

Minimality certificate:

```text
sha256:69c0fb05f4bed8faea259b6e3bb7ab54492b678f5827c19e740ddb0b6011af75
lower_bound: 1
achieved_count: 1
```

## Canonical synthetic evidence

The package binds `SYNTHETIC_VALIDATION` evidence matching Universe B's predicted `resolved` outcome:

```text
evidence:
sha256:20c64f6d41f46f34ca17e821b24b2144b0488150f820bc8d0db92039b0738451

assessment: UNIQUE_MATCH
sha256:0cbbea5018d0d0fbc410253964212fcc56a156a8e74bc5f93da691484d7d19d1

selected universe:
sha256:c08ead93885a46b8c53a8adf2f0d34d376845cfe5b460699a836c5bd3760c140
```

This bridges into v0.16 `EVIDENCE_GATED_SELECT`:

```text
governance decision:
sha256:3b11aafa7fbb0f8c8e2f9fbcce032797b8f32ff26fe52b5eae435e99a0c9d195
```

Both universe artifacts remain retained and replayable.

## Negative outcome validation

```text
UNKNOWN observation -> AMBIGUOUS_MATCH
impossible value    -> NO_MATCH
missing observation -> INCOMPLETE_EVIDENCE
```

None of these non-unique outcomes may drive universe selection.

## Executed tests

```text
new v0.17 tests: 33 passed
cumulative isolated compatibility suite: 297 passed / 0 failed
standalone v0.17 harness: PASS
fresh-extract checksum before replay: 197 / 197 PASS
fresh-extract checksum after replay: 197 / 197 PASS
ZIP CRC: PASS
```

The v0.17 tests cover candidate generation, deterministic minimal probe selection, minimality replay, stale governance rejection, equivalent-universe non-requirement, unique/ambiguous/no-match/incomplete assessment, evidence provenance, unknown/duplicate probe rejection, v0.16 governance bridging, provenance retention, codec/hash roundtrips, tamper detection, and deterministic replay.

## Boundary

```text
synthetic_validation_only = true
external_measurement_claim = false
universal_experiment_optimality_claim = false
causal_identifiability_claim = false
physical_observability_claim = false
universal_truth_adjudication_claim = false
terminal_claim = false
```

The historical upstream 215-test baseline was not freshly rerun in this execution container and is not counted as v0.17 evidence.

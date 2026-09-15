# NOVA Discriminating Experiment Objects / Universe Separation v0.17

**Status:** Experimental specification  
**Date:** 2026-09-15

## Purpose

v0.17 turns the v0.16 `REQUEST_REEXPERIMENT` state into an executable, replayable experiment contract:

$$
(U_A,U_B)
\rightarrow
\operatorname{Difference}
\rightarrow
\operatorname{PredictionContract}
\rightarrow
\operatorname{Experiment}
\rightarrow
\operatorname{Observation}
\rightarrow
\operatorname{Assessment}
\rightarrow
\operatorname{GovernanceUpdate}.
$$

The governing distinction is:

$$
\boxed{\text{Knowledge Difference}\neq\text{Experimental Evidence}}
$$

A universe comparison proposes candidate discriminators. It does not itself count as an observation.

## Preconditions

A discriminator may only be built for a v0.16 comparison with verdict `GOVERNANCE_REQUIRED` and a source governance decision with status `REEXPERIMENT_REQUIRED`.

The universes must already share the same rejected plan, parent set, CoreNorm state/profile, Program PEC frame, and budget. Context-divergent universes are different bounded questions and are rejected before experiment design.

## Atomic discriminator probes

Each v0.16 `KnowledgeDifference` is expanded into differing atomic fields. For logical item $k$ and field path $p$:

$$
\operatorname{Probe}_{k,p}(U)=\text{predicted canonical value at }(k,p).
$$

A probe is discriminating iff its predictions differ between the two retained universes.

The probe binds the comparison hash, knowledge-difference hash, logical key, field path, both universe hashes, both predicted outcomes, and the observation contract. It does not contain an observed result.

## Pairwise minimality

For the current two-universe setting, if any atomic discriminator exists then zero probes cannot discriminate while one differing atomic probe can. Therefore:

$$
\operatorname{minProbeCount}(U_A,U_B)=1.
$$

v0.17 emits a machine-checkable minimality certificate with `lower_bound=1`, `achieved_count=1`, and proof method `PAIRWISE_SINGLE_ATOMIC_WITNESS`.

This is not a universal optimal-design theorem for arbitrary N-universe experiment selection.

## Canonical experiment

The canonical v0.16 comparison expands to five atomic discriminator candidates. The deterministic minimal planner selects:

```text
category: debt
logical key: DEBT-FDT-COMPLETE-01
field path: status
Universe A prediction: deferred
Universe B prediction: resolved
```

## Evidence and assessment

Evidence is a separate artifact bound to an experiment hash, probe observations, evidence class, evidence references, and an observation authority.

Evidence classes currently include `SYNTHETIC_VALIDATION`, `EXTERNAL_MEASUREMENT`, and `INDEPENDENT_REPLAY`.

Assessment verdicts are:

```text
UNIQUE_MATCH
AMBIGUOUS_MATCH
NO_MATCH
INCOMPLETE_EVIDENCE
```

Unknown observations remain ambiguous; impossible observations match no retained universe; missing required observations remain incomplete.

Only `UNIQUE_MATCH` may bridge into the existing v0.16 `EVIDENCE_GATED_SELECT` governance policy.

The resulting selection is explicitly operational lifecycle control, not universal truth adjudication, and the non-selected valid universe remains retained and replayable.

## Canonical validation witness

The package uses synthetic validation evidence matching Universe B's predicted `resolved` value. This validates the experiment/evidence/assessment/governance mechanism only. It is not an external empirical measurement.

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

v0.17 converts `REQUEST_REEXPERIMENT` from a governance label into an explicit prediction-and-observation contract without claiming that the canonical synthetic witness establishes real-world truth.

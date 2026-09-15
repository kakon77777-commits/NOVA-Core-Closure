# NOVA N-Universe Adaptive Experiment Design v0.18

**Status:** Experimental specification  
**Track role:** Final primary proposition of the NOVA v0.1–v0.18 experimental line  
**Date:** 2026-09-15

## 1. Purpose

v0.17 established pairwise universe separation. v0.18 generalizes the mechanism to a finite competing set:

$$
\mathcal U=\{U_1,U_2,\ldots,U_n\},\qquad n\ge3.
$$

The objective is to construct a bounded adaptive decision tree whose observations reduce the surviving universe set until one universe remains, or until the declared probe family can no longer separate the survivors.

$$
\boxed{\text{finite competing universe set}\rightarrow\text{bounded exact-minimax adaptive experiment plan}}
$$

## 2. Context gate

All universes in one plan MUST share rejected-plan identity, parent-tip set, CoreNorm state/profile, Program PEC frame, and budget. A mismatch is rejected before planning.

## 3. Atomic probes

A probe is:

$$
p=(category,logical\_key,field\_path).
$$

For each universe it carries a canonical predicted outcome. A probe is admitted only when it produces at least two distinct outcomes over the current universe set.

The bounded probe family is derived from debt, frontier, reopen, challenge, and risk-flag records.

## 4. Exact finite minimax planner

For surviving set $S$:

$$
D(S)=
\begin{cases}
0,&|S|\le1,\\
1+\min_p\max_oD(S_o),&\text{if a probe splits }S,\\
\infty,&\text{otherwise}.
\end{cases}
$$

The implementation evaluates this recurrence using memoized dynamic programming over finite universe subsets. Deterministic tie breaking prefers smallest worst-case depth, smallest largest partition, largest number of outcome partitions, then semantic probe order.

This proves bounded optimality only for the explicit finite universe set and explicit finite candidate-probe family.

## 5. Canonical eight-universe experiment

The validation family contains three independent binary closure-knowledge dimensions, producing:

$$
2^3=8
$$

universes in one shared context.

The exact planner obtains:

$$
D(\mathcal U)=3
$$

and the information lower bound is:

$$
\lceil\log_2 8\rceil=3.
$$

Therefore the canonical plan reaches the bounded optimum:

$$
8\rightarrow4\rightarrow2\rightarrow1.
$$

## 6. Evidence protocol

Predictions are not observations. Adaptive evidence is an ordered transcript and every observation must match the probe requested by the current decision-tree node.

- out-of-order observation: reject;
- `UNKNOWN`: preserve current plurality as `AMBIGUOUS_MATCH`;
- out-of-model result: `NO_MATCH`;
- transcript stops before a leaf: `INCOMPLETE_EVIDENCE`;
- one unique leaf reached: `UNIQUE_MATCH`.

The system MUST NOT coerce unknown or out-of-model evidence into a selected universe.

## 7. Machine artifacts

v0.18 provides hash-checked canonical envelopes for:

- adaptive experiment plan;
- bounded optimality certificate;
- adaptive evidence;
- adaptive assessment;
- experimental-track freeze certificate.

Plan generation is invariant to input-universe ordering and replay must reproduce byte-identical managed artifacts.

## 8. Experimental-track freeze

After v0.18:

$$
\boxed{\text{v0.1--v0.18 Experimental Track}\rightarrow\text{FROZEN}}
$$

This is a research/project boundary, not a terminal truth claim. The line is explicitly reopenable when practical implementation exposes a concrete failed invariant.

The next primary track is:

$$
\boxed{\text{NOVA Practical Language Track}}
$$

Its first engineering questions are:

1. What is the practical human/AI authoring surface of NOVA?
2. How does NOVA compile, execute, debug, interoperate, and deploy?
3. What should be the first real software written primarily in NOVA?
4. How much verified corpus is required for reliable AI-native NOVA development?

## 9. Non-claims

v0.18 does NOT claim universal experiment optimality, empirical truth of synthetic observations, arbitrary causal identifiability, physical observability of every closure-knowledge field, production readiness, practical language readiness, or terminal completeness.

## 10. Final experimental-track invariant

$$
\boxed{\text{Enough structure to normalize, compare, branch, merge, conflict, govern, and discriminate}}
$$

while preserving:

$$
\boxed{\text{Unknown}\neq\text{False},\quad\text{Selected}\neq\text{True},\quad\text{Closed}\neq\text{Terminal}.}
$$

After v0.18, primary work moves from extending the abstract experimental chain to implementing NOVA as an actually usable programming language and runtime ecosystem.

# NOVA N-Parent / Merge-of-Merge Coherence v0.14

**Status:** Experimental specification  
**Date:** 2026-09-15

## 1. Objective

v0.14 generalizes the v0.12/v0.13 two-parent closure-knowledge merge into a common-base N-parent normalization layer and tests bounded merge coherence.

The central distinction is:

$$
\boxed{\text{Artifact Associativity}\neq\text{Knowledge Associativity}}
$$

A v0.13 Re-PEC changes verification frame, budget and evidence lineage. Therefore an already re-certified intermediate artifact is not treated as if it were still an untouched branch of the original common base.

v0.14 instead compares closure knowledge inside a common-base knowledge plane, then performs one fresh N-parent Re-PEC.

## 2. Bounded algebraic claim

For compatible branches $A,B,C$ descending from one certified base $B_0$:

$$
(A\bowtie B)\bowtie C\cong A\bowtie(B\bowtie C)\cong A\bowtie B\bowtie C
$$

where $\cong$ means equality of canonical closure-knowledge normal forms, not equality of intermediate certificate identities.

The claim is bounded to branches sharing:

- one base Program PEC;
- one CoreNorm state;
- one CoreNorm profile;
- one Program PEC frame;
- one resource budget;
- one lineage context;
- conflict-free logical edits under the declared merge policy.

## 3. N-way merge semantics

For one logical key with base value $b$ and parent values $p_1,\dots,p_n$:

- if no parent differs from $b$, keep $b$;
- if all changed parents agree on one new value, accept that value;
- if changed parents contain more than one distinct value, emit `CONFLICT`;
- deletion is a first-class value and therefore conflicts with incompatible modification.

The rule is permutation-invariant by construction.

## 4. Knowledge normal form

The v0.14 normal form contains:

- CoreNorm state reference;
- CoreNorm profile hash;
- canonical debt records;
- canonical frontier records;
- canonical reopening-condition records;
- canonical reopening-challenge records;
- normalized false-closure risk flags.

Lineage-specific evidence identities and Re-PEC frame/budget mutations are not used as the identity of closure knowledge.

## 5. N-parent merge plan

A successful plan has status:

```text
N_PARENT_MERGE_READY_FOR_REPEC
```

It records:

- all parent tips and heads;
- common base/state/profile/frame/budget;
- canonical merged knowledge normal form;
- conflict set;
- conservative verification interval;
- overlap-unknown flag;
- explicit `requires_repec=true`.

The plan itself does not certify closure.

## 6. Coherence certificate

For three parents the certificate binds:

$$
H_L=H((A\bowtie B)\bowtie C),
$$

$$
H_R=H(A\bowtie(B\bowtie C)),
$$

$$
H_D=H(A\bowtie B\bowtie C).
$$

`KNOWLEDGE_COHERENT` requires:

$$
H_L=H_R=H_D
$$

and equality across all six parent permutations.

The certificate must keep:

```text
artifact_associativity_claim = false
terminal_claim = false
```

## 7. N-parent fresh Re-PEC

Only after a mergeable plan and fresh verification may v0.14 issue:

```text
N_PARENT_REPEC_CLOSED
```

The new Program PEC must preserve the common CoreNorm state/profile and materialize the normalized closure knowledge.

Parent artifacts are not overwritten.

## 8. Merge-of-merge coherence lineage

The lineage DAG records three derivations:

$$
A,B\to AB\to L,
$$

$$
B,C\to BC\to R,
$$

$$
A,B,C\to D.
$$

The final witnesses must satisfy:

$$
H(L)=H(R)=H(D).
$$

The DAG has cycle guards, endpoint checks, codec/hash replay and tamper detection.

## 9. Conflict boundary

v0.14 rejects automatic N-parent merge on:

- different base PEC;
- different lineage context;
- CoreNorm state divergence;
- CoreNorm profile divergence;
- Program PEC frame divergence;
- budget divergence;
- incompatible concurrent edits to the same debt/frontier/reopen/challenge item;
- duplicate parent branches/tips.

## 10. Verification accounting

If parent test suites are not proven disjoint, their counts are not summed as a certified total.

For parent counts $n_i$ the pre-merge interval is:

$$
\max_i n_i\le n_{union}\le\sum_i n_i.
$$

A fresh N-parent Re-PEC records a new verification count separately.

## 11. Explicit non-claims

v0.14 does **not** claim:

- universal algebraic associativity for all future merge rules;
- associativity of certificate hashes or evidence lineages;
- cross-state merge;
- arbitrary heterogeneous frame/budget merge;
- verification-set disjointness;
- terminal completeness;
- full historical/future branch completeness.

## 12. Falsification criteria

The v0.14 claim fails if any accepted compatible parent set exhibits:

1. parent-order-dependent direct normal form;
2. different left/right associated normal forms;
3. disagreement between nested and direct N-parent normal forms;
4. hidden conflict accepted as mergeable;
5. stale/tampered plan accepted by Re-PEC;
6. cycle/tamper accepted by coherence lineage;
7. fresh Re-PEC changing the certified CoreNorm state/profile.

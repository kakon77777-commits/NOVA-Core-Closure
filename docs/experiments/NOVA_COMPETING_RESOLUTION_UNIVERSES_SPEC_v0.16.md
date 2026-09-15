# NOVA Competing Resolution Universes / Policy Governance v0.16

**Status:** Experimental  
**Date:** 2026-09-15  
**Parent:** NOVA Conflict Resolution Proof Objects / Policy Algebra v0.15

## 1. Purpose

v0.15 established that a declared closure-knowledge conflict can sometimes be resolved by an explicit, replayable policy proof and then freshly re-certified.

v0.16 addresses the next problem:

> the same rejected conflict plan may admit more than one mechanically valid, proof-carrying resolution.

Therefore:

$$
 c
 \longrightarrow
 \begin{cases}
 (\pi_A,\operatorname{Proof}_A,K_A),\\
 (\pi_B,\operatorname{Proof}_B,K_B)
 \end{cases}
$$

and both branches may independently pass fresh Re-PEC.

The system must not silently collapse this plurality by branch order, last-writer-wins, majority vote, or hidden implementation priority.

The v0.16 objective is:

$$
\boxed{
\text{Valid Resolution Alternatives}
\to
\text{Resolution Universes}
\to
\text{Comparison}
\to
\text{Explicit Governance}
}
$$

## 2. Non-goals

v0.16 does **not** claim:

- that one mechanically valid resolution is uniquely true;
- that majority vote establishes semantic truth;
- that a governance decision creates a new Program PEC;
- that different CoreNorm states may be governed as one problem;
- terminal completeness;
- universal policy soundness.

## 3. Resolution Universe

A resolution universe is a proof-carrying closure-knowledge state produced from one rejected N-parent plan:

$$
U=
(P_{\times},\Pi,R,RePEC,S,\Gamma,K,E).
$$

It records at minimum:

- rejected-plan hash;
- exact parent-tip set;
- conflict-resolution certificate hash;
- policy-bundle hash;
- resolution-proof hashes;
- resolved Re-PEC hash;
- merged Program PEC hash;
- CoreNorm state reference;
- CoreNorm profile;
- Program PEC frame hash;
- budget hash;
- closure-knowledge normal form;
- fresh verification count;
- provenance/evidence references.

The universe identity is:

$$
H_U=H(\operatorname{Canon}(U)).
$$

### 3.1 Truth boundary

A valid universe means:

> this resolution path is mechanically bound to its source alternatives, replayable, and freshly re-certified under its declared frame.

It does **not** mean:

> this resolution is metaphysically or mathematically the only possible truth.

Therefore every universe has:

```text
truth_claim = false
terminal_claim = false
```

## 4. Artifact identity vs knowledge identity

Two resolution universes may contain different:

- policy IDs;
- rationales;
- proof hashes;
- certificate hashes;
- evidence references;

while still reaching the same closure-knowledge normal form.

Thus:

$$
\boxed{
H_U(U_A)\neq H_U(U_B)
\centernot\Rightarrow
H_K(U_A)\neq H_K(U_B)
}
$$

v0.16 explicitly distinguishes:

$$
\text{Artifact Identity}
\neq
\text{Knowledge Identity}
\neq
\text{Program State Identity}.
$$

## 5. Resolution-universe comparison

The comparison operator is symmetric:

$$
\operatorname{Cmp}(U_A,U_B)
=
\operatorname{Cmp}(U_B,U_A).
$$

The input order is canonicalized by universe hash before comparison.

### 5.1 Context gates

Before closure knowledge is compared, the following must match:

1. rejected-plan hash;
2. parent-tip set;
3. CoreNorm state;
4. CoreNorm profile;
5. Program PEC frame;
6. resource/verification budget.

Failure produces one of:

```text
PLAN_DIVERGENCE
PARENT_DIVERGENCE
STATE_DIVERGENCE
PROFILE_DIVERGENCE
FRAME_DIVERGENCE
BUDGET_DIVERGENCE
```

These results cannot enter v0.16 governance because they are not treated as competing answers to the same bounded question.

### 5.2 Equivalent resolution universes

If context matches and:

$$
H_K(U_A)=H_K(U_B),
$$

then:

```text
EQUIVALENT
```

Even here both provenance artifacts remain retained.

### 5.3 Competing resolution universes

If context matches but:

$$
H_K(U_A)\neq H_K(U_B),
$$

then:

```text
GOVERNANCE_REQUIRED
```

The comparison records exact differences across:

- debt records;
- frontier records;
- reopening conditions;
- reopening challenges;
- risk flags.

## 6. Governance is not a truth oracle

A governance policy answers:

> which proof-carrying closure universe should remain operational for the next bounded workflow?

It does not answer:

> which universe is universally true?

Hence:

$$
\boxed{
\operatorname{GovernanceDecision}
\neq
\operatorname{TruthProof}
}
$$

## 7. Governance policies

v0.16 exposes four explicit policy kinds.

### 7.1 AUTO_REUNIFY_EQUIVALENT

Allowed only for `EQUIVALENT` universes.

It chooses one deterministic operational representative while retaining both original universe artifacts.

```text
status = EQUIVALENT_UNIVERSES_REUNIFIED
```

### 7.2 PRESERVE_PLURALITY

Both valid universes remain active.

```text
status = PLURALITY_PRESERVED
```

This is the default safe action when no discriminating evidence exists.

### 7.3 EVIDENCE_GATED_SELECT

One universe becomes operationally active only if the policy explicitly binds:

- the selected universe hash;
- non-empty evidence references;
- a named authority/governance reference;
- a rationale.

```text
status = UNIVERSE_OPERATIONALLY_SELECTED
```

The unselected universe remains retained and replayable.

This policy does **not** set `truth_claim=true`.

### 7.4 REQUEST_REEXPERIMENT

Both universes remain active and a new discriminating experiment is required.

```text
status = REEXPERIMENT_REQUIRED
requires_new_verification = true
```

## 8. Explicitly unsupported hidden governance

v0.16 has no policy equivalent to:

```text
MAJORITY_VOTE
LAST_WRITER_WINS
LEFT_BRANCH_WINS
NEWEST_CERTIFICATE_WINS
```

If such a policy is desired in a future domain, it must be introduced explicitly with its own assumptions and evidence semantics.

## 9. Retention invariant

Every governance decision preserves both competing universe artifacts:

$$
\boxed{
\{U_A,U_B\}
\subseteq
\operatorname{Retained}(G)
}
$$

Operational activation is separate from historical retention.

Thus an `EVIDENCE_GATED_SELECT` decision never deletes or rewrites the alternative universe.

## 10. Governance replay

A governance decision binds:

- comparison hash;
- governance-policy hash;
- left/right universe hashes;
- active universe set;
- retained universe set;
- evidence refs;
- claim boundary.

Replay reconstructs the decision from the original comparison and policy and requires the decision hash to match.

Any stale comparison or altered universe invalidates the decision lineage.

## 11. No implicit Re-PEC

v0.16 governance does not create a new merged Program PEC.

In particular:

```text
merged_pec = absent
new_state_ref = absent
```

A later experiment may use an active universe as input to a new closure episode, but that requires a new explicit certificate lineage.

## 12. Canonical v0.16 experiment

The canonical scenario starts from the v0.15 rejected three-conflict plan.

### Universe A

Resolution A uses:

```text
debt     -> SELECT_PARENT(branch-A)
frontier -> FIELDWISE_JOIN(A.summary, B.required_capability)
reopen   -> KEEP_BASE
```

### Universe B

Resolution B uses:

```text
debt     -> SELECT_PARENT(branch-B)
frontier -> KEEP_BASE
reopen   -> SELECT_PARENT(branch-A)
```

Both resolutions are source-bound, replayable, and freshly Re-PEC certified under the same state/profile/frame/budget.

Their knowledge normal forms differ, therefore the result is:

```text
GOVERNANCE_REQUIRED
```

## 13. Equivalent-artifact control experiment

A second experiment constructs two different policy/proof artifact paths that choose the same source records.

The proof/certificate identities differ, but:

$$
H_K(U_1)=H_K(U_2).
$$

The comparison therefore returns:

```text
EQUIVALENT
```

and `AUTO_REUNIFY_EQUIVALENT` succeeds while retaining both provenance artifacts.

## 14. Falsification conditions

v0.16 is falsified if any of the following occurs:

1. non-equivalent knowledge is automatically reunified;
2. input order changes the comparison hash;
3. context-diverged universes are allowed into governance;
4. `EVIDENCE_GATED_SELECT` works without evidence or authority;
5. selection deletes the alternative universe;
6. a governance decision silently creates a new Program PEC/state;
7. tampered universe/comparison/policy/decision envelopes decode successfully;
8. stale comparison hashes replay successfully;
9. governance artifacts claim universal truth or terminal completeness.

## 15. Relationship to SREG multi-universe reasoning

v0.16 operationalizes a bounded form of:

$$
U_A\neq U_B
$$

while still permitting:

$$
S_A=S_B
$$

and separately testing:

$$
K_A\stackrel{?}{=}K_B.
$$

The important point is that divergence is preserved as explicit structure rather than erased by a hidden chooser.

## 16. Boundary

```text
universal_truth_adjudication_claim = false
majority_truth_claim = false
cross_state_governance_claim = false
governance_creates_pec_claim = false
terminal_claim = false
```

The v0.16 result is a bounded governance layer for competing proof-carrying resolution universes.

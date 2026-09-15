# NOVA Conflict Resolution Proof Objects / Policy Algebra v0.15

**Status:** Experimental specification  
**Date:** 2026-09-15  
**Parent:** NOVA N-Parent / Merge-of-Merge Coherence v0.14

## 1. Purpose

v0.14 established a bounded closure-knowledge merge algebra for compatible common-base branches. v0.15 addresses the complementary case:

$$
\boxed{\text{explicit knowledge conflict}}
$$

A conflict is not silently resolved by ordering, branch priority, timestamp, or last-write-wins. A branch family that produces incompatible edits remains rejected until an explicit policy and replayable proof object are supplied.

The v0.15 pipeline is:

$$
\boxed{
\text{CONFLICT}
\to
\text{Resolution Policy}
\to
\text{Proof Object}
\to
\text{Resolved Knowledge Normal Form}
\to
\text{Fresh Re-PEC}
}
$$

The proof object proves deterministic policy application and binding to the exact conflict alternatives. It does **not** prove that the selected policy is universally or metaphysically correct. Fresh verification remains mandatory.

## 2. Scope

v0.15 supports proof-carrying resolution for these closure-knowledge categories:

- `debt`
- `frontier`
- `reopen`

Challenge/evidence conflicts and arbitrary semantic-state conflicts remain outside this version.

All participating branches must already satisfy the common-base / common-state / common-profile / common-frame / common-budget requirements inherited from v0.14. Cross-state conflict resolution is not claimed.

## 3. Conflict object

A conflict is identified by:

$$
c=(category,key,B,\{(p_i,R_i)\})
$$

where:

- $B$ is the common-base record or deletion state;
- $p_i$ identifies a parent branch;
- $R_i$ is that parent's changed record or deletion state.

The conflict hash binds the full conflict record.

## 4. Resolution policies

A policy is target-scoped:

$$
\pi=(id,category,key,kind,params,rationale,evidence)
$$

A policy may act **only** on the exact conflict key it names.

### 4.1 KEEP_BASE

$$
\operatorname{Resolve}(c,KEEP\_BASE)=B
$$

This explicitly rejects all competing branch changes for that item and preserves the certified base record.

### 4.2 SELECT_PARENT

$$
\operatorname{Resolve}(c,SELECT(p))=R_p
$$

The policy must bind both `parent_id` and the expected hash of $R_p$. A parent identifier alone is insufficient.

### 4.3 DELETE

$$
\operatorname{Resolve}(c,DELETE)=\varnothing
$$

Deletion is explicit and auditable. It cannot be inferred from absence.

### 4.4 FIELDWISE_JOIN

For a record with fields $f_1,\ldots,f_n$, a source map is declared:

$$
J:f_i\mapsto source_i.
$$

Every explicitly selected value must come from the base or one of the conflict alternatives. Literal value injection is not supported. A field not explicitly assigned may be accepted only when all available source records agree on that field.

Thus FIELDWISE_JOIN is a source-preserving structural recombination, not an unrestricted record editor.

## 5. Resolution proof object

A proof object binds:

- rejected N-parent plan hash;
- conflict hash;
- category and logical key;
- base record hash;
- every changed parent record hash;
- full resolution policy and policy hash;
- resolved record and resolved-record hash;
- evidence references;
- nonterminal claim boundary.

Replay requires:

$$
\boxed{
\operatorname{Apply}(c,\pi)=r
}
$$

and all input fingerprints must still match.

Any parent mutation, policy mutation, or result mutation invalidates replay.

## 6. Policy bundle algebra

Policies for different conflict targets can be composed into a bundle.

Let $\oplus$ denote compatible bundle composition.

For compatible bundles in the current bounded domain:

### Identity

$$
A\oplus I=I\oplus A=A.
$$

### Associativity

$$
(A\oplus B)\oplus C=A\oplus(B\oplus C).
$$

### Permutation invariance / commutativity

$$
A\oplus B=B\oplus A.
$$

However, this is a **partial algebra**. If two bundles contain different policies for the same conflict target:

$$
\boxed{
A_t\neq B_t\Rightarrow A\oplus B=\operatorname{PolicyConflict}
}
$$

No policy priority is inferred.

The algebra certificate records identity, associativity, and permutation-invariance evidence for the declared compatible policy set.

## 7. Resolution certificate

Given rejected plan $P_\times$ and policy bundle $\Pi$:

$$
R=\operatorname{ResolvePlan}(P_\times,\Pi).
$$

Statuses:

- `PARTIAL_RESOLUTION`
- `ALL_CONFLICTS_RESOLVED`

A partial resolution may be stored and replayed but cannot advance to Re-PEC.

Only:

$$
\boxed{
ALL\_CONFLICTS\_RESOLVED
}
$$

produces one resolved knowledge normal form and sets `requires_repec=true`.

Policies targeting non-conflict keys are rejected. This prevents resolution machinery from becoming a side channel for arbitrary knowledge mutation.

## 8. Fresh conflict-resolved Re-PEC

A resolution certificate does not itself close the program domain.

The next step is:

$$
\operatorname{FreshVerify}(K_R)\to PEC_R.
$$

v0.15 requires fresh verification cases at least as large as the rejected plan's conservative verification floor.

The recertified PEC binds:

- rejected plan hash;
- resolution certificate hash;
- policy bundle hash;
- every resolution-proof hash;
- every parent tip hash;
- fresh verification evidence;
- original common CoreNorm state/profile.

The resolved child must still satisfy:

$$
S_{child}=S_{base}
$$

and

$$
Profile_{child}=Profile_{base}.
$$

## 9. Canonical validation scenario

The v0.15 validation case creates three simultaneous conflicts over one common CoreNorm state:

1. a debt conflict resolved by `SELECT_PARENT`;
2. a frontier conflict resolved by `FIELDWISE_JOIN`;
3. a reopening-rule conflict resolved by `KEEP_BASE`.

The raw N-parent plan is rejected as `CONFLICT`.

After policy proof replay, the resolution certificate is `ALL_CONFLICTS_RESOLVED`, and fresh verification produces `RESOLVED_N_PARENT_REPEC_CLOSED`.

## 10. Safety / anti-overclaim rules

v0.15 does not claim:

```text
universal_policy_soundness = false
cross_state_resolution = false
arbitrary_literal_resolution = false
challenge_conflict_resolution = false
total_policy_algebra = false
terminal_claim = false
```

A successful proof demonstrates:

> this declared policy was applied deterministically to these exact conflict alternatives and produced this exact resolved record.

It does not demonstrate:

> this policy is the only correct policy, globally optimal, or universally valid.

## 11. Falsification criteria

The v0.15 claim fails if any of the following occurs:

- a policy can modify a non-conflict key;
- SELECT_PARENT can replay after the selected parent record changes;
- FIELDWISE_JOIN can inject a value not derivable from bound sources;
- an ambiguous unassigned field is silently accepted;
- incompatible policies for one target compose silently;
- partial resolution can advance to Re-PEC;
- fresh verification below the inherited floor is accepted;
- proof / policy / certificate tampering is not detected;
- parent mutation does not invalidate replay;
- resolved Re-PEC changes the common CoreNorm state without explicit cross-state semantics.

## 12. Next frontier

The next natural layer is no longer single-conflict resolution mechanics, but **resolution-policy governance / proof ordering / competing valid resolutions**: multiple proof-carrying policies may all be mechanically valid while yielding different closure-knowledge states. A later version should compare and reason about those alternative resolved universes without collapsing them by hidden priority.

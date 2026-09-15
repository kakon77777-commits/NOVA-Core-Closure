# NOVA Branch Comparison / Closure Knowledge Merge v0.12

**Status:** Experimental  
**Date:** 2026-09-15  
**Parent layer:** v0.11 Closure Evolution Graph  
**Scope:** bounded branch comparison and three-way closure-knowledge merge

## 1. Purpose

v0.11 turns closure history into a causal DAG. The next problem appears when a single certified closure tip forks into independent research branches.

Let a common base certificate be $C_0$ and let two independent branch tips be $C_L$ and $C_R$:

$$
C_0
\longrightarrow
\begin{cases}
C_L\\
C_R.
\end{cases}
$$

v0.12 asks whether their *closure knowledge* can be compared and safely recombined.

The key restriction is:

$$
\boxed{
\text{Knowledge Merge}
\neq
\text{Closed PEC Merge}
}
$$

A successful v0.12 merge creates a machine-verifiable knowledge-union artifact that **must still pass Re-PEC / verification before it becomes a new closure tip**.

---

## 2. Why two-way union is insufficient

A naive union cannot distinguish:

1. one branch changed an item while the other branch left it untouched;
2. both branches independently discovered the same change;
3. both branches changed the same logical item incompatibly.

v0.12 therefore uses a true three-way merge relative to the certified base.

For each logical knowledge item with base value $B$, left value $L$, and right value $R$:

$$
\operatorname{Merge}_3(B,L,R)=
\begin{cases}
L, & L=R,\\
R, & L=B,\\
L, & R=B,\\
\operatorname{Conflict}, & \text{otherwise}.
\end{cases}
$$

This rule also covers additions and removals by treating absence as $\varnothing$.

---

## 3. Branch head

A v0.12 branch head is:

$$
H_i=(
\text{branch-id},
C_0,
C_i,
G_L,
E_i
),
$$

where:

- $C_0$ is the common base PEC hash;
- $C_i$ is the branch-tip Program PEC;
- $G_L$ is the v0.11 lineage-graph hash;
- $E_i$ is optional branch evidence.

The branch-head hash is deterministic and binds the tip to its declared base and lineage context.

---

## 4. Compatibility gate

v0.12 deliberately restricts automatic merge to **knowledge-only branches over the same machine state**.

The compatibility predicate is:

$$
\operatorname{Compatible}(L,R\mid C_0)
$$

only if all of the following hold:

$$
\begin{aligned}
Base_L &= Base_R = C_0,\\
Lineage_L &= Lineage_R,\\
State_L &= State_R = State_0,\\
Profile_L &= Profile_R = Profile_0,\\
Frame_L &= Frame_R = Frame_0,\\
Budget_L &= Budget_R = Budget_0.
\end{aligned}
$$

If these fail, the comparison returns one of:

- `BASE_MISMATCH`
- `LINEAGE_CONTEXT_DIVERGENCE`
- `STATE_DIVERGENCE`
- `PROFILE_DIVERGENCE`
- `FRAME_DIVERGENCE`
- `BUDGET_DIVERGENCE`

These cases are not automatically forced into one branch universe.

---

## 5. Knowledge domains merged in v0.12

The three-way merge currently operates over four keyed knowledge sets:

$$
K=
K_D
\sqcup
K_F
\sqcup
K_R
\sqcup
K_C,
$$

where:

- $K_D$: debt ledger;
- $K_F$: frontier map;
- $K_R$: reopening conditions;
- $K_C$: reopening challenges.

Each logical key is compared against the base version.

False-closure risk flags and evidence references are conservatively unioned as monotone warning/evidence sets.

Derived audits and confidence vectors are **not** merged into a new closed certificate. They must be recomputed during Re-PEC.

---

## 6. Conflict semantics

If both branches independently modify the same logical item differently relative to the base:

$$
L\neq B,
\qquad
R\neq B,
\qquad
L\neq R,
$$

then:

$$
\boxed{
\operatorname{Merge}_3(B,L,R)=\operatorname{Conflict}.
}
$$

The comparison artifact stores:

- category;
- logical key;
- base record;
- left record;
- right record;
- conflict reason.

No lexical, timestamp, or branch-priority tie-breaker is used.

This prevents branch order from becoming hidden authority.

---

## 7. Comparison certificate

`BranchComparisonCertificate` records:

- base PEC hash;
- lineage context;
- left/right branch-head hashes;
- left/right tip PEC hashes;
- state/profile/frame/budget identities;
- three-way merge statistics;
- explicit conflicts;
- verification bounds;
- merge verdict.

The successful verdict is:

```text
MERGEABLE
```

but its claim boundary is only:

> knowledge-union is structurally safe under the declared v0.12 policy.

It does **not** mean a new PEC has already been certified.

---

## 8. Verification evidence is an interval, not a sum claim

Suppose branch $L$ reports $n_L$ verification cases and branch $R$ reports $n_R$.

Without proving that the two test sets are disjoint, v0.12 refuses to claim:

$$
n_{merged}=n_L+n_R.
$$

Instead it records:

$$
\boxed{
\max(n_L,n_R)
\le
n_{merged}
\le
n_L+n_R
}
$$

with:

```text
verification_overlap_unknown = true
```

For the canonical v0.12 example:

$$
112\le n_{merged}\le222.
$$

A later Re-PEC may deduplicate and certify a stronger evidence count.

---

## 9. Closure Knowledge Merge artifact

If comparison succeeds, v0.12 emits:

```text
MERGE_READY_FOR_REPEC
```

The artifact contains:

- two parent-tip hashes;
- comparison hash;
- common CoreNorm state;
- common profile/frame/budget identities;
- merged debt records;
- merged frontier records;
- merged reopening conditions;
- merged reopening challenges;
- unioned evidence references;
- unioned false-closure risk flags;
- conservative verification interval.

It also hard-codes:

```text
requires_repec = true
terminal_claim = false
```

Therefore:

$$
\boxed{
MergeKnowledge(C_L,C_R)
\not\Rightarrow
PEC_{closed}.
}
$$

---

## 10. Canonical v0.12 experiment

The canonical experiment forks from the v0.10 hardened PEC:

```text
sha256:d6378ad86f5e5ba40536e9ab4383517f905a58a70fb360c7deb276d1690eede4
```

under the v0.11 lineage graph:

```text
sha256:f805642d33761270725e084c827be2ee492de436c37f4c0ffb28b39dd35e3e85
```

Branch A adds route-oriented closure knowledge.

Branch B adds observer-oriented closure knowledge.

They share the same CoreNorm state/profile/frame/budget and edit disjoint logical items.

The comparison result is:

```text
MERGEABLE
```

and the merge result is:

```text
MERGE_READY_FOR_REPEC
```

A second probe makes both branches modify `DEBT-CONFLICT-01` incompatibly. The result is:

```text
CONFLICT
```

A third probe changes the right CoreNorm state. The result is:

```text
STATE_DIVERGENCE
```

---

## 11. SREG multi-universe interpretation

v0.12 is the first NOVA layer that explicitly treats independent closure branches as separate generative universes rather than as ordinary version-control branches.

Given two branch universes:

$$
U_L,
U_R,
$$

comparison is not based on surface similarity. It asks whether they share a common substrate state and whether their closure knowledge is compatible under an explicit merge operator.

This gives the bounded pattern:

$$
\boxed{
U_L\neq U_R
\quad\land\quad
Core(U_L)=Core(U_R)
\quad\land\quad
K_L\bowtie K_R
}
$$

where $\bowtie$ means three-way knowledge compatibility.

---

## 12. Non-goals

v0.12 does not claim:

- general semantic program merge;
- automatic merge across different CoreNorm states;
- automatic merge across different normalization profiles;
- proof that verification suites are disjoint;
- automatic construction of a new closed Program PEC;
- terminal closure;
- global multi-universe completeness.

---

## 13. Next step

The natural next layer is to consume a `MERGE_READY_FOR_REPEC` artifact and perform an actual multi-parent Re-PEC / lineage integration:

$$
(C_L,C_R)
\rightarrow
Merge_K
\rightarrow
RePEC_M
\rightarrow
C_M.
$$

That future layer would add a true multi-parent closure episode to the evolution DAG.

v0.12 intentionally stops one step before that claim.

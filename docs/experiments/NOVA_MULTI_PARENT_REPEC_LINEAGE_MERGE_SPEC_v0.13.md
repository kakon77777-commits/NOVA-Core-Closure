# NOVA Multi-Parent Re-PEC / Lineage Merge v0.13

**Status:** Experimental  
**Revision:** 1  
**Date:** 2026-09-15

## 1. Purpose

v0.12 proved that two compatible closure-knowledge branches can be compared and three-way merged into a `MERGE_READY_FOR_REPEC` artifact.

v0.13 closes the next gap:

$$
(C_L,C_R)
\rightarrow
Merge_K
\rightarrow
RePEC_M
\rightarrow
C_M.
$$

The result is not a Git-style source merge. It is a **multi-parent closure recertification** over one shared machine state.

## 2. Primary distinction

The v0.12 artifact states:

$$
\boxed{\text{knowledge merge is structurally admissible}}
$$

but intentionally does **not** state:

$$
\boxed{\text{a new merged closure is already certified}}.
$$

v0.13 therefore requires fresh verification before issuing a merged Program PEC.

$$
Merge_K
+V_{fresh}
\Rightarrow
RePEC_M.
$$

## 3. Two-parent invariant

A valid v0.13 certificate carries exactly two distinct parent PEC identities:

$$
Parents(RePEC_M)=\{C_L,C_R\},
\qquad C_L\neq C_R.
$$

Neither parent is overwritten.

The lineage action is fixed to:

```text
MERGE_WITH_LINEAGE_NOT_OVERWRITE
```

and the merged child must be a distinct artifact:

$$
C_M\neq C_L,\qquad C_M\neq C_R.
$$

## 4. State compatibility

v0.13 does not attempt cross-state semantic merge.

The v0.12 compatibility boundary is preserved:

$$
S_L=S_R=S_B.
$$

Fresh reconstruction must also recover the same CoreNorm state:

$$
S_M=S_L=S_R.
$$

Likewise the CoreNorm profile must remain identical.

A state/profile divergence invalidates the merge path before Re-PEC issuance.

## 5. Fresh verification and overlap

v0.12 deliberately preserves the uncertainty that two parent verification suites may overlap:

$$
n_{floor}\le n_{union}\le n_{ceiling}.
$$

For the canonical v0.12 pair:

$$
112\le n_{union}\le222.
$$

v0.13 does **not** resolve this uncertainty by pretending the old suites were disjoint.

Instead it performs a fresh merged verification run:

$$
V_{fresh}=169.
$$

The only minimum requirement is:

$$
V_{fresh}\ge n_{floor}.
$$

The merged PEC therefore does not use $222$ as a certified test count.

## 6. Knowledge materialization

The following v0.12 merged domains are materialized back into typed Program PEC structures:

- debt records;
- frontier records;
- reopening conditions;
- reopening challenge knowledge;
- false-closure risk observations;
- evidence references.

The fresh Program PEC builder then recomputes:

- cross-representation reconstruction;
- CoreNorm convergence;
- route coverage;
- six PEC audits;
- confidence vector;
- standard reopening challenge results.

The final child must satisfy:

$$
\bigwedge_{i=1}^{6} C_i=1
$$

before `MULTI_PARENT_REPEC_CLOSED` may be issued.

## 7. Multi-Parent Re-PEC artifact

The machine artifact format is:

```text
nova.multi-parent-repec/0.13
```

and records:

- immutable base PEC hash;
- both parent tip hashes;
- both parent branch-head hashes;
- v0.12 comparison hash;
- v0.12 knowledge-merge hash;
- parent lineage graph hash;
- merged Program PEC;
- old verification interval;
- fresh verification count;
- evidence references;
- lineage action;
- explicit claim boundary.

The certificate hash is domain separated:

$$
H_{MPR}=SHA256(tag_{0.13}\Vert Canon(record)).
$$

## 8. True two-parent lineage episode

v0.13 adds an additive lineage layer over the immutable v0.11 graph.

The causal spine is:

$$
C_B\to C_L,
\qquad
C_B\to C_R,
$$

$$
(C_L,C_R)\to Compare,
$$

$$
Compare\to Merge_K,
$$

$$
(C_L,C_R,Merge_K)\to RePEC_M,
$$

$$
RePEC_M\to C_M.
$$

Both parent PECs and the merged child also certify the same CoreNorm state node.

The extension graph therefore distinguishes:

$$
\text{program-state identity}
\neq
\text{closure-knowledge identity}.
$$

## 9. Parent graph immutability

The v0.11 lineage graph is not rewritten.

The v0.13 graph stores:

```text
parent_lineage_graph_hash
```

and validates that the declared merge base is a branch tip of that parent graph.

Thus:

$$
G_{0.11}
\xrightarrow{append-only-reference}
G^{merge}_{0.13}
$$

rather than mutation of $G_{0.11}$.

## 10. Required causal edges

The additive merge graph contains these relation families:

- `branches_to`;
- `compared_in`;
- `authorizes_merge`;
- `contributes_knowledge`;
- `requires_repec`;
- `parent_of_multi_repec`;
- `produces_merged_pec`;
- `certifies_state`.

A valid merge Re-PEC must have exactly two incoming `parent_of_multi_repec` edges.

## 11. Validation rules

v0.13 rejects:

1. a non-mergeable/stale comparison;
2. a stale or tampered knowledge-merge artifact;
3. parent-tip mismatch;
4. fresh verification below the v0.12 floor;
5. reconstructed CoreNorm state/profile divergence;
6. parent graph context mismatch;
7. missing or extra multi-parent causal parents;
8. lineage cycles;
9. child overwrite of a parent identity;
10. terminal-completeness claims;
11. certificate/graph envelope hash mismatch.

## 12. Replay

Both the Multi-Parent Re-PEC and merge-lineage graph are replayable:

$$
Artifact
\xrightarrow{rebuild(parent\ evidence)}
Artifact'.
$$

Acceptance requires:

$$
record'=record
\land
hash'=hash.
$$

Changing either parent invalidates replay.

## 13. Canonical validation instance

The canonical parents are the v0.12 route-oriented and observer-oriented branches.

The resulting identifiers are:

```text
left tip:
sha256:9729a97dbd23bb8da7be9f16a1ba7ff5ad75cf7dfa68c82f902253cfa2cfa2f9

right tip:
sha256:d12bd944f4b8db2b0abd606d2e55c0d7959271baf78dcbe50965087a49c3d7b0

v0.12 comparison:
sha256:b1374a8aea4d11001a52880b84f6599f5778af8f025805a4354ea43574af1929

v0.12 knowledge merge:
sha256:9e602abb4bf82de1a6be5e57f99c554f74fd65560ba2fb5aa5f6b4734635e4be

v0.13 Multi-Parent Re-PEC:
sha256:e15f223fbb6e0ef0656d21db6d366bd3595cf067b23c6796f8364fdd073ac59a

merged Program PEC:
sha256:ac4bd06e9f5a80a7670b94af4e82bad0b406affc71396ee7481b614146c1b633

v0.13 merge-lineage graph:
sha256:ebda42a91c885d3940eecb2e178640eedbeaa6573f7cac75e3ade9f149a3b912
```

All three PECs reference:

```text
CoreNorm state:
sha256:2a02aae792b64e699caef73dd49efe10933e6642ec9bffbd695dd74605c4546e
```

## 14. Claim boundary

v0.13 establishes a bounded, replayable **two-parent closure merge** for compatible branches that already passed v0.12 comparison.

It does not establish:

- cross-state semantic merge;
- arbitrary N-parent merge;
- proof that parent verification suites were disjoint;
- global Program equivalence;
- RGPEC;
- history completeness;
- future-branch completeness;
- terminal completeness.

The next natural extension is generalized N-parent closure composition or merge-of-merge episodes with associativity/coherence tests.

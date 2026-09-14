# NOVA CoreNorm v0.7 — Cross-Representation Structural Normalization Specification

**Date:** 2026-09-15  
**Status:** Experimental specification and executable prototype  
**Track:** NOVA post-textual / machine-native representation experiments  
**Canonical math delimiter:** `$...$` and `$$...$$`

---

## 0. Purpose

NOVA v0.1--v0.6 progressively separated schema spelling, semantic atom spelling, structural labels, human projection text, and scoped-symbol labels from machine authority.

v0.7 asks a different question:

> If two programs were constructed independently and therefore do not share persistent StructuralIDs, can NOVA still determine that they belong to the same bounded structural equivalence class?

Persistent identity answers:

$$
\text{Is this the same continuing object?}
$$

CoreNorm answers:

$$
\text{Does this object normalize to the same bounded machine structure?}
$$

Therefore:

$$
\boxed{
\text{Persistent Identity}
\neq
\text{Normalization Identity}
}
$$

---

# 1. Core definition

For a NOVA program $P$ and a declared normalization profile $\Pi$, define:

$$
\operatorname{CoreNorm}_{\Pi}(P)=C.
$$

Two programs are **CoreNorm-equivalent under profile $\Pi$** iff:

$$
\boxed{
P_1\equiv_{\Pi}P_2
\iff
\operatorname{CoreNorm}_{\Pi}(P_1)
=
\operatorname{CoreNorm}_{\Pi}(P_2)
}
$$

The corresponding hash is:

$$
H_{CN}(P,\Pi)
=
H\left(\operatorname{CoreNorm}_{\Pi}(P)\right).
$$

This is deliberately not defined as unrestricted semantic equivalence.

$$
\boxed{
P_1\equiv_{\Pi}P_2
\not\Rightarrow
P_1\equiv_{\mathrm{all\ semantics}}P_2
}
$$

The claim is only as strong as the explicitly versioned profile $\Pi$.

---

# 2. v0.7 bounded normalization profile

The default v0.7 profile permits only transformations for which the prototype has an explicit deterministic rule.

## 2.1 Structural alpha normalization

Mutable module, graph, node, and value labels do not participate in CoreNorm identity.

For label-only renaming $\rho$:

$$
\operatorname{CoreNorm}_{\Pi}(P)
=
\operatorname{CoreNorm}_{\Pi}(\rho(P)).
$$

Unlike v0.3, this does not require both programs to share the same persistent Identity Manifest.

## 2.2 Scoped binder alpha normalization

Graph-local symbolic dimensions such as `B`, `N`, or `Batch` are normalized by label-free occurrence signatures.

For a binder $\sigma$:

$$
\operatorname{Sig}_{CN}(\sigma)
=
\operatorname{Canon}
\{(\text{semantic structural path},c_i)\}.
$$

The human spelling is excluded.

Unique signatures are assigned local canonical binder indices:

$$
\sigma_i\mapsto b_i.
$$

If two different legacy binders are structurally indistinguishable under the current profile, v0.7 rejects normalization rather than using names as hidden tie-breakers.

## 2.3 Global semantic atom normalization

Known semantic atoms are reduced through the v0.2 Global Semantic Registry:

$$
\text{Add}\mapsto(d_{op},c_{Add}),
$$

$$
f32\mapsto(d_{dtype},c_{f32}).
$$

Unknown extension-owned atoms remain explicit extension text and therefore continue to affect the CoreNorm result.

## 2.4 Human projection stripping

Human-only fields already identified by v0.5 are excluded from CoreNorm authority.

Examples include:

- `reason`;
- source projection;
- provenance;
- migration commentary;
- non-semantic artifacts.

Thus:

$$
H_{CN}(P)=H_{CN}(P')
$$

when $P$ and $P'$ differ only in such human projections.

## 2.5 Safe trivial Identity elimination

v0.7 may eliminate an `Identity` node only when all of the following hold:

- exactly one input;
- exactly one output;
- no constraints;
- no attributes;
- no value type annotation;
- no shape type annotation;
- no non-pure effect;
- no differentiation annotation;
- no explicit edge requires guessed rewiring through that node.

Then:

$$
x\xrightarrow{Identity}y
$$

normalizes to the same value expression as $x$.

## 2.6 Commutative input normalization

For the bounded v0.7 operator set:

$$
\operatorname{Add}(x,y)
\equiv_{\Pi}
\operatorname{Add}(y,x),
$$

$$
\operatorname{Multiply}(x,y)
\equiv_{\Pi}
\operatorname{Multiply}(y,x).
$$

Their normalized input expressions are deterministically sorted.

No such reordering is applied to `Subtract`, `Divide`, `MatMul`, or other non-declared operators.

## 2.7 Canonical collection ordering

Set-like semantic collections such as constraint sets are re-sorted after projection stripping and binder normalization, preventing removed human text from indirectly affecting ordering.

Modules, graphs, normalized nodes, and explicit edges are ordered by their normalized structural records rather than human IDs.

---

# 3. Normalized graph model

For a bounded pure DAG graph $G$, v0.7 constructs:

$$
C_G
=
(
A,
O,
N,
E,
K,
M,
B
),
$$

where:

- $A$ is graph input arity;
- $O$ is the ordered list of normalized output expressions;
- $N$ is the sorted multiset of normalized node expressions;
- $E$ is the sorted explicit edge relation set;
- $K$ is graph-level constraints;
- $M$ is graph-level semantic metadata;
- $B$ is the number of alpha-normalized scoped binders.

A graph input is represented only by positional role:

$$
\operatorname{arg}(i).
$$

A produced value is represented by:

$$
\operatorname{out}(N_j,k),
$$

where $N_j$ is the normalized producer node and $k$ is the output index.

Human value names are therefore absent from the normalized dependency expression.

---

# 4. Example: independently authored equivalent programs

Program $P_1$ may contain:

```text
module app
graph main(x, y) -> sum
sum = Add(x, y)
shape symbol: B
```

Program $P_2$ may independently contain:

```text
module different_module_name
graph calculation(left, right) -> answer
temporary = Add(right, left)
answer = Identity(temporary)
shape symbol: Batch
```

The two programs need not share:

- module labels;
- graph labels;
- node labels;
- value labels;
- scoped-symbol labels;
- StructuralIDs;
- authoring provenance.

Under v0.7:

$$
H_{legacy}(P_1)
\neq
H_{legacy}(P_2),
$$

while:

$$
\boxed{
H_{CN}(P_1)
=
H_{CN}(P_2)
}
$$

and their canonical CoreNorm bytes are identical.

---

# 5. Explicit refusal boundary

v0.7 intentionally refuses cases not yet covered by a validated normalization rule.

## 5.1 Call nodes

Cross-graph call normalization requires recursive graph identity and possible recursion/fixed-point handling.

Therefore:

$$
\operatorname{Call}\notin\operatorname{Domain}(\operatorname{CoreNorm}_{0.7}).
$$

This is deferred to later reconstruction work.

## 5.2 Cyclic graphs

The prototype is a bounded DAG normalization experiment.

Unresolved cycles are rejected.

## 5.3 Dead nodes

v0.7 does not silently decide whether dead nodes are semantically irrelevant, resource-relevant, effect-relevant, or evidence-relevant.

A graph with non-trivial dead nodes is rejected under the default profile.

## 5.4 Ambiguous scoped binders

If two binders have identical name-independent structural occurrence signatures, the prototype does not invent a hidden lexical ordering.

It rejects normalization and requires a stronger future binder structure.

## 5.5 Identity elimination across explicit edges

If an explicit edge targets or originates from an Identity node selected for elimination, v0.7 refuses to guess how the edge should be rewired.

---

# 6. CoreNorm comparison certificate

v0.7 produces an explicit comparison record:

$$
\operatorname{Compare}_{CN}(P_1,P_2,\Pi).
$$

It records:

- source semantic hashes;
- normalized CoreNorm hashes;
- normalization-profile hash;
- equivalence result;
- first normalized difference when unequal;
- the claim boundary.

The claim boundary is always:

> bounded CoreNorm profile equivalence; not global semantic equivalence

This sentence is part of the machine-readable certificate so that downstream tools cannot silently upgrade the claim.

---

# 7. Witness statistics

A normalization witness records at least:

- graph count;
- node count;
- number of eliminated trivial Identity nodes;
- number of commutative reorder events;
- number of scoped binders alpha-normalized;
- unresolved obligations.

The witness is evidence about how the normalized object was constructed; it is not itself part of the normalized equivalence hash.

---

# 8. Idempotence target

The v0.7 logical target is normalization stability:

$$
\operatorname{Canon}
\left(
\operatorname{CoreNorm}_{\Pi}(P)
\right)
$$

must be deterministic across repeated execution.

Because CoreNorm currently emits a normalized IR record rather than a NOVA `Project`, the prototype tests deterministic byte equality rather than applying `CoreNorm` recursively to its own output type.

A future version may define a first-class normalized-program object and strengthen this into literal operator idempotence.

---

# 9. Falsification criteria

v0.7 is falsified within its declared domain if any of the following occurs:

1. label-only structural renaming changes CoreNorm output;
2. graph-local binder alpha-renaming changes CoreNorm output;
3. reversing inputs to declared commutative operators changes CoreNorm output;
4. inserting/removing a permitted trivial Identity changes CoreNorm output;
5. a semantic operator mutation such as `Add -> Subtract` does not change CoreNorm output;
6. reversing a non-commutative operator is incorrectly normalized as equivalent;
7. a human-only `reason` changes CoreNorm output;
8. an unsupported operation is silently accepted as equivalent instead of producing a refusal;
9. the same input produces non-deterministic CoreNorm bytes;
10. comparison certificates claim unrestricted semantic equivalence.

---

# 10. Relation to SREG methodology

v0.7 adopts the SREG cross-universe normalization principle:

$$
U_1\neq U_2
$$

may still admit:

$$
\operatorname{CoreNorm}(U_1)
\cong
\operatorname{CoreNorm}(U_2).
$$

In NOVA, the immediate experimental interpretation is:

$$
P_1\neq P_2
$$

while:

$$
\operatorname{CoreNorm}_{\Pi}(P_1)
=
\operatorname{CoreNorm}_{\Pi}(P_2).
$$

The crucial methodological constraint is that $\Pi$ remains explicit and versioned.

---

# 11. Transition to v0.8

v0.7 normalizes two already-constructed NOVA `Project` objects.

v0.8 should move one level outward and test **Cross-Representation Reconstruction**:

$$
\text{Surface}_i
\xrightarrow{R_i}
P_i
\xrightarrow{\operatorname{CoreNorm}}
C_i.
$$

The primary target becomes:

$$
\boxed{
C_1=C_2
}
$$

for semantically aligned source families such as:

- text-like source;
- graph-native authoring;
- AI-native structured construction;
- mathematical/formula projection.

This will test the stronger proposition that human-readable code can be a projection or import surface rather than the authoritative program object.

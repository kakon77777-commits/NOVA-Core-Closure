# NOVA Scoped Semantic Identity v0.6

**Date:** 2026-09-15  
**Status:** Experimental implementation specification  
**Branch:** `experiment/scoped-semantic-identity-v0.6`  
**Canonical math delimiter:** `$...$` and `$$...$$`

---

## 0. Purpose

NOVA v0.1–v0.5 progressively removed several accidental dependencies on human-readable text:

$$
\begin{aligned}
v0.1 &: \text{schema labels} \rightarrow \text{binary structural fields},\\
v0.2 &: \text{global semantic spelling} \rightarrow \text{Global Semantic ID},\\
v0.3 &: \text{structural labels} \rightarrow \text{StructuralID},\\
v0.4 &: \text{remaining text} \rightarrow \text{typed text domains},\\
v0.5 &: \text{Human Projection} \rightarrow \text{sidecar}.
\end{aligned}
$$

After v0.5, affine tensor dimensions such as `B`, `N`, and `H` still remain in the canonical semantic record as `Scoped Semantic Symbol` text.

For example, a shape may contain:

$$
(B,N,128).
$$

The letters are useful human projections, but the semantic object is not the spelling `B` itself. The required object is a scoped binder with persistent machine identity.

v0.6 therefore introduces:

$$
\boxed{
\sigma
=
(
S,
I,
F,
\Pi
)
}
$$

where:

- $S$ is the scope identity;
- $I$ is the persistent scoped-symbol identity;
- $F$ is the semantic symbol family;
- $\Pi$ is the human projection label.

For the v0.6 vertical slice, the scope is a NOVA Graph `StructuralID` and the supported family is `affine_dim`.

---

## 1. Core invariant

A human alpha-renaming must not change the machine program object:

$$
\boxed{
\operatorname{MID}_{6}(P,M_S,M_\sigma)
=
\operatorname{MID}_{6}(\alpha(P),M_S,\alpha(M_\sigma))
}
$$

where:

- $M_S$ is the persistent structural identity manifest from v0.3+;
- $M_\sigma$ is the v0.6 scoped-symbol manifest;
- $\alpha$ changes only scoped-symbol projection labels.

Thus:

$$
B \rightarrow \text{Batch}
$$

must not change NSM6 bytes if both labels refer to the same persistent scoped symbol.

Conversely, a semantic mutation such as:

$$
N \rightarrow 2N
$$

must change the machine identity hash.

---

## 2. Why a scoped symbol is not a global semantic atom

The v0.2 registry can assign a global identity to `MatMul`, `f32`, or `cpu` because those names denote globally shared semantic atoms.

A dimension variable is different.

Two graphs may both use the projection name `B` while referring to distinct binders:

$$
B_{G_1} \neq B_{G_2}.
$$

Therefore:

$$
\boxed{
\operatorname{ScopedID}
\neq
\operatorname{GlobalSemanticID}
}
$$

and:

$$
\operatorname{Identity}(B)
=
\operatorname{Identity}(\operatorname{scope},B).
$$

In v0.6:

$$
\operatorname{scope}=SID_{Graph}.
$$

---

## 3. Persistent scoped identity

A scoped symbol receives a 128-bit identity:

$$
SSID \in \{0,1\}^{128}.
$$

The human-facing text form is:

```text
ssid:<32 hex digits>
```

A manifest entry is conceptually:

```text
ScopedSymbolEntry {
  symbol_id
  scope_sid
  family
  label
  signature
}
```

The machine identity fields are:

$$
(symbol\_id,scope\_sid,family,signature).
$$

The human projection field is:

$$
label.
$$

Changing only `label` changes the projection hash but not the scoped-manifest identity hash.

---

## 4. Fresh migration without name-seeded identity

A critical rule is:

$$
\boxed{
SSID \not\leftarrow \operatorname{Hash}(\text{human symbol name})
}
$$

Otherwise `B` and `Batch` would become different machine objects during initial migration.

v0.6 instead derives a legacy binder's migration identity from its structural occurrence signature.

For a symbol $\sigma$:

$$
\operatorname{Sig}(\sigma)
=
\operatorname{Canon}
\left(
\left\{
(path_i,c_i)
\right\}_{i=1}^{n}
\right)
$$

where:

- $path_i$ is a structural semantic location inside the graph;
- $c_i$ is the affine coefficient at that occurrence.

The symbol identity is then derived from:

$$
SSID_\sigma
=
H_{128}
(
SID_G,
\operatorname{Sig}(\sigma)
).
$$

The human spelling does not participate.

### 4.1 Term-order leak prevention

Current affine terms may be lexically ordered by human symbol names. Therefore the term list index itself cannot be used as identity evidence.

v0.6 explicitly removes the term index from occurrence signatures.

This prevents an indirect leak:

$$
\text{rename}
\rightarrow
\text{lexical reorder}
\rightarrow
\text{different SSID}.
$$

---

## 5. Ambiguous migration

Some legacy expressions are genuinely symmetric.

For example:

$$
B+N
$$

with both symbols occurring in exactly the same structural position and with identical coefficients may provide no name-independent evidence that distinguishes which binder should receive which identity.

v0.6 does not solve this by secretly using the human names.

Instead:

$$
\boxed{
\operatorname{Sig}(B)=\operatorname{Sig}(N)
\Rightarrow
\operatorname{MigrationReject}
}
$$

with a requirement for an explicit persistent binder manifest.

This is intentional.

Ambiguity is made explicit rather than silently hidden.

---

## 6. NSM6

NSM6 extends the previous typed binary wire with a dedicated scoped-symbol reference tag.

A wire-level scoped reference contains:

$$
\operatorname{ScopedRef}
=
(SID_{scope},SSID_{symbol}).
$$

The v0.6 wire invariant is:

$$
\boxed{
\text{Scoped Semantic Symbol text}
\cap
\text{NSM6 machine payload}
=
\varnothing
}
$$

Human scoped-symbol labels live in the projection manifest/sidecar, not in the authoritative wire object.

NSM6 continues to preserve the v0.4/v0.5 rules:

- schema fields use field codes;
- registered semantic atoms use global IDs;
- structural objects use `StructuralID`;
- Human Projection is forbidden from the canonical payload;
- preserved text domains remain explicitly typed;
- untyped text is rejected.

---

## 7. Binder projection

Given a persistent scoped identity:

$$
SSID_x,
$$

multiple human projections are legal:

$$
\pi_{H_1}(SSID_x)=B,
$$

$$
\pi_{H_2}(SSID_x)=\text{Batch},
$$

$$
\pi_{H_3}(SSID_x)=b_0.
$$

These projections do not define the object.

Therefore:

$$
\boxed{
\text{Scoped Symbol Name}
\neq
\text{Scoped Symbol Identity}
}
$$

---

## 8. Scope separation

The same spelling in two graphs is not automatically the same binder.

For graph scopes $G_1$ and $G_2$:

$$
SID_{G_1}\neq SID_{G_2}
$$

implies independently derived symbols:

$$
SSID(B,G_1)\neq SSID(B,G_2).
$$

This prevents accidental global capture of locally meaningful shape variables.

---

## 9. Projection sidecar

The v0.6 sidecar records:

- `project_sid`;
- scoped-manifest machine identity hash;
- scoped-manifest projection hash;
- NSM6 machine hash;
- `SSID`;
- scope `StructuralID`;
- family;
- current human label;
- structural migration signature;
- stable projection anchor.

The projection anchor excludes the mutable label.

Therefore changing `B` to `Batch` preserves the attachment point for documentation and UI metadata.

---

## 10. Required precondition

The v0.6 migration assumes a persistent v0.3+ `IdentityManifest` already exists.

It does not regenerate structural object identity.

This boundary is deliberate:

$$
\boxed{
\text{Structural identity migration}
\prec
\text{Scoped binder migration}
}
$$

If a legacy project has no structural identity manifest, that manifest must first be created and persisted through the existing migration path.

---

## 11. Current scope and deferred work

v0.6 intentionally implements only graph-scoped affine dimension binders.

Deferred domains include:

- module-scoped type variables;
- project-scoped generic parameters;
- nested lexical binders;
- higher-order operator binders;
- existential/unification variables;
- proof-term variables;
- cross-graph explicitly shared dimensions.

These should not be silently collapsed into the graph-scoped model.

---

## 12. Acceptance conditions

v0.6 is accepted experimentally when all of the following hold:

1. `B -> Batch` changes legacy text-sensitive semantic hash;
2. the same rename does not change NSM6 bytes;
3. the same rename does not change v0.6 machine hash;
4. the same NSM6 blob can decode through a renamed scoped-symbol manifest;
5. scoped symbol spellings are absent from the tested wire payload;
6. identical spellings in different graph scopes receive distinct IDs;
7. changing an affine coefficient changes machine identity;
8. structurally ambiguous fresh binders are rejected;
9. scoped-manifest projection hash changes independently of identity hash;
10. v0.1–v0.5 isolated compatibility tests remain green.

---

## 13. Relation to SREG F-series

This implementation follows the SREG formalization principle:

$$
\boxed{
\text{Latent Ambiguity}
\rightarrow
\text{Explicit Structured Alternatives / Obligations}
}
$$

and the representation principle:

$$
\text{Visible Symbol}
\rightarrow
\text{Semantic Object}
\rightarrow
\text{Typed Operator Graph}
\rightarrow
\text{Executable / Verifiable State}.
$$

A visible mathematical variable is therefore treated as a projection over a scoped semantic object rather than as the object itself.

---

## 14. Next experimental gate

v0.6 prepares the next planned experiment:

$$
\boxed{
v0.7:\operatorname{CoreNorm}(P)
}
$$

CoreNorm will no longer focus on one textual domain at a time. It will test whether different authoring and representation surfaces can normalize to a shared machine structural core.

The intended transition is:

$$
\text{Identity Separation}
\rightarrow
\text{Representation Normalization}
\rightarrow
\text{Cross-Representation Reconstruction}.
$$

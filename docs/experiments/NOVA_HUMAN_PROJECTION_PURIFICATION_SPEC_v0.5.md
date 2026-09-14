# NOVA Human Projection Extraction / Semantic Purification v0.5

**Date:** 2026-09-15  
**Status:** Experimental implementation specification  
**Parent:** NOVA Symbol Domain Classification v0.4  
**Wire:** NSM5  
**Canonical math delimiter:** `$...$` and `$$...$$`

---

## 0. Executive statement

v0.4 established that not every remaining text token belongs to the same ontology. It also exposed one remaining authority leak: some values classified as `Human Projection` were still physically embedded inside the semantic record, most visibly diagnostic fields such as `reason`.

v0.5 removes that leak.

The governing invariant is:

$$
\boxed{
D_H\cap C_{\mathrm{semantic}}=\varnothing
}
$$

where $D_H$ is the Human Projection domain and $C_{\mathrm{semantic}}$ is the canonical machine semantic core.

Human-facing explanations are not deleted. They are extracted into a hash-linked sidecar whose attachment point is described by persistent structural identity and a purified semantic anchor.

---

## 1. What v0.5 changes

Before v0.5, a semantic constraint could contain:

```text
{
  kind: shape_obligation,
  proof_status: unknown,
  required_relation: eq,
  runtime_guard: true,
  reason: "batch dimensions must agree"
}
```

The first four fields participate in machine semantics. The last field is explanatory projection.

v0.5 separates them as:

$$
C
\longrightarrow
\left(
C^{\ast},
H_C
\right)
$$

where $C^{\ast}$ is the purified semantic object and $H_C$ is a human-projection sidecar entry.

---

## 2. Core invariants

### 2.1 Human projection exclusion

For every NSM5 canonical payload $P_5$:

$$
\operatorname{ContainsHumanProjection}(P_5)=\mathrm{false}.
$$

An NSM5 encoder rejects a record if a `DomainText(HUMAN_PROJECTION, ...)` survives purification.

### 2.2 Projection-edit invariance

Let $P$ and $P'$ differ only in Human Projection content while sharing an already-persisted Identity Manifest $M$. Then:

$$
\boxed{
\operatorname{NSM5}(P,M)
=
\operatorname{NSM5}(P',M)
}
$$

and therefore:

$$
H_{\mathrm{pure}}(P,M)
=
H_{\mathrm{pure}}(P',M).
$$

### 2.3 Semantic sensitivity

If a true semantic atom changes, for example:

$$
\operatorname{Add}\rightarrow\operatorname{Subtract},
$$

then:

$$
H_{\mathrm{pure}}(P,M)
\neq
H_{\mathrm{pure}}(P',M).
$$

### 2.4 Sidecar separability

Human-facing changes may alter:

$$
H_{\mathrm{sidecar}},
$$

without altering:

$$
H_{\mathrm{pure}}.
$$

Thus documentation can evolve independently of program identity.

---

## 3. Stable projection attachment

Line numbers and mutable labels are not sufficient attachment coordinates for externalized documentation.

Each extracted Human Projection entry therefore carries:

```text
owner_sid
semantic_anchor
path_hint
text
role
payload?
```

The authoritative attachment components are:

$$
\boxed{
(\operatorname{owner\_sid},\operatorname{semantic\_anchor})
}
$$

`path_hint` exists for diagnostics and user interfaces; it is not machine identity.

The semantic anchor is computed from the purified containing semantic object:

$$
A(C^{\ast})
=
\operatorname{SHA256}
\left(
\texttt{NOVA-PROJECTION-ANCHOR-v0.5}
\parallel
\operatorname{Canon}(C^{\ast})
\right).
$$

Consequently, editing only the explanatory text does not move its semantic anchor.

---

## 4. Constraint canonicalization after extraction

Legacy NOVA canonicalization sorts constraint records using their complete record form. If a human-only `reason` participates in that sort, changing the explanation may indirectly reorder constraints before purification.

v0.5 therefore performs a second canonicalization step after Human Projection removal:

$$
\operatorname{Sort}
\left(
\operatorname{constraints}^{\ast}
\right)
$$

using the purified representations themselves.

This closes an indirect path by which documentation could otherwise perturb machine bytes.

---

## 5. Purity-aware fresh identity bootstrap

v0.3 introduced persistent `StructuralID`, but its one-time bootstrap seed was created from the then-current semantic record. Because pre-v0.5 semantic records can contain human-only `reason` values, two otherwise identical legacy projects could theoretically bootstrap different project identities solely because their explanations differ.

v0.5 adds:

```text
bootstrap_purified_identity_manifest(project)
```

for **fresh migrations only**.

The rule is:

$$
\boxed{
\text{Existing Identity Manifest is immutable authority.}
}
$$

An existing manifest is never regenerated merely because v0.5 exists.

For a project that has never had a persistent identity manifest, the v0.5 bootstrap computes its seed from a reason-free purified semantic state:

$$
P
\rightarrow
D_4(P)
\rightarrow
\operatorname{Purify}
\rightarrow
P^{\ast}_{\mathrm{legacy}}
\rightarrow
\operatorname{Canon}
\rightarrow
\operatorname{Seed}_{0.5}.
$$

Hence if two fresh legacy projects differ only in Human Projection:

$$
\operatorname{Bootstrap}_{0.5}(P)
=
\operatorname{Bootstrap}_{0.5}(P').
$$

---

## 6. NSM5

NSM5 extends the experimental wire sequence:

$$
\mathrm{NSM1}
\rightarrow
\mathrm{NSM2}
\rightarrow
\mathrm{NSM3}
\rightarrow
\mathrm{NSM4}
\rightarrow
\mathrm{NSM5}.
$$

NSM5 retains all prior properties:

- numeric schema field identity;
- Global Semantic Registry atoms;
- persistent StructuralID;
- domain-tagged remaining text;
- strict refusal of unclassified text;

and adds:

$$
\boxed{
\text{Human Projection forbidden in canonical payload.}
}
$$

The header records:

```text
magic = NSM5
registry_revision
domain_revision
purification_revision
```

---

## 7. Human Projection Sidecar v0.5

The sidecar format is:

```text
nova.human-projection-sidecar/0.5
```

It contains:

- `project_sid`;
- `purified_machine_hash`;
- legacy semantic hash for migration traceability;
- extracted Human Projection entries that previously leaked into semantic structures;
- already-nonsemantic provenance / source projection / artifacts from the earlier sidecar boundary;
- a deterministic `sidecar_hash`.

The sidecar is not executable authority.

$$
\boxed{
H_{\mathrm{sidecar}}
\neq
H_{\mathrm{program}}
}
$$

---

## 8. Deliberate non-goals

v0.5 does **not** eliminate:

- scoped semantic symbols such as `B`, `N`, `H`;
- semantic string literals;
- external ABI / FFI / public-contract names;
- extension-owned opaque text;
- identity projection labels in the Identity Manifest.

Those belong to other domains and require separate treatment.

In particular:

$$
\text{Text remaining after v0.5}
\not\Rightarrow
\text{Human Projection leak}.
$$

---

## 9. Acceptance criteria

v0.5 passes when all of the following hold:

1. Human Projection inside semantic structures is extracted.
2. NSM5 rejects any residual Human Projection value.
3. Editing `reason` leaves NSM5 bytes unchanged with a persisted manifest.
4. Editing source projection / provenance leaves NSM5 bytes unchanged.
5. Editing true semantics changes the purified machine hash.
6. Extracted projection anchors remain stable across projection-text edits.
7. NSM5 decode/re-encode is byte-stable.
8. Fresh purity-aware bootstrap ignores Human Projection differences.
9. v0.2-v0.4 isolated compatibility tests remain green.
10. Sidecar and machine core remain separately hashable.

---

## 10. Resulting ontology

After v0.5, the authority split is:

$$
\boxed{
\mathcal P
=
\left(
C^{\ast},
M_{ID},
S_H,
X
\right)
}
$$

where:

- $C^{\ast}$ is purified canonical semantics;
- $M_{ID}$ is persistent structural identity plus human label projection;
- $S_H$ is Human Projection sidecar;
- $X$ contains explicitly typed external / extension boundaries.

The central consequence is simple:

> A human explanation may describe the program, but it no longer constitutes the program.

---

## 11. Next boundary

Once Human Projection is physically absent from canonical machine state, the next unresolved textual domain is the scoped semantic symbol:

$$
B,N,H,\ldots
$$

A future v0.6 can therefore address:

$$
\boxed{
\text{Scoped Semantic Symbol}
\rightarrow
\text{Scoped Semantic Identity}
}
$$

without mixing that problem with documentation extraction.

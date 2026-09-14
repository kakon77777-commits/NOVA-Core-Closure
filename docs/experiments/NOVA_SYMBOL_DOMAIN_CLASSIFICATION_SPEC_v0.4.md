# NOVA Symbol Domain Classification v0.4

**Status:** Experimental implementation specification  
**Date:** 2026-09-15  
**Branch:** `experiment/symbol-domain-classification-v0.4`  
**Canonical math delimiter:** `$...$` and `$$...$$`

## 0. Purpose

v0.1 proved that the canonical NOVA object can be serialized without repeating human-readable schema labels.  
v0.2 introduced a global numeric semantic registry.  
v0.3 separated persistent structural identity from mutable human labels.

v0.4 addresses the next boundary: **not every remaining string means the same kind of thing**.

Deleting or numerically replacing all remaining UTF-8 would be incorrect. A program may contain runtime string literals, ABI names, symbolic dimensions, extension-owned tokens, or explanatory text. These require different authority and migration rules.

The v0.4 objective is therefore classification before elimination.

$$
\boxed{
\text{Text occurrence}
\rightarrow
\text{explicit semantic domain}
\rightarrow
\text{domain-specific policy}
}
$$

## 1. Seven disjoint text domains

The implementation uses seven authoritative domains plus one rejection state:

$$
\mathcal D_{text}
=
D_I\sqcup D_A\sqcup D_S\sqcup D_L\sqcup D_E\sqcup D_H\sqcup D_X
$$

where:

- $D_I$ — **Structural Identity**: module, graph, node, value identities and identity-bearing references;
- $D_A$ — **Semantic Atom**: operator kinds, dtypes, devices, layouts, effect kinds, relation kinds, feature flags, schema/version atoms;
- $D_S$ — **Scoped Semantic Symbol**: local semantic symbols such as affine shape symbols (`B`, `N`, `H`);
- $D_L$ — **Semantic Literal**: runtime string/data literals whose textual bytes are program data;
- $D_E$ — **External Contract**: input/parameter binding names, import/export surfaces, ABI/FFI-facing names;
- $D_H$ — **Human Projection**: comments, provenance, source projection, diagnostic explanations;
- $D_X$ — **Extension Payload**: extension-owned keys and values whose interpretation belongs to a versioned extension.

A separate `UNCLASSIFIED` state is not a legal semantic domain. It means the Core does not yet have enough authority to transform the text safely.

## 2. Why five domains were insufficient

The initial v0.4 sketch considered identity, semantic atoms, external contracts, human projections, and extension payloads. Implementation exposed two missing cases.

### 2.1 Scoped semantic symbols

A shape symbol such as `B` in

$$
\operatorname{Tensor}[f32;(B,128)]
$$

is not a human label and not a globally registered atom. It is a local semantic variable. Treating it as either would destroy scope semantics.

### 2.2 Semantic literals

A constant program value such as `"hello world"` is actual runtime data. Removing it because it is human-readable would change program semantics.

Therefore v0.4 freezes seven domains rather than five.

## 3. Domain-specific dispositions

| Domain | Disposition |
|---|---|
| Structural Identity | lower to persistent SID |
| Semantic Atom | global registry code when known, otherwise typed semantic atom |
| Scoped Semantic Symbol | preserve with explicit scoped-symbol tag; stable scoped IDs deferred |
| Semantic Literal | preserve exact bytes as typed literal |
| External Contract | preserve exact contract spelling unless an external registry exists |
| Human Projection | sidecar target; semantic-core leakage is audited |
| Extension Payload | opaque owner-controlled payload |
| UNCLASSIFIED | strict encoding rejects |

Thus:

$$
\boxed{
\operatorname{Classify}(t)=\varnothing
\Longrightarrow
\operatorname{Encode}_{strict}(t)=\operatorname{Reject}
}
$$

## 4. NSM4: No Untyped Text

NSM4 adds a domain-tagged text representation.

The wire invariant is:

$$
\boxed{
\forall t\in\operatorname{Text}(NSM4),
\exists! d\in\mathcal D_{text}:\operatorname{tag}(t,d)
}
$$

In practice:

- canonical schema fields become numeric field references;
- registered semantic atoms become `(domain-id, atom-id)` GlobalRefs;
- v0.3 structural identities remain 128-bit SID bytes;
- every other retained UTF-8 payload becomes `DomainText(domain-code, bytes)`;
- raw untyped strings are rejected by the NSM4 encoder.

The fact that UTF-8 bytes may remain is therefore no longer ambiguous. Their authority is explicit.

## 5. Same spelling, different domain

Text classification is contextual, not lexical.

For example, `main` may be:

- a graph label in $D_I$ and therefore replaced by SID;
- part of an export contract such as `public.main` in $D_E$ and therefore preserved.

Hence:

$$
\boxed{
\operatorname{Domain}(t)
\neq
f(\operatorname{spelling}(t))
}
$$

The domain depends on structural position and semantic role.

## 6. Hidden structural references

v0.4 found an important class of references not covered by direct `id / inputs / outputs / edge` fields.

A NOVA `Call` currently stores the target graph in:

```text
attributes.callee
```

Although syntactically an attribute string, semantically it is a graph identity reference.

NSM4 therefore lowers:

$$
\texttt{Call.attributes.callee = "helper"}
\rightarrow
SID_{helper}
$$

before wire encoding.

When projected back through a renamed identity manifest, the same NSM4 bytes yield the new human graph label.

This restores the intended rename invariant across embedded references:

$$
\operatorname{NSM4}(P,M)
=
\operatorname{NSM4}(\rho(P),\rho(M)).
$$

## 7. Known operator / unknown attribute rule

For a registered Core operator, an unknown textual attribute is **not** silently interpreted as extension data.

Example:

```text
Add { mystery: "text" }
```

is classified as `UNCLASSIFIED` and strict NSM4 encoding rejects it.

For an unknown operator owned by an extension, e.g.

```text
FutureQuantumOp { mode: "phase weave" }
```

its unknown attributes are classified as extension-owned payload and preserved.

This asymmetry prevents accidental semantic authority transfer.

## 8. Human-projection leakage audit

v0.4 also distinguishes a human projection that is already outside the semantic core from one that still leaks into current semantic identity.

For example, current shape/constraint records can contain:

```text
reason: "explain only"
```

The classifier marks `reason` as $D_H$ while recording that it is presently inside the semantic core.

This does not silently rewrite historical Core semantics in v0.4. Instead it produces an explicit audit signal:

$$
\operatorname{Leak}_{H\rightarrow Core}>0.
$$

Moving those fields to sidecars is a later migration, not an implicit codec trick.

## 9. v0.4 implementation artifacts

The experimental implementation adds:

- `symbol_domains.py` — domain model, classifier, report, fingerprint;
- `domain_wire.py` — NSM4 domain-aware binary codec;
- `domain_identity.py` — identity + domain normalization, embedded structural-reference lowering, NSM4 round-trip and hash;
- `test_symbol_domains.py` — domain and wire acceptance tests;
- `run_validation_v04.py` — standalone executable validation.

No v0.1–v0.3 wire format is redefined.

## 10. Acceptance invariants

v0.4 accepts only if all of the following hold:

### Domain completeness

$$
N_{unclassified}=0
$$

for the covered validation program.

### Round-trip

$$
H_{sem}(P)
=
H_{sem}(D_{NSM4}(E_{NSM4}(P))).
$$

### Hidden-reference rename invariance

For label-only rename $\rho$:

$$
E_{NSM4}(P,M)
=
E_{NSM4}(\rho(P),\rho(M)).
$$

### Semantic mutation sensitivity

Changing semantic state while retaining the same SIDs must change the NSM4 machine hash.

### Strict unknown-text rejection

A registered Core operator with an unclassified textual attribute must be rejected.

## 11. What v0.4 does not claim

v0.4 does **not** claim that NOVA contains no UTF-8.

UTF-8 remains legitimate for:

- string literals;
- external names/contracts;
- scoped symbols pending stable scoped IDs;
- extension-owned payloads;
- temporarily leaked human projections.

The v0.4 claim is narrower and stronger:

$$
\boxed{
\text{NOVA no longer needs untyped text in its machine representation.}
}
$$

## 12. Next boundary

The remaining high-value targets are now explicit rather than guessed:

1. assign persistent identities to scoped semantic symbols;
2. extract human-projection leakage from semantic identity;
3. define contract registries only where external stability warrants them;
4. leave true semantic literals and extension-owned data intact.

This enables further text elimination without semantic destruction.

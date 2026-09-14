# NOVA Global Semantic Registry & NSM2 v0.2

**Status:** Experimental implementation specification  
**Target:** NOVA Core Closure 0.13.x  
**Compatibility:** Non-breaking; NSM1 decoding retained; Core schema unchanged  
**Registry revision:** 1

## 1. Purpose

NOVA already separates the canonical typed program graph from textual source. NSM1 proved that canonical semantic exchange does not require JSON syntax, but remaining semantic atoms such as `MatMul`, `f32`, `cpu`, and `row_major` were still stored as UTF-8 strings in a local symbol table.

NSM2 removes that requirement for known Core semantics.

$$
\boxed{
\text{known semantic atom}
\rightarrow
(\text{domain-id},\text{atom-id})
}
$$

while preserving forward compatibility:

$$
\boxed{
\text{unknown / extension atom}
\rightarrow
\text{deterministic local symbol}
}
$$

The registry is therefore not a closed vocabulary. It is a stable numeric identity layer for semantics that NOVA Core already recognizes.

## 2. Authority boundary

The registry does not redefine Core meaning. The existing NOVA graph, validators, type/shape systems, effect checks, execution semantics and semantic hash remain authoritative.

For a project $P$:

$$
P
\xrightarrow{E_{NSM2}}
B
\xrightarrow{D_{NSM2}}
P'
$$

must preserve:

$$
\boxed{
H_{sem}(P)=H_{sem}(P')
}
$$

The registry only replaces repeated human-readable semantic labels in the machine projection.

## 3. Registry identity model

Each globally registered atom has a pair:

$$
R(a)=(d,c)
$$

where $d$ is a stable domain code and $c$ is an append-only atom code inside that domain.

Initial domains are:

| Domain code | Domain |
|---:|---|
| 1 | record_kind |
| 2 | operator |
| 3 | dtype |
| 4 | device |
| 5 | layout |
| 6 | edge_kind |
| 7 | effect_kind |
| 8 | differentiation_kind |
| 9 | proof_status |
| 10 | relation |

Examples:

$$
R(\text{MatMul})=(2,10)
$$

$$
R(\text{f32})=(3,12)
$$

$$
R(\text{cpu})=(4,1)
$$

$$
R(\text{row\_major})=(5,2)
$$

These numeric identities are machine-facing. Human names remain projections and registry documentation.

## 4. Context-sensitive encoding

The same textual key can represent different semantic domains. `kind` is the obvious example: a Node kind is an operator, an Edge kind is an edge classification, while nested records such as `tensor_type` or `shape` use a structural record kind.

NSM2 therefore assigns a global identity from structural context rather than from spelling alone.

$$
\operatorname{Domain}(s,C)
$$

where $C$ is the surrounding canonical record structure.

This prevents accidental collapse of unrelated strings that happen to share the same text.

## 5. Wire-format change

NSM2 introduces:

- magic `NSM2`;
- a registry revision varint;
- a new typed value tag `GLOBAL`;
- payload `GLOBAL(domain-id, atom-id)`;
- append-only structural field codes;
- the existing deterministic local symbol table for unregistered atoms.

NSM1 remains decodable. NSM2 is the default encoder.

A decoder rejects a registry revision newer than it supports. A newer decoder may read an older revision because existing codes are immutable.

## 6. Global-known / local-fallback rule

The encoder MUST NOT reject a future operator, dtype, extension, symbolic dimension, user identifier, or attribute string merely because it is absent from the global registry.

Instead:

$$
E(s)=
\begin{cases}
\operatorname{GlobalRef}(d,c), & s\in R \\
\operatorname{LocalSymbol}(i), & s\notin R
\end{cases}
$$

This is required to preserve NOVA's existing forward-compatible extension boundary.

Global registration is an optimization and identity stabilization step, not permission to exist.

## 7. What NSM2 removes from the textual payload

For registered values, UTF-8 spelling no longer needs to appear in the semantic blob. Typical examples include:

- `Identity`, `MatMul`, `Relu`, `Softmax`;
- `f32`, `f64`;
- `cpu`, `cuda`, `rocm`;
- `dense`, `row_major`, sparse layouts;
- Core edge kinds;
- Core effect kinds;
- differentiability classes;
- known shape/proof relation atoms.

This means semantic equivalence is increasingly carried by numeric typed relations rather than by natural-language-like labels.

## 8. What remains textual in v0.2

NSM2 intentionally does NOT yet remove:

- module IDs;
- graph IDs;
- node IDs;
- value/input/output names;
- symbolic dimension names such as `B`;
- arbitrary attribute keys and values;
- feature flags and version strings;
- unknown extension atoms.

Those are candidates for later identity layers, especially v0.3 stable structural identity.

## 9. Non-goals

NSM2 does not:

1. change the NOVA Core graph schema;
2. normalize aliases such as `float32` into `f32`;
3. modify semantic hashes;
4. make registry membership a validity requirement;
5. replace human projections;
6. encode tensor payload blocks directly;
7. implement 128-bit structural IDs yet.

Alias normalization is deliberately excluded because changing spelling during decode could alter existing semantic identity.

## 10. Acceptance gate

NSM2 is accepted only if:

$$
H_{sem}(P)=H_{sem}(D_{NSM2}(E_{NSM2}(P)))
$$

NSM2 encoding is deterministic, NSM1 remains decodable, non-semantic sidecar changes do not affect the semantic blob, registered semantic atoms disappear from the UTF-8 payload, and unknown atoms continue to round-trip through deterministic local fallback.

## 11. Next target: v0.3

The next experiment moves from semantic labels to object identity.

Current:

$$
\text{node id}=\text{UTF-8 string}
$$

Target:

$$
\text{node identity}=ID_{128}
$$

with human names moved to an independent projection:

$$
ID_{128}\leftrightarrow\text{human label}.
$$

At that point NOVA's machine representation will no longer depend on natural-language-like names for most Core semantics or structural identity.

# NOVA Symbol-Minimal Canonical Encoding v0.1

**Status:** Experimental implementation specification  
**Target:** NOVA Core Closure 0.13.x  
**Compatibility:** Non-breaking; no Core schema change  

## 1. Purpose

NOVA already treats the typed structural graph as the authoritative program object. This experiment tests the stronger proposition that NOVA's machine-facing canonical exchange need not be a human-readable textual representation.

The experiment separates three objects:

$$
\boxed{
G^\ast \neq B_{SM} \neq V_H
}
$$

where:

- $G^\ast$ is the authoritative typed structural program object;
- $B_{SM}$ is a deterministic symbol-minimal machine encoding;
- $V_H$ is a human projection or documentation sidecar.

The machine encoding is not a new programming ontology. It is an alternative canonical transport/serialization projection of the existing semantic object.

## 2. Required invariant

For every supported NOVA project $P$:

$$
P
\xrightarrow{E_{SM}}
B
\xrightarrow{D_{SM}}
P'
$$

must satisfy:

$$
\boxed{
H_{sem}(P)=H_{sem}(P')
}
$$

This invariant is the primary acceptance criterion.

## 3. Separation of authority and annotation

NOVA already excludes provenance and source projections from semantic hashing. v0.1 makes that separation explicit at the encoding boundary:

$$
P
\rightarrow
\left(
B_{semantic},
S_{annotation}
\right)
$$

$B_{semantic}$ is machine authority for semantic exchange. $S_{annotation}$ contains human-facing labels, source projections, provenance, documentation references and other non-authoritative records.

Changing only $S_{annotation}$ must not change $B_{semantic}$ or $H_{sem}$.

## 4. v0.1 encoding model

The semantic project record is transformed in two steps.

First, known structural field names are replaced by append-only numeric field codes. Second, all remaining UTF-8 string atoms are interned into one deterministic local symbol table, ordered by their UTF-8 byte representation.

The binary body therefore contains typed values, field references and symbol references rather than repeated textual syntax.

The v0.1 value domain is:

$$
V=
\{
null,
boolean,
integer,
float64,
bytes,
array,
map,
symbol\_ref,
field\_ref
\}.
$$

Maps are sorted by canonical encoded key bytes. Integers use signed zig-zag varints. Floating point values use big-endian IEEE-754 binary64; NaN and infinity are rejected by the canonical encoder in v0.1.

## 5. What this proves and does not prove

A successful v0.1 demonstrates that:

1. NOVA execution identity does not require JSON syntax;
2. structural schema labels need not be repeated textual tokens;
3. machine exchange can remain deterministic and round-trip semantic identity;
4. comments and human projections can live outside the authoritative semantic payload;
5. the same NOVA object can support a machine-native representation and independent human views.

It does not yet prove that every semantic atom can be globally numeric. Node kinds, user identifiers, symbolic dimensions and extension payloads may still appear as UTF-8 atoms in the local symbol table.

## 6. Next steps

### v0.2 — Stable global registries

Introduce versioned registries for core operator kinds, dtypes, devices, layouts, edge kinds and effect kinds. Known semantic atoms then become global numeric identities rather than local strings.

### v0.3 — Stable structural identity

Evaluate 128-bit or content-derived stable identifiers for module, graph, node and value identity, with human names moved entirely into projections/sidecars.

### v0.4 — Tensor-native payload blocks

Add dense and sparse tensor payload blocks with explicit dtype, shape, device and layout descriptors, avoiding textual tensor materialization.

### v0.5 — AI-native direct construction

Allow AI builders to emit validated structural objects or symbol-minimal candidate patches directly, without generating an intermediate source-text representation.

## 7. Acceptance gate

The experiment is accepted only if all of the following hold:

$$
H_{sem}(P)=H_{sem}(D_{SM}(E_{SM}(P)))
$$

$$
E_{SM}(P)=E_{SM}(P)
$$

for repeated deterministic encoding, and changes restricted to non-semantic annotations leave $E_{SM}(P)$ unchanged.

The existing NOVA validator remains authoritative. The symbol-minimal codec may transport semantics; it may not redefine them.

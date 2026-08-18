# Round 00 — Basic Introduction

## Purpose

This round creates the public-facing project anchor for **NOVA Core Closure** before implementation begins.

It freezes three statements.

### 1. Program authority is structural

$$
\boxed{
\text{Authoritative Program Identity}
=
\text{Versioned Typed Program Graph}
}
$$

Human-readable text is a projection and interchange form, not the sole source of truth.

### 2. Tensor semantics are native

Tensor rank, shape, axes, broadcasting, contraction, device obligations, and differentiation metadata belong in the language semantics rather than being hidden inside an external library convention.

### 3. AI edits structure but does not define correctness

AI-native construction uses candidate graphs and GraphPatch transactions.

A patch may enter the authoritative graph only after the relevant deterministic checks pass.

## First implementation target

The next round begins Phase A:

```text
Canonical Graph Kernel
├── Project / Module / Graph schema
├── Node / Edge model
├── deterministic canonicalization
├── semantic hash
├── schema/version header
├── structured errors
├── GraphPatch transaction
└── rollback
```

This creates the irreversible engineering anchor on which tensor/shape semantics, execution, AD, projections, and AI-native construction can be built.

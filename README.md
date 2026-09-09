# NOVA Core Closure

**NOVA Core Closure** is the reference implementation project for the executable core of NOVA: a structure-first, tensor-native, differentiable, AI-assisted programming language architecture.

NOVA does **not** treat source text as the authoritative program object. The canonical program is a typed structural graph; text, mathematical notation, graph views, documentation, debugging views, and AI-facing patches are projections of that same program object.

$$
\boxed{
\text{Canonical Program}
=
\text{Typed Structural Graph}
}
$$

## Frozen NOVA Core model

$$
\boxed{
\mathcal N_{\mathrm{Core}}
=
(
\mathcal G,
\mathcal T,
\mathcal S,
\mathcal E,
\mathcal M,
\mathcal D,
\mathcal R
)
}
$$

where:

- $\mathcal G$ — typed program graph;
- $\mathcal T$ — values and tensor types;
- $\mathcal S$ — shape and constraint solving;
- $\mathcal E$ — effects and reproducibility;
- $\mathcal M$ — verifiable memory/resource planning;
- $\mathcal D$ — language-level automatic differentiation;
- $\mathcal R$ — backend implementations.

## Development status

### Round 00 — Basic Introduction

Repository bootstrap, recovered source basis, and Core Closure scope.

### Round 01 — Canonical Graph Kernel

**Implemented.** Immutable canonical graph objects, deterministic serialization, semantic hashing, typed validation, forward-compatible extensions, GraphPatch transaction and rollback.

### Round 02 — Tensor / Shape Semantic Kernel

**Implemented.** Tensor types, symbolic affine dimensions, bounded shape solver, explicit shape obligations, broadcasting, matmul/contraction, reshape, transpose, and canonical tensor-type serialization.

### Round 03 — Executable Closure

**Implemented.** NOVA can now execute its canonical structure directly:

- immutable runtime input/parameter environments;
- runtime tensor shape validation;
- typed execution errors;
- deterministic dependency-driven interpreter;
- pure arithmetic and tensor execution;
- `MatMul`, reshape/transpose, reductions and activations;
- explicit `If`, finite `BoundedLoop`, and pure graph `Call`;
- NumPy CPU backend with differential tests against the interpreter;
- structured-text projection;
- mathematical formula projection for the supported subset;
- Python `load/run/project` API;
- CLI `check`, `run`, `hash`, and `project`.

The executable identity invariant is:

$$
\boxed{
H_{\mathrm{sem}}(G_{\mathrm{before}})
=
H_{\mathrm{sem}}(G_{\mathrm{after}})
}
$$

Execution produces runtime state and traces; it does not rewrite the canonical program graph.

The reference interpreter is the semantic anchor. NumPy is a backend implementation, not the definition of NOVA semantics.

### Round 04 — Reverse-Mode Automatic Differentiation

**Next.** Round 04 will add language-level reverse-mode AD as an explicit graph transformation, finite-difference gradient verification, stop-gradient boundaries, and typed non-differentiable failure.

## Quick start

```text
python -m pip install -e .
nova check examples/executable_linear.json
nova run examples/executable_linear.json --module app --graph main --inputs examples/executable_inputs.json --backend numpy
nova project examples/executable_linear.json --module app --graph main --view formula
```

Expected formula projection:

$$
Y = (X \cdot W) + b.
$$

Expected numeric result for the included example:

```json
{"Y": [[8.5]]}
```

## AI-native boundary

AI-native NOVA does not mean AI-trusted NOVA.

$$
\text{Intent}
\rightarrow
\text{Candidate GraphPatch}
\rightarrow
\text{Deterministic Validation}
\rightarrow
G^\ast.
$$

AI proposals remain untrusted until the canonical validators, runtime guards, tests, and later proof obligations accept them.

## Round artifact rule

Each completed development round is packaged as a self-contained ZIP after the full verification gate.

Current delivery mode is **local ZIP handoff**. GitHub publication remains paused until explicitly resumed.

## Scope discipline

NOVA Core Closure does not collapse EML, ISQL, SOS, Cl-safe, HSO, or other EveMissLab systems into the Core. Those systems connect through versioned interfaces after the Core semantic contract is stable.

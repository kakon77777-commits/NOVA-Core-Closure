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

**Implemented.** Reference interpreter, NumPy CPU backend, runtime shape guards, pure arithmetic/tensor operations, explicit bounded control flow, projections, Python API and CLI.

### Round 04 — Reverse-Mode Automatic Differentiation

**Implemented.** NOVA now differentiates its own canonical graph as an explicit graph transformation:

$$
\boxed{
G
\xrightarrow{\mathcal D_{\mathrm{rev}}}
G_{\nabla}
}
$$

Round 04 includes:

- deterministic `DifferentiationRequest` and derivative graph identity;
- scalar `grad` and explicit-seed VJP construction;
- explicit VJP rule registry;
- fan-out gradient accumulation;
- broadcast-aware cotangent reduction;
- MatMul, reshape, transpose, reduce, mean, ReLU, sigmoid, tanh and softmax reverse rules;
- explicit `StopGradient` barriers;
- typed failure for unknown, non-differentiable and unsupported paths;
- derivative graph execution through Interpreter and NumPy backend;
- finite-difference gradient checking as an external validator;
- derivative text/formula projections;
- Python gradient API;
- CLI `nova grad`.

AI or external autograd systems do not define correctness. Finite differences verify the graph-level derivative transform but never replace it.

### Round 05 — Model Closure & Training Validation

**Implemented.** NOVA now composes its canonical graph, NumPy/interpreter execution, and reverse-mode derivative graph into a deterministic immutable full-batch SGD training runtime. Parameter values remain runtime state; optimizer steps never mutate canonical program identity.

Round 05 closes the original G1 three-model exit condition with:

- Linear Regression training closure;
- a deterministic small MLP training closure;
- a small single-head Attention model using MatMul, Transpose, Divide and Softmax;
- immutable `TrainingState` and structured `TrainingStepRecord`;
- deterministic runtime-only parameter-state hashing;
- explicit SGD updates;
- Python `train_project` API;
- CLI `nova train`;
- finite-difference validation for the Attention reverse path.

### Round 06 — DLPack / Interop & G1 Final Seal

**Implemented.** Python/NumPy runtime exchange, explicit dtype/shape/device contracts, DLPack provider and raw-capsule import/export, verified CPU zero-copy round-trip, typed interop failures, API/CLI diagnostics, and the final G1 verification matrix.

**G1 is now sealed.** The original executable-core requirements have a reference implementation, tests, examples, and a versioned schema.

### Round 07 — G2 Projection & Editing

**Next.** Enter G2: projection consistency, structured editing, structural diff, error views, and semantic-hash-preserving projection workflows.

## Quick start

```text
python -m pip install -e .
nova check examples/differentiable_linear.json
nova run examples/differentiable_linear.json --module app --graph main --inputs examples/differentiable_inputs.json --parameters examples/differentiable_parameters.json --backend numpy
nova grad examples/differentiable_linear.json --module app --graph main --target loss --wrt W --wrt b --inputs examples/differentiable_inputs.json --parameters examples/differentiable_parameters.json --backend numpy --check
nova train examples/training_linear.json --module app --graph main --target loss --wrt W --wrt b --inputs examples/training_linear_inputs.json --parameters examples/training_linear_parameters.json --steps 60 --learning-rate 0.2 --backend numpy
# DLPack diagnostics operate on NumPy .npy runtime artifacts:
# nova interop inspect tensor.npy
# nova interop roundtrip tensor.npy
```

## Identity invariant

Execution and differentiation do not mutate the primal graph:

$$
\boxed{
H_{\mathrm{sem}}(G_{\mathrm{before}})
=
H_{\mathrm{sem}}(G_{\mathrm{after}})
}
$$

A derivative graph is a new canonical program object with its own deterministic semantic hash.

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

AI proposals remain untrusted until canonical validators, runtime guards, tests, and later proof obligations accept them.

## Round artifact rule

Each completed development round is packaged as a self-contained ZIP after the full verification gate.

Current delivery mode is **local ZIP handoff**. GitHub publication remains paused until explicitly resumed.

## Scope discipline

NOVA Core Closure does not collapse EML, ISQL, SOS, Cl-safe, HSO, or other EveMissLab systems into the Core. Those systems connect through versioned interfaces after the Core semantic contract is stable.

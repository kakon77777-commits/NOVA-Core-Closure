# NOVA Core Closure Round 04 — Reverse-Mode Automatic Differentiation Design

## Status
Approved by continuation of the Round 03 roadmap.

## Goal
Make automatic differentiation a NOVA graph transformation rather than an external runtime trick.

$$
\boxed{
G
\xrightarrow{\mathcal D_{\mathrm{rev}}}
G_{\nabla}
}
$$

The derivative graph is a normal, versionable NOVA `Graph` and must execute through the existing reference runtime.

## Scope
Round 04 implements:

1. `DifferentiationRequest` and deterministic derivative graph identity;
2. reverse topological traversal and VJP rule registry;
3. gradient accumulation for fan-out;
4. scalar `grad` and explicit-seed VJP construction;
5. typed failure for non-differentiable, unknown, or unsupported nodes;
6. derivative execution primitives required for broadcast/shape reversal;
7. finite-difference gradient checking;
8. Python API and CLI exposure;
9. canonical serialization/hash stability of derivative graphs.

## Non-goals
Round 04 does not implement:

- forward-mode AD;
- higher-order derivatives;
- general differentiation through `If`, `BoundedLoop`, or `Call`;
- stochastic estimators;
- custom user derivative registration across package boundaries;
- memory checkpoint scheduling;
- JAX/PyTorch autograd delegation;
- optimizer/training APIs.

## Differentiation request

```text
DifferentiationRequest {
  target
  wrt[]
  seed_input?
  derivative_graph_id?
}
```

If `seed_input` is absent, `target` must be statically known as a scalar tensor. The transform inserts a scalar cotangent seed of `1.0`.

If `seed_input` is present, the derivative graph accepts that symbol as an additional graph input and computes an explicit vector-Jacobian product.

## Derivative graph contract

The derivative graph contains:

1. the original primal nodes;
2. deterministic backward nodes;
3. final identity nodes exposing one gradient output per requested `wrt` symbol.

The primal graph is not mutated.

$$
H_{\mathrm{sem}}(G)_{\mathrm{before}}
=
H_{\mathrm{sem}}(G)_{\mathrm{after}}.
$$

Repeated transformation of the same graph and request must produce the same derivative graph semantic hash.

## VJP rules

Round 04 supports:

- `Identity`;
- `Add`;
- `Subtract`;
- `Multiply`;
- `Divide`;
- `Negate`;
- `MatMul`;
- `Reshape`;
- `Transpose`;
- `ReduceSum`;
- `Mean`;
- `Relu`;
- `Sigmoid`;
- `Tanh`;
- `Softmax`;
- `StopGradient`.

`Input`, `Parameter`, and `Constant` are leaves.

## Internal derivative primitives

To keep the derivative graph explicit without smuggling NumPy logic into the transform, Round 04 introduces a small internal execution vocabulary:

```text
ADReduceToShape
ADBroadcastLike
ADReshapeLike
ADTransposeLast2
ADMeanGrad
ADReluGrad
ADZeroLike
StopGradient
```

These are canonical graph nodes with deterministic execution semantics. They are not hidden tapes.

## Gradient accumulation

If a symbol receives cotangents $g_1,\ldots,g_k$, the transform emits deterministic `Add` nodes:

$$
\bar x
=
g_1+\cdots+g_k.
$$

This makes fan-out accumulation observable in the derivative graph.

## Differentiability boundary

A node on the active reverse path is rejected if:

- `differentiation_type == NonDifferentiable`;
- `differentiation_type == UnknownDifferentiability`;
- its node kind has no registered Round 04 VJP rule.

Failure is `DiffError` with source node, kind, and repair candidates.

`StopGradient` is a legal explicit barrier and contributes no cotangent to its input.

## Validation

Round 04 requires:

- analytic gradients equal finite differences within tolerance;
- Interpreter and NumPy backend agree on derivative graph execution;
- fan-out gradients accumulate correctly;
- broadcasted bias gradients reduce to original shape;
- matrix gradients are correct;
- nonlinear activation gradients are correct;
- softmax VJP is correct;
- unsupported/non-differentiable paths fail explicitly;
- derivative graph hash is deterministic;
- original graph hash is unchanged.

## Release boundary

Round 04 raises NOVA Core runtime version to `0.4.0` while keeping graph storage schema at `0.1.0` unless a breaking storage change becomes necessary.

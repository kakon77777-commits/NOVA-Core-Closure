# Round 02 Release Notes

**Release:** NOVA Core Closure 0.2.0  
**Round:** 02 — Tensor / Shape Semantic Kernel  
**Date:** 2026-08-19

## Added

- immutable integer-affine `DimExpr`;
- immutable `Shape` and `TensorType`;
- bounded deterministic `ShapeSolver`;
- explicit `ProofStatus` and `ShapeObligation`;
- concrete/symbolic broadcasting;
- elementwise shape inference;
- batched `MatMul` shape inference;
- general contraction;
- reshape element-count validation;
- transpose permutation validation;
- typed tensor/shape canonical JSON integration;
- typed codec round-trip;
- forward-compatible tensor-type extension preservation.

## Safety boundary

Round 02 deliberately does not silently accept unresolved symbolic relations.

$$
\boxed{
\text{Unable to prove}
\neq
\text{Compatible}
}
$$

The solver returns an explicit obligation when a relation falls outside the bounded proof subset.

## Solver subset

The first solver supports:

- normalized integer-affine equality;
- concrete equality / inequality;
- symbol aliases;
- direct symbol bindings;
- single-symbol integral solutions.

It does not claim complete Presburger arithmetic support.

## Next

Round 03 begins **Executable Closure** using the now-explicit tensor/shape semantics as the reference execution contract.

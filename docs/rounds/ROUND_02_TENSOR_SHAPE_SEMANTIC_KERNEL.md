# Round 02 — Tensor / Shape Semantic Kernel

Round 02 makes tensor rank, shape, broadcasting, contraction, reshape, and transpose explicit NOVA semantic objects rather than backend conventions.

## Implemented

- `DimExpr`: normalized integer-affine dimension expressions;
- `Shape`: immutable rank-aware dimension tuples;
- `TensorType`: dtype + shape + layout + device;
- `ShapeSolver`: bounded deterministic equality solver;
- `ShapeObligation`: explicit unresolved shape relation;
- `broadcast_shapes` / `elementwise_shape`;
- `matmul_shape` / `contract_shape`;
- `reshape_shape` / `transpose_shape`;
- canonical/codec integration for typed tensor records.

## Deliberate solver boundary

Round 02 does not claim complete Presburger arithmetic support. Its proof kernel handles normalized affine integer equalities, direct symbol bindings, aliases, and integral single-symbol solutions.

If the kernel cannot prove or disprove a relation, NOVA returns an obligation:

$$
\boxed{
\text{Unknown}
\Rightarrow
\text{ShapeObligation}
}
$$

not an implicit success.

## Round 03 handoff

The next closure round can now execute typed graphs without inventing shape semantics in the backend. The first executable target remains:

$$
Y=XW+b.
$$

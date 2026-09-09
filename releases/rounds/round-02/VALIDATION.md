# NOVA Core Closure Round 02 Validation

**Release:** 0.2.0  
**Round:** 02 — Tensor / Shape Semantic Kernel  
**Date:** 2026-08-19  
**Delivery:** local ZIP handoff

## Functional verification

- Full pytest suite: **59 / 59 passed**.
- Python bytecode compilation: PASS.
- `examples/tensor_shape_graph.json` decode → canonical encode → decode: PASS.
- Example semantic hash remains stable across round-trip:

```text
sha256:d1b2af87e49c14a83ceb4457fa0d93380a7c7765225850cce71311af84afefdc
```

## Round 02 semantic coverage

Verified behaviors include:

- integer-affine dimension normalization;
- negative concrete dimensions rejected as actual shape dimensions;
- symbolic affine expressions may contain negative intermediate constants;
- scalar rank-0 tensor semantics;
- tensor dtype / shape / layout / device records;
- concrete shape equality proof and rejection;
- direct symbol bindings;
- symbol aliases;
- integral single-symbol solving;
- unresolved relations preserved as `ShapeObligation`;
- concrete and symbolic broadcasting;
- unresolved broadcast does not silently succeed;
- batched `MatMul` inference;
- explicit contraction obligations;
- general tensor contraction;
- concrete reshape element-count verification;
- symbolic reshape element-count obligation;
- transpose permutation validation;
- typed tensor canonical JSON;
- tensor/shape codec round-trip;
- nested future tensor-type fields preserved through `extensions`;
- semantic hash stability after typed round-trip;
- Node-level rejection when `TensorType.shape` and `shape_type` disagree.

## Solver claim boundary

Round 02 intentionally implements a bounded deterministic subset:

$$
\boxed{
\text{normalized affine integer equality}
+
\text{symbol bindings}
+
\text{symbol aliases}
+
\text{single-symbol integral solving}
}
$$

It does **not** claim a complete Presburger arithmetic solver.

When the current proof kernel cannot prove or disprove a shape relation, the result remains explicit:

$$
\boxed{
\text{UNKNOWN}
\Rightarrow
\text{ShapeObligation}
}
$$

## Source hygiene

Pre-release source scan:

- tracked files before release metadata: 29;
- UTF-8 failures: 0;
- replacement characters: 0;
- secret-pattern hits: 0;
- literal Unicode escape patterns: 0;
- hidden control characters: 0;
- alternate Markdown math delimiter forms: 0;
- `git diff --check`: PASS;
- working tree before metadata generation: clean.

## Important regression caught during release

The hygiene scan detected an ASCII backspace produced by an incorrectly escaped `\boxed` sequence in README generation. It was removed before release. The same block was checked for accidental tab expansion from `\text`; final source contains literal LaTeX commands and no hidden control characters.

## Deferred to later rounds

Round 02 does not implement:

- tensor value execution;
- interpreter or NumPy backend;
- reverse-mode AD execution;
- memory/resource planner;
- complete effect system;
- GPU/distributed lowering;
- complete Presburger arithmetic;
- EML / ISQL / SOS / Cl-safe integration.

Round 03 begins Executable Closure on top of these explicit tensor/shape semantics.

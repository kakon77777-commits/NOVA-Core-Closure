# NOVA Core Closure Round 06 — DLPack / Interop & G1 Final Seal Design

## Status

Approved continuation of the previously declared Round 06 milestone.

## Goal

Close the remaining G1 interoperability requirement without changing NOVA's canonical program ontology.

Round 06 adds runtime-boundary tensor exchange for Python/NumPy and DLPack, then produces a final G1 verification matrix covering the executable Core closure from Round 01 through Round 06.

## Core boundary

Canonical NOVA tensor semantics remain:

$$
\operatorname{Tensor}[\tau;(d_1,\ldots,d_r);\ell;\delta].
$$

Interop operates on runtime values. It must not make a NumPy ndarray, DLPack capsule, Python list, or any external framework object the authoritative program representation.

$$
\boxed{
\text{Canonical Tensor Contract}
\neq
\text{External Runtime Object}
}
$$

## Python / NumPy interop

Round 06 provides explicit conversion utilities that:

- accept Python scalars, nested sequences, and NumPy arrays;
- preserve or explicitly convert dtype;
- validate rank and concrete/symbolic shape against `TensorType`;
- return NumPy arrays for execution;
- export runtime arrays to Python-safe copies or views by explicit policy;
- never silently reinterpret incompatible shape or dtype.

## DLPack interop

The DLPack boundary follows the Python Array API convention:

- export from any object implementing `__dlpack__` and `__dlpack_device__` where applicable;
- import through `numpy.from_dlpack(provider)`;
- raw `PyCapsule` values are not treated as self-describing Python providers;
- a dedicated one-shot provider wrapper may bridge a raw capsule into `numpy.from_dlpack`;
- imported DLPack arrays may be read-only depending on producer/runtime semantics;
- capsule consumption is one-shot and must be typed as such;
- zero-copy is verified when NumPy reports shared memory for NumPy-to-NumPy DLPack exchange.

Round 06 does not promise arbitrary GPU framework support; device metadata that cannot be realized by the CPU reference runtime returns typed `InteropError`.

## Typed failure

Interop failures are explicit and auditable:

- `InteropError` — unsupported or invalid external object;
- `DTypeInteropError` — incompatible dtype or conversion policy;
- `DLPackInteropError` — export/import/capsule protocol failure;
- existing `RuntimeShapeError` — shape contract failure.

No interop helper may silently coerce a failure into a best-effort result.

## Public interfaces

Python API:

```text
to_numpy(value, expected=None, dtype_policy="safe")
from_numpy(array, *, copy=False)
to_python(value, *, copy=True)
to_dlpack(value)
from_dlpack(provider_or_capsule, expected=None)
dlpack_device(value)
```

CLI additions:

```text
nova interop inspect <npy-file>
nova interop roundtrip <npy-file>
```

The CLI is a diagnostic surface only. It does not introduce a new source language.

## G1 final seal

Round 06 creates `G1_VERIFICATION_MATRIX.md` and machine-readable `g1_verification.json` with evidence for:

1. Core Graph schema;
2. type and symbolic shape semantics;
3. interpreter;
4. NumPy CPU backend;
5. reverse-mode AD;
6. CLI;
7. structured-text/formula projection;
8. Python/NumPy/DLPack interop;
9. Linear Regression training;
10. MLP training;
11. Small Attention training;
12. deterministic serialization/hash and no-silent-failure rules.

The seal means G1's stated MVP exit criteria are implemented and reproducibly tested. It does not claim G2 projectional editing, G3 resource safety, or later roadmap gates are complete.

## Non-goals

Round 06 does not add:

- PyTorch/JAX/TensorFlow dependencies;
- GPU DLPack execution;
- C ABI;
- ONNX;
- MLIR lowering;
- optimizer changes;
- new tensor operators;
- projectional editing;
- memory/resource planner behavior.

## Release rule

Version becomes `0.6.0`. Graph storage schema remains `0.1.0` because runtime interop does not require a breaking canonical schema change.

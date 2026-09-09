# Round 06 — DLPack / Interop & G1 Final Seal

## Purpose

Round 06 closes the remaining G1 interoperability requirement without changing NOVA's canonical graph ontology.

The runtime boundary now supports explicit Python/NumPy conversion and DLPack exchange while preserving the rule:

$$
\boxed{
\text{External Runtime Tensor}
\neq
\text{Canonical Program Identity}
}
$$

## Python / NumPy contract

Implemented capabilities:

- Python scalar and nested-sequence import;
- NumPy ndarray import;
- NOVA dtype aliases including `f32`, `f64`, integer and complex families;
- `safe` and `exact` dtype policies;
- runtime shape validation against `TensorType`;
- CPU device and realized-layout checks;
- explicit NumPy copy/view policy;
- plain-Python scalar/list export;
- canonical graph hash invariance across interop operations.

An ndarray with an explicit external dtype is never silently narrowed under `safe` policy.

## DLPack contract

Implemented capabilities:

- provider-based import through `numpy.from_dlpack`;
- raw `PyCapsule` bridge through a one-shot provider adapter;
- NumPy export through `__dlpack__`;
- DLPack device inspection;
- CPU-only device enforcement for the Round 06 reference runtime;
- dtype and shape validation after import;
- typed rejection of consumed capsules and unsupported providers;
- verified shared-memory zero-copy exchange for NumPy CPU arrays.

DLPack does not become NOVA's storage format. It is a runtime exchange protocol.

## Public surfaces

Python:

```text
to_numpy
from_numpy
to_python
to_dlpack
from_dlpack
dlpack_device
```

API wrappers:

```text
interop_to_numpy
interop_to_dlpack
interop_from_dlpack
```

CLI diagnostics:

```text
nova interop inspect tensor.npy
nova interop roundtrip tensor.npy
```

## Typed failures

Round 06 adds:

```text
InteropError
DTypeInteropError
DLPackInteropError
```

Shape violations continue to use `RuntimeShapeError`.

## G1 seal

The G1 seal covers the implementation lineage from Round 01 through Round 06:

1. canonical graph schema and deterministic identity;
2. tensor and symbolic shape semantics;
3. interpreter;
4. NumPy CPU backend;
5. reverse-mode automatic differentiation;
6. CLI;
7. structured-text and formula projections;
8. Python/NumPy/DLPack interoperability;
9. Linear Regression training closure;
10. small MLP training closure;
11. Small Attention training closure;
12. typed failure and no-silent-guess rules.

The seal means the declared G1 MVP exit criteria have a reference implementation, tests, examples, and reproducible release evidence. It does not imply G2 projectional editing, G3 memory/resource safety, or later gates are complete.

## Next gate

Round 07 enters **G2 Projection & Editing**.

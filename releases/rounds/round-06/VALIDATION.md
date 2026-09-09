# NOVA Core Closure Round 06 — Validation Record

**Release:** 0.6.0  
**Round:** DLPack / Interop & G1 Final Seal  
**Date:** 2026-08-20

## 1. Baseline provenance

Round 06 was reconstructed from the verified Round 05 ZIP release.

- inherited Round 05 checksum manifest: **81 / 81 PASS**
- inherited Round 05 full test suite: **144 / 144 PASS** before Round 06 implementation

## 2. Full regression

Fresh Round 06 full suite before release metadata freeze:

```text
167 passed
0 failed
```

Warnings are promoted to errors for bytecode compilation:

```text
python -W error -m compileall -q src tests
PASS
```

## 3. Python / NumPy interoperability

Validated behaviors include:

- Python scalars and nested sequences imported as NumPy runtime tensors;
- explicit NOVA dtype aliases;
- `safe` and `exact` dtype policies;
- narrowing ndarray casts rejected under `safe` policy;
- rank/shape validation through the existing runtime shape guard;
- non-CPU reference contracts rejected;
- explicit NumPy copy/view policy;
- plain Python scalar/list export;
- canonical Graph semantic hash unchanged by interop.

## 4. DLPack interoperability

Real CLI inspection on a `float32` tensor of shape `[3, 4]`:

```json
{"device": [1, 0], "dtype": "float32", "ok": true, "shape": [3, 4]}
```

Real raw-capsule round-trip:

```json
{"dtype": "float32", "equal": true, "ok": true, "shape": [3, 4], "shared_memory": true}
```

Additional verified properties:

- NumPy provider import through `numpy.from_dlpack`;
- raw `PyCapsule` bridge through a one-shot provider wrapper;
- second consumption of the same capsule returns typed `DLPackInteropError`;
- DLPack CPU device metadata resolves to `(1, 0)`;
- non-CPU providers are rejected before import in the NumPy reference runtime;
- imported dtype and shape remain subject to NOVA `TensorType` contracts.

## 5. Cross-version model closure smoke

The Round 05 `0.5.0` canonical training examples were executed unchanged on the Round 06 `0.6.0` runtime. Graph storage schema remains `0.1.0`.

### Linear Regression

- initial loss: `8.583333333333334`
- final loss: `3.367186314304342e-05`
- final / initial: `3.922935511810883e-06`
- parameter-state hash: `sha256:cf299d122f6dc6cfb5ffa63c1dfd1d46b316a529d9c0f6c724c2371a15b093f7`

### Small MLP

- initial loss: `2.9549560326371003`
- final loss: `0.0009714653144726783`
- final / initial: `0.00032875795908398356`
- parameter-state hash: `sha256:ae617cbab7e0103854a395bdd4023d2c1c271a8723b1830d8234b683ee540af3`

### Small Attention

- initial loss: `0.3036979145895332`
- final loss: `0.0022048669470125237`
- final / initial: `0.00726006614168734`
- parameter-state hash: `sha256:3b0a8208a46af4b87a6ab29e0a209d52d20b670bb2c2b8f2e71eb1a888816789`

These values match the Round 05 release evidence, demonstrating that the new interop boundary does not change existing execution/training semantics.

## 6. G1 verification matrix

The final G1 matrix is recorded in:

- `docs/G1_VERIFICATION_MATRIX.md`
- `examples/g1_verification.json`

The sealed requirements are:

1. canonical Graph schema;
2. deterministic serialization and semantic identity;
3. tensor and symbolic shape semantics;
4. reference interpreter;
5. NumPy CPU backend;
6. reverse-mode AD and numerical validation;
7. CLI;
8. structured text/formula projection;
9. Python/NumPy interoperability;
10. DLPack interoperability;
11. Linear Regression training closure;
12. MLP training closure;
13. Small Attention training closure;
14. typed failure / no-silent-guess rules.

## 7. Source hygiene

Pre-metadata source scan:

- tracked files: **93**
- UTF-8 decode failures: `0`
- secret-pattern hits: `0`
- Unicode escape-pattern hits: `0`
- hidden control-character hits: `0`
- alternate Markdown math-delimiter hits: `0`
- invalid tracked JSON files: `0`
- `git diff --check`: PASS

## 8. Version boundary

- NOVA Core release version: `0.6.0`
- Graph storage schema version: `0.1.0`
- NumPy reference runtime observed during release: `2.3.5`

Round 06 adds runtime interoperability only. It does not require a breaking canonical Graph storage migration.

## 9. Scope conclusion

G1 is **SEALED** for the declared NOVA Core MVP/reference implementation.

This seal does not claim completion of G2 projectional editing, G3 memory/resource safety, or later roadmap gates. Round 07 proceeds to G2 Projection & Editing.

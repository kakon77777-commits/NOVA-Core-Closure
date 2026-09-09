# NOVA G4 Verification Matrix

## Gate

**G4 — Nova-A AI-Native Program Construction**

Status: **SEALED** in Round 10 / runtime `0.10.0`.

Graph storage schema remains `0.1.0`.

## Core invariant

$$
\boxed{
\text{AI Proposal}
\neq
\text{Accepted Program}
}
$$

An AI-native producer may submit a structured `AIBuildRequest`. Every mutation still lowers to the existing `GraphPatch` and passes sandbox, canonical validation, explicit constraints, structured tests, differentiation obligations, preview/audit, and commit-time revalidation.

## Acceptance matrix

| Requirement | Evidence | Result |
|---|---|---|
| AI adds a layer without source text | `add_relu_request.json` adds `Relu(y)->z` and changes graph output to `z` | PASS |
| AI changes tensor shape/type metadata | `typed_shape_request.json` replaces `op` with `TensorType[f32;(2,4)]` | PASS |
| Constraint-driven repair | `(4,2)` candidate fails required `(2,4)` constraint; corrected `(2,4)` candidate is READY | PASS |
| AI adds/runs a structured test | `relu-negative`: input `x=-2`, observed `z=0` | PASS |
| AI adds a differentiation request | `target=z`, `wrt=x`, explicit VJP seed; derivative graph generated | PASS |
| Effectful build is sandboxed | `Network` effect request rejected with `effects_forbidden` | PASS |
| Stale preview cannot commit | candidate created from old base rejected after another commit | PASS |
| Rollback restores exact record | post-commit rollback restores original record hash | PASS |
| Preview does not mutate working Project | unit and acceptance tests compare base record hash before/after preview | PASS |
| Tampered request/candidate identity rejected | request-hash and preview/commit divergence tests | PASS |

## Recorded hashes

From `examples/g4_verification.json`:

```text
base semantic:
sha256:0f822c5e180f9a2fc19ef9ae993a02d7d29a22a3d2a989b6b6442bbf9f925fba

add-layer candidate:
sha256:0b6dcb4b12943f734042e085d625041a48e9e8b572a4bd9ac653a989d21c6c96

typed-shape candidate:
sha256:1dfbfcb7f438d665f4a8b086e124d37c1d911d2c7768565b99148e024b5144cc

derivative graph:
sha256:6d30754aa6c06d6e1f2e0ce2e8f312fcc4ec1a2876310107e4d4f577dd7dad12
```

## Security boundary

The first Nova-A sandbox is structural. It does not call a remote model, network, filesystem tool, shell, or arbitrary evaluator. Structured validation tests use only the existing interpreter or NumPy backend against explicit JSON-compatible inputs/parameters/expected outputs.

G4 therefore proves the **construction contract**, not general autonomous-agent safety.

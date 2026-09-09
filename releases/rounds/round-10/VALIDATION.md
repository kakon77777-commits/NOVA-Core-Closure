# NOVA Core Closure Round 10 Validation

## Release

- Round: **10**
- Gate: **G4 — Nova-A AI-Native Graph Construction**
- Runtime version: **0.10.0**
- Graph schema version: **0.1.0**
- Feature-freeze commit:   `12bea3ec37a521734caaa47f2cfbedb3e1240f06`
- Delivery mode: **local ZIP only**

## Fresh functional gate

- Full pytest suite: **289 / 289 passed**
- Python compile with warnings promoted to errors: **PASS**
- `git diff --check`: **PASS**
- Public Nova-A package imports: **PASS**

## Real Nova-A CLI smoke

Base semantic hash:

`sha256:0f822c5e180f9a2fc19ef9ae993a02d7d29a22a3d2a989b6b6442bbf9f925fba`

Add-layer request:

- preview status: **ready**
- sandbox: **passed**
- candidate semantic hash:   `sha256:0b6dcb4b12943f734042e085d625041a48e9e8b572a4bd9ac653a989d21c6c96`
- structured validation test: **PASS**, observed `z = 0.0`
- differentiation request: **PASS**
- derivative semantic hash:   `sha256:6d30754aa6c06d6e1f2e0ce2e8f312fcc4ec1a2876310107e4d4f577dd7dad12`
- commit reproduced preview hash: **PASS**

Typed-shape request:

- preview status: **ready**
- candidate semantic hash:   `sha256:1dfbfcb7f438d665f4a8b086e124d37c1d911d2c7768565b99148e024b5144cc`
- required dtype `f32`: **PASS**
- required shape `[2,4]`: **PASS**

Effectful request:

- preview status: **rejected**
- sandbox: **failed as intended**
- violation: `effects_forbidden`
- commit exit status: **failure as intended**
- rejected output file created: **no**

Transaction acceptance:

- stale candidate rejection: **PASS**
- tampered request hash rejection: **PASS**
- preview/commit divergence rejection: **PASS**
- exact rollback to base record hash: **PASS**

## G4 acceptance matrix

All eight G4 acceptance scenarios in `examples/g4_verification.json` are **true**:

1. add layer / change graph output;
2. change shape/type metadata;
3. constraint-driven repair;
4. structured test execution;
5. differentiation request;
6. sandbox rejection;
7. stale candidate rejection;
8. rollback.

## Source hygiene

Tracked files before checksum refresh: **157**.

- UTF-8 decode failures: **0**
- probable secret hits: **0**
- Unicode escape source patterns: **0**
- hidden control characters: **0**
- alternate Markdown math delimiters: **0**
- invalid JSON files: **0**

## Safety statement

Round 10 does **not** include a model-provider call or unrestricted Agent. It verifies the Nova-A construction contract:

1957
\boxed{
\text{AI Build Request}
\rightarrow
\text{Sandbox}
\rightarrow
\text{Candidate GraphPatch}
\rightarrow
\text{Deterministic Validation}
\rightarrow
\text{Explicit Commit}
}
1957

AI provenance or confidence never acts as a correctness proof.

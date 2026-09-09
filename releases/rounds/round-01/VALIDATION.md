# NOVA Core Closure — Round 01 Validation

**Round:** 01 — Canonical Graph Kernel  
**Release date:** 2026-08-19  
**Package version:** 0.1.0  
**Delivery mode:** local downloadable artifact (GitHub upload skipped for this round at user request)

## Implemented boundary

Round 01 implements only the Canonical Graph Kernel:

- `SchemaHeader`, `Project`, `Module`, `Graph`, `Node`, `Edge`;
- structural validation and typed errors;
- deterministic UTF-8 canonical JSON;
- semantic hash separated from provenance and migration history;
- forward-compatible unknown-field preservation;
- JSON decode/encode round-trip;
- `GraphPatch` base-hash conflict detection;
- candidate validation before mutation;
- exact transaction rollback.

Tensor/Shape inference is intentionally deferred to Round 02.

## Fresh verification

- Tests: **24 / 24 passed**
- Python compile: **PASS**
- Package version: **0.1.0**
- Example decode → encode → decode semantic hash: **PASS**
- Example semantic hash: `sha256:11df0ab71ed03dd3fba6c0f3bfaeff35c3bc767ed7dc7b70a71628294e7cea23`
- UTF-8 failures: **0**
- `\\uXXXX` source escape hits: **0**
- Hidden control character hits: **0**
- Alternate math delimiter hits in Markdown: **0**
- Secret-pattern hits: **0**

## Canonicalization regression caught during release reconstruction

The release tests explicitly verify that container insertion order for nodes and edges is non-semantic, while operand order remains semantic.

Therefore:

$$
H_{\mathrm{sem}}(\operatorname{Subtract}(a,b))
\neq
H_{\mathrm{sem}}(\operatorname{Subtract}(b,a)).
$$

This prevents canonicalization from incorrectly sorting ordered operator inputs.

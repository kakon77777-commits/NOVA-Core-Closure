# NOVA CoreNorm v0.7 — Validation Record

**Date:** 2026-09-15  
**Status:** Experimental validation passed  
**Target:** bounded pure-DAG CoreNorm profile

## Executed validation

Standalone harness:

```text
NOVA v0.7 CoreNorm validation harness: PASS
legacy semantic hash left: sha256:9f8b913757229abae100509a3a168d296c7762a594bf3755b747c457110c5730
legacy semantic hash right: sha256:855f84005b2025d4ef143417fda7acce6dd684bb1d483b92d2a10014baf6af4e
CoreNorm hash: sha256:2256c17e9eb32bb0b31b6fcbfadf57a966a0f68d5395fe478c706cce3db3403f
CoreNorm bytes: 1521
identity nodes eliminated (right): 1
commutative reorder count (right): 1
scoped binders normalized: 1
```

Compatibility set:

```text
51 passed
```

The isolated set covers v0.2 through v0.7 experiments packaged in this artifact.

## Primary positive result

Two independently named programs were constructed without shared StructuralIDs or manifests.

The first directly computes `Add(x, y)`.

The second:

- uses different module, graph, node, and value names;
- reverses the inputs to `Add`;
- inserts a trivial `Identity` output projection;
- renames the graph-local shape binder from `B` to `Batch`;
- changes human `reason` text.

Their legacy semantic hashes differ, while their CoreNorm hashes and CoreNorm bytes are identical.

## Negative controls

The validation set confirms that CoreNorm does not collapse:

- `Add` and `Subtract`;
- reversed inputs of `Subtract`;
- non-trivial dead-node graphs;
- `Call` nodes outside the v0.7 profile;
- structurally ambiguous scoped binders;
- explicit edges requiring guessed rewiring through eliminated Identity nodes.

## Comparison certificate

The v0.7 comparison certificate records both source hashes and normalized hashes, plus the normalization-profile hash and first normalized difference for non-equivalent pairs.

Its machine-readable claim boundary is:

```text
bounded CoreNorm profile equivalence; not global semantic equivalence
```

## Full-suite limitation

The complete upstream NOVA regression suite is not reconstructed inside this execution container. The historical pre-experiment `main` result of 215 passing tests remains baseline evidence only and is not reported as a fresh v0.7 full-suite run.

The current v0.7 claim is limited to the packaged standalone harness and isolated compatibility suite.

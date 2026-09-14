# NOVA Cross-Representation Reconstruction v0.8 — Validation Record

**Date:** 2026-09-15  
**Status:** Experimental validation passed  
**Branch:** `experiment/cross-representation-reconstruction-v0.8`

## Standalone result

```text
NOVA v0.8 cross-representation harness: PASS
common CoreNorm: sha256:2a02aae792b64e699caef73dd49efe10933e6642ec9bffbd695dd74605c4546e
CoreNorm bytes: 1367
```

Three independent source identities:

```text
text : sha256:5ae6e78f5e0d8a3c180b2e66bc195f01824500ace875598780cb7ed0e25df345
graph: sha256:b9879ec2886bd16cd6f58050e060d9cdde5c7fb172c284c61fda295ccd238ea3
ai   : sha256:693e1edef9e43d496446a0084a0f2d38da30294a50848ee6bb08bc1beb4749c7
```

Three distinct lowered legacy semantic hashes:

```text
text : sha256:c88fefd02f5bd8162ccd68c29f30f95e61645057807ca0af2e2a9f58d45e9cb0
graph: sha256:b519869c94007943a0ddb8f25fbca13ced91482e5e3d4c22cb6ca72696fee4d1
ai   : sha256:7f53264d8f3dd81ddd9c2b4828bda4a813bf12d21d75136b6e19a9f45e20aa16
```

Yet all three reconstruct the same bounded CoreNorm object.

## Compatibility set

```text
62 passed
```

The isolated set covers the experiment line through v0.8.

## Verified properties

- independent text-like, graph-native, and AI-native lowerings;
- no shared intermediate source representation;
- distinct source hashes;
- distinct lowered legacy semantic hashes;
- identical CoreNorm hashes and bytes;
- text whitespace/comment variation does not change CoreNorm;
- graph node ordering and safe trivial Identity variation do not change CoreNorm;
- `Add -> Subtract` in one representation breaks convergence;
- unresolved AI references are rejected;
- unresolved graph references are rejected;
- text input cannot execute arbitrary host-language syntax;
- certificate explicitly states its bounded claim boundary.

## Full-suite limitation

The upstream historical 215-test main baseline is not freshly rerun in this execution container. v0.8 claims only the packaged standalone harness and isolated compatibility set.

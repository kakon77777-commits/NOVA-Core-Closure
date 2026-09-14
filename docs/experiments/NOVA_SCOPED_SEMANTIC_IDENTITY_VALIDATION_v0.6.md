# NOVA Scoped Semantic Identity v0.6 — Validation Record

**Date:** 2026-09-15  
**Status:** Experimental validation passed  
**Branch:** `experiment/scoped-semantic-identity-v0.6`

## Executed validation

Standalone harness:

```text
NOVA v0.6 validation harness: PASS
legacy semantic hash before: sha256:c9275c411953cc3e135fac613e18de21231058babc2886886626f7abfa0ecb61
legacy semantic hash after alpha rename: sha256:71ed8f7bd8dd7740092bfdcd61c5e93fd2436a83c255586df9559bbb6228ec97
scoped machine hash: sha256:2a8b985515a2b61bca6a27d292b8e0b4fbca5cb4a48951727738a218ac951acd
scoped manifest identity hash: sha256:e244e196ac70b84d8cf4e6cbe69804ed7693341941cf2a60b523f06d486578df
NSM5 bytes: 475
NSM6 bytes: 574
scoped symbols: 2
projection anchors stable: True
```

Compatibility set:

```text
40 passed in 0.26s
```

The 40-test isolated set covers:

- v0.2 Global Semantic Registry / NSM1-NSM2;
- v0.3 Stable Structural Identity;
- v0.4 Symbol Domain Classification / NSM4;
- v0.5 Human Projection purification / NSM5;
- v0.6 Scoped Semantic Identity / NSM6.

## Verified properties

- Graph-scoped affine dimension symbols receive persistent 128-bit `ScopedSymbolID` values.
- Fresh binder migration derives identity from structural occurrence signatures rather than human labels.
- Affine term list indices are excluded from the migration signature, preventing lexical-name sorting from leaking into identity.
- `BatchDimension -> Batch` and `WidthDimension -> Width` change the legacy semantic hash but not NSM6 bytes.
- The scoped-manifest machine identity hash is unchanged by label projection edits.
- The scoped-manifest projection hash changes when labels change.
- The same NSM6 blob can be decoded through a renamed symbol manifest to reconstruct new human labels.
- Tested scoped-symbol spellings are physically absent from NSM6.
- The same spelling used in two different graph scopes receives different identities.
- A semantic coefficient change changes the v0.6 machine hash.
- Structurally symmetric legacy binders with indistinguishable occurrence signatures are rejected instead of being disambiguated by name.
- v0.6 projection anchors remain stable across symbol-label edits.

## Size observation

For the validation graph:

```text
NSM5: 475 bytes
NSM6: 574 bytes
```

The 99-byte increase is expected for this small graph because NSM6 stores explicit 128-bit scope identity plus 128-bit scoped-symbol identity references.

Compression is not the v0.6 objective.

The objective is alpha-renaming invariance and explicit binder identity.

## Full-suite limitation

The complete upstream NOVA regression suite is not reconstructed inside this execution container. The historical pre-experiment `main` result of 215 passing tests remains baseline evidence only and is not reported as a fresh v0.6 full-suite run.

The current v0.6 claim is limited to the packaged standalone harness and 40-test isolated compatibility set.

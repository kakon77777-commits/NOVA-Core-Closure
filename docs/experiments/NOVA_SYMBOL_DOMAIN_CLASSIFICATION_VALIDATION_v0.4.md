# NOVA Symbol Domain Classification v0.4 — Validation Record

**Date:** 2026-09-15  
**Status:** Experimental validation passed  
**Branch:** `experiment/symbol-domain-classification-v0.4`

## Executed validation

Standalone harness:

```text
NOVA v0.4 validation harness: PASS
NSM4 bytes: 791
domain counts: {
  'structural_identity': 18,
  'semantic_atom': 17,
  'scoped_semantic_symbol': 1,
  'semantic_literal': 1,
  'external_contract': 3,
  'human_projection': 3,
  'extension_payload': 2,
  'unclassified': 0
}
human-projection semantic leaks: 1
domain fingerprint: sha256:99b24196a44f447c0d76bf9187bbdc930e823c8df3bb02321db3b5f3bcc5b60a
machine hash: sha256:d58caa91b278fda8c236a6fae808f6e37222452543f95c15e2de86030c12452d
```

Compatibility test set:

```text
23 passed in 0.11s
```

The 23 tests cover v0.2 registry/NSM1-NSM2 behavior, v0.3 structural identity, and v0.4 domain classification/NSM4 behavior.

## Verified properties

- Seven text domains are distinguished.
- Validation program has zero unclassified text occurrences.
- NSM4 round-trips to the same legacy semantic hash.
- Structural labels and registered semantic spellings do not appear in the tested NSM4 payload.
- Scoped symbol, semantic literal, and external-contract text remains but is domain-tagged.
- `Call.attributes.callee` is lowered to graph StructuralID.
- The same NSM4 bytes reproject through renamed manifests, including the embedded Call target.
- A known Core operator with unknown text attributes is rejected in strict mode.
- An unknown extension operator retains its extension-owned text attributes.
- Human-projection text embedded in semantic structures is reported as leakage rather than silently removed.

## Full-suite limitation

The complete upstream NOVA regression suite is not reconstructed inside this container. The historical pre-experiment `main` baseline remains 215 passing tests, but v0.4 does not report that baseline as a fresh full-suite result.

The current v0.4 claim is limited to the executable standalone harness and the 23-test isolated compatibility set packaged with this artifact.

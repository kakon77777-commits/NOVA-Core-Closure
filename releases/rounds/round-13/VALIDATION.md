# NOVA Core Closure Round 13 Validation

**Round:** 13 — G7 ISQL High-Dimensional Semantic Interface Final Seal
**Runtime:** 0.13.0
**Graph schema:** 0.1.0
**Date:** 2026-08-20
**Delivery mode:** local ZIP only; GitHub not modified

## Functional verification

- Full regression suite: **383 tests collected and passed**.
- Python warnings-as-errors compile: PASS.
- `git diff --check`: PASS.
- Versioned `SemanticTensor` codec/hash: PASS.
- Deterministic SemanticBridgeTemplate codec: PASS.
- Multi-candidate intent bridge: PASS.
- G4 validation applied independently to every candidate: PASS.
- Ambiguity and unresolved obligations remain explicit: PASS.
- Human selection produces resolution evidence without mutating the source Project or tensor: PASS.
- Parent-linked semantic refinement: PASS.
- Stale candidate selection rejection: PASS.
- Semantic back-projection / fidelity / traceability: PASS.
- Exact byte-level reconstruction is not claimed: PASS.

## Release activation intent evidence

Source SemanticTensor:

- tensor hash: `sha256:67fd0ae59290c4c46c742f6d56317f6f7a18988a877e06d6714bda1a89915538`
- source confidence: `0.8`
- protocol: `ISQL-Core/0.2`
- registry: `ISQL-NOVA-G7` version `1`
- decoder contract: `semantic-candidate-set/v1`

Candidate set:

- candidate-set hash: `sha256:8a54cab0b4edd7d6d4c132424288cccf208904eaa7114b9cc9a131be035b6c51`
- candidate count: `2`
- set ambiguity: `multiple_template_match`
- auto-selected candidate: none

Candidate `sigmoid`:

- status: READY
- bridge confidence: `0.38`
- graph semantic hash: `sha256:9ebcc5dc135b74765137471587907148415f27a19aef1d16305a3a0da6d4f285`
- unresolved obligation: `confirm_activation_range`

Candidate `tanh`:

- status: READY
- bridge confidence: `0.36000000000000004`
- graph semantic hash: `sha256:4155df426da7dcc4de1a81940df9ef4f1a676d39bfac7711949a6e37db0f820d`
- unresolved obligation: `confirm_activation_range`

Determinism check:

- reversing template input order preserves candidate-set hash: PASS
- reversing template input order preserves candidate ordering/scores: PASS

## Human correction and resolution evidence

Selection:

- selected candidate: `sigmoid`
- selection status: `selected`
- source Project unchanged: PASS
- source SemanticTensor unchanged: PASS

Semantic refinement:

- action: set `bounded_output = required`
- derived tensor hash: `sha256:ff49d2c984362bfa23c7b41ddd37250c887a7d75d508dbaa4dc39548b372f1d9`
- derived provenance points to source tensor hash: PASS
- historical tensor remains unchanged: PASS

Stale candidate test:

- base Project changed after candidate generation
- resolution result: rejected with `ISQLResolutionError`
- stale candidate did not become authoritative: PASS

## Semantic back-projection evidence

Selected candidate `sigmoid` back-projects with:

- traceable: true
- provenance complete: true
- exact reconstruction claimed: false
- unresolved dimension: `bounded_output`
- unresolved bridge obligation count: greater than zero

This is semantic-fidelity evidence, not a byte-identical reconstruction claim.

## CLI verification

Fresh CLI smoke passed for:

```text
nova isql inspect
nova isql bridge
nova isql resolve
nova isql back-project
nova isql correct
```

`isql correct` writes a derived tensor and refuses source overwrite.

## G7 final seal

Verified capabilities:

1. versioned SemanticTensor schema and deterministic hash;
2. protocol / registry / decoder provenance;
3. deterministic semantic bridge templates;
4. same intent can produce multiple different READY candidate graphs;
5. required predicate mismatch excludes a template rather than inventing a match;
6. optional mismatch creates explicit ambiguity/obligation evidence;
7. every candidate crosses the existing G4 deterministic preview boundary;
8. rejected G4 candidate receives zero bridge confidence;
9. bridge confidence is deterministic routing evidence, not correctness probability;
10. no implicit unique-candidate selection;
11. append-only human semantic correction;
12. separate candidate resolution evidence;
13. stale/rejected candidate selection protection;
14. semantic back-projection with fidelity and traceability evidence;
15. exact reconstruction is not silently claimed;
16. source Project and source SemanticTensor identities remain invariant during bridge/review.

**G7 ISQL High-Dimensional Semantic Interface: SEALED.**

## Comparative-metric boundary

Round 13 instruments intent preservation, correction count, structural validity, and traceability. It does **not** claim empirical superiority over a natural-language intermediary. Comparative superiority remains deferred until a dedicated benchmark corpus and experiment exist.

## Source hygiene

Fresh pre-release scan over tracked files:

- tracked files: 215;
- UTF-8 decode failures: 0;
- probable secret hits: 0;
- literal Unicode escape patterns: 0;
- hidden control characters: 0;
- alternate Markdown math delimiters: 0;
- invalid JSON files: 0;
- git working tree before release metadata: clean.

## Deferred intentionally

Not part of Round 13 / G7 seal:

- learned ISQL encoder or decoder models;
- free-form LLM decoding as an authoritative semantic bridge;
- automatic collapse to one candidate;
- automatic Project commit after semantic selection;
- empirical natural-language versus ISQL benchmark claims;
- G8 ProgramHandle / capability-token / real-execution control layer.

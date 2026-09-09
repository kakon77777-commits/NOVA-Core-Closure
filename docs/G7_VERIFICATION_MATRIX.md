# NOVA G7 Verification Matrix — ISQL High-Dimensional Semantic Interface

**Round:** 13  
**Runtime:** 0.13.0  
**Graph schema:** 0.1.0  
**Status:** SEALED candidate pending final release gate

## Scope

G7 connects a versioned ISQL `SemanticTensor` to one or more ordinary NOVA program candidates. The bridge is an extension layer: it does not alter canonical Graph schema or make semantic intent itself executable.

The governing mapping is:

$$
\mathcal B_{\mathrm{Nova}}:
T_{\mathrm{sem}}
\rightarrow
\{(\mathcal N_i,\mathcal O_i)\}_{i=1}^{k}.
$$

Here $\mathcal O_i$ contains unresolved obligations and ambiguity evidence for candidate $i$.

## Verified acceptance scenario

The release fixture encodes one activation intent with:

- `operation_family = activation`;
- `smoothness = preferred`;
- `bounded_output = desired`;
- relation `operation_family prefers smoothness`;
- source confidence `0.8`;
- explicit protocol, registry, decoder, resolution, context, and source provenance.

Two bridge templates are valid for the same intent:

| Candidate | NOVA node | Bridge confidence | Candidate graph semantic hash |
| --- | --- | ---: | --- |
| `sigmoid` | `Sigmoid` | 0.38 | `sha256:9ebcc5dc135b74765137471587907148415f27a19aef1d16305a3a0da6d4f285` |
| `tanh` | `Tanh` | 0.36000000000000004 | `sha256:4155df426da7dcc4de1a81940df9ef4f1a676d39bfac7711949a6e37db0f820d` |

Candidate-set hash:

`sha256:8a54cab0b4edd7d6d4c132424288cccf208904eaa7114b9cc9a131be035b6c51`

Source SemanticTensor hash:

`sha256:67fd0ae59290c4c46c742f6d56317f6f7a18988a877e06d6714bda1a89915538`

## Acceptance matrix

| Requirement | Evidence | Result |
| --- | --- | --- |
| Same intent can produce multiple candidates | `sigmoid` and `tanh` are both READY | PASS |
| Candidate programs are genuinely distinct | two different canonical graph semantic hashes | PASS |
| Ambiguity is visible | candidate set includes `multiple_template_match` | PASS |
| Unresolved obligations remain visible | both candidates include `confirm_activation_range` | PASS |
| Confidence is deterministic | reversed input template order produces the same candidate-set hash and scores | PASS |
| No silent unique answer | `SemanticCandidateSet` has no implicit selected candidate | PASS |
| Human correction can select a candidate | `select-sigmoid-001` creates a `selected` resolution | PASS |
| Semantic refinement is append-only | refined tensor records `parent_tensor_hash` | PASS |
| Stale selection is rejected | changing the base Project invalidates the old candidate set | PASS |
| Semantic back-projection is traceable | tensor → template → request → graph chain is complete | PASS |
| Source identity is invariant | bridge/selection/back-projection do not mutate source Project or SemanticTensor | PASS |
| Exact-recovery overclaim is prevented | `exact_reconstruction_claimed = false` | PASS |

## Human correction evidence

Human selection chooses `sigmoid` without committing or mutating the source intent. A separate refinement changes `bounded_output` from `desired` to `required` and produces the derived tensor hash:

`sha256:ff49d2c984362bfa23c7b41ddd37250c887a7d75d508dbaa4dc39548b372f1d9`

The derived tensor points back to the original tensor through `parent_tensor_hash` and correction metadata.

## Back-projection evidence

The selected `sigmoid` candidate back-projects with:

- traceability: true;
- exact reconstruction claimed: false;
- unresolved dimension: `bounded_output`;
- unresolved bridge obligation: `confirm_activation_range`;
- correction count visible in fidelity evidence.

This distinguishes semantic preservation evidence from byte-identical reconstruction.

## Confidence boundary

`bridge_confidence` is a deterministic routing score composed from source confidence, predicate coverage, template support, unresolved-obligation penalty, and G4 validation status. It is **not** a calibrated probability that the candidate is the user's true intent.

A G4-rejected candidate receives validation factor zero and therefore bridge confidence zero.

## Comparative-metric boundary

G7 exposes instrumentation for semantic fidelity, correction count, structural validity, and traceability. This release does **not** claim that ISQL is empirically superior to a natural-language intermediary. Such a claim requires a separate benchmark corpus and comparative experiment.

## Source basis

The implementation follows the recovered NOVA roadmap requirements for `SemanticTensor`, multi-candidate lowering, ambiguity preservation, provenance, human correction, and semantic back-projection, together with the ISQL Core rule that semantic reconstruction must not be confused with exact byte-level recovery and that protocol/registry/decoder meaning must be versioned.

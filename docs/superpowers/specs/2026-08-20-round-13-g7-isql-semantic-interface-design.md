# Round 13 — G7 ISQL High-Dimensional Semantic Interface Design

## Status
Approved continuation of the NOVA Unified Roadmap G7 gate. This design adds a versioned ISQL bridge above NOVA Core and does not modify canonical Graph storage semantics.

## Goal
Connect versioned high-dimensional intent state to NOVA as an explicit candidate set with ambiguity, confidence, provenance, unresolved obligations, human correction, and semantic back-projection, without pretending that one intent has exactly one correct program.

## Source boundary
The G7 roadmap requires a `SemanticTensor` containing `dimensions[]`, `phase`, `spectrum`, `topology`, `relations[]`, `confidence`, and `provenance`. It requires an intent-to-candidate-graph converter, ambiguity set, confidence, provenance, human correction interface, and semantic back-projection. The bridge may return multiple NOVA candidates plus unresolved obligations.

ISQL's own versioning/reconstruction guidance further requires published meaning not to drift silently and distinguishes exact reconstruction from semantic reconstruction. Therefore bridge confidence is not a correctness probability, and semantic equivalence is never presented as byte identity.

## Authority boundary
- ISQL is authoritative for the upstream semantic-intent artifact and its versioned provenance.
- G7 bridge rules/templates are authoritative only for deterministic candidate generation from that artifact.
- G4/NOVA validation remains authoritative for whether each candidate Project is structurally/type/shape/effect valid.
- G6 planning may inspect a validated candidate after bridge generation but does not change candidate semantic identity.
- Human correction selects or refines candidates but cannot bypass NOVA validation.
- No confidence, model id, or provenance field can turn a rejected candidate into an accepted one.

## SemanticTensor schema
`SemanticTensor` is an immutable, deterministic record with:

- `dimensions: tuple[SemanticDimension, ...]`
- `phase: SemanticField | None`
- `spectrum: tuple[SemanticField, ...]`
- `topology: SemanticTopology`
- `relations: tuple[SemanticRelation, ...]`
- `confidence: float` constrained to `[0,1]`
- `provenance: SemanticProvenance`
- `extensions`

`SemanticDimension` uses a stable name plus a JSON-compatible semantic value and optional importance weight. No universal ontology of dimension names is invented in Round 13; registries define meanings.

`SemanticProvenance` records at minimum:

- protocol version;
- registry id and registry version;
- domain;
- registry hash when known;
- encoder version;
- decoder contract;
- model id when applicable;
- resolution;
- context policy;
- source id / parent semantic-tensor hash when applicable.

Canonical serialization and semantic-tensor hashing are deterministic. Mapping insertion order never changes the hash.

## Bridge templates instead of free-form generation
Round 13 uses deterministic `SemanticBridgeTemplate` objects. A template contains:

- stable template id/version;
- target module/graph;
- an ordinary G4 `AIBuildRequest` whose patch describes the candidate graph change;
- required semantic dimension predicates;
- optional relation predicates;
- explicit unresolved obligations;
- template support weight and rationale.

This design deliberately reuses G4 instead of creating an ISQL-only mutation path.

A template may match exactly, partially, or not at all. Partial matches remain candidates only when the missing information is represented as explicit ambiguity/obligations rather than silently assumed.

## Candidate generation
The bridge function is conceptually:

$$
\mathcal B_{\mathrm{Nova}}:
T_{\mathrm{sem}}
\times
\mathcal P
\times
\mathcal R_B
\rightarrow
\{C_1,\ldots,C_k\},
$$

where `P` is the base Project and `R_B` is a versioned bridge-template registry.

Each `SemanticGraphCandidate` contains:

- candidate id;
- template id/version;
- original semantic-tensor hash;
- G4 request hash;
- G4 preview status/evidence;
- candidate Project semantic/record hash when valid;
- bridge confidence;
- matched dimensions/relations;
- unmatched dimensions/relations;
- ambiguity items;
- unresolved obligations;
- structural/semantic diff summary;
- semantic fidelity metrics.

Candidates are sorted deterministically by bridge confidence, validation status, unresolved-obligation count, then candidate id. Sorting is presentation only; it does not assert a uniquely correct program.

## Bridge confidence
`bridge_confidence` is a deterministic routing score, not a calibrated probability of program correctness.

Round 13 computes it from explicit evidence:

- source `SemanticTensor.confidence`;
- weighted required-dimension coverage;
- required-relation coverage;
- template support weight;
- penalty for unresolved obligations;
- zeroing/rejection when deterministic NOVA validation fails.

The score is constrained to `[0,1]` and the component breakdown is included in the candidate record.

## Ambiguity and obligations
`SemanticAmbiguity` is a typed record such as:

- `missing_dimension`;
- `dimension_conflict`;
- `multiple_template_match`;
- `missing_relation`;
- `underspecified_shape`;
- `underspecified_effect`;
- `decoder_context_gap`.

`SemanticObligation` records what evidence or human correction would resolve the ambiguity. An unresolved item is not treated as false and is not silently defaulted away.

## Human correction
Human correction is an append-only versioned record, not mutation of historical intent.

`SemanticCorrection` records:

- correction id;
- actor id;
- source semantic-tensor hash;
- action: `select_candidate`, `reject_candidate`, `set_dimension`, `add_relation`, or `resolve_obligation`;
- candidate id when relevant;
- corrected value/evidence;
- rationale;
- parent correction id when chained.

Applying semantic refinements creates a derived `SemanticTensor` whose provenance references the original tensor hash and correction chain. Selecting a candidate creates a `SemanticResolution` but does not rewrite the source tensor.

A selected candidate must already be G4/NOVA-valid. Rejected or stale candidates cannot be selected.

## Semantic back-projection
`back_project_candidate(...)` returns a deterministic `SemanticBackProjection` containing:

- source tensor hash;
- selected candidate id and graph hash;
- preserved dimensions/relations;
- unresolved/omitted dimensions/relations;
- candidate diff summary;
- bridge confidence and fidelity metrics;
- correction-chain references;
- provenance chain.

Back-projection is explicitly a semantic reconstruction view, not byte-exact reconstruction of the original tensor.

## Fidelity and traceability metrics
Round 13 instruments, but does not fabricate empirical superiority over natural-language coding. Metrics include:

- weighted dimension preservation ratio;
- relation preservation ratio;
- unresolved obligation count;
- candidate structural validation status;
- correction count;
- provenance-chain completeness;
- traceability flag linking tensor → template → request → candidate graph.

The G7 seal may assert that these metrics are deterministic and auditable. It must not claim that ISQL universally outperforms natural language without a separate benchmark corpus.

## Candidate-set acceptance scenario
The release example uses one ambiguous activation intent applied to a base graph with an `Identity` placeholder. The same `SemanticTensor` is intentionally compatible with multiple deterministic templates, such as `Sigmoid` and `Tanh`, while a preference dimension changes ranking rather than deleting alternatives.

Acceptance must show:

1. one SemanticTensor produces at least two validated NOVA candidates;
2. candidate graph hashes differ;
3. differences and unresolved obligations are visible;
4. bridge confidence components are visible and deterministic;
5. no candidate is auto-declared uniquely correct;
6. human correction can select one valid candidate;
7. semantic refinement creates a derived tensor with parent provenance rather than mutating the original;
8. stale/rejected candidate selection is refused;
9. back-projection reports preserved and unresolved semantic content;
10. semantic-tensor and base-project hashes remain unchanged by pure candidate generation.

## API / CLI surface
Python API:

- `encode_semantic_tensor` / `decode_semantic_tensor`
- `semantic_tensor_hash`
- `bridge_semantic_tensor`
- `apply_semantic_correction`
- `resolve_semantic_candidate`
- `back_project_semantics`

CLI:

```text
nova isql inspect TENSOR.json
nova isql bridge PROJECT TENSOR.json TEMPLATES.json
nova isql correct TENSOR.json CORRECTION.json --output DERIVED.json
nova isql resolve PROJECT TENSOR.json TEMPLATES.json --candidate ID
nova isql back-project PROJECT TENSOR.json TEMPLATES.json --candidate ID
```

CLI commands are diagnostic/transformational only and never overwrite inputs implicitly.

## Versioning
Runtime version advances to `0.13.0`. Canonical graph schema remains `0.1.0` because G7 records are versioned external bridge artifacts. ISQL protocol/registry/template versions are stored independently from the NOVA runtime version.

## Non-goals
- no natural-language encoder benchmark claim;
- no learned semantic decoder/model call;
- no universal ontology of semantic dimensions;
- no claim that bridge confidence is calibrated correctness probability;
- no forced single-candidate collapse;
- no G8 ProgramHandle/capability execution;
- no canonical Graph schema migration;
- no replacement of G4 validation or G6 execution planning.

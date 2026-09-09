# Round 13 G7 ISQL High-Dimensional Semantic Interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic versioned ISQL→NOVA bridge that preserves ambiguity, provenance, unresolved obligations, human correction, and semantic back-projection while reusing existing G4 validation.

**Architecture:** Add a new `isql.py` domain/bridge module above NOVA Core. `SemanticTensor` and bridge-template records are external versioned artifacts; candidate generation delegates each candidate patch to existing G4 preview/validation, and correction/back-projection operate on immutable evidence records rather than mutating canonical graph or historical intent.

**Tech Stack:** Python 3.13, dataclasses, standard-library JSON/hashlib, existing NOVA Project/Graph/G4 AIBuildRequest/preview/diff/projection infrastructure, pytest.

**Spec:** `docs/superpowers/specs/2026-08-20-round-13-g7-isql-semantic-interface-design.md`

## Global Constraints

- Runtime version becomes `0.13.0`.
- Canonical Graph schema remains `0.1.0`.
- `SemanticTensor` must expose dimensions, phase, spectrum, topology, relations, confidence, and provenance.
- Published semantic meaning must be versioned; protocol/registry/decoder/template versions must not drift silently.
- Bridge confidence is deterministic routing evidence, never correctness probability.
- One SemanticTensor may produce multiple candidates; no implicit unique-candidate collapse.
- Every graph candidate must go through existing G4/NOVA deterministic validation.
- Human correction is append-only evidence; source SemanticTensor and base Project remain immutable.
- Back-projection is semantic reconstruction, never byte-identity claim.
- No learned model call, no G8 ProgramHandle, no Graph schema migration.

---

### Task 1: SemanticTensor domain, versioning, codec, and hash

**Files:**
- Create: `src/nova_core/isql.py`
- Modify: `src/nova_core/errors.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_isql_tensor.py`

**Interfaces:**
- Produces: `SemanticDimension`, `SemanticField`, `SemanticTopology`, `SemanticRelation`, `SemanticProvenance`, `SemanticTensor`.
- Produces: `encode_semantic_tensor(tensor) -> str`, `decode_semantic_tensor(value) -> SemanticTensor`, `semantic_tensor_hash(tensor) -> str`.
- Produces typed `ISQLError`, `ISQLCodecError`.

- [ ] **Step 1: Write failing domain/codec tests**

```python
def test_semantic_tensor_roundtrip_and_hash_ignore_mapping_order():
    tensor = sample_tensor()
    encoded = encode_semantic_tensor(tensor)
    decoded = decode_semantic_tensor(encoded)
    assert decoded == tensor
    assert semantic_tensor_hash(decoded) == semantic_tensor_hash(tensor)


def test_confidence_must_be_bounded():
    with pytest.raises(ValueError):
        SemanticTensor(..., confidence=1.1, ...)
```

Also test required provenance fields, deterministic relation/dimension ordering, unknown extension preservation, and non-JSON semantic values rejected.

- [ ] **Step 2: Run RED**

Run: `PYTHONPATH=src pytest -q tests/test_isql_tensor.py`
Expected: import/attribute failures because G7 types do not exist.

- [ ] **Step 3: Implement immutable records and canonical codec**

Use frozen dataclasses, mapping freezing, explicit `to_record`/decode helpers, canonical `json.dumps(..., sort_keys=True, separators=(",", ":"))`, and SHA-256 over UTF-8 bytes. Do not attach these fields to Graph records.

- [ ] **Step 4: Run GREEN plus canonical regression**

Run: `PYTHONPATH=src pytest -q tests/test_isql_tensor.py tests/test_canonical.py tests/test_codec.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/nova_core/isql.py src/nova_core/errors.py src/nova_core/__init__.py tests/test_isql_tensor.py
git commit -m "feat: add versioned ISQL SemanticTensor domain"
```

---

### Task 2: Deterministic multi-candidate ISQL→NOVA bridge

**Files:**
- Modify: `src/nova_core/isql.py`
- Test: `tests/test_isql_bridge.py`
- Test support: existing `src/nova_core/ai_build.py`, `src/nova_core/diff.py`

**Interfaces:**
- Produces: `DimensionPredicate`, `RelationPredicate`, `SemanticBridgeTemplate`, `SemanticAmbiguity`, `SemanticObligation`, `BridgeConfidenceBreakdown`, `SemanticGraphCandidate`, `SemanticCandidateSet`.
- Produces: `bridge_semantic_tensor(project, tensor, templates) -> SemanticCandidateSet`.

- [ ] **Step 1: Write failing bridge tests**

```python
def test_same_tensor_can_produce_two_validated_candidates():
    result = bridge_semantic_tensor(base_project(), activation_tensor(), (sigmoid_template(), tanh_template()))
    assert len(result.candidates) == 2
    assert all(c.validation_status == "ready" for c in result.candidates)
    assert len({c.candidate_semantic_hash for c in result.candidates}) == 2


def test_partial_match_surfaces_ambiguity_and_obligation():
    result = bridge_semantic_tensor(...)
    assert result.candidates[0].ambiguities
    assert result.candidates[0].obligations
```

Also test deterministic ordering/hash, original tensor/project hash invariance, validation failure zeroes acceptance and cannot rank above READY candidate, confidence breakdown components, relation matching, multiple-template-match ambiguity, and confidence never exceeds `[0,1]`.

- [ ] **Step 2: Run RED**

Run: `PYTHONPATH=src pytest -q tests/test_isql_bridge.py`
Expected: missing bridge types/functions.

- [ ] **Step 3: Implement bridge using G4 preview**

For each template:
1. evaluate dimension/relation predicates;
2. create explicit ambiguity/obligation records for partial information;
3. call existing `preview_ai_build(project, template.request)`;
4. derive graph hashes/diff/evidence from the G4 candidate;
5. compute deterministic bridge confidence from source confidence, weighted coverage, template support, obligation penalty, and validation state;
6. sort presentation deterministically without deleting alternatives.

Do not bypass `preview_ai_build` and do not mutate the Project.

- [ ] **Step 4: Run GREEN plus G4 regression**

Run: `PYTHONPATH=src pytest -q tests/test_isql_bridge.py tests/test_ai_build_preview.py tests/test_ai_build_transaction.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/nova_core/isql.py tests/test_isql_bridge.py
git commit -m "feat: add ambiguity-preserving ISQL candidate bridge"
```

---

### Task 3: Human correction, candidate resolution, back-projection, fidelity

**Files:**
- Modify: `src/nova_core/isql.py`
- Test: `tests/test_isql_correction.py`
- Test: `tests/test_isql_backprojection.py`

**Interfaces:**
- Produces: `SemanticCorrection`, `SemanticResolution`, `SemanticFidelity`, `SemanticBackProjection`.
- Produces: `apply_semantic_correction(tensor, correction) -> SemanticTensor` for semantic refinements.
- Produces: `resolve_semantic_candidate(project, candidate_set, correction) -> SemanticResolution` for selection/rejection.
- Produces: `back_project_semantics(tensor, candidate_set, candidate_id, corrections=()) -> SemanticBackProjection`.

- [ ] **Step 1: Write failing correction/back-projection tests**

```python
def test_set_dimension_creates_derived_tensor_with_parent_hash():
    original = activation_tensor()
    derived = apply_semantic_correction(original, SemanticCorrection(... action="set_dimension" ...))
    assert semantic_tensor_hash(derived) != semantic_tensor_hash(original)
    assert derived.provenance.parent_tensor_hash == semantic_tensor_hash(original)


def test_select_candidate_does_not_mutate_tensor_or_project():
    resolution = resolve_semantic_candidate(base, candidates, select_correction)
    assert resolution.selected_candidate_id == "sigmoid"
    assert semantic_tensor_hash(original) == before_tensor_hash
    assert semantic_hash(base) == before_project_hash
```

Also test rejected/stale/nonexistent candidate cannot be selected, correction chain deterministic, back-projection preserved/unresolved fields, fidelity ratios bounded, correction count, and traceability tensor→template→request→graph.

- [ ] **Step 2: Run RED**

Run: `PYTHONPATH=src pytest -q tests/test_isql_correction.py tests/test_isql_backprojection.py`
Expected: missing correction/back-projection interfaces.

- [ ] **Step 3: Implement immutable correction/resolution/back-projection**

Semantic refinements create a new tensor with parent provenance; selection creates a resolution record only. Candidate resolution requires READY G4 status and matching source tensor/base graph hashes. Back-projection reports semantic preservation and omissions without claiming exact reconstruction.

- [ ] **Step 4: Run GREEN plus projection/diff regression**

Run: `PYTHONPATH=src pytest -q tests/test_isql_correction.py tests/test_isql_backprojection.py tests/test_projection.py tests/test_diff.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/nova_core/isql.py tests/test_isql_correction.py tests/test_isql_backprojection.py
git commit -m "feat: add ISQL correction and semantic back projection"
```

---

### Task 4: Public API/CLI, examples, metrics, 0.13.0, G7 final seal

**Files:**
- Modify: `src/nova_core/api.py`
- Modify: `src/nova_core/cli.py`
- Modify: `src/nova_core/__init__.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Create: `tests/test_isql_api_cli.py`
- Create: `tests/test_round13_package.py`
- Create: `examples/isql/activation_intent.json`
- Create: `examples/isql/activation_templates.json`
- Create: `examples/isql/select_sigmoid_correction.json`
- Create: `examples/isql/activation_base_project.json`
- Create: `docs/G7_VERIFICATION_MATRIX.md`
- Create: `docs/rounds/ROUND_13_G7_ISQL_FINAL_SEAL.md`
- Create: `releases/rounds/round-13/G7_SEAL.json`
- Regenerate: `VALIDATION.md`, `CHECKSUMS.sha256`

**Interfaces:**
- API wrappers for inspect/bridge/correct/resolve/back-project.
- CLI commands `nova isql inspect|bridge|correct|resolve|back-project`.

- [ ] **Step 1: Write failing API/CLI/package tests**

Test:
- runtime/version contract `0.13.0`, graph schema `0.1.0`;
- inspect returns tensor hash and version/provenance summary;
- bridge returns at least two candidate records and never silently selects one;
- correct writes only requested output file;
- resolve names one candidate and preserves source inputs;
- back-project returns fidelity/traceability evidence;
- G7 seal/examples exist and machine-readable seal marks all acceptance cases true.

- [ ] **Step 2: Run RED**

Run: `PYTHONPATH=src pytest -q tests/test_isql_api_cli.py tests/test_round13_package.py`
Expected: missing wrappers/commands/version/artifacts.

- [ ] **Step 3: Implement API/CLI and release examples**

CLI files are deterministic JSON. `correct` requires `--output` and refuses overwrite of source path. `resolve` is diagnostic/selection evidence and does not modify the Project. Build the activation example with one tensor that produces multiple validated candidate graphs.

- [ ] **Step 4: Run G7 acceptance and full regression**

Required acceptance evidence:
1. same tensor → two or more READY candidates;
2. distinct candidate graph hashes;
3. visible ambiguity and unresolved obligations;
4. deterministic confidence breakdown;
5. no auto unique selection;
6. explicit human selection succeeds only for READY candidate;
7. semantic refinement creates parent-linked derived tensor;
8. rejected/stale selection fails;
9. back-projection reports preserved/unresolved content;
10. source tensor/base Project hashes unchanged by bridge.

Run full suite: `PYTHONPATH=src pytest -q`.

- [ ] **Step 5: Release hygiene and immutable local ZIP**

Run warnings-as-errors compile, `git diff --check`, UTF-8/secret/unicode-escape/control-character/alternate-math-delimiter/JSON scans, regenerate manifest excluding itself, commit release metadata, rerun the full fresh gate from exact release commit, package only `git ls-files`, test ZIP CRC, extract and verify every manifest hash, then compute ZIP SHA-256.

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "release: seal round13 G7 ISQL semantic interface"
```

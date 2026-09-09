# Round 13 — G7 ISQL High-Dimensional Semantic Interface Final Seal

## 1. Goal

Round 13 connects high-dimensional intent state to verified NOVA program candidates without forcing an ambiguous intent into one supposedly authoritative graph.

The bridge is:

$$
T_{\mathrm{sem}}
\rightarrow
\{\mathcal N_1,\ldots,\mathcal N_k\}
+
\mathcal A
+
\mathcal O,
$$

where $\mathcal A$ is ambiguity evidence and $\mathcal O$ is unresolved obligations.

## 2. SemanticTensor

The versioned bridge artifact now includes:

- dimensions;
- phase;
- spectrum;
- topology;
- relations;
- confidence;
- protocol / registry / decoder provenance;
- extensions.

It has deterministic canonical JSON and SHA-256 identity, independent of mapping insertion order.

## 3. Multi-candidate bridge

A `SemanticBridgeTemplate` contains semantic predicates and an ordinary G4 `AIBuildRequest`. Required predicate mismatch excludes the template. Optional mismatch does not silently assume a value; it creates `SemanticAmbiguity` and `SemanticObligation` evidence.

Every surviving candidate still crosses the existing G4 deterministic boundary:

$$
T_{\mathrm{sem}}
\rightarrow
\text{Template}
\rightarrow
\text{AIBuildRequest}
\rightarrow
\text{G4 Preview}
\rightarrow
\mathcal N_i.
$$

ISQL therefore does not bypass NOVA type, shape, sandbox, GraphPatch, or transaction semantics.

## 4. Bridge confidence

Confidence is a deterministic routing score rather than a correctness probability:

$$
C_B
=
C_{\mathrm{source}}
\cdot C_{\mathrm{dimension}}
\cdot C_{\mathrm{relation}}
\cdot C_{\mathrm{template}}
\cdot C_{\mathrm{obligation}}
\cdot C_{\mathrm{validation}}.
$$

A rejected NOVA candidate has $C_{\mathrm{validation}}=0$.

## 5. Append-only correction

`SemanticCorrection` never rewrites historical intent in place.

Semantic refinements produce:

$$
T'
=
\operatorname{Correct}(T,c),
$$

with:

$$
\operatorname{parent}(T')=H(T).
$$

Candidate selection/rejection instead produces a separate `SemanticResolution` evidence object.

## 6. Back-projection

`SemanticBackProjection` reports:

- preserved dimensions;
- unresolved dimensions;
- preserved relations;
- unresolved relations;
- unresolved obligation count;
- correction count;
- provenance completeness;
- traceability;
- candidate graph hash;
- request hash;
- bridge confidence;
- graph diff summary.

It explicitly records:

`exact_reconstruction_claimed = false`.

## 7. Public surface

Python API now provides loaders and bridge/correction/resolution/back-projection helpers.

CLI:

```text
nova isql inspect TENSOR
nova isql bridge PROJECT TENSOR TEMPLATES
nova isql correct TENSOR CORRECTION --output DERIVED
nova isql resolve PROJECT TENSOR TEMPLATES --candidate ID
nova isql back-project PROJECT TENSOR TEMPLATES --candidate ID
```

`isql correct` refuses to overwrite the source tensor.

## 8. Acceptance fixture

The release activation fixture produces two READY candidates, `sigmoid` and `tanh`, with distinct graph hashes and visible ambiguity/obligations. Human selection chooses `sigmoid`; an independent semantic refinement creates a parent-linked derived tensor; stale resolution is rejected; back-projection remains traceable while retaining an unresolved `bounded_output` dimension.

See `docs/G7_VERIFICATION_MATRIX.md` and `releases/rounds/round-13/G7_SEAL.json` for exact hashes and evidence.

## 9. Versioning

Runtime version: `0.13.0`.

Graph storage schema remains `0.1.0`. ISQL artifacts use independent bridge schema/version fields and do not migrate canonical Graph storage.

## 10. Deferred intentionally

Round 13 does not implement:

- learned semantic encoder/decoder models;
- free-form LLM intent decoding as an authoritative path;
- silent unique-candidate collapse;
- automatic project commit after human selection;
- empirical natural-language-vs-ISQL benchmark claims;
- G8 ProgramHandle/capability execution.

## 11. Seal

G7 is sealed when the final repository verification gate passes and the ZIP manifest verifies after extraction.

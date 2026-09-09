# NOVA Core Closure Round 07 — Validation Record

**Release:** Round 07 — Projection Integrity & Structured Editing  
**Runtime version:** 0.7.0  
**Graph storage schema:** 0.1.0  
**Delivery:** local ZIP only; no GitHub publication

## Functional verification

Fresh full regression:

```text
193 passed in 0.45s
```

Round 07 verifies:

- concise structured-text projection;
- mathematical projection where supported;
- machine-readable graph projection;
- deterministic lossless editable structured-text projection;
- projection semantic-hash invariance;
- structured and semantic graph diff;
- provenance-only structural change classification;
- node and edge replacement diff;
- graph interface/constraint/attribute diff;
- Candidate GraphPatch generation from edited projection;
- candidate validation before commit;
- semantic-hash and record-hash conflict protection;
- preview/commit hash equality;
- rollback to exact base record;
- typed projection-edit failure;
- audit/error projection;
- Python API and CLI projection/editing workflows.

## Real CLI smoke

A real editing demo was executed using `examples/editing/base_project.json` and `examples/editing/edited_graph.json`.

```text
CLI_SMOKE=PASS
BEFORE=sha256:59135573b38f30a34325168cf0f33bb1a200ce94dd8c5930e95dd5a088251799
AFTER=sha256:43ca436f9aeea5e9fff558e60399247166c62bc191d4ffc8e2c6bb67219338fb
```

Commands exercised:

```text
nova project --view graph
nova project --view editable
nova edit-preview
nova edit-commit
nova diff
```

The commit command wrote a new canonical project file; the input file was not overwritten.

## Identity and edit boundary

Projection alone leaves semantic identity unchanged.

An edit is never committed by modifying a projection object directly. The path is:

$$
\text{Projection Edit}
\rightarrow
\text{Parsed Candidate Graph}
\rightarrow
\text{GraphDiff}
\rightarrow
\text{Candidate GraphPatch}
\rightarrow
\text{Validation}
\rightarrow
\text{Explicit Commit}
$$

Formula projection remains read-only in Round 07. The editable structured-text projection is the deterministic lossless path.

## Build and hygiene

- warnings-as-errors Python compile: PASS
- git diff check: PASS
- tracked files before release metadata refresh: 108
- UTF-8 failures: 0
- secret-pattern hits: 0
- Unicode-escape pattern hits: 0
- hidden control characters: 0
- alternate Markdown math delimiter hits: 0
- invalid tracked JSON files: 0

## G2 status

Round 07 implements the machine-verifiable G2 core but does not claim the full G2 seal. Remaining G2 work is intentionally scoped to Round 08:

- interactive node-graph edit primitives;
- bounded local formula editing components;
- Notebook prototype;
- final three-view workflow verification and G2 seal.

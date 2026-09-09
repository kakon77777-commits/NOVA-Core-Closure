# Round 07 — Projection Integrity & Structured Editing

Round 07 begins G2 by making projections observable, comparable, and safely editable without changing NOVA's authority model.

## Implemented

- projection snapshots carrying one semantic identity across concise text, formula, machine graph, and editable structured text;
- deterministic lossless editable Graph JSON projection;
- structured/semantic graph diff with field-level node and edge changes;
- explicit separation of provenance-only structural changes from semantic changes;
- GraphPatch replacement and graph-interface update support;
- optional base record hash concurrency protection;
- projection edit interpretation as Candidate GraphPatch;
- candidate validation before commit;
- preview/commit/rollback consistency;
- typed projection-edit errors;
- audit and error projections;
- CLI graph/editable projection, diff, edit-preview, and edit-commit commands.

## Boundary

Round 07 does not claim a full projectional IDE. Formula projection remains read-only and may be unsupported for control flow. The lossless editable projection is the structured-text fallback allowed by the original roadmap.

## Next

Round 08 continues G2 with node-graph interaction primitives, local formula components, Notebook prototype, and G2 final verification/seal.

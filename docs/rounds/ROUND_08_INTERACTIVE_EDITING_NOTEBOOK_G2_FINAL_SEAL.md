# Round 08 — Interactive Editing, Notebook Prototype, and G2 Final Seal

Round 08 completes the non-IDE core of G2 Projection & Editing.

Implemented:

- typed node-graph edit primitives that build validated Candidate GraphPatches;
- bounded local formula editing using safe AST parsing without evaluation;
- record-hash concurrency protection inherited from Round 07;
- graph-cell Notebook prototype with explicit external and prior-cell bindings;
- deterministic per-cell output evidence and graph semantic hashes;
- API/CLI preview and commit flows;
- G2 final verification matrix.

The canonical NOVA graph remains the sole source of truth. Node views, formulas, editable structured text, notebook cells, and audit views are projections or controlled edit frontends.

## G2 seal

G2 is considered sealed in NOVA Core `0.8.0` when the release gate confirms multi-projection identity invariance, lossless structured-text round-trip, structural/semantic diff separation, node edit preview/commit/rollback, bounded formula editing, structured error/audit views, graph-cell notebook execution, and full regression compatibility.

## Deferred beyond G2

A full graphical IDE, arbitrary multi-node formula synthesis, collaborative editing, and rich notebook text/media cells remain outside this seal.

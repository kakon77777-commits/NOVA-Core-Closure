# G2 Final Verification Matrix

**Release:** NOVA Core 0.8.0  
**Gate:** G2 Projection & Editing  
**Status:** **SEALED**

| Requirement | Implementation | Fresh Round 08 evidence |
|---|---|---|
| Mathematical projection | `project_formula` | projection regression suite passes |
| Structured text projection | deterministic editable Graph JSON | full record/hash round-trip passes |
| Node graph view | `project_graph_view` | machine view shares canonical semantic hash |
| Semantic hash invariance | `project_snapshot` | snapshot hash equals source graph hash |
| Structural diff | `GraphDiff` | node/edge/graph field deltas pass |
| Semantic diff | semantic classification flags | provenance-only changes remain non-semantic |
| Error view | `project_error_view` | typed `NovaError` payload preserved |
| Audit view | `project_audit_view` | patch + before/candidate semantic/record hashes |
| Node graph editing | typed immutable edit operations | preview base `5913...1799` to candidate `c67f...fbf2` |
| Formula editing | bounded safe AST frontend | preview candidate `b0de...8879`; no `eval`/`exec` |
| Concurrency | semantic + record hash guards | stale record conflicts rejected |
| Explicit commit | `GraphTransaction` | preview/commit equality and rollback tests pass |
| Notebook prototype | canonical graph-cell runner | two-cell result `z=[0.0,2.5]` |
| Notebook evidence | per-cell graph/output hashes | final digest `774d...0689` |
| Source immutability | candidate-only edits and notebook run | base project file SHA unchanged in CLI smoke |
| Regression | complete suite | **226 tests collected and passed** |

## Seal statement

Round 08 completes the non-IDE core promised by G2. A full graphical IDE, rich text/media notebook cells, collaborative editing, and arbitrary multi-node formula synthesis remain outside this seal and are not required for G2 correctness.

The next gate is **G3 — verifiable memory/resource planning**.

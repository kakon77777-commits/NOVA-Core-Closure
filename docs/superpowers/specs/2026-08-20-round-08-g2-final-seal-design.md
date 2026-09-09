# Round 08 — Interactive Editing, Notebook Prototype, and G2 Final Seal Design

**Status:** approved continuation of the previously declared Round 08 scope  
**Date:** 2026-08-20  
**Target release:** NOVA Core `0.8.0`  
**Storage schema:** remains `0.1.0`

## 1. Goal

Round 08 closes the remaining G2 surface without building a full IDE. It adds three bounded human-facing interaction paths that all converge on the existing canonical graph and GraphPatch transaction model:

1. interactive node-graph edit primitives;
2. bounded local formula editing;
3. a graph-cell Notebook prototype.

The release ends with a G2 verification matrix and final seal.

## 2. Authority invariant

The authoritative object remains the canonical graph:

$$
G^* \rightarrow \{V_{text},V_{formula},V_{graph},V_{notebook},V_{audit}\}.
$$

No new projection becomes a second source of truth. Every editable projection must lower to a candidate graph and then to a validated `GraphPatch` before commit.

## 3. Interactive node-graph editing

### 3.1 Operation model

Round 08 introduces typed immutable operations:

- `AddNodeEdit(node)`
- `ReplaceNodeEdit(node_id, node)`
- `RemoveNodeEdit(node_id)`
- `SetNodeInputsEdit(node_id, inputs)`
- `SetNodeAttributesEdit(node_id, attributes)`
- `AddEdgeEdit(edge)`
- `RemoveEdgeEdit(edge_key)`
- `SetGraphOutputsEdit(outputs)`

Operations apply in order to an immutable candidate `Graph`. The original graph is never mutated.

### 3.2 Candidate flow

$$
G^* \xrightarrow{E_1,\ldots,E_n} G_c
\rightarrow \operatorname{Diff}(G^*,G_c)
\rightarrow \Delta G
\rightarrow \operatorname{Validate}
\rightarrow \operatorname{Preview}.
$$

The final candidate reuses the Round 07 `ProjectionEditCandidate`, including semantic hash, record hash, audit view, commit equality, and rollback.

### 3.3 Concurrency

Both semantic and record hashes remain part of the patch baseline. A provenance-only concurrent change must still invalidate a stale interactive edit preview.

## 4. Bounded local formula editing

Formula editing is intentionally **not** a complete NOVA text parser.

### 4.1 Editable unit

One formula edit targets exactly one existing node with exactly one output:

```text
Y = X + b
Y = X - b
Y = X * b
Y = X / b
Y = X @ W
Y = -X
Y = relu(X)
Y = sigmoid(X)
Y = tanh(X)
Y = softmax(X)
Y = identity(X)
```

The right-hand side must contain exactly one supported operator layer. Nested formulas such as `relu(X + b)` are rejected in Round 08 because they would create multiple nodes.

### 4.2 Safety rules

- The assignment LHS must equal the target node's sole output symbol.
- Operand names are symbolic references, not evaluated Python.
- Python `ast` may be used only as a parser; no `eval` or `exec` is allowed.
- Unsupported literals, nested calls, attribute access, indexing, comprehensions, or arbitrary function names are rejected as `FormulaEditError`.
- Existing node metadata is preserved except for `kind`, ordered `inputs`, and operation-specific attributes.
- If a formula changes into a shape family that cannot safely preserve existing shape/type annotations, the edit is rejected rather than silently clearing or guessing metadata.

### 4.3 Shape families

For typed nodes, Round 08 permits operator replacement only within compatible local families:

- unary shape-preserving: `Identity`, `Negate`, `Relu`, `Sigmoid`, `Tanh`, `Softmax`;
- binary elementwise: `Add`, `Subtract`, `Multiply`, `Divide`;
- matrix multiplication: `MatMul` only with `MatMul` unless the node carries no static tensor/shape annotation.

This is a bounded edit rule, not a claim that these are the only mathematically valid rewrites.

## 5. Notebook prototype

### 5.1 Cell ontology

A Notebook cell is a reference to a canonical NOVA subgraph, not a text snippet:

```text
NotebookCell {
  id
  module_id
  graph_id
  bindings
}
```

Each graph input is explicitly bound to either:

- `ExternalInput(name)`; or
- `CellOutput(cell_id, output_name)` from an earlier cell.

### 5.2 Execution

Cells execute deterministically in declared order. Forward references and cycles are rejected. Each cell run records:

- cell ID;
- module/graph ID;
- graph semantic hash;
- dependency cell IDs;
- backend;
- output value digest;
- output dtype/shape summary.

Notebook execution does not mutate the canonical project.

### 5.3 Prototype boundary

Round 08 Notebook does not include:

- rich text cells;
- arbitrary code cells;
- hidden mutable kernel state;
- out-of-order execution;
- reactive scheduling;
- collaborative editing;
- GUI widgets.

It is a minimal proof that Notebook identity can be subgraph-first instead of text-cell-first.

## 6. API and CLI

Public API additions:

- `preview_node_graph_edit(...)`
- `preview_formula_edit(...)`
- `decode_node_graph_edits(...)`
- `Notebook`, `NotebookCell`, `ExternalInput`, `CellOutput`
- `decode_notebook(...)`
- `run_notebook(...)`

CLI additions:

```text
nova node-edit-preview PROGRAM --ops edits.json
nova node-edit-commit PROGRAM --ops edits.json --output new.json
nova formula-edit-preview PROGRAM --node NODE --formula 'Y = X - b'
nova formula-edit-commit PROGRAM --node NODE --formula 'Y = X - b' --output new.json
nova notebook-run PROGRAM --notebook notebook.json --inputs inputs.json --backend numpy
```

Commit commands refuse to overwrite the input project.

## 7. G2 final seal criteria

G2 is sealed only if fresh verification demonstrates:

1. text/formula/graph/editable snapshots preserve semantic identity;
2. editable structured text round-trips losslessly;
3. structural and semantic diff remain distinct;
4. node-graph edit preview/commit/rollback works;
5. bounded formula edit preview/commit works and rejects unsupported syntax;
6. error and audit views remain structured;
7. Notebook graph cells execute with explicit dependencies and stable result digests;
8. no projection/edit/notebook action mutates the canonical source project implicitly;
9. all Round 01–07 regressions remain green.

## 8. Non-goals

Round 08 does not implement:

- a visual drag-and-drop IDE;
- complete formula parsing;
- arbitrary multi-node formula synthesis;
- general three-way merge UI;
- collaborative cursors or remote state;
- G3 memory/resource planning;
- G4 autonomous AI graph construction.

## 9. Release conclusion

If the criteria pass, the project may record:

```text
G2 Projection & Editing: SEALED
```

The next gate is G3: verifiable memory/resource planning.

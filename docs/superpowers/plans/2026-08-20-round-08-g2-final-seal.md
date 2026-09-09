# Round 08 G2 Final Seal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete interactive node editing, bounded local formula editing, a graph-cell Notebook prototype, and the G2 final seal.

**Architecture:** Keep the Round 07 canonical graph, diff, `ProjectionEditCandidate`, `GraphPatch`, and transaction semantics unchanged. New edit frontends construct immutable candidate graphs and reuse the existing candidate/validation/commit path. Notebook execution references canonical graphs and records immutable execution evidence without becoming a source of truth.

**Tech Stack:** Python 3.13, frozen dataclasses, Python `ast` parsing without evaluation, NumPy reference backend, pytest.

**Spec:** `docs/superpowers/specs/2026-08-20-round-08-g2-final-seal-design.md`

## Global Constraints

- TDD: every behavior begins with a failing test.
- `nova_core_version` becomes `0.8.0`; storage `schema_version` remains `0.1.0`.
- No `eval` or `exec` in formula editing.
- No implicit mutation of canonical `Project` or `Graph` objects.
- Every committed edit must pass through `GraphPatch` validation and record-hash concurrency protection.
- Notebook cells are graph references, not source-text cells.
- GitHub is not used; final delivery is a local ZIP.

---

### Task 1: Interactive node-graph edit primitives

**Files:**
- Create: `src/nova_core/interactive.py`
- Modify: `src/nova_core/editing.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_node_graph_editing.py`

**Interfaces:**
- Consumes: `Project`, `Graph`, `Node`, `Edge`, Round 07 candidate/patch/diff infrastructure.
- Produces: typed edit dataclasses, `decode_node_graph_edits()`, and `preview_node_graph_edit()`.

- [ ] **Step 1: Write failing tests** covering add/replace/remove node, ordered input rewiring, node attribute edit, add/remove edge, graph-output edit, validation failure, deterministic operation order, and record-hash conflict compatibility.
- [ ] **Step 2: Run the focused tests** with `PYTHONPATH=src python -m pytest tests/test_node_graph_editing.py -q` and verify they fail because the new API does not exist.
- [ ] **Step 3: Implement immutable edit operations** that transform a candidate graph in order and then reuse the Round 07 candidate-building path.
- [ ] **Step 4: Add JSON edit decoding** using `decode_node()` and `decode_edge()`; reject malformed or unknown operation kinds with `ProjectionEditError`.
- [ ] **Step 5: Run focused and inherited projection tests** and keep them green.
- [ ] **Step 6: Commit** with `feat: add interactive node graph editing`.

### Task 2: Bounded local formula editing

**Files:**
- Create: `src/nova_core/formula_editing.py`
- Modify: `src/nova_core/errors.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_formula_editing.py`

**Interfaces:**
- Consumes: Round 08 node replacement candidate path.
- Produces: `FormulaEditError`, `parse_local_formula()`, and `preview_formula_edit()`.

- [ ] **Step 1: Write failing tests** for binary arithmetic, matmul, unary functions, LHS mismatch, nested expression rejection, arbitrary-call rejection, attribute/index/literal rejection, typed shape-family guard, preview hash stability, and commit equality.
- [ ] **Step 2: Run focused tests** and verify RED on the missing formula-edit API.
- [ ] **Step 3: Implement a safe AST parser** that accepts only one assignment and one supported expression layer; never evaluate the AST.
- [ ] **Step 4: Replace only the targeted node's operation semantics** while preserving node identity/output and compatible metadata.
- [ ] **Step 5: Run formula, editing, shape, and projection tests**.
- [ ] **Step 6: Commit** with `feat: add bounded local formula editing`.

### Task 3: Graph-cell Notebook prototype

**Files:**
- Create: `src/nova_core/notebook.py`
- Modify: `src/nova_core/errors.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_notebook.py`
- Create: `examples/notebook_chain.json`
- Create: `examples/notebook_chain_inputs.json`

**Interfaces:**
- Consumes: canonical project/graph lookup, Interpreter/NumPy backend execution, semantic hashing.
- Produces: notebook data model, JSON decoder, deterministic cell runner, result/value digests.

- [ ] **Step 1: Write failing tests** for external bindings, prior-cell output bindings, forward-reference rejection, missing binding rejection, deterministic cell result hashes, source graph hash invariance, and Interpreter/NumPy equivalence.
- [ ] **Step 2: Run focused tests** and verify RED.
- [ ] **Step 3: Implement frozen notebook structures** and strict decoding for `external` and `cell_output` binding kinds.
- [ ] **Step 4: Implement ordered execution** with explicit dependency resolution and immutable result records.
- [ ] **Step 5: Add a two-cell example** and verify it runs on NumPy.
- [ ] **Step 6: Commit** with `feat: add graph cell notebook prototype`.

### Task 4: API/CLI integration and G2 final seal

**Files:**
- Modify: `src/nova_core/api.py`
- Modify: `src/nova_core/cli.py`
- Modify: `src/nova_core/model.py`
- Modify: `src/nova_core/__init__.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Create: `tests/test_round08_api_cli.py`
- Create: `tests/test_round08_package.py`
- Create: `docs/rounds/ROUND_08_INTERACTIVE_EDITING_NOTEBOOK_G2_FINAL_SEAL.md`
- Create: `docs/G2_VERIFICATION_MATRIX.md`
- Create: `examples/g2_verification.json`

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: public API/CLI, version `0.8.0`, G2 seal artifacts.

- [ ] **Step 1: Write failing API/CLI/package tests** for node edit preview/commit, formula edit preview/commit, notebook run, overwrite refusal, version/header defaults, docs, and machine-readable G2 seal.
- [ ] **Step 2: Run focused tests** and verify RED only on missing integration/release surfaces.
- [ ] **Step 3: Implement API/CLI adapters** without introducing new canonical semantics.
- [ ] **Step 4: Update package version/header defaults to `0.8.0`** while preserving schema `0.1.0`.
- [ ] **Step 5: Write G2 final verification matrix and release docs** with explicit evidence fields.
- [ ] **Step 6: Run the complete regression suite**.
- [ ] **Step 7: Run release hygiene**: warnings-as-errors compile, CLI smokes, UTF-8/secret/escape/control/math/JSON scans, checksum manifest, git clean.
- [ ] **Step 8: Create the local ZIP**, run CRC and extracted-manifest verification, and record ZIP SHA-256.
- [ ] **Step 9: Commit release metadata** with `release: seal G2 projection and editing`.

# Round 07 Projection Integrity & Structured Editing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the verifiable G2 projection/editing core while keeping the canonical graph as the only authority.

**Architecture:** Extend the existing projection and GraphPatch layers rather than creating a second parser-owned program model. A deterministic editable graph projection round-trips through the existing graph decoder; edits are diffed into a candidate GraphPatch and fully validated before explicit commit.

**Tech Stack:** Python 3.11+, dataclasses, JSON, existing NOVA graph/codec/patch/validation layers, pytest.

**Spec:** `docs/superpowers/specs/2026-08-20-round-07-projection-editing-design.md`

## Global Constraints
- Canonical program authority remains `Graph` / `Project`.
- Projection calls must not change semantic hash.
- Invalid or ambiguous editing must fail explicitly.
- No direct in-place edit of input project files.
- No new dependency beyond the existing package requirements.
- TDD: every production behavior starts with a failing test.

---

### Task 1: Projection Snapshot and Lossless Editable Projection

**Files:**
- Create: `src/nova_core/projection_model.py`
- Modify: `src/nova_core/projection.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_projection_snapshot.py`

**Interfaces:**
- Produces: `ProjectionSnapshot`, `project_graph_view`, `project_editable_text`, `parse_editable_text`, `project_snapshot`.

- [ ] Write tests proving four projections preserve semantic hash and editable text round-trips.
- [ ] Run tests and observe missing-interface failure.
- [ ] Implement the minimum deterministic projection model.
- [ ] Run projection tests and inherited projection tests.
- [ ] Commit the green checkpoint.

### Task 2: Structural and Semantic Graph Diff

**Files:**
- Create: `src/nova_core/diff.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_graph_diff.py`

**Interfaces:**
- Produces: `FieldChange`, `NodeDelta`, `GraphDiff`, `diff_graphs`.

- [ ] Write tests for additions, removals, node field modifications, interface/constraint/attribute changes, deterministic ordering, and semantic-change classification.
- [ ] Run tests and observe missing-interface failure.
- [ ] Implement deterministic diff records and `to_dict()`.
- [ ] Run diff tests plus canonical tests.
- [ ] Commit the green checkpoint.

### Task 3: Projection Edit to Candidate GraphPatch

**Files:**
- Modify: `src/nova_core/patch.py`
- Create: `src/nova_core/editing.py`
- Modify: `src/nova_core/errors.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_projection_editing.py`

**Interfaces:**
- GraphPatch adds `replaced_nodes`, `changed_inputs`, `changed_outputs`, `changed_attributes`.
- Produces: `ProjectionEditCandidate`, `interpret_structured_text_edit`, `commit_projection_edit`.

- [ ] Write tests for replacement/interface edits, preview without mutation, invalid edit rollback, base-hash conflict, preview/commit hash equality, and unchanged edits.
- [ ] Run tests and observe expected failure.
- [ ] Extend GraphPatch atomically and implement edit interpretation through `parse_editable_text` + `diff_graphs`.
- [ ] Revalidate the entire candidate project before returning preview.
- [ ] Run editing and inherited patch tests.
- [ ] Commit the green checkpoint.

### Task 4: Audit/Error Views, API/CLI, Package Contract and Release

**Files:**
- Create: `src/nova_core/audit.py`
- Modify: `src/nova_core/api.py`
- Modify: `src/nova_core/cli.py`
- Modify: `src/nova_core/__init__.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Create: `docs/rounds/ROUND_07_PROJECTION_INTEGRITY_STRUCTURED_EDITING.md`
- Create: `examples/editing/`
- Test: `tests/test_projection_editing_api_cli.py`
- Test: `tests/test_round07_package.py`

**Interfaces:**
- Produces: `project_error_view`, `project_audit_view`, API preview/commit/diff helpers, CLI projection/diff/edit commands.

- [ ] Write failing API/CLI/package tests.
- [ ] Implement audit/error views and API helpers.
- [ ] Extend CLI and add deterministic editing examples.
- [ ] Raise package version to `0.7.0`; storage schema remains `0.1.0`.
- [ ] Run full regression and real CLI smoke.
- [ ] Run UTF-8/secret/escape/control/math/JSON hygiene, compile warnings-as-errors, checksum manifest and git-clean gates.
- [ ] Create and verify the local Round 07 ZIP.

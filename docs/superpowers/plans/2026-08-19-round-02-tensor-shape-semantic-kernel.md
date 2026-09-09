# NOVA Round 02 Tensor / Shape Semantic Kernel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Round 01 canonical graph kernel with explicit tensor types, symbolic affine dimensions, shape obligations, deterministic shape solving, and core tensor shape rules without adding execution or AD.

**Architecture:** Add independent immutable semantic objects under `nova_core.shape` and `nova_core.types`, then a deterministic `ShapeSolver` and pure shape-rule functions under `nova_core.ops`. Existing `Node` values may embed these semantic objects through an explicit `to_record()` protocol; codec support recognizes tagged NOVA semantic records while preserving unknown extension fields.

**Tech Stack:** Python 3.11+, stdlib dataclasses, pytest. No solver framework dependency and no tensor runtime dependency in Round 02.

**Spec:** `README.md` Round 02 scope and recovered NOVA Core Baseline v3.0 Phase B requirements.

## Global Constraints

- Do not add interpreter, backend execution, or reverse-mode AD in Round 02.
- Unknown shape relations produce explicit `ShapeObligation`; they are never silently accepted as compatible.
- The decidable solver subset is intentionally bounded: normalized affine integer expressions plus direct/single-symbol equality bindings.
- Container insertion order may be normalized, but operand order remains semantic.
- Generated Markdown uses only `$...$` and `$$...$$` math delimiters.
- All source files are UTF-8 and must not use unicode-escape round trips.

---

### Task 1: Dimension, Shape, and Tensor Types

**Files:**
- Create: `src/nova_core/shape.py`
- Create: `src/nova_core/types.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_shape_types.py`

**Interfaces:**
- Produces: `DimExpr`, `Shape`, `TensorType`, `as_dim()` and deterministic `to_record()` representations.

- [ ] **Step 1: Write failing tests** for constants, symbols, affine canonicalization, scalar rank-0 tensors, shape rank, invalid negative concrete dimensions, and deterministic records.
- [ ] **Step 2: Run `pytest tests/test_shape_types.py -q` and confirm RED** because the modules do not exist.
- [ ] **Step 3: Implement minimal immutable semantic objects.**
- [ ] **Step 4: Run `pytest tests/test_shape_types.py tests/test_model.py -q` and confirm GREEN.**
- [ ] **Step 5: Commit.**

### Task 2: Shape Solver and Obligations

**Files:**
- Modify: `src/nova_core/shape.py`
- Modify: `src/nova_core/errors.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_shape_solver.py`

**Interfaces:**
- Produces: `ProofStatus`, `ShapeConstraint`, `ShapeObligation`, `ShapeSolver`, `ShapeError`.

- [ ] **Step 1: Write failing tests** for proven equality, disproven concrete equality, single-symbol binding, contradictory bindings, and unresolved affine equality producing an obligation.
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Implement bounded deterministic solver.**
- [ ] **Step 4: Run solver plus inherited tests and confirm GREEN.**
- [ ] **Step 5: Commit.**

### Task 3: Core Shape Rules

**Files:**
- Create: `src/nova_core/ops.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_shape_ops.py`

**Interfaces:**
- Produces: `ShapeInference`, `broadcast_shapes`, `elementwise_shape`, `matmul_shape`, `contract_shape`, `reshape_shape`, `transpose_shape`.

- [ ] **Step 1: Write failing tests** for concrete/symbolic broadcasting, explicit unresolved broadcast obligations, matmul contraction, batch matmul, contraction, reshape element-count validation, and transpose permutation validation.
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Implement pure shape rules.**
- [ ] **Step 4: Run new and inherited tests and confirm GREEN.**
- [ ] **Step 5: Commit.**

### Task 4: Canonical/Codec Integration and Round 02 Release

**Files:**
- Modify: `src/nova_core/model.py`
- Modify: `src/nova_core/canonical.py`
- Modify: `src/nova_core/codec.py`
- Modify: `src/nova_core/__init__.py`
- Modify: `README.md`
- Modify: `pyproject.toml`
- Create: `examples/tensor_shape_graph.json`
- Create: `docs/rounds/ROUND_02_TENSOR_SHAPE_SEMANTIC_KERNEL.md`
- Create: `tests/test_tensor_codec.py`
- Modify: `tests/test_package.py`

**Interfaces:**
- Node `value_type` can contain a `TensorType` and survive encode/decode without changing semantic hash.
- Tagged semantic records remain forward-compatible through `extensions`.

- [ ] **Step 1: Write failing integration/package tests.**
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Implement semantic-object canonicalization/codec support and release-facing docs.**
- [ ] **Step 4: Run complete pytest suite, compileall, example round-trip, source hygiene scans.**
- [ ] **Step 5: Generate `VALIDATION.md`, `CHECKSUMS.sha256`, and local Round 02 ZIP; verify ZIP CRC and extracted checksums.**

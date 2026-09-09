# NOVA Round 03 Executable Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute validated NOVA canonical graphs through a reference interpreter and NumPy CPU backend, with projections, CLI, and Python interoperability.

**Architecture:** Keep canonical graph identity unchanged. Add execution as a derived runtime layer: runtime binding + deterministic dependency execution + typed runtime errors + trace. Treat the interpreter as semantic reference and NumPy as a differential-tested backend.

**Tech Stack:** Python 3.11+, dataclasses, NumPy, pytest, stdlib argparse/json.

**Spec:** `docs/superpowers/specs/2026-08-19-round-03-executable-closure-design.md`

## Global Constraints

- Do not mutate canonical program graphs during execution.
- Do not add reverse-mode AD in Round 03.
- Do not parse text as authoritative source.
- Unsupported operations fail explicitly.
- Loops are finite and explicit.
- Runtime checks may discharge obligations but may not silently accept unknown shapes.
- Use UTF-8 and only `$...$` / `$$...$$` math delimiters in project Markdown.

---

### Task 1: Runtime Values and Structured Runtime Errors

**Files:**
- Create: `src/nova_core/runtime.py`
- Modify: `src/nova_core/errors.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_runtime_values.py`

**Interfaces:**
- Produces `ExecutionEnvironment`, `ExecutionTrace`, `ExecutionResult`, runtime value validation helpers, and structured runtime error subclasses.

- [ ] Write failing tests for input binding, missing inputs, tensor runtime shape validation, and immutable execution metadata.
- [ ] Run the new tests and confirm RED because runtime interfaces do not exist.
- [ ] Implement the minimal runtime value layer and typed errors.
- [ ] Run new tests and inherited tests until GREEN.

### Task 2: Reference Interpreter

**Files:**
- Create: `src/nova_core/interpreter.py`
- Test: `tests/test_interpreter.py`
- Test: `tests/test_control_flow.py`

**Interfaces:**
- Produces `Interpreter.run_graph(graph, inputs, parameters=None)`.
- Supports the Round 03 node-kind subset from the spec.

- [ ] Write failing tests for arithmetic, `Y=XW+b`, missing dependencies, unsupported node kind, `If`, and `BoundedLoop`.
- [ ] Confirm RED.
- [ ] Implement deterministic dependency execution and the supported operations.
- [ ] Verify graph semantic hash is unchanged before/after execution.
- [ ] Run new and inherited tests until GREEN.

### Task 3: NumPy CPU Backend and Differential Validation

**Files:**
- Create: `src/nova_core/backends/__init__.py`
- Create: `src/nova_core/backends/numpy_backend.py`
- Test: `tests/test_numpy_backend.py`

**Interfaces:**
- Produces `NumPyBackend.run_graph(...)` with the same externally observable result contract as the interpreter.

- [ ] Write failing differential tests for arithmetic, matmul+bias, reductions, activations, reshape, transpose, and softmax.
- [ ] Confirm RED.
- [ ] Implement NumPy backend operations without changing semantic rules.
- [ ] Compare backend outputs to interpreter outputs under numeric tolerance.
- [ ] Run all tests until GREEN.

### Task 4: Structured Text and Formula Projections

**Files:**
- Create: `src/nova_core/projection.py`
- Test: `tests/test_projection.py`

**Interfaces:**
- Produces `project_text(graph)` and `project_formula(graph)`.

- [ ] Write failing deterministic projection tests, including formula projection for $Y=XW+b$ and explicit unsupported formula cases.
- [ ] Confirm RED.
- [ ] Implement deterministic projection from canonical structure.
- [ ] Verify projections do not mutate semantic hash.
- [ ] Run all tests until GREEN.

### Task 5: Python API and CLI

**Files:**
- Create: `src/nova_core/api.py`
- Create: `src/nova_core/cli.py`
- Modify: `pyproject.toml`
- Test: `tests/test_api.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces `load_project`, `run_graph`, `run_project`, and CLI commands `check`, `run`, `hash`, `project`.

- [ ] Write failing API/CLI tests.
- [ ] Confirm RED.
- [ ] Implement APIs and CLI with structured JSON errors.
- [ ] Run API/CLI tests and then the entire suite until GREEN.

### Task 6: Round 03 Examples, Package Contract, and Release

**Files:**
- Create: `examples/executable_linear.json`
- Create: `examples/executable_inputs.json`
- Create: `docs/rounds/ROUND_03_EXECUTABLE_CLOSURE.md`
- Modify: `README.md`
- Modify: `src/nova_core/__init__.py`
- Modify: `pyproject.toml`
- Test: `tests/test_package.py`

**Interfaces:**
- Package version becomes `0.3.0` while graph schema version remains compatible unless a storage-breaking change is introduced.

- [ ] Write failing package contract tests for version, docs, examples, and CLI entry point.
- [ ] Confirm RED.
- [ ] Update package metadata/docs/examples.
- [ ] Run full suite.
- [ ] Run compile and hygiene scans.
- [ ] Generate `VALIDATION.md`, `CHECKSUMS.sha256`, and Round 03 ZIP.
- [ ] Verify ZIP CRC and extracted manifest.

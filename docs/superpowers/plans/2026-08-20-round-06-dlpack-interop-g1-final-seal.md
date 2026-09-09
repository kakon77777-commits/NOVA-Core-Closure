# Round 06 DLPack / Interop & G1 Final Seal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit Python/NumPy/DLPack runtime tensor exchange and close the G1 verification matrix.

**Architecture:** Interop is isolated in `nova_core.interop`; canonical graph and tensor types remain unchanged. Runtime shape validation reuses `validate_runtime_value`; DLPack import/export uses the Python `__dlpack__` protocol and NumPy reference runtime. G1 sealing is evidence generation, not a new semantic layer.

**Tech Stack:** Python 3.11+, NumPy >=1.26, pytest, stdlib JSON/hashlib/pathlib.

**Spec:** `docs/superpowers/specs/2026-08-20-round-06-dlpack-interop-g1-final-seal-design.md`

## Global Constraints

- No GitHub writes; local ZIP delivery only.
- TDD for production behavior.
- UTF-8 source.
- Markdown math uses `$...$` and `$$...$$` only.
- No silent dtype/shape/device coercion.
- No PyTorch/JAX/TensorFlow dependency.
- Runtime interop must not mutate canonical graph identity.
- Package version `0.6.0`; schema version remains `0.1.0`.

---

### Task 1: Python / NumPy Interop Contract

**Files:**
- Create: `src/nova_core/interop.py`
- Modify: `src/nova_core/errors.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_interop.py`

**Interfaces:**
- Produces: `to_numpy`, `from_numpy`, `to_python`, `InteropError`, `DTypeInteropError`.
- Reuses: `validate_runtime_value(value, expected)`.

- [ ] Write failing tests for scalar/list/ndarray conversion, safe dtype policy, shape validation, copy/view policy, canonical hash invariance.
- [ ] Run targeted tests and confirm RED because `nova_core.interop` does not exist.
- [ ] Implement the minimal explicit conversion contract.
- [ ] Run targeted tests and inherited runtime/type tests until GREEN.
- [ ] Commit the checkpoint.

### Task 2: DLPack Bridge

**Files:**
- Modify: `src/nova_core/interop.py`
- Test: `tests/test_dlpack_interop.py`

**Interfaces:**
- Produces: `to_dlpack`, `from_dlpack`, `dlpack_device`, internal one-shot raw-capsule provider.

- [ ] Write failing tests for NumPy DLPack zero-copy round-trip, one-shot capsule semantics, provider import, shape validation, unsupported object/device errors.
- [ ] Run targeted tests and confirm RED.
- [ ] Implement the DLPack protocol bridge using NumPy's native protocol.
- [ ] Verify shared memory where applicable and explicit typed failure elsewhere.
- [ ] Commit the checkpoint.

### Task 3: Public API and CLI Diagnostics

**Files:**
- Modify: `src/nova_core/api.py`
- Modify: `src/nova_core/cli.py`
- Test: `tests/test_interop_api.py`
- Test: `tests/test_interop_cli.py`

**Interfaces:**
- Public API wrappers expose interop helpers without duplicating semantics.
- CLI adds `nova interop inspect` and `nova interop roundtrip` for `.npy` files.

- [ ] Write failing API/CLI tests.
- [ ] Confirm RED.
- [ ] Add wrappers/subcommands and JSON diagnostics including dtype, shape, device, shared-memory result.
- [ ] Run targeted tests and complete regression suite.
- [ ] Commit the checkpoint.

### Task 4: G1 Verification Matrix and Release

**Files:**
- Create: `docs/rounds/ROUND_06_DLPACK_INTEROP_G1_FINAL_SEAL.md`
- Create: `docs/G1_VERIFICATION_MATRIX.md`
- Create: `examples/g1_verification.json`
- Modify: `README.md`
- Modify: `pyproject.toml`
- Modify: `src/nova_core/__init__.py`
- Modify: `VALIDATION.md`
- Modify: `CHECKSUMS.sha256`
- Test: `tests/test_round06_package.py`

**Interfaces:**
- Version `0.6.0`; storage schema `0.1.0`.
- G1 matrix records reproducible commands and expected evidence.

- [ ] Write failing package/seal tests requiring version, docs, matrix, and executable evidence.
- [ ] Confirm RED.
- [ ] Add Round 06 docs/matrix and update package metadata.
- [ ] Run full tests, warnings-as-errors compile, interop smoke, three-model training smoke, hygiene scans.
- [ ] Generate fresh manifest from tracked release files.
- [ ] Re-run final gate from exact release commit.
- [ ] Build ZIP from tracked files only; verify CRC and extracted manifest.

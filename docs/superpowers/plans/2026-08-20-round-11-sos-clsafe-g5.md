# Round 11 SOS / Cl-safe G5 Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the G5 SOS / Cl-safe integration as a deterministic operator descriptor/closure library with C→G→S RVP, typed failures, BrokenOperator isolation, safe lowering into ordinary NOVA graphs, and a local release seal.

**Architecture:** SOS remains an extension layer over the existing NOVA Core. Immutable descriptors and closures are validated by a pure Cl-safe RVP, and only safe supported unary closures may lower into existing NOVA node kinds; the ordinary NOVA validator and runtime remain authoritative for executable graph legality.

**Tech Stack:** Python 3.13, dataclasses, existing NOVA canonical/model/runtime APIs, pytest, standard-library JSON/hash tooling.

**Spec:** `docs/superpowers/specs/2026-08-20-round-11-sos-clsafe-g5-design.md`

## Global Constraints

- Runtime target: `0.11.0`.
- Graph storage schema stays `0.1.0`.
- RVP core check order is exactly C → G → S.
- Default $K_S=256$.
- Default composition depth limit is 32 (Round 11 implementation decision).
- No SOS path bypasses existing NOVA validation.
- Broken operators never silently continue a composition chain.
- No G6/G7/G8 functionality in this round.

---

### Task 1: Operator descriptor domain and deterministic basic library

**Files:**
- Create: `src/nova_core/sos.py`
- Modify: `src/nova_core/errors.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_sos_descriptors.py`

**Interfaces:**
- Produces: `SemanticSlot`, `CompositionSlot`, `ProjectionSlot`, `OperatorDescriptor`, `OperatorRegistry`, `descriptor_hash()`, `basic_operator_registry()`.

- [ ] Write failing tests for descriptor validation, deterministic hash/codec-equivalent records, finite semantic transition integrity, registry lookup, and the six basic unary NOVA operator descriptors.
- [ ] Run `pytest -q tests/test_sos_descriptors.py` and verify RED due to missing SOS API.
- [ ] Implement the minimal immutable descriptor domain and basic registry.
- [ ] Run `pytest -q tests/test_sos_descriptors.py` and verify GREEN.
- [ ] Commit `feat: add SOS operator descriptor domain`.

### Task 2: Cl-safe C→G→S RVP and typed failures

**Files:**
- Modify: `src/nova_core/sos.py`
- Modify: `src/nova_core/errors.py`
- Test: `tests/test_clsafe_rvp.py`

**Interfaces:**
- Produces: `CompositionContext`, `RVPCheck`, `CompositionReport`, `validate_composition()`, typed composition errors.

- [ ] Write failing tests proving exact check order C→G→S, legal Comp intersection, empty-intersection `CompCollapseError`, G connectivity/orientation/scale/canonical-kind rejection, bounded finite-map fixed point, toggle-map `SemDivergenceError`, and effect-policy conflict.
- [ ] Run `pytest -q tests/test_clsafe_rvp.py` and verify RED.
- [ ] Implement the minimal ordered validator with $K_S=256$ default and typed evidence.
- [ ] Run `pytest -q tests/test_clsafe_rvp.py` and verify GREEN.
- [ ] Commit `feat: add Cl-safe runtime validation protocol`.

### Task 3: Safe closure, BrokenOperator isolation, depth limit, and NOVA lowering

**Files:**
- Modify: `src/nova_core/sos.py`
- Create: `src/nova_core/sos_lowering.py`
- Test: `tests/test_sos_composition.py`
- Test: `tests/test_sos_lowering.py`

**Interfaces:**
- Produces: `OperatorClosure`, `BrokenOperator`, `compose()`, `compose_chain()`, `lower_closure_to_project()`.

- [ ] Write failing tests for strict typed failures, diagnostic BrokenOperator return, immediate downstream BrokenOperator propagation stop, max-depth rejection, deterministic closure hash, and safe two/three-member closure creation.
- [ ] Run `pytest -q tests/test_sos_composition.py` and verify RED.
- [ ] Implement closure composition and BrokenOperator isolation.
- [ ] Write failing lowering tests for a safe `ReLU → Tanh` closure, normal NOVA validation, Interpreter/NumPy equivalence, and unsupported multi-input lowering rejection.
- [ ] Run `pytest -q tests/test_sos_lowering.py` and verify RED.
- [ ] Implement minimal lowering through ordinary NOVA node kinds.
- [ ] Run both SOS composition/lowering test files and verify GREEN.
- [ ] Commit `feat: add safe operator closures and NOVA lowering`.

### Task 4: API/CLI, acceptance artifacts, version 0.11.0, and G5 final seal

**Files:**
- Modify: `src/nova_core/api.py`
- Modify: `src/nova_core/cli.py`
- Modify: `src/nova_core/__init__.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Create: `tests/test_sos_api_cli.py`
- Create: `tests/test_round11_package.py`
- Create: `examples/sos/legal_chain.json`
- Create: `examples/sos/comp_collapse.json`
- Create: `examples/sos/sem_divergence.json`
- Create: `examples/sos/projection_incoherence.json`
- Create: `examples/sos/effect_conflict.json`
- Create: `docs/G5_VERIFICATION_MATRIX.md`
- Create: `docs/rounds/ROUND_11_G5_SOS_CLSAFE_FINAL_SEAL.md`
- Create: `releases/rounds/round-11/G5_SEAL.json`
- Modify: `VALIDATION.md`
- Modify: `CHECKSUMS.sha256`

**Interfaces:**
- Produces: stable `nova sos` CLI family, Python API wrappers, machine-readable G5 seal and local ZIP release.

- [ ] Write failing API/CLI/package tests for list/validate/compose/lower, runtime version `0.11.0`, schema continuity, required acceptance artifacts, and G5 seal fields.
- [ ] Run the new tests and verify RED.
- [ ] Implement API/CLI and release-facing metadata without changing RVP semantics.
- [ ] Run the full regression suite and repair only real regressions or stale historical version invariants.
- [ ] Execute release smoke cases for legal composition, Comp collapse, Sem divergence, projection/GCI failure, effect conflict, BrokenOperator propagation, depth limit, and lowered Interpreter/NumPy equivalence.
- [ ] Run warnings-as-errors compile, source hygiene scans, checksum manifest verification, and `git diff --check`.
- [ ] Commit release metadata.
- [ ] Re-run the full final gate from the exact release commit.
- [ ] Package tracked files into `NOVA_Core_Closure_Round_11_G5_SOS_Clsafe_Integration_2026-08-20.zip`, run ZIP CRC, and verify extracted manifest.

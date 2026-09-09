# Round 09 G3 Verifiable Memory & Resource Planning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement deterministic resource analysis, verifiable memory-plan candidates, safe buffer reuse/device transfers, conservative fallback, and seal G3.

**Architecture:** Add a compiler/runtime resource layer beside the canonical Graph. Resource analysis recomputes schedule, ownership, lifetime, size, and device facts. Planners produce immutable MemoryPlan candidates; a separate verifier recomputes the facts and validates aliasing/transfers/accounting before selection.

**Tech Stack:** Python 3.11+, dataclasses, enum, hashlib/json, existing NOVA Graph/TensorType/semantic hash, pytest.

**Spec:** `docs/superpowers/specs/2026-08-20-round-09-g3-resource-planning-design.md`

## Global Constraints

- Runtime version: `0.9.0`.
- Graph schema version remains `0.1.0`.
- No production code without a failing test first.
- No AI/model output may be accepted as a safety proof.
- No buffer reuse when size is unknown or lifetimes overlap.
- No source Graph mutation.
- Unknown facts become explicit obligations or conservative fallback.
- Local ZIP delivery only; do not push GitHub.

---

### Task 1: Resource Facts, Ownership, Lifetime, and Static Size

**Files:**
- Create: `src/nova_core/resources.py`
- Modify: `src/nova_core/errors.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_resource_analysis.py`

**Interfaces:**
- Consumes: `Graph`, `Node`, `TensorType`, `semantic_hash`.
- Produces: `OwnershipState`, `ResourceObligation`, `ValueLifetime`, `ResourceAnalysis`, `analyze_resources`, `dtype_nbytes`.

- [ ] **Step 1: Write failing tests for deterministic schedule, ownership, lifetime, concrete byte size, graph-output lifetime, and symbolic-size obligations.**

```python
def test_sequential_lifetimes_are_deterministic():
    analysis = analyze_resources(sequential_graph(), {"x": TensorType("f32", Shape((4,)))})
    assert analysis.schedule == ("n1", "n2", "n3")
    assert analysis.values["a"].first_step == 0
    assert analysis.values["a"].last_step == 1
    assert analysis.values["c"].last_step == 3


def test_symbolic_size_becomes_obligation():
    analysis = analyze_resources(symbolic_graph())
    assert analysis.values["y"].size_bytes is None
    assert any(o.kind == "runtime_size" and o.symbol == "y" for o in analysis.obligations)
```

- [ ] **Step 2: Run the tests and confirm RED because `nova_core.resources` does not exist.**

Run: `PYTHONPATH=src pytest tests/test_resource_analysis.py -q`

- [ ] **Step 3: Implement immutable resource facts and deterministic analysis.**

Implementation must include exact dtype-byte mapping, virtual graph-exit step, borrowed input/parameter ownership, shared immutable constants, owned/device-resident intermediates, and explicit runtime-size obligations.

- [ ] **Step 4: Run Task 1 tests and the inherited model/runtime tests.**

Run: `PYTHONPATH=src pytest tests/test_resource_analysis.py tests/test_model.py tests/test_interpreter.py -q`

- [ ] **Step 5: Commit.**

```bash
git add src/nova_core/resources.py src/nova_core/errors.py src/nova_core/__init__.py tests/test_resource_analysis.py
git commit -m "feat: add deterministic resource analysis"
```

### Task 2: MemoryPlan, Conservative Plan, Reuse, and Transfers

**Files:**
- Modify: `src/nova_core/resources.py`
- Create: `tests/test_memory_planner.py`

**Interfaces:**
- Consumes: `ResourceAnalysis`.
- Produces: `BufferBinding`, `DeviceTransfer`, `MemoryPlan`, `plan_memory`, `conservative_memory_plan`, `memory_plan_hash`.

- [ ] **Step 1: Write failing tests for unique conservative buffers, safe reuse, reduced reserved bytes, device transfers, and no reuse for unknown-size values.**

```python
def test_optimized_plan_reuses_non_overlapping_buffer():
    conservative = conservative_memory_plan(graph, facts)
    optimized = plan_memory(graph, facts, mode="optimized")
    assert optimized.peak_reserved_bytes < conservative.peak_reserved_bytes
    assert optimized.buffer_for("a") == optimized.buffer_for("c")


def test_device_mismatch_generates_transfer():
    plan = plan_memory(device_graph, device_facts)
    assert ("x", "cpu", "gpu0", "gpu_op") in {
        (t.symbol, t.source_device, t.target_device, t.before_node) for t in plan.transfers
    }
```

- [ ] **Step 2: Run tests and confirm RED because plan objects/functions do not exist.**

Run: `PYTHONPATH=src pytest tests/test_memory_planner.py -q`

- [ ] **Step 3: Implement deterministic conservative and optimized planners.**

The optimized planner must be a greedy deterministic allocator ordered by first-step then symbol. It may only reuse static, compatible, non-overlapping buffers. The conservative planner must assign unique physical buffers.

- [ ] **Step 4: Run Task 1+2 tests.**

Run: `PYTHONPATH=src pytest tests/test_resource_analysis.py tests/test_memory_planner.py -q`

- [ ] **Step 5: Commit.**

```bash
git add src/nova_core/resources.py tests/test_memory_planner.py
git commit -m "feat: add deterministic memory planning"
```

### Task 3: Independent Verifier and Conservative Fallback

**Files:**
- Create: `src/nova_core/resource_verifier.py`
- Modify: `src/nova_core/errors.py`
- Modify: `src/nova_core/__init__.py`
- Create: `tests/test_memory_verifier.py`

**Interfaces:**
- Consumes: `Graph`, `MemoryPlan`, `ResourceAnalysis`.
- Produces: `VerificationStatus`, `PlanViolation`, `MemoryPlanVerification`, `PlanSelection`, `verify_memory_plan`, `select_memory_plan`.

- [ ] **Step 1: Write failing tests for malicious overlapping aliases, missing transfers, forged peak bytes, graph-hash mismatch, safe plan acceptance, conditional dynamic-size acceptance, and unsafe-candidate fallback.**

```python
def test_overlapping_alias_candidate_is_unsafe():
    bad = replace(plan, buffers=(shared_buffer_for_overlapping_values(),), peak_reserved_bytes=16)
    report = verify_memory_plan(graph, bad, facts)
    assert report.status is VerificationStatus.UNSAFE
    assert "overlapping_lifetime" in {v.kind for v in report.violations}


def test_unsafe_candidate_falls_back():
    selected = select_memory_plan(graph, bad, facts)
    assert selected.fallback_used is True
    assert selected.selected.verification_mode == "conservative"
```

- [ ] **Step 2: Run verifier tests and confirm RED.**

Run: `PYTHONPATH=src pytest tests/test_memory_verifier.py -q`

- [ ] **Step 3: Implement verifier with independent recomputation and selection fallback.**

The verifier must recompute schedule/lifetimes/required transfers/physical capacity/peak reserved bytes. It must never trust candidate metrics. `CONDITIONALLY_SAFE` is reserved for runtime obligations such as symbolic size; invariant violations are always `UNSAFE`.

- [ ] **Step 4: Run Tasks 1-3 and full inherited regression.**

Run: `PYTHONPATH=src pytest -q`

- [ ] **Step 5: Commit.**

```bash
git add src/nova_core/resource_verifier.py src/nova_core/errors.py src/nova_core/__init__.py tests/test_memory_verifier.py
git commit -m "feat: verify memory plans with conservative fallback"
```

### Task 4: Codec, API, CLI, G3 Verification Matrix, and Round 09 Release

**Files:**
- Modify: `src/nova_core/resources.py`
- Modify: `src/nova_core/api.py`
- Modify: `src/nova_core/cli.py`
- Modify: `src/nova_core/model.py`
- Modify: `src/nova_core/__init__.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Create: `tests/test_resource_codec_api_cli.py`
- Create: `tests/test_round09_package.py`
- Create: `examples/resource_planning/static_reuse_project.json`
- Create: `examples/resource_planning/static_reuse_types.json`
- Create: `examples/resource_planning/device_transfer_project.json`
- Create: `examples/resource_planning/device_transfer_types.json`
- Create: `docs/G3_VERIFICATION_MATRIX.md`
- Create: `docs/rounds/ROUND_09_G3_RESOURCE_PLANNING_FINAL_SEAL.md`
- Create: `examples/g3_verification.json`
- Modify: `VALIDATION.md`
- Modify: `CHECKSUMS.sha256`

**Interfaces:**
- Consumes: all Task 1-3 APIs.
- Produces: `encode_memory_plan`, `decode_memory_plan`, project-level resource API, resource CLI, G3 seal artifacts, release ZIP.

- [ ] **Step 1: Write failing codec/API/CLI/package tests.**

```python
def test_memory_plan_codec_roundtrip_keeps_hash():
    restored = decode_memory_plan(encode_memory_plan(plan))
    assert memory_plan_hash(restored) == memory_plan_hash(plan)


def test_round09_version_and_g3_seal():
    assert nova_core.__version__ == "0.9.0"
    assert Path("docs/G3_VERIFICATION_MATRIX.md").exists()
    assert json.loads(Path("examples/g3_verification.json").read_text())["status"] == "sealed"
```

- [ ] **Step 2: Run the new tests and confirm RED for missing API/CLI/package artifacts.**

Run: `PYTHONPATH=src pytest tests/test_resource_codec_api_cli.py tests/test_round09_package.py -q`

- [ ] **Step 3: Implement codec/API/CLI and generate G3 example/seal artifacts.**

CLI must support `resource-plan`, `resource-verify`, and `resource-select`, all emitting JSON. `resource-select` must show candidate hash, selected hash, verifier status, violations, obligations, and fallback flag.

- [ ] **Step 4: Run the full fresh release gate.**

Run all tests, warnings-as-errors compile, real resource CLI smoke, UTF-8/secret/escape/control/math/JSON hygiene, checksum verification, and git cleanliness.

- [ ] **Step 5: Commit release metadata, rerun the full gate from the exact release commit, then create and verify the local ZIP.**

Expected ZIP name:

```text
NOVA_Core_Closure_Round_09_G3_Verifiable_Memory_Resource_Planning_2026-08-20.zip
```

# Round 12 G6 Explicit Execution-Paradigm Planner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build deterministic sixteenfold paradigm classification, candidate ranking, bonding validation, conservative fallback, API/CLI surfaces, and the G6 final seal.

**Architecture:** Add a `paradigm.py` domain/classifier/cost layer and a `paradigm_planner.py` selection/bonding layer. Both consume existing immutable NOVA Graphs and do not mutate or reinterpret Core semantics. Public API/CLI wraps the same deterministic planner.

**Tech Stack:** Python 3.11+, dataclasses/enums, existing NOVA canonical/model/runtime modules, pytest, JSON CLI.

**Spec:** `docs/superpowers/specs/2026-08-20-round-12-g6-paradigm-planner-design.md`

## Global Constraints
- Current runtime release becomes `0.12.0`; storage schema remains `0.1.0`.
- Same graph/profile/configuration must produce identical plan hashes.
- `R` requires explicit stable-recognition evidence and retains offline costs.
- Planner never modifies the canonical graph.
- Every region has a conservative sequential fallback.
- Do not implement G7 or claim global optimality.

---

### Task 1: Sixteenfold domain and region classifier

**Files:**
- Create: `src/nova_core/paradigm.py`
- Modify: `src/nova_core/errors.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_paradigm_domain.py`
- Test: `tests/test_paradigm_classifier.py`

**Interfaces:**
- Produces `BaseSpace`, `FillMode`, `ObservationMode`, `ParadigmTag`, `StrategyRegion`, `RegionEvidence`, `extract_strategy_regions(graph)`, `classify_region(region, profile)`.

- [ ] Write failing tests for the 16-tag table, stable codes, graph-hash invariance, and four evidence classes.
- [ ] Run the focused tests and confirm RED because the domain does not exist.
- [ ] Implement immutable enums/tags, complete P1–P16 table, region extraction, and conservative evidence classifier.
- [ ] Run focused plus representative inherited graph tests and confirm GREEN.
- [ ] Commit `feat: add sixteenfold paradigm domain and classifier`.

### Task 2: Cost model and candidate ranking

**Files:**
- Create: `src/nova_core/paradigm_planner.py`
- Test: `tests/test_paradigm_costs.py`
- Test: `tests/test_paradigm_candidates.py`

**Interfaces:**
- Consumes Task 1 regions/tags.
- Produces `PlannerProfile`, `CostBreakdown`, `ExecutionStrategyCandidate`, `candidate_strategies(region, profile)`, `rank_candidates(...)`.

- [ ] Write failing tests showing dense→P, sparse→J, sequential→C, explicit stable cache→R, profile-driven ranking, and nonzero R offline cost.
- [ ] Run focused tests and confirm RED.
- [ ] Implement deterministic cost components and ranking with sequential fallback.
- [ ] Run focused and inherited tests and confirm GREEN.
- [ ] Commit `feat: add paradigm candidate cost model`.

### Task 3: Bonding, plan selection, fallback, and profile evidence

**Files:**
- Modify: `src/nova_core/paradigm_planner.py`
- Modify: `src/nova_core/errors.py`
- Test: `tests/test_paradigm_bonding.py`
- Test: `tests/test_paradigm_planner.py`

**Interfaces:**
- Produces `BondTransition`, `BondViolation`, `BondDecision`, `ExecutionStrategyPlan`, `validate_bonds(...)`, `plan_graph(...)`, `plan_hash(...)`.

- [ ] Write failing tests for fill monotonicity, R terminality, stability reset, C→D/D→C asymmetry, deterministic hash, and conservative fallback when ranked chain is illegal.
- [ ] Run focused tests and confirm RED.
- [ ] Implement bonding validator and deterministic selection/fallback pipeline.
- [ ] Run all planner tests plus representative G3/G5 tests and confirm GREEN.
- [ ] Commit `feat: add paradigm bonding and plan selection`.

### Task 4: API, CLI, examples, G6 verification, and release seal

**Files:**
- Modify: `src/nova_core/api.py`
- Modify: `src/nova_core/cli.py`
- Modify: `src/nova_core/__init__.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Create: `tests/test_paradigm_api_cli.py`
- Create: `tests/test_round12_package.py`
- Create: `examples/paradigm/*.json`
- Create: `docs/G6_VERIFICATION_MATRIX.md`
- Create: `docs/rounds/ROUND_12_G6_PARADIGM_PLANNER_FINAL_SEAL.md`
- Create: `docs/G6_FINAL_SEAL.json`
- Modify: `VALIDATION.md`
- Modify: `CHECKSUMS.sha256`

**Interfaces:**
- Produces project-level planning API and `nova paradigm classify|plan|validate-bonds` CLI JSON surfaces.

- [ ] Write failing API/CLI/package tests for `0.12.0`, four acceptance examples, deterministic hashes, and seal files.
- [ ] Run focused tests and confirm RED.
- [ ] Implement wrappers/CLI and generate examples from real planner runs.
- [ ] Execute fresh full regression and real four-scenario CLI acceptance.
- [ ] Generate verification matrix/seal from observed evidence, run warnings-as-errors compile and source hygiene, rebuild checksums, and commit release metadata.
- [ ] Re-run final full test/CLI/manifest/git-clean gate from the exact release commit.
- [ ] Create the local Round 12 ZIP, run CRC and extracted-manifest verification, and record ZIP SHA-256.

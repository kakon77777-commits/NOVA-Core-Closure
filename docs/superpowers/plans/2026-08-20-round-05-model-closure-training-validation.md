# NOVA Core Closure Round 05 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic immutable full-batch SGD training runtime and close the original G1 three-model validation condition with Linear Regression, MLP, and Small Attention.

**Architecture:** Training is a runtime composition over the existing canonical Graph, execution backends, and reverse-mode derivative graph. Parameter values remain outside canonical program identity; each optimizer step creates a new immutable TrainingState and verifies that the graph semantic hash did not change.

**Tech Stack:** Python 3.11+, NumPy, dataclasses, existing NOVA Graph/Interpreter/NumPyBackend/autodiff APIs, pytest.

**Spec:** `docs/superpowers/specs/2026-08-20-round-05-model-closure-training-validation-design.md`

## Global Constraints

- Release version is `0.5.0`; graph storage schema remains `0.1.0`.
- Only deterministic full-batch SGD is implemented in Round 05.
- Optimizer targets must be outputs of `Parameter` nodes.
- Training must not mutate canonical Graph/Node/Project objects.
- Parameter arrays stored in TrainingState must be copies with `writeable=False`.
- Derivative graph is generated once per training run.
- The loss target must be scalar and finite.
- Non-finite gradients, gradient shape mismatches, missing parameter bindings, and semantic-hash drift are typed failures.
- No Adam, momentum, mini-batching, random initialization, GPU training, memory planner, JIT/AOT, or optimizer DSL.

---

### Task 1: Immutable Training State and Explicit SGD

**Files:**
- Create: `src/nova_core/training.py`
- Modify: `src/nova_core/errors.py`
- Modify: `src/nova_core/__init__.py`
- Test: `tests/test_training_state.py`

**Interfaces:**
- Produces `TrainingConfig`, `TrainingState`, `TrainingStepRecord`, `TrainingResult`.
- Produces `parameter_bindings(graph)`, `parameter_state_hash(parameters)`, and `sgd_update(...)`.
- `TrainingConfig(target: str, wrt: tuple[str,...], steps: int, learning_rate: float, backend: str = "numpy")`.
- `sgd_update(parameters, gradients, bindings, learning_rate) -> Mapping[str, np.ndarray]` returns fresh read-only arrays.

- [ ] **Step 1: Write failing tests** for Parameter binding resolution, immutable array copies, deterministic parameter-state hash, SGD numeric update, previous-state immutability, and rejection of invalid learning rates / non-Parameter optimizer targets.

- [ ] **Step 2: Run** `PYTHONPATH=src pytest tests/test_training_state.py -q` and confirm failure because `nova_core.training` does not exist.

- [ ] **Step 3: Implement** the dataclasses, parameter binding extraction, read-only array freezing, hash function, SGD update, and typed `TrainingError` validation.

- [ ] **Step 4: Run** `PYTHONPATH=src pytest tests/test_training_state.py -q` and then `PYTHONPATH=src pytest tests/test_training_state.py tests/test_autodiff_execution.py -q`.

- [ ] **Step 5: Commit** with `feat: add immutable training state and SGD`.

---

### Task 2: Generic Training Loop, Python API, and CLI

**Files:**
- Modify: `src/nova_core/training.py`
- Modify: `src/nova_core/api.py`
- Modify: `src/nova_core/cli.py`
- Test: `tests/test_training_loop.py`
- Test: `tests/test_training_api_cli.py`

**Interfaces:**
- Produces `train_graph(graph, inputs, initial_parameters, config) -> TrainingResult`.
- Produces `train_project(project, module_id, graph_id, inputs, initial_parameters, config) -> TrainingResult`.
- Adds CLI `nova train` with target, repeated wrt, steps, learning rate, backend, inputs and parameters files.

- [ ] **Step 1: Write failing training-loop tests** using a scalar quadratic model. Assert loss history length is `steps + 1`, loss decreases, derivative graph is generated once, graph semantic hash is unchanged, state hashes change only with parameters, and identical runs replay identically.

- [ ] **Step 2: Run** `PYTHONPATH=src pytest tests/test_training_loop.py -q` and confirm missing `train_graph` behavior.

- [ ] **Step 3: Implement** the generic loop: validate config; resolve Parameter bindings; build one DifferentiationRequest and one derivative graph; execute primal and derivative on each step; reject non-scalar/non-finite loss and non-finite/mismatched gradients; apply fresh SGD state; append TrainingStepRecord; compute final post-update loss.

- [ ] **Step 4: Write failing API/CLI tests** and implement `train_project` plus `nova train`. JSON output must include `initial_loss`, `final_loss`, `loss_history`, `final_parameters`, `parameter_state_hash`, `graph_semantic_hash`, and `derivative_semantic_hash`.

- [ ] **Step 5: Run** both new test files and inherited CLI/API tests.

- [ ] **Step 6: Commit** with `feat: add deterministic NOVA training loop`.

---

### Task 3: Linear Regression and MLP Closure

**Files:**
- Create: `examples/training_linear.json`
- Create: `examples/training_linear_inputs.json`
- Create: `examples/training_linear_parameters.json`
- Create: `examples/training_mlp.json`
- Create: `examples/training_mlp_inputs.json`
- Create: `examples/training_mlp_parameters.json`
- Test: `tests/test_model_closure_linear_mlp.py`

**Interfaces:**
- Uses only existing canonical node kinds and `train_project`.
- No special model-specific runtime code.

- [ ] **Step 1: Add failing model-closure tests** that construct or load a linear-regression graph and require a bounded deterministic SGD run to reduce loss by at least 90% on a tiny fixed dataset. Confirm Interpreter/NumPy primal agreement and graph semantic-hash invariance.

- [ ] **Step 2: Add the linear example JSON/input/parameter artifacts** and tune only dataset, initial values, learning rate and step count until the generic runtime passes the acceptance criteria.

- [ ] **Step 3: Add failing MLP closure tests** for `tanh(XW1+b1) -> HW2+b2 -> MSE`, requiring deterministic replay and substantial loss reduction from fixed initial values.

- [ ] **Step 4: Add MLP example artifacts** and validate that repeated training from the same state produces identical loss history and final parameter-state hash.

- [ ] **Step 5: Run** `PYTHONPATH=src pytest tests/test_model_closure_linear_mlp.py -q` and then the entire training subset.

- [ ] **Step 6: Commit** with `test: close linear regression and MLP training models`.

---

### Task 4: Small Attention Closure and Round 05 Release

**Files:**
- Create: `examples/training_attention.json`
- Create: `examples/training_attention_inputs.json`
- Create: `examples/training_attention_parameters.json`
- Test: `tests/test_model_closure_attention.py`
- Modify: `src/nova_core/__init__.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Create: `docs/rounds/ROUND_05_MODEL_CLOSURE_TRAINING_VALIDATION.md`
- Modify/Create: `VALIDATION.md`
- Rebuild: `CHECKSUMS.sha256`

**Interfaces:**
- Attention graph is one-head dense attention using existing `MatMul`, `Transpose`, `Divide`, `Softmax`, `Subtract`, `Multiply`, and `Mean` nodes.
- Trainable symbols are `WQ`, `WK`, `WV`, `WO`.

- [ ] **Step 1: Write failing attention tests** for primal execution, reverse AD execution, finite-difference checks on a bounded parameter subset, and bounded SGD loss reduction.

- [ ] **Step 2: Add fixed attention example artifacts** with no random initialization. Choose a tiny sequence/model dimension so gradient checks and training complete quickly.

- [ ] **Step 3: Run** the attention test and tune only fixed data, initialization, learning rate and bounded step count; do not add model-specific optimizer rules.

- [ ] **Step 4: Upgrade package metadata to `0.5.0`**, update README and write Round 05 technical notes. Preserve `schema_version = 0.1.0`.

- [ ] **Step 5: Run the full regression suite** with `PYTHONPATH=src pytest -q` and warnings-as-errors compile with `python -W error -m compileall -q src tests`.

- [ ] **Step 6: Run real CLI smokes** for linear, MLP, and attention training; record exact initial/final losses and parameter-state hashes in `VALIDATION.md`.

- [ ] **Step 7: Run source hygiene**: UTF-8 decode, secret scan, Unicode-escape scan, hidden-control scan, alternate Markdown math-delimiter scan, JSON parse, and `git diff --check`.

- [ ] **Step 8: Rebuild `CHECKSUMS.sha256`** from tracked source files excluding the manifest itself. Commit release metadata, rerun the entire final gate from the exact release commit, and require a clean git tree.

- [ ] **Step 9: Create local ZIP** `NOVA_Core_Closure_Round_05_Model_Closure_Training_Validation_2026-08-20.zip` from tracked files only. Verify ZIP CRC and extracted checksum manifest.

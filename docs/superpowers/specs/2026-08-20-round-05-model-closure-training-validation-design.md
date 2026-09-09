# NOVA Core Closure Round 05 — Model Closure & Training Validation Design

**Status:** approved continuation of the Round 05 direction announced at the end of Round 04  
**Date:** 2026-08-20  
**Release target:** `0.5.0`  
**Storage schema:** remains `0.1.0`

## 1. Goal

Round 05 closes the original G1 executable-model exit condition by demonstrating that the existing NOVA stack can train three distinct canonical program graphs:

1. Linear Regression;
2. a small MLP;
3. a small single-head Attention model.

This round is not a new language layer. It composes the capabilities already implemented in Rounds 01–04:

$$
\text{Structure}
\rightarrow
\text{Tensor/Shape}
\rightarrow
\text{Execution}
\rightarrow
\text{Reverse AD}
\rightarrow
\text{Training Validation}.
$$

## 2. Canonical/runtime boundary

The canonical graph describes Parameter nodes, types, structure, operators, and differentiation semantics.

Parameter **values** belong to runtime training state, not to canonical program identity.

Therefore a training step must satisfy:

$$
H_{\mathrm{sem}}(G_{t+1})
=
H_{\mathrm{sem}}(G_t).
$$

Only the runtime parameter state changes:

$$
\Theta_{t+1}
=
\Theta_t-\eta\nabla_{\Theta}L.
$$

No optimizer step may mutate a `Graph`, `Node`, or `Project` object.

## 3. Round 05 training state

Introduce an immutable runtime training model:

```text
TrainingConfig
TrainingState
TrainingStepRecord
TrainingResult
```

`TrainingConfig` contains only the bounded reference-training controls needed in this round:

```text
target
wrt[]
steps
learning_rate
backend
```

`TrainingState` contains:

```text
step
parameters
loss_history
graph_semantic_hash
parameter_state_hash
```

Every parameter array copied into a state is read-only. An SGD update returns a new state; it never edits the previous arrays in place.

## 4. Explicit parameter bindings

A trainable NOVA parameter is a `Parameter` node with exactly one output symbol.

For a parameter node:

```text
Node(kind="Parameter", outputs=["W"], attributes={"name":"weight"})
```

NOVA distinguishes:

- canonical symbol: `W`;
- runtime binding name: `weight`.

Training requests use canonical symbols in `wrt`; the training runtime resolves them to runtime parameter names before applying updates.

Only Parameter outputs may be optimized in Round 05. Graph inputs and intermediate symbols may still be differentiated for analysis, but `train_graph` rejects them as optimizer targets.

## 5. Optimizer scope

Round 05 implements one optimizer only:

$$
\boxed{\text{explicit deterministic full-batch SGD}}
$$

with:

$$
\theta_{t+1}=\theta_t-\eta g_t.
$$

Not included:

- momentum;
- Adam;
- weight decay;
- gradient clipping;
- learning-rate schedules;
- mixed precision;
- mini-batching;
- distributed training.

Those features are not required to validate G1 closure.

## 6. Training loop

For each step:

1. execute the primal graph and require the target to be scalar;
2. execute the already-generated derivative graph;
3. collect gradients for the requested Parameter symbols;
4. compute an immutable SGD parameter update;
5. append a structured `TrainingStepRecord`;
6. verify that the canonical graph semantic hash is unchanged.

The derivative graph is generated once per training run, not regenerated at every step.

The loss history contains the initial loss and the post-update loss after every step, so its length is `steps + 1`.

## 7. Deterministic parameter-state hash

Round 05 adds a runtime-only parameter-state hash for audit/replay comparisons.

The hash includes, in sorted binding-name order:

- binding name;
- normalized NumPy dtype;
- shape;
- contiguous value bytes.

This hash is not a NOVA semantic program hash and must never replace `semantic_hash(Graph)`.

## 8. Three model closures

### 8.1 Linear Regression

Canonical structure:

$$
Y=XW+b,
\qquad
L=\operatorname{Mean}((Y-T)^2).
$$

Trainable symbols:

```text
W, b
```

Acceptance:

- training loss decreases substantially;
- both Interpreter and NumPy backends can execute the model;
- gradient check remains valid;
- graph semantic hash is unchanged after training.

### 8.2 Small MLP

Canonical structure:

$$
H=\tanh(XW_1+b_1),
$$

$$
Y=HW_2+b_2,
$$

$$
L=\operatorname{Mean}((Y-T)^2).
$$

Trainable symbols:

```text
W1, b1, W2, b2
```

Acceptance:

- deterministic full-batch SGD reduces loss on a fixed tiny dataset;
- the same initial state produces the same loss trajectory and final parameter hash.

### 8.3 Small Attention

Use one-head dense attention:

$$
Q=XW_Q,
\quad
K=XW_K,
\quad
V=XW_V,
$$

$$
A=\operatorname{softmax}\left(\frac{QK^\top}{\sqrt d}\right),
$$

$$
Y=AVW_O,
$$

$$
L=\operatorname{Mean}((Y-T)^2).
$$

Trainable symbols:

```text
WQ, WK, WV, WO
```

This model intentionally exercises `MatMul`, `Transpose`, `Divide`, `Softmax`, broadcast-compatible arithmetic, and reverse-mode VJP composition.

Acceptance:

- primal execution succeeds;
- reverse AD executes;
- finite-difference gradient validation passes for a bounded parameter subset;
- a bounded SGD run decreases loss.

## 9. API and CLI

Python API:

```text
parameter_bindings(graph)
parameter_state_hash(parameters)
sgd_update(parameters, gradients, bindings, learning_rate)
train_graph(graph, inputs, initial_parameters, config)
train_project(project, module_id, graph_id, inputs, initial_parameters, config)
```

CLI:

```text
nova train PROGRAM
  --module app
  --graph main
  --target loss
  --wrt W
  --wrt b
  --inputs inputs.json
  --parameters parameters.json
  --steps 100
  --learning-rate 0.05
  --backend numpy
```

CLI output is structured JSON containing initial/final loss, loss history, final parameters, final parameter-state hash, derivative graph hash, and canonical graph hash.

## 10. Failure model

Round 05 must reject explicitly:

- zero/negative step count;
- non-positive or non-finite learning rate;
- non-scalar training target;
- `wrt` symbol that is not a Parameter output;
- missing runtime parameter binding;
- gradient shape mismatch;
- non-finite loss;
- non-finite gradient;
- graph semantic hash drift during training.

Failures use typed NOVA errors, not raw assertions.

## 11. Non-goals

Round 05 does not implement:

- optimizer language semantics;
- stateful mutable Parameter nodes;
- checkpoint files;
- dataset iterators or mini-batches;
- random initialization inside the runtime;
- GPU training;
- JIT/AOT compilation;
- memory planning;
- effectful training callbacks;
- learned optimizer selection.

## 12. Release evidence

The release must include fresh evidence for:

- inherited regression suite;
- unit tests for immutable training state and SGD;
- linear-regression training convergence;
- MLP training convergence and deterministic replay;
- small-attention primal/AD/gradient-check/training validation;
- CLI training smoke;
- graph semantic-hash invariance;
- UTF-8/source hygiene;
- checksum manifest;
- ZIP CRC and extracted-manifest verification.

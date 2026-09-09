# NOVA Core Closure — Round 05: Model Closure & Training Validation

**Release:** 0.5.0  
**Schema:** 0.1.0  
**Date:** 2026-08-20

## Purpose

Round 05 validates that the four earlier kernels form a usable training stack rather than four isolated demonstrations:

$$
\text{Canonical Graph}
\rightarrow
\text{Tensor/Shape}
\rightarrow
\text{Execution}
\rightarrow
\text{Reverse AD}
\rightarrow
\text{Training}.
$$

The central invariant is that training updates runtime Parameter values, not canonical program identity:

$$
H_{\mathrm{sem}}(G_t)=H_{\mathrm{sem}}(G_{t+1}).
$$

## Training runtime

Round 05 adds:

- `TrainingConfig`;
- immutable `TrainingState`;
- `TrainingStepRecord`;
- `TrainingResult`;
- Parameter symbol to runtime-binding resolution;
- deterministic runtime-only parameter-state hashing;
- explicit full-batch SGD;
- `train_graph` and `train_project`;
- CLI `nova train`.

Parameter arrays captured by a TrainingState are copies marked read-only. Every SGD step creates fresh arrays and a fresh state.

## Model closure

### Linear Regression

$$
Y=XW+b,
\qquad
L=\operatorname{Mean}((Y-T)^2).
$$

A bounded deterministic run reduces loss by more than 99% while preserving the graph semantic hash.

### Small MLP

$$
H=\tanh(XW_1+b_1),
$$

$$
Y=HW_2+b_2,
$$

$$
L=\operatorname{Mean}((Y-T)^2).
$$

The model is trained against a fixed teacher-generated tiny dataset. Repeating the run from the same initial Parameter state reproduces the same loss history and final parameter-state hash.

### Small Attention

$$
Q=XW_Q,
\quad
K=XW_K,
\quad
V=XW_V,
$$

$$
A=\operatorname{softmax}\left(\frac{QK^\top}{\sqrt 2}\right),
$$

$$
Y=AVW_O,
$$

$$
L=\operatorname{Mean}((Y-T)^2).
$$

This model validates a compound reverse path through MatMul, Transpose, Divide, Softmax and Mean. A bounded finite-difference check validates `WQ` and `WV`, and deterministic SGD reduces the loss to below 2% of its initial value.

## Scope boundary

Round 05 does not add Adam, momentum, mini-batches, random initialization, mixed precision, GPU training, optimizer DSLs, or memory planning.

The remaining G1 interoperability surface is intentionally left for Round 06.

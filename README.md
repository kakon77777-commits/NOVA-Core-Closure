# NOVA Core Closure

**NOVA Core Closure** is the implementation project for the executable core of NOVA: a structure-first, tensor-native, differentiable, AI-assisted programming language architecture.

NOVA does **not** treat source text as the authoritative program object. The canonical program is a typed structural graph; text, mathematical notation, graph views, documentation, debugging views, and AI-facing patches are projections of that same program object.

$$
\boxed{
\text{Canonical Program}
=
\text{Typed Structural Graph}
}
$$

## Core principle

NOVA starts from:

$$
\text{Structure}
\rightarrow
\{
\text{Text},
\text{Formula},
\text{Graph},
\text{Document},
\text{Debug View},
\text{AI View}
\}
$$

rather than requiring:

$$
\text{Text}
\rightarrow
\text{Parse}
\rightarrow
\text{Structure}.
$$

Text remains important for exchange, Git diff, CLI, accessibility, review, and long-term preservation. It is simply no longer the only authoritative container of program identity.

## NOVA Core

The frozen core model is:

$$
\boxed{
\mathcal N_{\mathrm{Core}}
=
(
\mathcal G,
\mathcal T,
\mathcal S,
\mathcal E,
\mathcal M,
\mathcal D,
\mathcal R
)
}
$$

where:

- $\mathcal G$ — typed program graph;
- $\mathcal T$ — values and tensor types;
- $\mathcal S$ — shape and constraint solving;
- $\mathcal E$ — effects and reproducibility;
- $\mathcal M$ — verifiable memory/resource planning;
- $\mathcal D$ — language-level automatic differentiation;
- $\mathcal R$ — backend implementations.

## Core Closure 0.1

The first implementation milestone is intentionally small and complete.

It targets:

- canonical Project / Module / Graph / Node / Edge schemas;
- deterministic serialization and semantic hashing;
- scalar and tensor values;
- symbolic shape constraints;
- broadcasting, contraction, reshape, transpose, elementwise operations and matrix multiplication;
- pure functions, `if`, and bounded loops;
- a reference interpreter;
- a CPU / NumPy reference backend;
- reverse-mode automatic differentiation;
- structured text and formula projections;
- CLI and Python interoperability;
- GraphPatch transactions with validation, provenance, rollback, and tests.

The first executable validation cases are:

1. linear regression;
2. a small MLP;
3. a small attention model.

## AI-native does not mean AI-trusted

NOVA allows AI to construct and modify the program structure directly:

$$
\text{Intent}
\rightarrow
\text{Candidate Graph}
\rightarrow
\text{Constraint Validation}
\rightarrow
G^\ast.
$$

AI may propose:

- graph patches;
- type and shape constraints;
- differentiation requests;
- resource plans;
- backend candidates;
- proof obligations and tests.

But AI output is untrusted input until it passes deterministic validation.

$$
\boxed{
\text{AI Proposal}
\neq
\text{Correctness Proof}
}
$$

## What Core Closure 0.1 is not

This milestone does **not** attempt to finish:

- a full projectional IDE;
- deep GPU optimization;
- distributed execution;
- the complete effect system;
- the full MSSP-AISMBI memory planner;
- complete EML / ISQL / SOS / Cl-safe integration;
- the sixteen-paradigm planner;
- minimal-symbol control;
- unrestricted autonomous deployment.

Those systems connect through versioned interfaces after the core executable semantics are stable.

## Repository rule

Each completed development round is packaged as a ZIP artifact and committed to this repository before the round is reported complete.

Round artifacts are stored under:

```text
releases/rounds/
```

The chat-side downloadable ZIP and the repository ZIP should represent the same completed round.

## Current status

```text
Round 00
Recover → Reconcile → Freeze Core
Status: Basic introduction / repository bootstrap
```

The next engineering milestone is **NOVA Core Closure 0.1 — Phase A: Canonical Graph Kernel**.

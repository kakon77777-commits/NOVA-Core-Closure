# NOVA Core Closure

**NOVA Core Closure** is the reference implementation project for the executable core of NOVA: a structure-first, tensor-native, differentiable, AI-assisted programming language architecture.

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

## Frozen NOVA Core model

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

## Development status

### Round 00 — Basic Introduction

Repository bootstrap, recovered source basis, and Core Closure scope.

### Round 01 — Canonical Graph Kernel

**Implemented.** Round 01 establishes the first executable authoritative NOVA object model:

- immutable `SchemaHeader`, `Project`, `Module`, `Graph`, `Node`, and `Edge` objects;
- deterministic UTF-8 canonical JSON serialization;
- semantic hashing independent of semantically irrelevant insertion order;
- semantic hash separation from provenance / migration history;
- structural validation with typed `NovaError` / `ValidationError` objects;
- forward-compatible unknown-field preservation through `extensions`;
- JSON decode → canonicalize → encode round-trip;
- transactional `GraphPatch` with base-hash conflict detection;
- candidate validation before working-state mutation;
- rollback to the exact base semantic hash.

The key identity rule is now executable:

$$
\boxed{
H_{\mathrm{sem}}(G)
=
\operatorname{SHA256}(\operatorname{Canon}_{\mathrm{sem}}(G))
}
$$

Projection/provenance metadata can change without changing $H_{\mathrm{sem}}$, while executable structural changes do change it.

### Round 02 — Tensor / Shape Semantic Kernel

**Next.** Round 02 will add the first native tensor semantics:

- scalar / tensor value types;
- symbolic dimension expressions;
- shape equality and obligations;
- broadcasting;
- contraction / `MatMul` shape rules;
- reshape / transpose;
- explicit unknown-shape handling;
- a minimal decidable constraint subset.

Round 02 will not yet add the interpreter or reverse-mode AD; those remain later closure rounds.

## GraphPatch boundary

AI-native NOVA does not mean AI-trusted NOVA.

$$
\text{Intent}
\rightarrow
\text{Candidate GraphPatch}
\rightarrow
\text{Deterministic Validation}
\rightarrow
G^\ast.
$$

A patch may contain provenance, proof obligations, tests, and rationale, but it can update the candidate graph only after its base semantic hash matches and the resulting project validates.

$$
\boxed{
\text{AI Proposal}
\neq
\text{Correctness Proof}
}
$$

## Quick reference

```python
from nova_core import (
    Graph,
    GraphPatch,
    GraphTransaction,
    Module,
    Node,
    Project,
    SchemaHeader,
    semantic_hash,
)

project = Project(
    header=SchemaHeader(
        nova_core_version="0.1.0",
        schema_version="0.1.0",
        feature_flags=("graph-kernel",),
    ),
    modules=(
        Module(
            id="app",
            graphs=(
                Graph(
                    id="main",
                    inputs=("x",),
                    outputs=("y",),
                    nodes=(
                        Node(
                            id="identity_1",
                            kind="Identity",
                            inputs=("x",),
                            outputs=("y",),
                        ),
                    ),
                ),
            ),
        ),
    ),
)

print(semantic_hash(project))
```

## Repository release rule

Each completed development round is packaged as a ZIP artifact and committed to this repository before the round is reported complete.

```text
releases/rounds/
```

The chat-side downloadable ZIP and repository ZIP represent the same completed round.

## Scope discipline

NOVA Core Closure does not collapse EML, ISQL, SOS, Cl-safe, HSO, or other EveMissLab systems into the Core. Those systems connect through versioned interfaces after the Core semantic contract is stable.

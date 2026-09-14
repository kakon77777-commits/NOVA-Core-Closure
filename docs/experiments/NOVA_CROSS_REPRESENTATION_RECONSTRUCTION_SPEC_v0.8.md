# NOVA Cross-Representation Reconstruction v0.8

**Status:** Experimental specification  
**Date:** 2026-09-15  
**Lineage:** v0.7 CoreNorm → v0.8 Cross-Representation Reconstruction

## 0. Conclusion first

v0.8 tests the stronger claim that independently authored representation families can lower into different NOVA Projects and still reconstruct the same bounded machine structure.

The target invariant is:

$$
\boxed{
\operatorname{CoreNorm}(P_T)
=
\operatorname{CoreNorm}(P_G)
=
\operatorname{CoreNorm}(P_A)
}
$$

where:

- $P_T$ is reconstructed from a bounded text-like surface;
- $P_G$ is reconstructed from a graph-native exchange surface;
- $P_A$ is reconstructed from an AI-native typed construction plan.

This is stronger than multi-projection of one already-existing NOVA object. The three adapters do not share an intermediate source representation.

---

## 1. Research question

Traditional language pipelines often make source text authoritative:

$$
\text{Text}\to\text{Parse}\to\text{Program}.
$$

NOVA v0.8 asks whether authority can instead sit after reconstruction:

$$
R_i
\xrightarrow{L_i}
P_i
\xrightarrow{\operatorname{CoreNorm}_\Pi}
C,
$$

with several independent representation families $R_i$ converging on the same bounded normalization class $C$.

The experiment therefore distinguishes:

$$
\text{Source Identity}
\neq
\text{Lowered Project Identity}
\neq
\text{CoreNorm Identity}.
$$

---

## 2. Three independent adapters

### 2.1 Text-like adapter

Module: `surface_text.py`

The text surface is deliberately small and not Python-compatible. It accepts a graph declaration and assignment statements such as:

```text
graph calculation(left, right) -> (answer)
temporary = Add(right, left) :: f32[Batch,8]
answer = Identity(temporary)
```

It never uses `eval` or `exec`.

### 2.2 Graph-native adapter

Module: `surface_graph.py`

The graph surface uses explicit nodes, arguments, bindings, tensor contracts, graph inputs, and graph outputs. Node order is not authoritative.

### 2.3 AI-native adapter

Module: `surface_ai.py`

The AI surface is a typed construction plan. References are explicit:

```text
{"input": 0}
{"value": "work"}
```

It does not generate source text before constructing the NOVA Project.

---

## 3. Reconstruction pipeline

For representation family $i$:

$$
R_i
\xrightarrow{L_i}
P_i
\xrightarrow{H_{sem}}
h_i
\xrightarrow{\operatorname{CoreNorm}_\Pi}
C_i.
$$

A convergence certificate may claim:

$$
\operatorname{Converged}_\Pi(R_1,\ldots,R_n)
\iff
\forall i,j,
H(C_i)=H(C_j).
$$

The certificate retains separately:

- representation kind;
- adapter revision;
- exact source hash;
- lowered legacy semantic hash;
- CoreNorm hash;
- CoreNorm byte size;
- obligations;
- CoreNorm profile hash.

---

## 4. Why legacy Project hashes are allowed to differ

The three lowerings deliberately preserve representation-local naming and construction choices. Therefore:

$$
H_{sem}(P_T),
H_{sem}(P_G),
H_{sem}(P_A)
$$

may all differ.

That is not a failure. The v0.8 claim is exactly that:

$$
\boxed{
H_{sem}(P_T)\neq H_{sem}(P_G)\neq H_{sem}(P_A)
}
$$

can coexist with:

$$
\boxed{
H_{CN}(P_T)=H_{CN}(P_G)=H_{CN}(P_A).
}
$$

---

## 5. Bounded equivalences used by this experiment

v0.8 inherits the v0.7 CoreNorm profile. In the validation example it relies on:

- structural alpha-renaming;
- scoped-binder alpha-renaming;
- Human Projection exclusion;
- safe trivial `Identity` elimination;
- bounded `Add` commutative input normalization;
- deterministic semantic atom normalization.

No new unrestricted equivalence theorem is introduced by v0.8.

---

## 6. Falsification conditions

The experiment must fail or refuse to claim convergence if:

1. a semantic operator changes, e.g. `Add -> Subtract`;
2. an adapter contains an unresolved reference;
3. the text source falls outside the bounded grammar;
4. the graph source contains unresolved values;
5. CoreNorm rejects the lowered Project;
6. CoreNorm hashes differ.

The AI adapter must not silently repair unknown references. The text adapter must not execute arbitrary host-language code.

---

## 7. Claim boundary

The certificate carries the exact claim boundary:

```text
bounded adapter reconstruction plus CoreNorm profile equivalence;
not global language or behavioral equivalence
```

Thus:

$$
\boxed{
\operatorname{Converged}_{v0.8}
\not\Rightarrow
\text{unrestricted semantic equivalence}.
}
$$

---

## 8. Relation to SREG F-series

v0.8 is the first NOVA experiment that directly instantiates the SREG cross-universe normalization idea:

$$
U_1\neq U_2
\quad\text{but}\quad
\operatorname{CoreNorm}(U_1)
\cong
\operatorname{CoreNorm}(U_2).
$$

For NOVA, the universes are representation families rather than mathematical foundations.

The engineering interpretation is:

$$
\boxed{
\text{Program surface}
\neq
\text{Program authority}.
}
$$

---

## 9. Non-goals

v0.8 does not claim:

- complete Python/Rust/C import;
- arbitrary visual-language equivalence;
- behavioral equivalence of effectful programs;
- theorem proving over all rewrite systems;
- unrestricted decompilation;
- that every representation admits a unique NOVA reconstruction.

Those remain later research domains.

---

## 10. Acceptance criteria

v0.8 is accepted experimentally when:

1. text, graph, and AI sources have distinct source hashes;
2. their lowered NOVA Projects have distinct legacy semantic hashes;
3. their CoreNorm hashes and bytes are equal;
4. whitespace/comment-only text changes preserve CoreNorm;
5. graph surface ordering / trivial Identity differences preserve CoreNorm;
6. semantic operator mutation breaks convergence;
7. unresolved references are rejected;
8. the bounded claim boundary is present in the certificate;
9. the prior isolated compatibility suite continues to pass.

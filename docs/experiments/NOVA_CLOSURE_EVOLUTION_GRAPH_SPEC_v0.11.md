# NOVA Reopening Lineage / Closure Evolution Graph v0.11

**Status:** Experimental specification  
**Date:** 2026-09-15  
**Parent experiment:** v0.10 ART/FDT Reopening + Re-PEC

## 1. Purpose

v0.9 introduced a bounded Program DPEC certificate. v0.10 attacked that certificate with ART/FDT and emitted a lineage-linked Re-PEC. v0.11 turns those artifacts into an explicit, machine-verifiable evolution graph.

The central separation is:

$$
\boxed{
\text{Program State Evolution}
\neq
\text{Closure-Knowledge Evolution}
}
$$

A program may remain in the same CoreNorm state while its closure certificate, debt ledger, frontier map, reopening rules, and verification evidence evolve.

Therefore a sequence of files is insufficient. NOVA needs a causal lineage object.

## 2. Closure Evolution Graph

The v0.11 graph is a typed DAG:

$$
\mathcal G_C=(V,E,\mathcal E)
$$

where $V$ contains six node families:

$$
V=
V_{PEC}
\sqcup
V_{ART}
\sqcup
V_{RePEC}
\sqcup
V_{State}
\sqcup
V_{Debt}
\sqcup
V_{Frontier}.
$$

The current concrete episode is:

$$
PEC_{0.9}
\rightarrow
ART/FDT_{0.10}
\rightarrow
RePEC_{0.10}
\rightarrow
PEC^{hard}_{0.10}.
$$

The parent PEC is never overwritten.

## 3. Node semantics

### 3.1 PEC node

A PEC node is content-addressed by its certificate hash and records its status, level, CoreNorm state reference, manifest reference, verification count, and terminality flag.

### 3.2 ART/FDT node

An ART/FDT node is content-addressed by the report hash and records the attacked baseline certificate, attack/control counts, status, and Re-PEC requirement.

### 3.3 Re-PEC node

A Re-PEC node records:

$$
(parent\ PEC, ART/FDT\ report, hardened\ PEC).
$$

Its admissible lineage action is:

```text
SUPERSEDE_WITH_LINEAGE_NOT_OVERWRITE
```

### 3.4 CoreNorm state node

A state node is keyed by the machine-state reference:

$$
S=H_{CoreNorm}(P).
$$

Multiple closure certificates may certify the same state node. This is intentional.

### 3.5 Debt snapshot

Debt is versioned as a snapshot attached to a particular PEC:

$$
D_i@PEC_t.
$$

The logical key remains stable across snapshots, while status/content may evolve.

### 3.6 Frontier snapshot

Frontier is treated analogously:

$$
F_i@PEC_t.
$$

Frontier retirement and introduction are explicit lineage events rather than silent list replacement.

## 4. Edge semantics

The v0.11 relation vocabulary is typed and closed for this revision:

- `stressed_by`: PEC $\to$ ART/FDT;
- `parent_of_repec`: PEC $\to$ Re-PEC;
- `supports_repec`: ART/FDT $\to$ Re-PEC;
- `produces_hardened_pec`: Re-PEC $\to$ PEC;
- `certifies_state`: PEC $\to$ CoreNorm state;
- `contains_debt`: PEC $\to$ debt snapshot;
- `contains_frontier`: PEC $\to$ frontier snapshot;
- `debt_evolves`: debt snapshot $\to$ debt snapshot;
- `frontier_evolves`: frontier snapshot $\to$ frontier snapshot;
- `introduces_debt`: Re-PEC $\to$ debt snapshot;
- `introduces_frontier`: Re-PEC $\to$ frontier snapshot;
- `retires_frontier`: frontier snapshot $\to$ Re-PEC.

A relation whose endpoint kinds do not match the schema is invalid.

## 5. Episode delta

Each closure episode carries an explicit delta:

$$
\Delta_C=
(\Delta S,
 \Delta V,
 \Delta R,
 \Delta D,
 \Delta F).
$$

For v0.9 $\to$ v0.10:

- CoreNorm state changed: **false**;
- verification cases: $80\to98$;
- added reopening conditions:
  - `REOPEN-FDT-FAMILY`;
  - `REOPEN-PRIMITIVE`;
  - `REOPEN-ROUTE`;
  - `REOPEN-SEMANTIC`;
  - `REOPEN-SUBSTRATE`;
- debt:
  - `DEBT-ART-01`: deferred $\to$ resolved;
  - `DEBT-FDT-COMPLETE-01`: introduced as deferred;
  - `DEBT-UPSTREAM-01`: unchanged;
- frontier:
  - `FRONTIER-ART-01`: retired;
  - `FRONTIER-FDT-COMPLETE-01`: introduced.

This makes epistemic/closure change observable even when the program state is unchanged.

## 6. Hashing and snapshots

Artifact nodes retain the authoritative external artifact hash.

Debt/frontier snapshots receive a v0.11 snapshot hash over:

$$
(kind, owner\ PEC, logical\ key, record).
$$

Therefore changing a debt/frontier record without changing its snapshot hash is detected.

The entire graph is hashed as:

$$
H_G=
SHA256(
\texttt{NOVA-CLOSURE-EVOLUTION-GRAPH-v0.11}\;||\;Canon(\mathcal G_C)
).
$$

## 7. Causal and branch consistency

A valid graph must satisfy:

$$
\boxed{\operatorname{DAG}(\mathcal G_C)}
$$

and every closure episode must contain the causal spine:

$$
PEC_p\to ART\to RePEC\to PEC_c,
$$

plus the direct parent relation:

$$
PEC_p\to RePEC.
$$

Additional invariants:

1. every edge endpoint exists;
2. every edge obeys its source/target type rule;
3. every non-root node is reachable from the root PEC;
4. a child PEC has at most one lineage-producing closure episode in v0.11;
5. parent and child PEC hashes differ;
6. episode IDs are content-derived;
7. overwrite lineage actions are rejected;
8. PEC parent-child lineage is acyclic;
9. terminal completeness cannot be asserted by the graph.

## 8. Branch tips

For episode relation $P\to C$, graph tips are:

$$
Tips(\mathcal G)=Children-Parents.
$$

The current tip is the v0.10 hardened PEC.

The data model is intentionally branch-capable. A future parent PEC may generate more than one child episode, while each child has a unique producer under the v0.11 rule.

## 9. Extension

`extend_closure_evolution_graph()` appends a new closure episode without rebuilding or overwriting prior lineage.

The extension parent must already exist in the graph. New nodes/edges are deduplicated by deterministic identity, and conflicts are rejected.

Thus future history can be represented as:

$$
PEC_0
\rightarrow ART_0\rightarrow RePEC_1\rightarrow PEC_1
\rightarrow ART_1\rightarrow RePEC_2\rightarrow PEC_2
\rightarrow\cdots
$$

or as a branch where multiple future experiments reopen one certified parent under different regimes.

## 10. Replay

The graph supports:

$$
Build\to Encode\to Decode\to Validate\to Replay.
$$

`replay_closure_evolution_graph()` reconstructs the graph from the authoritative v0.9 PEC, v0.10 ART/FDT report, and v0.10 Re-PEC and requires both canonical record equality and graph-hash equality.

## 11. Tamper/failure conditions

v0.11 explicitly rejects:

- envelope/hash tampering;
- debt/frontier snapshot mutation without hash update;
- missing edge endpoints;
- relation type violations;
- causal cycles;
- PEC-lineage cycles;
- detached nodes;
- episode-ID mutation;
- parent/report/child reference mismatch;
- overwrite lineage action;
- multiple producers for one child PEC;
- extension from a parent absent from the graph;
- terminal completeness claim.

## 12. Current bounded result

The canonical v0.9 $\to$ v0.10 graph has:

```text
20 nodes
30 edges
1 closure episode
```

Node counts:

```text
PEC                2
ART/FDT            1
Re-PEC             1
CoreNorm state     1
Debt snapshots     5
Frontier snapshots 10
```

Both PEC certificates point to the same CoreNorm state node.

This proves only that the **closure knowledge changed while the bounded normalized program state remained constant** in this episode.

It does not prove that the program state can never change in future closure episodes.

## 13. Claim boundary

v0.11 claims:

$$
\boxed{
\text{machine-verifiable causal lineage for the declared closure artifacts}
}
$$

It does **not** claim:

- complete history of all possible NOVA experiments;
- global semantic completeness;
- complete ART/FDT family coverage;
- terminal closure;
- that every future closure episode must preserve CoreNorm state.

The correct interpretation is:

$$
\boxed{
\text{Closure is now an evolving graph object, not a terminal file.}
}
$$

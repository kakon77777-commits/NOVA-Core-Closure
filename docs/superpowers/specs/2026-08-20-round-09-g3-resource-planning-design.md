# Round 09 — G3 Verifiable Memory & Resource Planning Design

## Status

Approved implementation design for NOVA Core Closure Round 09.

## Goal

Seal G3 by making memory/resource planning a versioned, deterministic, independently verifiable program artifact rather than an opaque backend heuristic.

The target boundary is:

$$
\boxed{
\text{Graph}
\rightarrow
\text{Resource Facts}
\rightarrow
\text{MemoryPlan Candidate}
\rightarrow
\text{Independent Verification}
\rightarrow
\text{Safe / Conditional / Fallback}
}
$$

A planner or AI may propose a plan. It may not declare the plan safe.

## Non-goals

Round 09 does not implement:

- a native malloc/free allocator;
- GPU kernel compilation;
- JIT memory code generation;
- arbitrary shared mutable memory;
- distributed memory;
- a learned AI planner;
- automatic mutation of canonical program semantics;
- G4 AI graph construction.

## 1. Resource ontology

Round 09 introduces runtime/compiler resource objects without changing the canonical Graph storage schema.

### Ownership states

The first implementation recognizes:

- `owned`;
- `borrowed_immutable`;
- `borrowed_mutable`;
- `shared_immutable`;
- `device_resident`;
- `moved`;
- `released`;
- `external_unmanaged`.

For normal pure G1/G2 graphs:

- graph inputs are borrowed immutable unless explicitly overridden;
- Parameters are borrowed immutable;
- Constants are shared immutable;
- produced tensor intermediates are owned;
- non-CPU produced tensors may be marked device resident;
- graph outputs remain live through graph exit.

### Lifetime

For each symbol $v$:

$$
L(v)=[t_{\mathrm{first}},t_{\mathrm{last}}].
$$

The planner uses the same deterministic dependency ordering as the reference interpreter.

Graph exit is a virtual step after the last node. A graph output's lifetime is extended through this exit step.

## 2. Tensor size and external facts

`TensorType` remains the authoritative static tensor contract when present.

External graph-input types may be provided through a `ResourceFacts` mapping. Missing or symbolic sizes are not guessed. They produce explicit runtime-size obligations.

Static byte size is:

$$
B(T)=\operatorname{sizeof}(\tau)\prod_i d_i
$$

only when every $d_i$ is concrete and the dtype size is known.

## 3. Physical buffer pool

A `MemoryPlan` binds owned tensor symbols to physical buffers.

A conservative plan assigns a distinct buffer to every allocatable symbol.

An optimized candidate may reuse a physical buffer only when all of the following hold:

1. prior symbol lifetime ends strictly before the next symbol begins;
2. device is equal;
3. dtype is equal;
4. layout is equal;
5. physical capacity is at least the requested static byte size;
6. neither symbol is marked non-reusable by a safety rule;
7. unknown-size values are not reused.

Because the first implementation models a statically reserved buffer pool, planned peak reserved bytes are the sum of unique physical buffer capacities. Safe reuse can therefore reduce planned peak reserved memory without pretending logical live bytes disappeared.

## 4. Device transfer planning

Each node has an execution device derived in order from:

1. explicit node `value_type.device` when it is a TensorType;
2. `attributes.device` when present;
3. CPU fallback.

If an input symbol's known device differs from the node execution device, the plan must contain a transfer before that node.

Transfers are explicit records:

```text
DeviceTransfer {
  symbol
  source_device
  target_device
  before_node
  reason
}
```

Redundant same-device transfers are verifier errors.

## 5. Candidate plans are untrusted

`MemoryPlan` contains:

- graph semantic hash;
- deterministic schedule;
- value lifetimes;
- buffer bindings;
- device transfers;
- obligations;
- planned peak reserved bytes;
- planner mode;
- proposer/provenance metadata;
- optional confidence.

The plan may originate from the deterministic planner, a human, or a future AI adapter.

The verifier does not trust:

- candidate schedule;
- candidate lifetimes;
- candidate peak bytes;
- candidate transfer claims;
- candidate buffer alias claims.

It recomputes each from the Graph plus ResourceFacts.

## 6. Verification states

Verification returns one of:

```text
safe
conditionally_safe
unsafe
```

`safe` means all relevant static obligations are proven.

`conditionally_safe` means the structural plan is safe but runtime guards remain, for example unknown symbolic buffer sizes.

`unsafe` means at least one invariant is violated.

Typed violations include:

- graph hash mismatch;
- schedule mismatch;
- lifetime mismatch;
- missing allocation;
- incompatible buffer alias;
- overlapping lifetime reuse;
- insufficient buffer capacity;
- device mismatch;
- missing transfer;
- redundant transfer;
- invalid peak accounting.

## 7. Conservative fallback

The final selection function is:

$$
\boxed{
\operatorname{Select}(G,P_c)
=
\begin{cases}
P_c,&\operatorname{Verify}(P_c)\in\{safe,conditionally\_safe\}\\
P_{safe},&\operatorname{Verify}(P_c)=unsafe
\end{cases}
}
$$

where $P_{safe}$ is independently regenerated in conservative mode.

Fallback must record:

- rejected candidate hash;
- rejected violations;
- selected plan hash;
- whether fallback was used.

## 8. AI boundary

Round 09 does not add a model call. It adds the contract future AI planners must obey.

An AI may submit a `MemoryPlan` candidate with proposer metadata. The deterministic verifier treats it exactly like any other untrusted external candidate.

This is the G3 meaning of "AI suggestion":

$$
\boxed{
\text{AI Candidate}
\neq
\text{Memory Safety Proof}
}
$$

## 9. API and CLI

Python API:

- `analyze_resources(graph, symbol_types=None)`;
- `plan_memory(graph, symbol_types=None, mode="optimized")`;
- `conservative_memory_plan(graph, symbol_types=None)`;
- `verify_memory_plan(graph, plan, symbol_types=None)`;
- `select_memory_plan(graph, candidate, symbol_types=None)`;
- `encode_memory_plan(plan)` / `decode_memory_plan(text)`.

CLI:

```text
nova resource-plan PROGRAM --module M --graph G [--types types.json] --mode optimized|conservative
nova resource-verify PROGRAM PLAN --module M --graph G [--types types.json]
nova resource-select PROGRAM PLAN --module M --graph G [--types types.json]
```

All commands emit machine-readable JSON.

## 10. G3 exit criteria

Round 09 seals G3 only if all of the following are demonstrated:

1. deterministic lifetime analysis;
2. exact static buffer-size accounting for concrete tensors;
3. conservative unique-buffer plan;
4. verified lifetime-based buffer reuse with lower reserved bytes in a sequential typed graph;
5. explicit CPU→device and device→CPU transfer planning;
6. malicious overlapping alias plan rejected;
7. missing transfer plan rejected;
8. unsafe external/AI candidate falls back to conservative plan;
9. symbolic dynamic size produces an explicit runtime obligation instead of guessed bytes;
10. existing G1/G2 execution, AD, training, interop, projection/editing, Notebook tests remain green.

## 11. Versioning

Round 09 runtime version becomes `0.9.0`.

Graph storage schema remains `0.1.0`; G3 introduces compiler/runtime resource artifacts and does not require a breaking canonical Graph schema migration.

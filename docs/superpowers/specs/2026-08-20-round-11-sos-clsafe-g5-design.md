# Round 11 — SOS / Cl-safe G5 Integration Design

**Status:** Approved implementation design derived from the already-approved Round 11 direction.  
**Date:** 2026-08-20  
**Target runtime version:** `0.11.0`  
**Graph storage schema:** remains `0.1.0`.

## 1. Goal

Round 11 implements the G5 integration boundary between NOVA Core and the Symbol-as-Operator System (SOS): a versioned `OperatorDescriptor`, deterministic operator closure composition, Cl-safe Runtime Validation Protocol (RVP), typed composition failures, explicit `BrokenOperator` isolation, depth limits, a small operator closure library, and lowering of safe unary closures into ordinary NOVA graphs.

The primary safety invariant is:

$$
\boxed{\text{SOS composition extends NOVA contracts; it does not replace NOVA validation.}}
$$

## 2. Source-derived requirements

The NOVA Unified Roadmap G5 requires:

- `OperatorDescriptor`;
- Sem / Comp / Projection slots;
- compose API;
- `BrokenOperator` isolation;
- RVP;
- depth limits;
- traceable failure;
- a basic operator closure library;
- validation of legal composition, Comp collapse, Sem divergence, projection inconsistency, effect conflict, and deep-chain damage propagation.

The Cl-safe specification defines safe composition by three core conditions:

$$
\text{Comp}_A \cap \text{Comp}_B \neq \emptyset,
$$

$$
\exists n \le K_S : (\text{Sem}_A \circ \text{Sem}_B)^n = (\text{Sem}_A \circ \text{Sem}_B)^{n+1},
$$

$$
\text{GCI}(G_A \otimes G_B)=\text{True}.
$$

The mandatory RVP order is:

$$
C \rightarrow G \rightarrow S,
$$

with typed failures `CompCollapseError`, `GIncoherenceError`, and `SemDivergenceError`. The source recommends $K_S=256$ for the first implementation and requires `BrokenOperator` to prevent silent propagation.

The Core Baseline reserves `OperatorDescriptor` and `CompositionValidator` as extension interfaces; their integration must not alter NOVA Core semantics.

## 3. Source gaps and Round 11 engineering decisions

The sources deliberately leave several implementation details open. Round 11 resolves only the minimum needed for a falsifiable executable baseline.

### 3.1 Projection slot as the NOVA-facing form of the SOS G slot

The original SOS documents use a geometric $G$ slot, while the newer NOVA integration uses `projection_slot`. Round 11 represents the minimum GCI data inside `ProjectionSlot`:

- connectivity;
- orientation;
- positive finite scale;
- canonical NOVA kind identity.

This is an integration mapping, not a claim that projection exhausts the full future SOS geometry ontology.

### 3.2 Finite-state semantic abstraction for RVP

General Sem safety is not statically decidable. Round 11 therefore models the executable RVP Sem slot as a finite deterministic state transition system:

```text
SemanticSlot {
  states
  transition
}
```

Composition forms the transition $f_A \circ f_B$. RVP compares successive whole-map powers, not a single sample trajectory, until either:

$$
f^n=f^{n+1}
$$

or $K_S=256$ is exhausted.

This finite-state model is an engineering test substrate for the source RVP definition, not a claim that all future semantic spaces are finite.

### 3.3 Depth limit

The source requires a depth limit but does not fix a value. Round 11 sets the default implementation limit to **32 members**. The value is versioned in `CompositionContext` and may change in later versions.

### 3.4 Effect integration

Effect conflict is a G5 acceptance requirement but is outside the original C/G/S triple. Round 11 treats it as a NOVA integration safety check after the core RVP succeeds. The context may specify allowed effects and forbidden effect pairs. This does not replace NOVA effect semantics.

## 4. Core types

### 4.1 OperatorDescriptor

```text
OperatorDescriptor {
  operator_id
  nova_kind
  semantic_slot
  composition_slot
  projection_slot
  state_schema
  effect_schema
  version
}
```

Descriptors are immutable, deterministically serializable, and content-hashable.

### 4.2 CompositionSlot

```text
CompositionSlot {
  contexts
  input_arity
  output_arity
}
```

Round 11 closure lowering is intentionally restricted to single-output unary chains. The registry may hold other descriptors, but lowering rejects unsupported arity instead of guessing a graph topology.

### 4.3 ProjectionSlot

```text
ProjectionSlot {
  canonical_kind
  connected
  orientation
  scale
}
```

Minimum GCI checks:

1. both operands are connected;
2. non-neutral orientations agree;
3. composed scale is finite, positive, and within `max_scale`;
4. each projection's canonical kind matches its descriptor's NOVA kind.

### 4.4 SemanticSlot

A finite total transition map over a shared ordered state space. Descriptor validation rejects transitions outside the declared state space.

### 4.5 CompositionContext

```text
CompositionContext {
  k_s = 256
  max_depth = 32
  max_scale
  allowed_effects
  forbidden_effect_pairs
}
```

## 5. RVP

`validate_composition(left, right, context)` performs:

1. broken/depth guards;
2. **C** — Comp intersection;
3. **G** — minimum GCI;
4. **S** — bounded whole-map fixed-point iteration;
5. NOVA integration effect policy.

Every check emits ordered evidence. A failure is never reduced to a boolean.

### 5.1 Failure types

- `CompCollapseError`
- `GIncoherenceError`
- `SemDivergenceError`
- `EffectCompositionError`
- `CompositionDepthError`
- `BrokenOperatorPropagationError`
- `OperatorDescriptorError`

All extend NOVA's typed error model.

## 6. Composition results

### 6.1 Strict mode

`compose(..., strict=True)` raises the typed error returned by the first failing check.

### 6.2 Diagnostic mode

`compose(..., strict=False)` returns an immutable `BrokenOperator` containing:

- left/right operator identities;
- failed check;
- full composition report;
- original typed error payload.

Any later attempt to compose a `BrokenOperator` fails immediately and does not run downstream checks.

### 6.3 Safe closure

A successful composition returns `OperatorClosure` containing:

- ordered member descriptors;
- depth;
- composed Sem/Comp/Projection slots;
- merged state/effect schemas;
- RVP evidence;
- deterministic closure hash.

## 7. Basic operator library

Round 11 ships a small pure unary closure library mapped to existing NOVA kinds:

- `Identity`
- `Negate`
- `ReLU`
- `Sigmoid`
- `Tanh`
- `Softmax`

The library exists to validate the SOS/NOVA integration path, not to freeze the future complete SOS symbol universe.

## 8. NOVA lowering

`lower_closure_to_graph(...)` is restricted to safe unary closures from the basic library. It emits ordinary NOVA nodes using their existing `nova_kind` values and then calls the existing NOVA project validator.

Therefore:

$$
\boxed{\text{SOS Safe} \not\Rightarrow \text{skip NOVA validation}.}
$$

The generated graph remains ordinary NOVA and can run through the existing Interpreter/NumPy backend.

## 9. API / CLI

Python API:

- registry lookup/list;
- `compose_operator_ids(...)`;
- `validate_operator_ids(...)`;
- `lower_operator_ids(...)`.

CLI:

```text
nova sos list
nova sos validate <ids...>
nova sos compose <ids...>
nova sos lower <ids...>
```

Outputs are JSON audit/evidence records.

## 10. G5 acceptance matrix

Round 11 must demonstrate, with executable tests and release smoke evidence:

1. legal composition;
2. Comp collapse;
3. G/projection incoherence;
4. Sem divergence at bounded $K_S$;
5. effect policy conflict;
6. strict typed failure;
7. diagnostic `BrokenOperator` creation;
8. broken-operator downstream propagation prevention;
9. depth-limit rejection;
10. deterministic closure hashing;
11. safe closure lowering to a normal NOVA graph;
12. Interpreter and NumPy execution equivalence of a lowered closure;
13. original NOVA graph/hash semantics remain unchanged.

## 11. Deferred intentionally

Not part of Round 11:

- full future SOS geometry tensor algebra;
- arbitrary user-defined semantic executors;
- hardware Cl-check primitive;
- learned semantic convergence models;
- complete effect algebra;
- general multi-input closure lowering;
- G6 execution-paradigm planning;
- G7 ISQL integration;
- G8 ProgramHandle control.

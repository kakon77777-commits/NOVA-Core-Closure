# NOVA Core Closure Round 03 — Executable Closure Design

## Status

Approved implementation design for Round 03.

## Goal

Make NOVA canonical graphs executable without changing their identity model or delegating semantics to a text language.

Round 03 establishes:

$$
\boxed{
\text{Canonical Graph}
\rightarrow
\text{Validated Execution Plan}
\rightarrow
\text{Reference Result}
}
$$

The reference interpreter is the semantic anchor. The NumPy CPU backend is an alternative implementation that must agree with the interpreter for supported operations.

## Scope

Round 03 implements only:

1. runtime values and parameter/input binding;
2. pure operation execution;
3. `if`;
4. bounded loops;
5. graph/function execution order;
6. reference interpreter;
7. NumPy CPU backend;
8. structured-text projection;
9. formula projection for the supported mathematical subset;
10. CLI;
11. Python API interoperability;
12. differential tests between interpreter and NumPy backend.

Round 03 does not implement reverse-mode AD, optimizer passes, GPU lowering, general effects, memory planning, general recursion, async execution, or distributed runtime.

## Core invariants

### E1 — Structure remains authoritative

Execution consumes a validated NOVA graph. Text is never parsed as the authoritative runtime source.

### E2 — Interpreter is the semantic oracle

For every supported pure graph $G$ and input environment $x$:

$$
\operatorname{Run}_{\mathrm{interp}}(G,x)
$$

is the reference meaning of the supported executable subset.

A backend is accepted only if:

$$
\operatorname{Run}_{b}(G,x)
\simeq
\operatorname{Run}_{\mathrm{interp}}(G,x)
$$

under the declared numeric tolerance.

### E3 — Execution must not mutate the canonical graph

Running a graph cannot change its semantic hash.

### E4 — No silent missing values

Missing graph inputs, parameters, operator implementations, or unresolved execution dependencies produce structured runtime errors.

### E5 — Bounded control only

Round 03 supports finite control structures only. Loops must have an explicit finite trip count or finite iteration collection.

### E6 — Unknown shapes remain obligations

Runtime execution may discharge a runtime shape guard, but it may not reinterpret an unresolved static shape obligation as automatically safe.

## Runtime value model

Runtime values are ordinary Python scalar values or NumPy arrays at the implementation boundary, but they are checked against NOVA `TensorType` where a type is present.

A runtime environment is:

```text
Environment {
  value_name -> runtime_value
}
```

Graph inputs are resolved from the environment. `Parameter` nodes may resolve from a parameter environment or an embedded constant value.

## Supported node kinds

The initial executable subset is intentionally narrow:

```text
Input
Parameter
Constant
Identity
Add
Subtract
Multiply
Divide
Negate
MatMul
Reshape
Transpose
ReduceSum
Mean
Relu
Sigmoid
Tanh
Softmax
If
BoundedLoop
Call
```

Unsupported kinds return a typed `RuntimeError` / `BackendError`; they are never ignored.

## Execution order

Round 03 uses dependency-driven topological execution for acyclic dataflow subgraphs. Cycles are not interpreted as implicit loops.

`BoundedLoop` is an explicit control node with finite iteration count and an embedded body graph reference or body specification.

`If` chooses between explicitly referenced branch graphs or branch values.

## Interpreter

The interpreter:

1. validates the project/graph;
2. binds inputs/parameters;
3. checks runtime tensor shape compatibility when types are present;
4. executes ready nodes in deterministic order;
5. records a lightweight execution trace;
6. returns named graph outputs.

The trace records node id, kind, input names, output names, and result shape/type metadata. It does not become part of canonical program identity.

## NumPy CPU backend

The NumPy backend supports the same Round 03 pure operation subset.

It may use vectorized NumPy implementations, but no backend-specific rule may redefine NOVA semantics.

Backend differential tests compare results against the reference interpreter.

## Projection

### Structured text

Projection is generated from canonical graph structure. It is not authoritative source.

A minimal projection may resemble:

```text
module linear
input X: Tensor[f32; B,I]
param W: Tensor[f32; I,O]
param b: Tensor[f32; O]
Y = add(matmul(X, W), b)
return Y
```

### Formula

For supported mathematical graphs, emit deterministic formulas such as:

$$
Y = XW + b.
$$

If a graph cannot be faithfully projected to the formula subset, the formula projector must return an explicit unsupported result rather than inventing notation.

## CLI

Round 03 adds:

```text
nova check <graph.json>
nova run <graph.json> --inputs <inputs.json>
nova hash <graph.json>
nova project <graph.json> --view text|formula
```

CLI JSON output is deterministic where practical and errors are structured.

## Python interop

Public API:

```python
load_project(...)
run_project(...)
run_graph(...)
project_text(...)
project_formula(...)
```

The Python API accepts canonical NOVA objects directly, preserving structure-first semantics.

## Validation cases

Round 03 exit cases:

1. $Y=XW+b$;
2. elementwise pure arithmetic;
3. a small `if` graph;
4. a finite bounded loop;
5. interpreter versus NumPy equivalence;
6. runtime shape rejection;
7. missing input rejection;
8. unsupported node rejection;
9. execution does not change semantic hash;
10. CLI run/check/hash/project smoke.

## Round boundary

Round 04 will add language-level reverse-mode automatic differentiation on top of this executable subset. Round 03 must not use an external autograd engine to pretend that AD is already implemented.

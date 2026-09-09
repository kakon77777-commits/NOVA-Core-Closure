# Round 03 — Executable Closure

## Status

**Implemented.**

Round 03 makes the NOVA canonical graph executable for a bounded pure subset without changing the structure-first authority model.

The core relation is now:

$$
\boxed{
\text{Canonical Graph}
\rightarrow
\text{Reference Interpreter}
\rightarrow
\text{Runtime Result}
}
$$

with a NumPy CPU backend required to agree with the reference interpreter for supported operations.

## Implemented runtime layer

- immutable execution environments;
- runtime tensor shape guards;
- typed runtime errors;
- deterministic dependency scheduling;
- immutable execution traces;
- `Input`, `Parameter`, `Constant`, `Identity`;
- arithmetic operators;
- `MatMul`;
- `Reshape` and `Transpose`;
- `ReduceSum` and `Mean`;
- `Relu`, `Sigmoid`, `Tanh`, `Softmax`;
- scalar `If`;
- explicit finite `BoundedLoop`;
- pure graph `Call`;
- NumPy CPU backend;
- structured-text projection;
- formula projection for the supported mathematical subset;
- Python API;
- CLI `check`, `run`, `hash`, and `project`.

## Runtime identity invariant

Execution is derived state and does not mutate program identity:

$$
H_{\mathrm{sem}}(G_{\mathrm{before}})
=
H_{\mathrm{sem}}(G_{\mathrm{after}}).
$$

Round 03 also extends semantic hashing to support an individual `Graph` in addition to a complete `Project`, using the same existing canonical graph record.

## Control-flow boundary

Round 03 does not infer loops from graph cycles. Cyclic dependencies remain runtime errors.

A loop must be represented by an explicit bounded control node with a finite trip count.

This is intentional:

$$
\boxed{
\text{Graph Cycle}
\neq
\text{Implicit Loop}
}
$$

## Backend boundary

The reference interpreter is the semantic anchor.

The NumPy backend is accepted only through differential agreement on the supported subset:

$$
\operatorname{Run}_{\mathrm{NumPy}}(G,x)
\simeq
\operatorname{Run}_{\mathrm{Interpreter}}(G,x).
$$

NumPy is an implementation backend, not the source of NOVA semantics.

## Projection boundary

Structured text and mathematical formulas are generated from the canonical graph.

They remain projections, not authoritative source files.

Formula projection refuses control structures or node kinds outside its supported subset rather than inventing misleading notation.

## CLI

Examples:

```text
nova check examples/executable_linear.json
nova hash examples/executable_linear.json
nova run examples/executable_linear.json --module app --graph main --inputs examples/executable_inputs.json --backend numpy
nova project examples/executable_linear.json --module app --graph main --view text
nova project examples/executable_linear.json --module app --graph main --view formula
```

## Explicit non-goals

Round 03 does not implement:

- reverse-mode automatic differentiation;
- optimizer passes;
- GPU lowering;
- general effects;
- memory planning;
- recursion;
- async execution;
- distributed runtime.

Those remain later closure stages.

## Next

**Round 04 — Reverse-Mode Automatic Differentiation** will turn differentiation into an explicit NOVA graph transformation and validate gradients against finite differences without delegating language semantics to an external autograd engine.

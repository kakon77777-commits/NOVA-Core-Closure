# NOVA Core Closure — Round 04 Validation

**Round:** 04 — Reverse-Mode Automatic Differentiation  
**Date:** 2026-08-20  
**Core version:** `0.4.0`  
**Graph schema version:** `0.1.0`  
**Source freeze commit:** `1c2884cb0ee5f46de77a1ee832f7242250b19004`

## 1. Scope validated

Round 04 validates language-level reverse-mode AD as an explicit NOVA graph transformation:

$$
G
\xrightarrow{\mathcal D_{\mathrm{rev}}}
G_{\nabla}.
$$

Validated capabilities:

- deterministic `DifferentiationRequest`;
- deterministic derivative graph identity and semantic hash;
- scalar `grad` and explicit-seed VJP;
- VJP rule registry;
- explicit fan-out gradient accumulation;
- broadcast-aware cotangent reduction;
- MatMul, reshape, transpose, ReduceSum, Mean, ReLU, Sigmoid, Tanh and Softmax reverse rules;
- explicit `StopGradient` barrier;
- typed `DiffError` for unsupported, non-differentiable and unknown paths;
- derivative graph execution by the reference Interpreter and NumPy backend;
- central finite-difference verification;
- Python API, projections and `nova grad` CLI.

Finite differences are used only for validation; they do not implement NOVA AD.

## 2. Full regression suite

Command:

```text
PYTHONPATH=src python -m pytest -q
```

Result:

```text
125 collected
125 passed
```

The inherited Round 01–03 regression suite and all new Round 04 tests pass together.

## 3. Compiler / syntax gate

Command:

```text
python -W error -m compileall -q src
```

Result: **PASS**.

All Python syntax warnings are treated as errors for this gate.

## 4. Real CLI executable example

Program:

```text
examples/differentiable_linear.json
```

Inputs:

```text
examples/differentiable_inputs.json
```

Parameters:

```text
examples/differentiable_parameters.json
```

Primal execution:

```json
{"loss": 1.125}
```

Reverse-mode request:

```text
target = loss
wrt = W, b
```

Analytic NOVA derivative graph output:

```json
{
  "W": [[1.5], [3.0]],
  "b": [1.5]
}
```

Primal semantic hash:

```text
sha256:046a434ef4557c572299c934733e55e0c0cb43d44790d63d379b7a80f37cf6e9
```

Derivative graph ID:

```text
main__rev__loss__f7b8516d6db2
```

Derivative semantic hash:

```text
sha256:6ea40692f2b686580e1e1c7af12dd0f943bd0e9059bf64d6e4125be647efd7e6
```

## 5. Finite-difference falsification check

Central finite-difference settings:

```text
epsilon = 1e-6
rtol = 1e-5
atol = 1e-7
```

Results:

```text
W max_abs_error = 1.5419345800182782e-09
W max_rel_error = 1.0279563856221579e-09
b max_abs_error = 1.1226006790820975e-09
b max_rel_error = 7.484004532815015e-10
passed = true
```

The analytic derivative graph therefore survives the numeric counter-check for the release example.

## 6. Identity and determinism

Tests verify:

$$
H_{\mathrm{sem}}(G_{\mathrm{before}})
=
H_{\mathrm{sem}}(G_{\mathrm{after}})
$$

for differentiation of the primal graph.

Repeated transformation of the same primal graph with the same differentiation request yields the same derivative semantic hash.

Derivative graph construction is additive: it creates a new canonical graph object and does not mutate the primal object.

## 7. Projection validation

The derivative graph can be projected to structured text and formula views.

A regression test also verifies that composite operands are parenthesized when required, preventing formula projection from changing apparent operator precedence.

## 8. Source hygiene gate

Tracked files: **64**.

Results:

```text
non_utf8 = 0
secret_hits = 0
unicode_escape_patterns = 0
hidden_control_characters = 0
alternate_markdown_math_delimiters = 0
invalid_json = 0
git_diff_check = PASS
```

Markdown formal math uses only `$...$` and `$$...$$` delimiters.

## 9. Release manifest

`CHECKSUMS.sha256` contains SHA-256 entries for every tracked release file except the manifest itself.

Expected manifest entries: **63**.

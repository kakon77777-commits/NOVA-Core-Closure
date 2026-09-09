# NOVA Core Closure Round 11 Validation

**Round:** 11 — G5 SOS / Cl-safe Integration Final Seal  
**Version:** 0.11.0  
**Schema:** 0.1.0  
**Date:** 2026-08-20  
**Delivery mode:** local ZIP only; GitHub not modified

## Functional verification

Fresh pre-release evidence:

- Full regression suite: **320 tests collected and passed**.
- Python warnings-as-errors compile: PASS.
- `git diff --check`: PASS.
- Basic deterministic operator registry: `identity`, `negate`, `relu`, `sigmoid`, `softmax`, `tanh`.
- Legal closure `relu ∘ tanh ∘ negate`: PASS.
- Legal closure hash: `sha256:556b98204c184edc8899073cbe57f8f5b7bbcbc83582572447755a2d6a3935b1`.
- Core RVP order: `C → G → S`; NOVA effect integration check follows as `EFFECT`.
- Default semantic RVP bound: `$K_S=256$`.
- Default composition depth limit: `32`.
- Comp collapse: typed `CompCollapseError` PASS.
- Sem two-cycle divergence: typed `SemDivergenceError` PASS.
- Projection/GCI inconsistency: typed `GIncoherenceError` PASS.
- Effect conflict: typed `EffectCompositionError` PASS.
- BrokenOperator diagnostic isolation: PASS.
- Deep-chain propagation prevention / depth error: PASS.
- Safe closure lowering: `relu ∘ tanh` lowers to ordinary NOVA `Tanh → Relu` nodes.
- Interpreter / NumPy lowering equivalence: max absolute error `0.0`.
- CLI `nova sos list`: PASS.
- CLI `nova sos validate relu tanh`: PASS.
- CLI `nova sos compose relu tanh`: PASS.
- CLI `nova sos lower relu tanh`: PASS.
- CLI depth-limit failure returns nonzero with `CompositionDepthError`: PASS.

## G5 final seal

Verified capabilities:

1. immutable, deterministic `OperatorDescriptor` contracts;
2. Sem / Comp / Projection / state / effect / version slots;
3. deterministic basic operator closure registry;
4. source-ordered Cl-safe RVP checks;
5. typed composition failure classes;
6. minimum GCI validation for connectivity, orientation consistency, and bounded scale;
7. bounded whole-map semantic fixed-point validation;
8. explicit effect-policy integration after the core RVP;
9. strict composition and diagnostic `BrokenOperator` mode;
10. BrokenOperator downstream isolation;
11. explicit composition depth limit;
12. deterministic `OperatorClosure` identity;
13. lowering of safe unary closures to ordinary existing NOVA graph nodes;
14. Python API and CLI surfaces;
15. machine-readable G5 acceptance examples and seal.

**G5 SOS / Cl-safe Integration: SEALED.**

## Source hygiene

Fresh scan over tracked files before release metadata finalization:

- tracked files: 175;
- UTF-8 decode failures: 0;
- probable secret hits: 0;
- literal Unicode escape patterns: 0;
- hidden control characters: 0;
- alternate Markdown math delimiters: 0;
- invalid JSON files: 0;
- git working tree before metadata: clean.

## Deferred intentionally

Not part of Round 11 / G5 seal:

- full original SOS geometric language beyond the minimum executable GCI prototype;
- unbounded or complete static proof of Sem safety;
- hardware `Cl-check` primitive;
- arbitrary multi-input SOS closure lowering;
- G6 execution-paradigm planner;
- G7 ISQL semantic-tensor interface;
- G8 ProgramHandle / minimal sufficient control.

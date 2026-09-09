# NOVA Core Closure Round 12 Validation

**Round:** 12 — G6 Explicit Execution-Paradigm Planner Final Seal
**Version:** 0.12.0
**Schema:** 0.1.0
**Date:** 2026-08-20
**Delivery mode:** local ZIP only; GitHub not modified

## Functional verification

Fresh pre-release evidence:

- Full regression suite: **351 tests collected and passed**.
- Python warnings-as-errors compile: PASS.
- `git diff --check`: PASS.
- Sixteenfold domain: all 16 tags in `{C,D} × {C,J,P,R} × {C,D}` are represented.
- Dense tensor example: selected `DPD` / fill `P`, default total cost `22.5`.
- Sparse selective-access example: selected `DJD` / fill `J`, total cost `47.0`.
- Sequential bounded-loop example: selected `DCD` / fill `C`, total cost `100.0`.
- Stable precomputed recognition example: selected `DRD` / fill `R`.
  - online work: `0.0`
  - precompute: `4.0`
  - storage: `4.0`
  - maintenance: `4.0`
  - risk: `1.0`
  - total cost: `13.0`
- Recognition therefore does not erase offline cost: PASS.
- Bond rule `DRD → DPD`: rejected with both `recognition_terminal` and `fill_monotonicity` violations.
- Explicit stability reset `DRD → DCD --reset-after 0`: accepted with `stability_reset` obligation.
- Space conversion model:
  - `C → D` relative conversion cost: `1.0`;
  - `D → C` relative conversion cost: `10.0` plus `reconstruction_assumption` obligation.
- Illegal ranked mixed chain falls back deterministically to a conservative legal chain: PASS.
- Same dense graph under fast profile selected `P` with total cost `9.85`.
- Same dense graph under constrained profile selected conservative `C` with total cost `100.0`.
- Profile changes plan ranking without changing canonical graph identity: PASS.
- CLI `nova paradigm classify`: covered by regression suite.
- CLI `nova paradigm plan`: real dense/sparse/sequential/recognition smoke PASS.
- CLI `nova paradigm validate-bonds`: illegal and reset cases PASS with expected return codes.

## G6 final seal

Verified capabilities:

1. complete deterministic P1–P16 paradigm registry;
2. explicit base-space, fill-mode, and observation axes;
3. evidence-bearing strategy-region classification;
4. conservative sequential fallback always available;
5. recognition candidate requires explicit stable/precomputed evidence;
6. explicit `CostBreakdown` for online work, random access, synchronization, precompute, storage, maintenance, conversion, and risk;
7. profile-sensitive candidate ranking without mutation of the canonical graph;
8. fill-complexity bonding monotonicity `C → J → P → R`;
9. asymmetric continuous/discrete conversion obligations;
10. stable recognition as terminal state unless an explicit stability reset begins a new chain segment;
11. deterministic illegal-chain fallback;
12. deterministic plan hashing;
13. Python project API and CLI surfaces;
14. machine-readable G6 acceptance examples and seal;
15. no claim of global optimum or zero total cost for recognition.

**G6 Explicit Execution-Paradigm Planner: SEALED.**

## Source hygiene

Fresh scan over tracked files before release metadata finalization:

- tracked files: 195;
- UTF-8 decode failures: 0;
- probable secret hits: 0;
- literal Unicode escape patterns: 0;
- hidden control characters: 0;
- alternate Markdown math delimiters: 0;
- invalid JSON files: 0;
- git working tree before metadata: clean.

## Deferred intentionally

Not part of Round 12 / G6 seal:

- learned or model-driven paradigm classifier;
- claim of globally optimal strategy selection;
- hardware-specific code generation or execution-strategy enforcement;
- automatic creation of recognition structures without explicit evidence;
- G7 ISQL semantic-tensor interface;
- G8 ProgramHandle / minimal-control execution.

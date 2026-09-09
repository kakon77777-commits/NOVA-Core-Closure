# G6 Verification Matrix — Explicit Execution-Paradigm Planner

**Runtime:** NOVA Core Closure 0.12.0  
**Schema:** 0.1.0  
**Gate:** G6  
**Status:** SEALED by executable evidence

## Authority boundary

The planner classifies and ranks execution-strategy candidates. It does not replace NOVA graph/type/shape/effect/resource semantics and does not claim global optimality.

## Acceptance matrix

| Requirement | Evidence | Result |
|---|---|---|
| Sixteenfold domain | 16 unique `{C,D} × {C,J,P,R} × {C,D}` tags, P1–P16 | PASS |
| Dense tensor | `examples/paradigm/dense_parallel.json` selects `DPD`, cost 22.5 | PASS |
| Sparse/selective | `examples/paradigm/sparse_jump.json` selects `DJD`, cost 47.0 | PASS |
| Sequential dependency | `examples/paradigm/sequential_loop.json` selects `DCD`, cost 100.0 | PASS |
| Stable recognition | explicit stable+precomputed evidence selects `DRD`; online work 0, total cost 13.0 | PASS |
| R offline accounting | precompute=4, storage=4, maintenance=4, risk=1 | PASS |
| Fill monotonicity | `C → J → P → R` legal; reverse complexity increase rejected | PASS |
| R terminality | `DRD → DPD` rejected under stable conditions | PASS |
| Stability reset | `DRD → DCD` accepted only with explicit reset boundary | PASS |
| Space conversion | C→D cost=1; D→C cost=10 + reconstruction assumption | PASS |
| Profile evidence | same dense graph: fast profile selects DPD, constrained profile selects DCD | PASS |
| Semantic identity | profile change leaves graph semantic hash unchanged | PASS |
| Fallback | mixed `DPD → DCD` ranked chain is illegal; planner selects deterministic `DCD → DCD` fallback | PASS |
| Determinism | repeated same graph/profile produces identical plan hash | PASS |

## Observed plan hashes

- dense parallel: `sha256:b696a98ac7d8e38d9174ac38833dd9e91b1b30a15693f0fe7cc7df3a6c3bd571`
- sparse jump: `sha256:69da83b5ab0dc6a6aa89132039b03f3e13ba6b88e53682e44db68255521b4af5`
- sequential: `sha256:ecc6ca37922c840028e056f184a3db08932fc70d399fdf5589d08075212d68fa`
- stable recognition: `sha256:4af28bfcad2df8e8df452364513366ceb8dc297a06fdbcd378d85a417615f639`
- illegal-chain conservative fallback: `sha256:bf7b8983caeb099380a908c19c2b3de76085b154f5ca33290a90d50f7d55d552`

## Interpretation boundary

The cost values are deterministic relative planning units, not physical timing predictions. `R` represents zero online fill only in the theoretical fill-axis sense; the planner explicitly carries offline precompute, storage, maintenance, and risk cost. A lower candidate cost is not a correctness proof and does not authorize semantic replacement.

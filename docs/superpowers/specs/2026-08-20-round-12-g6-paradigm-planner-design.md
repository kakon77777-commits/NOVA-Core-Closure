# Round 12 — G6 Explicit Execution-Paradigm Planner Design

## Status
Approved continuation of the NOVA Unified Roadmap G6 gate. This design extends NOVA through a versioned strategy interface and does not modify Core graph/type/shape/effect semantics.

## Goal
Implement a deterministic, inspectable planner that classifies NOVA computation regions in the sixteenfold paradigm space and ranks legal execution-strategy candidates under explicit bonding rules and cost evidence.

## Canonical paradigm space
A paradigm is a triple:

$$
(a,b,c)\in\{C,D\}\times\{C,J,P,R\}\times\{C,D\}.
$$

Axis 1 is base-space continuity/discreteness. Axis 2 is fill mode: sequential-continuous `C`, jump `J`, parallel-simultaneous `P`, recognition/zero-fill `R`. Axis 3 is observation continuity/discreteness. The implementation exposes all sixteen triples and the historical P1–P16 names.

## Authority boundary
- NOVA Core remains authoritative for graph, type, shape, effect, differentiation, memory/resource, and backend legality.
- The G6 classifier describes computational strategy evidence. It does not override Core semantics.
- The G6 planner ranks only candidates that have explicit preconditions and pass bonding validation.
- A low cost is not a proof of semantic equivalence or global optimality.

## Region model
The planner operates on explicit `StrategyRegion` objects derived from graph nodes. It recognizes a conservative set of evidence:

1. `sequential_dependency`: bounded loops or explicitly ordered/stateful regions → fill `C` candidate.
2. `sparse_or_selective_access`: gather/index/lookup-like regions or explicit sparse/selective hint → fill `J` candidate.
3. `parallel_independent`: dense elementwise/tensor regions without ordering/effect constraints → fill `P` candidate.
4. `stable_recognition`: explicit stable-cache/precomputed-recognition evidence → fill `R` candidate.

Unknown regions always retain a sequential fallback candidate. Recognition is never inferred merely because a model has parameters.

Base-space and observation axes use explicit graph/node evidence first; absent evidence, NOVA program graphs default conservatively to discrete `D` because the authoritative object is a finite typed graph and runtime outputs are discrete tensor objects unless a continuous projection contract is explicitly attached.

## Strategy candidate
Each `ExecutionStrategyCandidate` contains:
- region id;
- `ParadigmTag`;
- preconditions;
- evidence strings;
- deterministic `CostBreakdown`;
- fallback tag;
- confidence class (`proven`, `supported`, `fallback`), never a probabilistic correctness claim.

## Cost model
The planner exposes a deterministic relative cost model, not a hardware benchmark predictor. Components:

- `online_work`;
- `random_access`;
- `parallel_sync`;
- `precompute`;
- `storage`;
- `maintenance`;
- `space_conversion`;
- `risk_penalty`.

`R` may have low online work only when stable-recognition evidence exists, while retaining precompute/storage/maintenance costs. Therefore `O(0)` online fill is never represented as zero total cost.

## Bonding rules
A chain of selected paradigms is validated by three rules from the paradigm-bonding supplement:

1. Fill complexity is monotonically non-increasing: `C → J → P → R`, with equal steps allowed.
2. Base-space transitions are costed asymmetrically: `C → D` is relatively cheap but marked lossy; `D → C` is expensive and creates a reconstruction-assumption obligation.
3. `R` is terminal under stable conditions. A later fill step is legal only across an explicit `stability_reset` boundary, which starts a new chain segment.

The planner returns typed `BondViolation` / obligations rather than silently rewriting an illegal chain.

## Planning workflow

```text
Graph
→ extract StrategyRegions
→ classify candidate paradigms
→ compute explicit relative cost evidence
→ rank candidates per region
→ validate paradigm bonds
→ if chain invalid, choose deterministic conservative fallback chain
→ ExecutionStrategyPlan
```

Fallback is always available: a discrete sequential strategy for regions that cannot be proven eligible for J/P/R.

## Profile evidence
`PlannerProfile` allows deterministic environment evidence such as:
- available parallelism;
- random-access cost weight;
- synchronization cost weight;
- precompute/storage/maintenance budgets;
- recognition enabled/disabled;
- stable-cache evidence;
- conversion cost weights.

A profile changes ranking, not program semantics. Same graph + same profile must produce the same plan hash.

## Acceptance scenarios
Round 12 must demonstrate four distinct fill choices:
1. dense independent tensor region → `P` candidate selected;
2. sparse/selective lookup region → `J` candidate selected;
3. sequential bounded-loop region → `C` selected;
4. explicitly stable cached-recognition region → `R` selected.

It must also demonstrate:
- illegal `R → P/C/J` bond rejected without reset;
- legal reset-mediated restart;
- `D → C` reconstruction obligation and higher conversion cost;
- recognition plan retains nonzero precompute/storage/maintenance total cost;
- profile can change ranking without changing graph semantic hash;
- deterministic plan hash;
- planner disabled or uncertain → conservative fallback.

## Non-goals
- no G7 ISQL semantic tensor interface;
- no learned strategy model;
- no claim of globally optimal plans;
- no backend code generation or scheduling execution;
- no runtime autotuner loop beyond recorded profile evidence;
- no claim that theoretical `O(0)` online fill has zero real-world cost.

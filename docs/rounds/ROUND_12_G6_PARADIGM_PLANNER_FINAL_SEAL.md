# Round 12 — G6 Explicit Execution-Paradigm Planner Final Seal

## Result

Round 12 implements the G6 strategy-planning extension over the already sealed NOVA Core. The canonical program remains unchanged; planning creates a separate deterministic evidence object.

## Three-axis domain

$$
(a,b,c)\in\{C,D\}\times\{C,J,P,R\}\times\{C,D\}.
$$

The implementation exposes all P1–P16 tags. Region classification is evidence-driven and always retains a sequential fallback.

## Planner closure

```text
Canonical Graph
→ Strategy Regions
→ Evidence-backed Paradigm Candidates
→ Explicit Relative Cost
→ Candidate Ranking
→ Paradigm Bonding Validation
→ Conservative Fallback when needed
→ ExecutionStrategyPlan
```

The four G6 acceptance classes execute as follows:

- dense `MatMul` → `DPD` (`P` fill);
- selective `Gather` → `DJD` (`J` fill);
- bounded loop → `DCD` (`C` fill);
- explicit stable precomputed lookup → `DRD` (`R` fill).

Recognition is never inferred merely from the presence of parameters.

## Bonding closure

The implementation enforces:

1. fill complexity non-increase `C → J → P → R`;
2. asymmetric base-space conversion cost;
3. stable `R` as terminal;
4. explicit stability reset before a new chain segment may restart.

A ranked but illegal chain never gets silently repaired into another “optimized” chain. The deterministic fallback is a legal sequential plan.

## Cost boundary

`R` may have `online_work = 0`, but the observed default recognition plan has:

```text
precompute = 4
storage = 4
maintenance = 4
risk = 1
total = 13
```

Therefore G6 does not treat theoretical zero-fill recognition as zero total physical/economic cost.

## Seal

The machine-readable evidence lives at `releases/rounds/round-12/G6_SEAL.json`.

**G6 Explicit Execution-Paradigm Planner: SEALED.**

**Next:** G7 — ISQL high-dimensional semantic interface. Round 12 does not implement it.

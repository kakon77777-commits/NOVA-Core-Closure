# G3 Verification Matrix

## Status

**SEALED — Round 09 / NOVA Core 0.9.0**

| Requirement | Evidence | Result |
|---|---|---|
| Deterministic ownership/lifetime analysis | independent `ResourceAnalysis` tests | PASS |
| Concrete byte accounting | `f32[4] = 16 bytes` | PASS |
| Conservative unique buffers | sequential example: 3 buffers / 48 bytes | PASS |
| Verified safe buffer reuse | optimized example: 2 buffers / 32 bytes | PASS |
| Device transfer planning | CPU→gpu0 and gpu0→CPU records | PASS |
| Independent candidate verification | schedule/lifetime/hash/capacity/transfer recomputation | PASS |
| Overlapping alias rejection | malicious external candidate | PASS |
| Missing transfer rejection | forged device plan | PASS |
| Forged peak rejection | candidate `peak=1` recomputed as 32 | PASS |
| Conservative fallback | unsafe AI/external candidate → 48-byte conservative plan | PASS |
| Dynamic symbolic size | explicit runtime obligation, conditionally safe | PASS |
| AI trust boundary | proposer metadata never bypasses verifier | PASS |
| G1/G2 regression | complete inherited test suite | PASS |

## Physical buffer-pool evidence

For the typed sequential graph:

$$
\text{conservative reserved}=48\;\text{bytes}
$$

$$
\text{optimized reserved}=32\;\text{bytes}
$$

The reduction comes only from the proven non-overlap of `a` and `c`; `a` and `b` overlap at node `n2` and are forbidden from sharing a buffer.

## Safety rule

$$
\boxed{\text{Candidate Plan}\neq\text{Verified Plan}}
$$

A human, deterministic heuristic, or future AI may propose the same `MemoryPlan` record. Safety status is produced only by independent deterministic verification.

## Fresh release evidence

- Full regression: **255 / 255 tests**.
- Optimized plan hash: `sha256:1278a21dc837ae2e9f9bbd38662d5da3966a9fe7a6e9aaf057a20541aa7c6adf`.
- Static physical pool: **48 → 32 bytes** after verified reuse.
- Device transfers: **2**.
- Forged AI/external plan: `unsafe`, violation `peak_mismatch`, conservative fallback selected.
- Dynamic symbolic size: `conditionally_safe` with explicit runtime-size obligations.

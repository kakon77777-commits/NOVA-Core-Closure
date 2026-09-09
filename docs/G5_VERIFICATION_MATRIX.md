# G5 Verification Matrix

**Gate:** G5 — SOS / Cl-safe Integration  
**Runtime:** 0.11.0  
**Schema:** 0.1.0

| Requirement | Evidence | Result |
|---|---|---|
| OperatorDescriptor + Sem/Comp/Projection slots | deterministic descriptor records and basic registry | PASS |
| Legal composition | `relu ∘ tanh ∘ negate`, closure `sha256:556b98204c184edc8899073cbe57f8f5b7bbcbc83582572447755a2d6a3935b1` | PASS |
| RVP ordered checks | `C → G → S → EFFECT` | PASS |
| Comp collapse | disjoint contexts → `CompCollapseError` | PASS |
| Sem divergence | two-state toggle, `K_S=8` → `SemDivergenceError` | PASS |
| Projection inconsistency | forward/reverse mismatch → `GIncoherenceError` | PASS |
| Effect conflict | State/Network forbidden pair → `EffectCompositionError` | PASS |
| BrokenOperator isolation | diagnostic broken value cannot silently re-enter a chain | PASS |
| Depth limit | three operators with max depth 2 → `CompositionDepthError` | PASS |
| NOVA lowering | `relu ∘ tanh` lowers to ordinary `Tanh → Relu` nodes | PASS |
| Runtime equivalence | Interpreter = NumPy = `max(tanh(x), 0)` | PASS |

## Boundary

SOS extends operator-level semantic/composition contracts. NOVA remains authoritative for executable graph type, shape, effect, AD, and runtime semantics.

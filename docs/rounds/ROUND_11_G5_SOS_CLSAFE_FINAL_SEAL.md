# Round 11 — G5 SOS / Cl-safe Integration Final Seal

Round 11 integrates the SOS operator-closure layer with NOVA without changing NOVA Core semantics.

The executable RVP prototype follows the source-defined fail-fast order:

$$
C ightarrow G ightarrow S
$$

followed by the NOVA effect-policy integration check. The default semantic bound is $K_S=256$.

## Implemented

- immutable `OperatorDescriptor` with semantic, composition, projection, state, effect, and version contracts;
- deterministic basic operator registry;
- typed `CompCollapseError`, `GIncoherenceError`, `SemDivergenceError`, and `EffectCompositionError`;
- strict composition and diagnostic `BrokenOperator`;
- bounded semantic fixed-point RVP;
- minimum GCI checks for connectivity, orientation consistency, and bounded scale;
- explicit composition depth limit;
- deterministic `OperatorClosure`;
- lowering of safe unary closures to ordinary NOVA nodes;
- Python API and CLI `nova sos`;
- machine-readable G5 seal and acceptance examples.

## Acceptance

All eight G5 acceptance conditions in `releases/rounds/round-11/G5_SEAL.json` are verified.

**G5: SEALED.**

# NOVA Stable Structural Identity v0.3 — Scope Marker

This file marks the start of the v0.3 experiment. The implementation is developed on a branch cut from `experiment/symbol-minimal-canonical-v0.2`.

Target invariant:

$$
\operatorname{MID}(P,M)=\operatorname{MID}(\rho(P),\rho(M))
$$

for label-only renaming $\rho$, while semantic state changes must change the machine identity hash.

The v0.3 implementation will keep the existing NOVA Core schema intact and introduce a persistent 128-bit structural identity manifest plus an NSM3 identity-normalized wire projection.

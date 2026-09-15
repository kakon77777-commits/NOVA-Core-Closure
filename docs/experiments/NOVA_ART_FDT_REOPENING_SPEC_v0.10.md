# NOVA ART / FDT Reopening v0.10

**Date:** 2026-09-15  
**Status:** Experimental implementation specification  
**Parent:** Program DPEC v0.9  
**Sources:** SREG-F07 Future-Dimension Test and SREG-F08 Multi-Universe Experimental Protocol

## 0. Purpose

v0.10 attacks the closed v0.9 Program DPEC rather than expanding the original claim by assertion.

The lifecycle is:

$$
\boxed{
DPEC_{0.9}
\rightarrow
ART/FDT_{0.10}
\rightarrow
Reopen
\rightarrow
Harden
\rightarrow
Re\text{-}PEC_{0.10}
}
$$

The old certificate is immutable. A successful Re-PEC is a child artifact with explicit lineage.

## 1. Non-terminal principle

Passing the bounded v0.10 suite means only that reopening gain was measured for the declared test family. It does **not** imply that all possible future tests have zero reopening gain.

Therefore both the ART/FDT Report and the Re-PEC certificate carry:

```text
test_family_completeness_claim = false
terminal_claim = false
```

## 2. ART suite

The implemented ART family contains six required probes:

1. ART-Representation — add a representation outside the certified text/graph/AI family.
2. ART-Operator — replace a semantic operator inside one route.
3. ART-Route — mutate the lowering/proof route grammar without changing surface families.
4. ART-Budget — expand the finite resource envelope.
5. ART-Counterexample — directly attack the cross-representation convergence claim.
6. ART-Observer — raise the equivalence/observer resolution.

## 3. FDT suite

The implemented Future-Dimension Test family follows SREG-F07:

1. FDT-A Representation Mutation.
2. FDT-B Operator Arity Mutation.
3. FDT-C Meta-Operator Injection.
4. FDT-D Primitive Reframing.
5. FDT-E Observer Lift.
6. FDT-F Semantic Lift.
7. FDT-G Cross-Substrate Reopening.

## 4. Control probes

ART/FDT must discriminate reopening from harmless perturbation. v0.10 therefore includes three controls:

- human comment/projection noise;
- source mapping order permutation;
- independent alpha renaming of text, graph, AI, and scoped binder labels.

A valid suite requires every ART/FDT probe to observe reopening while every control avoids false reopening.

## 5. Operational reopen gain

v0.10 stores a bounded engineering proxy over these axes:

```text
representation
operator
route
budget
observer
semantic
substrate
state
```

For probe $j$, reopen gain is the fraction of these declared axes changed by the probe. This is an engineering proxy, not an information-theoretic proof of structural information gain.

## 6. v0.9 hardening gaps discovered

The stronger v0.10 suite exposed missing dedicated rules for:

- route mutation;
- semantic-carrier lift;
- primitive reframing;
- cross-substrate reopening.

These are evidence that ART/FDT performed useful reopening work; they are not retroactive claims that v0.9 violated its original bounded DPEC contract.

## 7. Hardened reopening rules

Re-PEC adds:

```text
REOPEN-ROUTE
REOPEN-SEMANTIC
REOPEN-SUBSTRATE
REOPEN-PRIMITIVE
REOPEN-FDT-FAMILY
```

`REOPEN-FDT-FAMILY` is especially important: the test family itself is reopenable.

## 8. False-closure audit

v0.10 explicitly records the ten SREG-F08 categories:

```text
search
representation
operator
budget
verification
ambiguity
compression
observer
memory
consensus
```

A category may be `checked`, `partial`, or `deferred`. Silence is not treated as coverage.

## 9. Re-PEC lineage

The new artifact stores the parent PEC hash and ART/FDT report hash. The lineage action is:

```text
SUPERSEDE_WITH_LINEAGE_NOT_OVERWRITE
```

Thus the old certificate remains replayable.

## 10. Debt transition

After the bounded full ART/FDT suite:

```text
DEBT-ART-01 -> resolved
DEBT-FDT-COMPLETE-01 -> deferred
FRONTIER-FDT-COMPLETE-01 -> open frontier
```

because completeness of the FDT family is not established.

## 11. Acceptance criteria

v0.10 is accepted only if all six ART probes and all seven FDT probes correctly reopen, all controls avoid false reopening, report/Re-PEC codec and tamper checks pass, Re-PEC preserves parent lineage, cumulative isolated tests remain green, and terminal/test-family-completeness claims remain false.

## 12. Claim boundary

v0.10 establishes a bounded adversarial reopening/reclosure protocol for the existing NOVA experimental domain. It does not establish RGPEC, terminal language completeness, global program equivalence, complete ART/FDT test-family coverage, backend behavioral equivalence, or multi-implementation consensus.

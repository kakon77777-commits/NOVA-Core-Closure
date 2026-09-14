# NOVA Program PEC / Closure Certificate v0.9

**Date:** 2026-09-15  
**Status:** Experimental specification  
**Lineage:** NOVA v0.1–v0.8 + SREG-F04/F07/F08  
**Canonical math delimiter:** `$...$` and `$$...$$`

## 0. Purpose

v0.9 introduces a machine-verifiable closure artifact for a bounded NOVA program domain.
It does **not** claim that NOVA, programming, or program equivalence is globally complete.

The central statement is:

$$
\boxed{
\operatorname{Closed}_{\Gamma,B}(P)
\neq
\operatorname{TerminalComplete}(P)
}
$$

A v0.9 certificate records what was closed, under which frame and resource envelope,
what remains open, what was verified, and what conditions must reopen the certificate.

The first certified domain is the v0.8 cross-representation reconstruction family:

$$
\text{Text-like}\to P_T,
\quad
\text{Graph-native}\to P_G,
\quad
\text{AI-native}\to P_A,
$$

with bounded CoreNorm convergence:

$$
\operatorname{CoreNorm}(P_T)
=
\operatorname{CoreNorm}(P_G)
=
\operatorname{CoreNorm}(P_A).
$$

## 1. SREG alignment

SREG-F04 defines Pulse Exhaustive Closure as the conjunction:

$$
\boxed{
\operatorname{PEC}
=
\operatorname{Reach}
\land
\operatorname{Novel}
\land
\operatorname{Debt}
\land
\operatorname{Frontier}
\land
\operatorname{Verify}
\land
\operatorname{Reopen}
}
$$

v0.9 preserves these six audit axes rather than collapsing closure into one scalar.

SREG-F07 adds the non-terminal boundary:

$$
\operatorname{RGPEC}_{\Gamma,B}
\not\Rightarrow
\operatorname{TerminalComplete}.
$$

v0.9 is deliberately weaker still: it certifies only **DPEC**, a domain-level closure.
The builder rejects RGPEC requests.

## 2. Program pulse boundary

The program closure boundary is represented by:

$$
\Pi_P
=
(
\Gamma,
B,
\mathcal R,
\mathcal O,
\mathcal V,
\mathcal H
).
$$

Where:

- $\Gamma$: frame;
- $B$: finite resource envelope;
- $\mathcal R$: declared representation routes;
- $\mathcal O$: declared operator family;
- $\mathcal V$: validation regime;
- $\mathcal H$: observer/equivalence conditions.

No closure statement is valid without this boundary.

## 3. Frame schema

`ProgramPECFrame` contains:

```text
ProgramPECFrame {
  domain
  assumptions[]
  representation_family[]
  operator_family[]
  route_grammar[]
  validation_regime[]
  observer_conditions[]
  backend_family[]
}
```

The v0.9 default frame declares:

- domain: cross-representation reconstruction;
- representations: text / graph / AI;
- operators: Input / Add / Identity;
- route: surface adapter → NOVA Project → CoreNorm v0.7;
- observer: CoreNorm equality plus adapter rejection behavior;
- backend semantics: not claimed.

## 4. Resource envelope

`ProgramResourceBudget` is finite and versioned:

```text
ProgramResourceBudget {
  budget_id
  max_representation_routes
  max_modules_per_project
  max_graphs_per_module
  max_nodes_per_graph
  verification_case_budget
  reopening_challenge_budget
  tool_regime[]
}
```

A certificate cannot silently exceed its declared resource envelope.

## 5. Reach audit

Let:

$$
\mathcal R^{adm}
$$

be the declared representation family and:

$$
\mathcal R^{seen}
$$

be the successfully reconstructed family.

For finite routes:

$$
C_R
=
\frac{|\mathcal R^{seen}\cap\mathcal R^{adm}|}
{|\mathcal R^{adm}|}.
$$

v0.9 requires exact route coverage for `DPEC_CLOSED`.
A missing AI, graph, or text route reopens the certificate.

## 6. Novelty audit

Within the declared representation family, the current novelty criterion is intentionally bounded:
all admissible routes must reduce to one CoreNorm class and carry no unresolved reconstruction obligations.

$$
N_{class}
=
\left|
\{
H_{CN}(P_r):r\in\mathcal R^{seen}
\}
\right|.
$$

The bounded v0.9 condition is:

$$
N_{class}=1.
$$

This means representation-class saturation **inside the declared family only**.
It does not imply global program novelty exhaustion.

## 7. Debt ledger

A closure artifact must preserve unresolved work.

```text
DebtItem {
  debt_id
  category
  summary
  severity
  status
  scope
  reopen_trigger
}
```

Scopes:

- `in_claim`;
- `frontier`.

A critical unresolved `in_claim` debt blocks closure.
Deferred frontier debt can remain open if it is explicitly outside the claim and has a reopening trigger.

The v0.9 artifact preserves two known frontier debts:

1. fresh upstream integration evidence is absent;
2. full ART/FDT has not yet been executed.

## 8. Frontier map

`FrontierItem` requires:

```text
FrontierItem {
  frontier_id
  domain
  summary
  required_capability
  reopen_trigger
}
```

A mature closure must know where it stops.
An empty frontier map is not accepted as mature DPEC closure in v0.9.

Current frontier includes:

- new representation families;
- expanded operator/CoreNorm families;
- backend behavioral equivalence;
- fresh upstream full-suite integration;
- full ART/FDT and Re-PEC.

## 9. Verification summary

`ProgramVerificationEvidence` records external executable evidence:

```text
ProgramVerificationEvidence {
  isolated_cases_passed
  isolated_cases_failed
  standalone_harness_passed
  upstream_full_suite_fresh
  evidence_refs[]
}
```

The verification condition requires:

$$
V
=
V_{reconstruction}
\land
V_{convergence}
\land
V_{profile}
\land
V_{tests}.
$$

A certificate cannot become CLOSED without explicit verification evidence.

## 10. Reopening challenges

v0.9 executes an ART-lite suite.
It is intentionally not the full v0.10 ART/FDT program.

Current challenges:

### ART-LITE-OPERATOR-01

Mutate one `Add` route to `Subtract`.
Expected result:

$$
\text{convergence breaks}.
$$

### ART-LITE-REFERENCE-01

Inject an unresolved structured reference.
Expected result:

$$
\text{adapter rejects}.
$$

### ART-LITE-SURFACE-01

Inject unsupported host-language execution syntax into the text route.
Expected result:

$$
\text{text adapter rejects}.
$$

Passing these challenges is necessary but not sufficient for terminality.

## 11. Reopening conditions

The artifact stores explicit triggers:

- representation family changes;
- operator family or CoreNorm profile changes;
- backend behavior enters the claim;
- resource budget expands;
- observer/equivalence regime changes;
- a critical in-claim debt appears;
- replay or evidence verification fails.

Thus:

$$
\operatorname{Reopen}
\not\Rightarrow
\operatorname{PreviouslyWrong}.
$$

A reopened certificate may have been valid under its earlier frame.

## 12. Closure confidence vector

v0.9 uses the six-axis vector:

$$
\mathbf C
=
(c_R,c_N,c_D,c_F,c_V,c_A).
$$

The components correspond to:

- reachability;
- bounded novelty saturation;
- debt control;
- frontier audit;
- verification coverage;
- adversarial reopening robustness.

This vector is not a global completion percentage.

## 13. Closure levels

The schema recognizes:

- `LPEC`;
- `DPEC`;
- `RGPEC`.

But the v0.9 builder only emits:

$$
\boxed{DPEC}
$$

for the declared cross-representation domain.

Attempting to request RGPEC is rejected.
No `TerminalComplete` mode exists in this builder.

## 14. Certificate status

A certificate is `DPEC_CLOSED` iff all six audit conditions pass:

$$
DPEC_{closed}
\iff
R\land N\land D\land F\land V\land A.
$$

Otherwise it is:

$$
DPEC_{open}.
$$

`OPEN` is a structured result, not an exception.
Boundary inconsistency, such as exceeding the declared route budget, is a validation error.

## 15. Closure artifact

The machine artifact records the F04/F08-style fields:

```text
claim_summary
route_coverage
novelty_stats
debt_ledger
frontier_map
verification_summary
false_closure_risk_flags
reopen_conditions
manifest_ref
state_ref
```

It additionally stores:

- CoreNorm profile hash;
- cross-reconstruction certificate hash;
- six condition audits;
- confidence vector;
- reopening challenge evidence.

## 16. Machine identity

The certificate itself has deterministic identity:

$$
H_{PEC}
=
SHA256(
\operatorname{Canon}(Cert)
).
$$

The encoded envelope stores both the certificate and its hash.
Decoding recomputes the hash and rejects tampering.

## 17. Replay

`replay_program_pec_certificate()` rebuilds the certificate from the supplied sources under the stored frame, budget, debts, frontier, reopening conditions, profile, and verification evidence.

Replay checks:

- status;
- profile hash;
- reconstruction certificate hash;
- state reference;
- manifest reference;
- route coverage;
- novelty stats;
- verification summary;
- audits;
- confidence vector;
- reopening challenge results;
- final certificate hash.

## 18. State and manifest references

`state_ref` points to the common CoreNorm state:

$$
state\_ref
=
H_{CN}(P).
$$

`manifest_ref` commits to:

$$
(
\Gamma,
B,
H_{profile}
).
$$

Thus changing the frame or budget changes the closure manifest identity even if the normalized program state remains the same.

## 19. False-closure risk

The current artifact explicitly records non-zero risk flags:

- bounded representation family;
- bounded operator family;
- bounded CoreNorm profile;
- backend behavior not claimed;
- fresh upstream full suite not in current scope;
- full ART/FDT not yet claimed.

The presence of risk flags is intentional.
A certificate that erased them would be less trustworthy, not more complete.

## 20. Acceptance criteria

v0.9 is accepted when:

1. all three declared representation routes reconstruct;
2. they converge to the same CoreNorm class;
3. explicit verification evidence has zero failures;
4. no critical in-claim debt remains;
5. frontier is explicit;
6. ART-lite challenges pass;
7. reopening conditions are explicit;
8. certificate encode/decode preserves identity;
9. tampered certificate envelopes are rejected;
10. RGPEC overclaim is rejected;
11. cumulative v0.2–v0.9 isolated tests pass;
12. release ZIP passes fresh-extract verification.

## 21. Non-claims

v0.9 does not prove:

- global program equivalence;
- all representation families are exhausted;
- all operators are exhausted;
- backend behavioral equivalence;
- all NOVA execution semantics are closed;
- RGPEC;
- terminal completeness.

## 22. Next experiment

v0.10 should no longer merely store reopening conditions.
It should systematically attack the closure artifact through versioned ART/FDT suites:

$$
\text{DPEC}
\rightarrow
\text{ART/FDT}
\rightarrow
\text{Re-PEC}.
$$

Candidate axes:

- representation perturbation;
- operator injection/ablation;
- route mutation;
- budget perturbation;
- counterexample generation;
- observer shift;
- future-dimension tests.

That step will measure closure resistance rather than only closure declaration.

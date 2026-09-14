# NOVA Program PEC / Closure Certificate v0.9 — Validation Record

**Date:** 2026-09-15  
**Status:** Experimental validation passed  
**Target branch:** `experiment/program-pec-v0.9`

## Program DPEC result

The certified domain is the v0.8 cross-representation reconstruction family under the v0.7 bounded CoreNorm profile.

```text
status: DPEC_CLOSED
certificate hash: sha256:2090f2e6db301b62b47e9006462451578f7b0eaddfe77711fdbe83273b570468
state ref: sha256:2a02aae792b64e699caef73dd49efe10933e6642ec9bffbd695dd74605c4546e
manifest ref: sha256:3adb1d784f404d624758a7455f9b98cf922b67dad32b3491b79159ea18a407ba
reconstruction cert hash: sha256:5d14e21d8243ab8e99e5297c731f9085c294ba1eb0d5473a7aca67813ce5febd
```

The closure confidence vector is:

$$
\mathbf C=(1,1,1,1,1,1).
$$

This vector is scoped to the declared frame and is not a global completion percentage.

## Six PEC audits

```text
Reach:    PASS
Novel:    PASS
Debt:     PASS
Frontier: PASS
Verify:   PASS
Reopen:   PASS
```

## Explicit frontier

The certificate preserves five frontier items:

1. representation families outside the v0.8 adapters;
2. effectful/control-flow/call equivalence outside bounded CoreNorm;
3. backend behavioral equivalence;
4. fresh upstream full-suite integration;
5. full ART/FDT and Re-PEC.

## Debt ledger

Two deferred frontier debts remain explicit:

- fresh upstream full-suite integration evidence;
- full ART/FDT coverage.

Neither is silently interpreted as solved.

## Reopening conditions

Seven reopening conditions are stored, including representation, operator/profile, backend, budget, observer, new critical debt, and failed replay/evidence verification.

## ART-lite reopening challenges

Three challenges pass:

- semantic operator mutation breaks convergence;
- unresolved structured reference is rejected;
- unsupported host-language text surface is rejected.

Full ART/FDT is not claimed in v0.9.

## Verification evidence

```text
standalone v0.9 harness: PASS
isolated compatibility tests: 80 passed / 0 failed
Program PEC codec roundtrip: PASS
tamper detection: PASS
certificate replay: PASS
RGPEC overclaim rejection: PASS
```

The historical upstream 215-test baseline was not freshly rerun in this execution container and remains explicitly outside the present DPEC claim.

## Boundary result

The v0.9 builder only certifies DPEC.
Requests for RGPEC are rejected.
The certificate carries:

```text
terminal_claim: false
```

Therefore:

$$
\boxed{
DPEC_{\Gamma,B}
\not\Rightarrow
RGPEC
\not\Rightarrow
TerminalComplete.
}
$$

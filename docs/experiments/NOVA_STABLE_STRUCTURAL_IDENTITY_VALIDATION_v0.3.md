# NOVA Stable Structural Identity v0.3 — Validation Record

**Date:** 2026-09-14  
**Status:** Experimental validation passed  
**Branch:** `experiment/stable-structural-identity-v0.3`  
**Canonical math delimiter:** `$...$` and `$$...$$`

## Result

The v0.3 experimental harness verifies:

$$
\boxed{
\text{Object Identity}
\neq
\text{Human Label}
\neq
\text{Semantic State}
}
$$

For a complete label-only rename of the test project:

```text
legacy semantic hash before:
sha256:a4c5c5211716c08c8d1e3eb1dc740aed85aa21bd717cd35b4f438ebc57f3c2d5

legacy semantic hash after:
sha256:74bba94779601175b086dc45f3e3ae47710b98a9dad3959c7a8c6cb52d1d4bfd

machine identity hash before/after:
sha256:743b0c11fd539706bc0be3b7b7f23236920403b3a170658cb9a67f84e2463af7
```

Thus the current legacy `semantic_hash` remains label-sensitive, while NSM3 machine identity is label-invariant.

The same NSM3 bytes can be decoded through a renamed persistent identity manifest to produce the renamed human projection.

A semantic mutation `Add -> Subtract` using the same persistent node identity changes the machine identity hash, confirming that stable object identity does not hide semantic-state changes.

## Executed tests

```text
NOVA v0.3 validation harness: PASS
16 passed in 0.10s
```

The 16-test isolated compatibility set includes the v0.2 Global Semantic Registry / NSM1-NSM2 behavior and the new v0.3 structural-identity tests.

For the small validation graph:

```text
NSM1: 209 bytes
NSM2: 189 bytes
NSM3: 322 bytes
```

The NSM3 size increase is expected because v0.3 introduces persistent 128-bit identities. Compression is not the v0.3 objective.

The tested NSM3 payload does not contain these human/known-semantic spellings:

```text
app
main
add_node
left
right
sum
Add
Pure
Differentiable
```

This does not imply that all UTF-8 has been eliminated. Extension payloads, symbolic dimensions, external contracts, diagnostics, and other unclassified domains may still contain text.

## Full-suite limitation

The complete upstream NOVA regression suite was not re-executed in the current container because the environment could not clone/download the full GitHub repository. The pre-experiment `main` baseline of 215 passing tests remains historical baseline evidence only; it is not reported as a v0.3 full-suite result.

The v0.3 acceptance claim is therefore limited to the isolated executable validation above until a local or CI full-suite run is performed.

# NOVA Core Closure Round 03 — Validation

**Round:** 03 — Executable Closure  
**Package version:** 0.3.0  
**Graph schema version:** 0.1.0  
**Source commit before release metadata:** `b49948d67e4fff13bcf9ceb4a5f49d43fc52a7d9`

## Functional verification

- Full pytest suite: **89 / 89 passed**.
- Python bytecode compilation: PASS.
- Canonical example decode/check: PASS.
- NumPy execution example: PASS.
- Structured formula projection smoke: PASS.
- Git whitespace check: PASS.

## Executable smoke

Program:

$$
Y=(X \cdot W)+b.
$$

Inputs:

```json
{
  "X": [[1.0, 2.0]],
  "W": [[2.0], [3.0]],
  "b": [0.5]
}
```

Observed NumPy backend output:

```json
{"Y": [[8.5]]}
```

Observed execution trace:

```text
MatMul(X, W) -> XW
Add(XW, b) -> Y
```

Observed formula projection:

```text
Y = (X \cdot W) + b
```

## Runtime invariants covered by tests

- execution environment input / parameter binding;
- missing runtime values return typed errors;
- concrete and symbolic runtime shape guards;
- deterministic dependency scheduling;
- cyclic dependencies are rejected rather than treated as loops;
- graph semantic hash remains stable across execution;
- explicit finite `BoundedLoop` only;
- pure graph `Call` works through an explicit graph lookup;
- unsupported operations fail explicitly;
- interpreter and NumPy backend agree on the supported subset;
- formula projection refuses unsupported control structures;
- CLI `check`, `hash`, `run`, and `project` paths execute successfully.

## Source hygiene

Tracked source files at the pre-metadata gate: **48**.

- UTF-8 decode failures: 0
- replacement characters: 0
- secret-pattern hits: 0
- Unicode-escape source patterns: 0
- hidden control characters: 0
- alternate Markdown math delimiters: 0
- invalid tracked JSON files: 0

## Release rule

Round 03 remains a local ZIP handoff. No GitHub publication is required for this release.

The release artifact must pass:

1. fresh 89-test suite;
2. compile gate;
3. source hygiene gate;
4. checksum manifest verification;
5. ZIP CRC verification;
6. extracted manifest verification.

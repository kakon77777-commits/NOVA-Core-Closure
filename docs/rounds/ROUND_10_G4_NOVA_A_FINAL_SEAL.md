# Round 10 — G4 Nova-A AI-Native Graph Construction Final Seal

## Result

Round 10 implements and seals the first Nova-A construction interface.

The machine-native flow is:

$$
\boxed{
\text{AIBuildRequest}
\rightarrow
\text{Sandbox}
\rightarrow
\text{Candidate GraphPatch}
\rightarrow
\text{Constraints / Tests / AD}
\rightarrow
\text{Diff + Audit}
\rightarrow
\text{Explicit Commit}
}
$$

No source-text generation is required.

## Implemented components

- deterministic `AIProvenance`;
- `AISandboxPolicy` patch budgets, node-kind allowlists, effect policy, interface/constraint permissions;
- `BuildConstraint` post-build constraint API;
- structured `BuildTestCase` execution through Interpreter/NumPy;
- existing `DifferentiationRequest` as a build obligation;
- deterministic build-request JSON codec and SHA-256 identity;
- pure `preview_ai_build` candidate creation;
- READY / REJECTED candidate state;
- structured sandbox / constraint / test / differentiation evidence;
- semantic and structural diff review;
- machine-readable AI build audit view;
- `AIBuildTransaction` with stale-candidate protection, preview/commit reproduction, and rollback;
- project-level API;
- CLI preview/audit/commit commands.

## Safety properties

### No AI-only mutation path

Every accepted change is an ordinary `GraphPatch`.

### Preview is non-mutating

The working Project remains byte/record identical during preview.

### Commit is independently reproduced

Commit recomputes the request hash and performs a fresh preview before applying the patch through the existing `GraphTransaction`.

### Rejected evidence remains inspectable

Sandbox/constraint/test/AD failures return a REJECTED candidate with audit evidence but no committable Project.

### Confidence is not authority

Provenance/model metadata never changes validation semantics.

## Acceptance examples

The release includes:

```text
examples/ai_build/base_project.json
examples/ai_build/add_relu_request.json
examples/ai_build/typed_shape_request.json
examples/ai_build/effectful_rejected_request.json
examples/g4_verification.json
```

`add_relu_request.json` demonstrates one structured request simultaneously:

- adding a node/layer;
- changing graph output;
- satisfying explicit graph/node constraints;
- running a structured execution test;
- validating a reverse-mode differentiation request.

`effectful_rejected_request.json` demonstrates the default structural sandbox refusing a `Network` effect.

## Boundary

Round 10 does not make NOVA an autonomous coding agent. It establishes a machine-native, auditable, deterministic construction interface that an AI can use without becoming the authority on correctness.

## Next gate

Round 11 proceeds to **G5 — SOS / Cl-safe integration**: operator descriptors, explicit composition contracts, composition failure isolation, and safe operator closure over the already verified NOVA Core.

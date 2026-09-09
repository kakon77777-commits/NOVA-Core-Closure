# Round 10 — G4 Nova-A AI-Native Graph Construction Design

## Status

Approved implementation design for NOVA Core Closure Round 10.

## Goal

Seal G4 by allowing an AI or other structured producer to construct and modify NOVA canonical graphs directly through a constrained, auditable build transaction without first generating source text and without bypassing NOVA validation.

The target boundary is:

$$
\boxed{
\text{AI Build Request}
\rightarrow
\text{Structural Sandbox}
\rightarrow
\text{Candidate GraphPatch}
\rightarrow
\text{Validation Evidence}
\rightarrow
\text{Diff / Audit}
\rightarrow
\text{Explicit Commit or Reject}
}
$$

AI construction is a proposal mechanism, not a correctness authority.

## Non-goals

Round 10 does not implement:

- a network/model-provider client;
- an autonomous long-horizon Agent;
- unrestricted tool use or filesystem/network effects;
- direct mutation of a Project without GraphPatch validation;
- automatic acceptance based on AI confidence;
- a learned safety model;
- SOS / Cl-safe composition;
- G5 operator closure;
- arbitrary code execution in test definitions.

## 1. Construction request as a first-class machine interface

Nova-A does not require text source. A producer submits an immutable `AIBuildRequest` containing:

- request identity and provenance;
- one target module/graph;
- a `GraphPatch` candidate;
- explicit post-build constraints;
- zero or more executable validation cases;
- zero or more differentiation requests;
- a structural sandbox policy.

The embedded GraphPatch remains the only mutation language. This preserves the Round 01/07 transaction model instead of creating an AI-only mutation path.

## 2. Deterministic provenance

`AIProvenance` records:

```text
request_id
actor_id
source
model_id?
session_id?
metadata{}
```

No timestamp is generated implicitly. If time is important, the caller supplies it in metadata. This keeps request and audit hashes reproducible.

Provenance is record/audit data. It does not silently change the semantic identity of the target graph.

## 3. Structural sandbox

`AISandboxPolicy` constrains what a single request may modify. The first version supports:

- maximum added / replaced / removed node counts;
- maximum added / removed / replaced edge counts;
- an optional node-kind allowlist;
- whether graph inputs/outputs may change;
- whether graph constraints may change;
- whether node removal is allowed;
- whether non-empty effects are allowed;
- whether validation tests may execute;
- whether differentiation requests may execute.

The sandbox only inspects structured NOVA objects. It never executes arbitrary text.

A request outside policy becomes a rejected candidate with typed violations. It is never partially applied.

## 4. Constraint API

`BuildConstraint` is a small deterministic post-build contract. Round 10 supports these kinds:

```text
require_graph_output
require_node
require_node_kind
require_tensor_dtype
require_tensor_shape
forbid_effects
```

Each constraint yields a `ConstraintCheckResult` with `passed`, `message`, and machine-readable evidence.

Unknown constraint kinds are rejected. Constraints are evaluated against the fully validated candidate graph, not the untrusted patch declaration.

Tensor dtype/shape constraints inspect the candidate node's actual `TensorType`. They never trust auxiliary AI metadata.

## 5. Sandboxed executable validation cases

`BuildTestCase` contains only structured values:

```text
name
inputs{}
parameters{}
expected_outputs{}
backend
atol
rtol
```

Allowed backends are `interpreter` and `numpy`.

The test runner executes the candidate graph through the existing NOVA runtime and compares declared outputs with deterministic numerical equality/allclose rules. It never evaluates source strings.

If the sandbox disables test execution, a request that contains tests is rejected rather than silently ignoring them.

## 6. Differentiation requests as build obligations

An `AIBuildRequest` may include existing `DifferentiationRequest` values.

For every request, the candidate graph must successfully pass `differentiate_graph`. Evidence records the derivative graph semantic hash and gradient output mapping.

This makes “add a differentiation request” a verifiable build obligation rather than documentation metadata.

## 7. Candidate preview pipeline

Preview is pure with respect to the working Project:

$$
\boxed{
P
\xrightarrow{\operatorname{Preview}(R)}
C
\quad\text{while}\quad
P_{after}=P_{before}
}
$$

The preview order is:

1. validate request identity / target / base hashes;
2. verify structural sandbox policy;
3. apply GraphPatch to a candidate Project through existing `apply_graph_patch`;
4. recompute graph diff;
5. evaluate build constraints;
6. run structured validation cases;
7. run differentiation requests;
8. emit immutable audit evidence.

Any failure produces `BuildStatus.REJECTED`. A rejected candidate is still auditable, but it has no committable Project.

A successful candidate has `BuildStatus.READY` and stores exact candidate semantic/record hashes.

## 8. Build transaction

`AIBuildTransaction` owns a working Project and uses the existing `GraphTransaction` internally.

`preview(request)` never changes `current`.

`commit(candidate)` must verify:

- candidate status is `READY`;
- current semantic hash equals candidate base semantic hash;
- current record hash equals candidate base record hash;
- candidate request hash still matches the request;
- independently reapplying the GraphPatch yields the same candidate semantic/record hashes.

Only then is the existing GraphTransaction committed.

`rollback()` delegates to the existing rollback history and restores the exact prior Project record.

This prevents stale candidate approval and preview/commit divergence.

## 9. Review and audit surface

`project_ai_build_audit(candidate)` returns a machine-readable review object containing:

- request/provenance summary;
- sandbox policy and violations;
- constraint results;
- test results;
- differentiation evidence;
- base/candidate semantic and record hashes;
- GraphPatch summary;
- structural/semantic diff;
- final build status.

Human or AI reviewers inspect this evidence before commit.

## 10. Codec and command-line surface

Round 10 adds deterministic JSON codecs for:

- `AIProvenance`;
- `AISandboxPolicy`;
- `BuildConstraint`;
- `BuildTestCase`;
- `AIBuildRequest`.

CLI commands:

```text
nova ai-build-preview PROJECT REQUEST
nova ai-build-audit PROJECT REQUEST
nova ai-build-commit PROJECT REQUEST --output NEW_PROJECT
```

`ai-build-commit` never overwrites the input file.

## 11. G4 acceptance demonstrations

The verification matrix must demonstrate, using structured build requests rather than source text, that Nova-A can:

1. add a layer/node and change graph output;
2. change tensor shape/type metadata while satisfying an explicit shape constraint;
3. repair a candidate type/shape mismatch by replacing the node with a constraint-satisfying version;
4. attach and pass a structured execution test;
5. attach and validate a differentiation request;
6. reject an effectful or over-budget patch in sandbox;
7. reject a stale candidate;
8. rollback an accepted build.

## 12. Versioning and seal

Runtime version becomes `0.10.0`.

Graph storage schema remains `0.1.0` because the canonical Graph record is not broken. Nova-A request records are external/versioned construction artifacts.

G4 is sealed when:

- all inherited tests pass;
- the G4 verification matrix passes;
- a structured AI build request can preview, audit, commit, and rollback;
- rejected candidates cannot mutate the working Project;
- no AI confidence/provenance field bypasses deterministic validation.


# Round 04 — Reverse-Mode Automatic Differentiation

Round 04 makes differentiation a NOVA graph transformation:

$$
\boxed{
G
\xrightarrow{\mathcal D_{\mathrm{rev}}}
G_{\nabla}
}
$$

Implemented capabilities:

- immutable `DifferentiationRequest`;
- deterministic derivative graph IDs and semantic hashes;
- explicit scalar seeds and explicit-seed VJPs;
- VJP rule registry;
- fan-out cotangent accumulation;
- broadcast reversal and shape-aware cotangent reduction;
- matrix multiplication gradients;
- reshape, transpose, reduction, mean, activation and softmax VJPs;
- explicit `StopGradient`;
- typed `DiffError` for unsupported, non-differentiable and unknown paths;
- derivative graph execution in Interpreter and NumPy backend;
- finite-difference validation;
- Python API and `nova grad` CLI.

Finite differences are validation only. They are not the language's differentiation mechanism.

The canonical invariant remains:

$$
H_{\mathrm{sem}}(G)_{\mathrm{before}}
=
H_{\mathrm{sem}}(G)_{\mathrm{after}}.
$$

The derivative graph is a new versionable program object; the primal graph is not mutated.

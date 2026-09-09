# NOVA G1 Verification Matrix

**Gate:** G1 — Nova Core Executable Closure  
**Release:** NOVA Core Closure 0.6.0  
**Status:** SEALED

| Requirement | Status | Primary evidence |
|---|---:|---|
| Canonical Graph schema | PASS | `tests/test_model.py`, `tests/test_codec.py`, Round 01 |
| Deterministic serialization / semantic hash | PASS | `tests/test_canonical.py`, `tests/test_patch.py` |
| Tensor types / symbolic shape | PASS | `tests/test_shape_types.py`, `tests/test_shape_solver.py`, `tests/test_shape_ops.py` |
| Reference interpreter | PASS | `tests/test_interpreter.py`, `tests/test_control_flow.py` |
| NumPy CPU backend | PASS | `tests/test_numpy_backend.py` |
| Reverse-mode AD | PASS | `tests/test_autodiff_transform.py`, `tests/test_autodiff_execution.py` |
| Gradient numerical validation | PASS | `tests/test_gradcheck.py`, Small Attention finite-difference validation |
| CLI | PASS | `tests/test_cli.py`, `tests/test_autodiff_api_cli.py`, `tests/test_training_api_cli.py`, `tests/test_interop_cli.py` |
| Structured text / formula projection | PASS | `tests/test_projection.py` |
| Python / NumPy interop | PASS | `tests/test_interop.py`, `tests/test_interop_api.py` |
| DLPack interop | PASS | `tests/test_dlpack_interop.py`, zero-copy capsule round-trip |
| Linear Regression model exit | PASS | `tests/test_model_closure_linear_mlp.py`, `examples/training_linear.json` |
| MLP model exit | PASS | `tests/test_model_closure_linear_mlp.py`, `examples/training_mlp.json` |
| Small Attention model exit | PASS | `tests/test_model_closure_attention.py`, `examples/training_attention.json` |
| Typed failures / no silent guess | PASS | error-domain tests across shape, execution, AD, training, interop |
| Python/DLPack FFI surface | PASS | explicit runtime conversion and DLPack exchange APIs |

## Exit interpretation

G1 is sealed because the original executable-core requirements now have:

$$
\boxed{
\text{Spec}
+
\text{Reference Implementation}
+
\text{Tests}
+
\text{Examples}
+
\text{Versioned Schema}
}
$$

The graph storage schema remains `0.1.0`; the Core implementation version is `0.6.0`.

## Out of scope for this seal

- full projectional editing;
- structural three-way merge UX;
- complete effect system;
- MSSP-AISMBI resource planner;
- GPU-native lowering;
- distributed runtime;
- SOS / Cl-safe / ISQL integration.

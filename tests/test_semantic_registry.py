from nova_core.semantic_registry import (
    REGISTRY_REVISION,
    domain_code,
    global_code,
    registry_fingerprint,
    registry_snapshot,
    resolve_global,
)


def test_registry_codes_are_stable_and_roundtrip() -> None:
    assert REGISTRY_REVISION == 1
    assert domain_code("operator") == 2
    assert global_code("operator", "MatMul") == (2, 10)
    assert global_code("dtype", "f32") == (3, 12)
    assert global_code("device", "cpu") == (4, 1)
    assert global_code("layout", "row_major") == (5, 2)
    assert resolve_global(2, 10) == "MatMul"
    assert resolve_global(3, 12) == "f32"


def test_unknown_atoms_are_not_forced_into_global_registry() -> None:
    assert global_code("operator", "FutureQuantumOp") is None
    assert global_code("dtype", "future-fp7") is None
    assert global_code("not-a-domain", "anything") is None


def test_registry_snapshot_and_fingerprint_are_deterministic() -> None:
    first = registry_snapshot()
    second = registry_snapshot()
    assert first == second
    assert first["revision"] == REGISTRY_REVISION
    assert registry_fingerprint() == registry_fingerprint()
    assert registry_fingerprint().startswith("sha256:")

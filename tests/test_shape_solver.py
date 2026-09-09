import pytest

from nova_core import (
    DimExpr,
    ProofStatus,
    ShapeError,
    ShapeSolver,
)


def test_solver_proves_identical_affine_expressions():
    n = DimExpr.symbol("N")
    solver = ShapeSolver()
    assert solver.prove_equal(2 * n + 1, n + n + 1) is ProofStatus.PROVEN


def test_solver_disproves_distinct_concrete_dimensions():
    solver = ShapeSolver()
    assert solver.prove_equal(3, 4) is ProofStatus.DISPROVEN


def test_solver_binds_single_symbol_from_affine_equality():
    n = DimExpr.symbol("N")
    solver = ShapeSolver()
    solver.add_equal(n + 1, 5)
    assert solver.prove_equal(n, 4) is ProofStatus.PROVEN
    assert solver.bindings == {"N": 4}


def test_solver_aliases_symbols_and_propagates_equality():
    n = DimExpr.symbol("N")
    m = DimExpr.symbol("M")
    solver = ShapeSolver()
    solver.add_equal(n, m)
    solver.add_equal(m, 8)
    assert solver.prove_equal(n + 2, 10) is ProofStatus.PROVEN


def test_contradictory_binding_is_typed_shape_error():
    n = DimExpr.symbol("N")
    solver = ShapeSolver()
    solver.add_equal(n, 4)
    with pytest.raises(ShapeError, match="contradictory shape equality"):
        solver.add_equal(n, 5)


def test_non_integral_single_symbol_solution_stays_unknown():
    n = DimExpr.symbol("N")
    solver = ShapeSolver()
    assert solver.prove_equal(2 * n, 5) is ProofStatus.UNKNOWN
    obligation = solver.require_equal(2 * n, 5, reason="axis equality")
    assert obligation is not None
    assert obligation.proof_status is ProofStatus.UNKNOWN
    assert obligation.runtime_guard is True
    assert obligation.reason == "axis equality"


def test_multiple_unknowns_produce_obligation_not_guess():
    n = DimExpr.symbol("N")
    m = DimExpr.symbol("M")
    solver = ShapeSolver()
    obligation = solver.require_equal(n + m, 12, reason="symbolic shape")
    assert obligation is not None
    assert obligation.left == n + m
    assert obligation.right == DimExpr.constant(12)
    assert obligation.proof_status is ProofStatus.UNKNOWN


def test_require_equal_rejects_proven_false_relation():
    solver = ShapeSolver()
    with pytest.raises(ShapeError, match="shape equality disproven"):
        solver.require_equal(2, 7, reason="matmul contraction")

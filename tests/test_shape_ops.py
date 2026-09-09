import pytest

from nova_core import (
    DimExpr,
    Shape,
    ShapeError,
    ShapeSolver,
    broadcast_shapes,
    contract_shape,
    elementwise_shape,
    matmul_shape,
    reshape_shape,
    transpose_shape,
)


def test_concrete_broadcast_shape():
    result = broadcast_shapes(Shape.of(2, 1, 4), Shape.of(1, 3, 4))
    assert result.shape == Shape.of(2, 3, 4)
    assert result.obligations == ()
    assert result.validated is True


def test_symbol_alias_makes_broadcast_provable():
    n = DimExpr.symbol("N")
    m = DimExpr.symbol("M")
    solver = ShapeSolver()
    solver.add_equal(n, m)
    result = elementwise_shape(Shape.of(n, 3), Shape.of(m, 1), solver=solver)
    assert result.shape == Shape.of(n, 3)
    assert result.obligations == ()


def test_unknown_broadcast_is_explicit_obligation_not_silent_acceptance():
    n = DimExpr.symbol("N")
    m = DimExpr.symbol("M")
    result = broadcast_shapes(Shape.of(n, 4), Shape.of(m, 4))
    assert result.shape is None
    assert len(result.obligations) == 1
    assert result.obligations[0].required_relation == "broadcast_compatible"
    assert result.validated is False


def test_concrete_incompatible_broadcast_is_rejected():
    with pytest.raises(ShapeError, match="broadcast dimensions are incompatible"):
        broadcast_shapes(Shape.of(2, 4), Shape.of(3, 4))


def test_batched_matmul_infers_broadcasted_output():
    b = DimExpr.symbol("B")
    result = matmul_shape(Shape.of(b, 5, 7), Shape.of(1, 7, 11))
    assert result.shape == Shape.of(b, 5, 11)
    assert result.obligations == ()


def test_matmul_unknown_contraction_returns_output_plus_obligation():
    k = DimExpr.symbol("K")
    j = DimExpr.symbol("J")
    result = matmul_shape(Shape.of(5, k), Shape.of(j, 9))
    assert result.shape == Shape.of(5, 9)
    assert len(result.obligations) == 1
    assert result.obligations[0].reason == "matmul contraction"
    assert result.validated is False


def test_matmul_concrete_contract_mismatch_is_rejected():
    with pytest.raises(ShapeError, match="shape equality disproven"):
        matmul_shape(Shape.of(5, 7), Shape.of(8, 9))


def test_general_contraction_removes_selected_axes():
    b = DimExpr.symbol("B")
    result = contract_shape(Shape.of(2, b, 3), Shape.of(4, b, 5), left_axis=1, right_axis=1)
    assert result.shape == Shape.of(2, 3, 4, 5)
    assert result.obligations == ()


def test_reshape_concrete_element_count_is_checked():
    assert reshape_shape(Shape.of(2, 3, 4), Shape.of(6, 4)).shape == Shape.of(6, 4)
    with pytest.raises(ShapeError, match="reshape element count mismatch"):
        reshape_shape(Shape.of(2, 3, 4), Shape.of(5, 5))


def test_symbolic_reshape_returns_element_count_obligation():
    b = DimExpr.symbol("B")
    source = Shape.of(b, 4)
    target = Shape.of(2, 2, b)
    result = reshape_shape(source, target)
    assert result.shape == target
    assert len(result.obligations) == 1
    assert result.obligations[0].required_relation == "element_count_equal"
    assert result.obligations[0].left == source
    assert result.obligations[0].right == target


def test_transpose_reorders_axes_and_rejects_invalid_permutation():
    shape = Shape.of("B", "T", "D")
    assert transpose_shape(shape, (1, 0, 2)).shape == Shape.of("T", "B", "D")
    with pytest.raises(ShapeError, match="transpose axes must be a permutation"):
        transpose_shape(shape, (0, 0, 2))

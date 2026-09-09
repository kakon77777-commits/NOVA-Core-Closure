import pytest

from nova_core import DimExpr, Shape, TensorType, ValidationError, as_dim


def test_constant_and_symbol_dimensions_have_stable_records():
    assert as_dim(7).to_record() == {"kind": "affine_dim", "const": 7, "terms": []}
    assert as_dim("B").to_record() == {"kind": "affine_dim", "const": 0, "terms": [["B", 1]]}


def test_affine_dimension_normalizes_term_order_and_coefficients():
    n = DimExpr.symbol("N")
    m = DimExpr.symbol("M")
    expr = 2 * n + 3 * m + 1 - n
    assert expr.to_record() == {
        "kind": "affine_dim",
        "const": 1,
        "terms": [["M", 3], ["N", 1]],
    }
    assert expr == (3 * m + n + 1)


def test_negative_concrete_dimension_is_rejected():
    with pytest.raises(ValidationError, match="dimension must be non-negative"):
        as_dim(-1)


def test_shape_is_immutable_ranked_tuple_of_dimensions():
    shape = Shape.of("B", 128, DimExpr.symbol("D") + 1)
    assert shape.rank == 3
    assert shape.to_record()["dims"][0] == {"kind": "affine_dim", "const": 0, "terms": [["B", 1]]}


def test_scalar_is_rank_zero_tensor():
    scalar = TensorType.scalar("f32")
    assert scalar.rank == 0
    assert scalar.shape == Shape(())
    assert scalar.to_record() == {
        "kind": "tensor_type",
        "dtype": "f32",
        "shape": {"kind": "shape", "dims": []},
        "layout": "dense",
        "device": "cpu",
    }


def test_tensor_type_carries_shape_layout_and_device():
    tensor = TensorType(dtype="f32", shape=Shape.of("B", 64), layout="row_major", device="gpu:0")
    assert tensor.rank == 2
    assert tensor.to_record()["shape"]["dims"][1]["const"] == 64


def test_affine_expression_allows_negative_intermediate_constant_but_shape_does_not():
    n = DimExpr.symbol("N")
    expr = n - 5
    assert expr.to_record() == {"kind": "affine_dim", "const": -5, "terms": [["N", 1]]}
    with pytest.raises(ValidationError, match="dimension must be non-negative"):
        Shape((DimExpr.constant(-1),))

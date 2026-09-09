from __future__ import annotations

from dataclasses import dataclass
from math import prod

from .errors import ShapeError
from .shape import DimExpr, ProofStatus, Shape, ShapeObligation, ShapeSolver


@dataclass(frozen=True)
class ShapeInference:
    shape: Shape | None
    obligations: tuple[ShapeObligation, ...] = ()

    @property
    def validated(self) -> bool:
        return self.shape is not None and not self.obligations


def _is_one(dim: DimExpr) -> bool:
    return dim.is_concrete and dim.const == 1


def _broadcast_dim(left: DimExpr, right: DimExpr, solver: ShapeSolver) -> tuple[DimExpr | None, ShapeObligation | None]:
    if _is_one(left):
        return right, None
    if _is_one(right):
        return left, None
    status = solver.prove_equal(left, right)
    if status is ProofStatus.PROVEN:
        return left, None
    if status is ProofStatus.DISPROVEN:
        raise ShapeError(
            "broadcast dimensions are incompatible",
            context={"left": left.to_record(), "right": right.to_record()},
        )
    return None, ShapeObligation(
        left=left,
        right=right,
        required_relation="broadcast_compatible",
        proof_status=ProofStatus.UNKNOWN,
        runtime_guard=True,
        reason="broadcast compatibility",
    )


def broadcast_shapes(left: Shape, right: Shape, *, solver: ShapeSolver | None = None) -> ShapeInference:
    solver = solver or ShapeSolver()
    max_rank = max(left.rank, right.rank)
    ldims = (DimExpr.constant(1),) * (max_rank - left.rank) + left.dims
    rdims = (DimExpr.constant(1),) * (max_rank - right.rank) + right.dims
    result: list[DimExpr] = []
    obligations: list[ShapeObligation] = []
    unresolved = False
    for ldim, rdim in zip(ldims, rdims):
        dim, obligation = _broadcast_dim(ldim, rdim, solver)
        if obligation is not None:
            obligations.append(obligation)
        if dim is None:
            unresolved = True
        else:
            result.append(dim)
    return ShapeInference(None if unresolved else Shape(tuple(result)), tuple(obligations))


def elementwise_shape(*shapes: Shape, solver: ShapeSolver | None = None) -> ShapeInference:
    if not shapes:
        raise ShapeError("elementwise shape requires at least one input")
    if len(shapes) == 1:
        return ShapeInference(shapes[0], ())
    solver = solver or ShapeSolver()
    current = shapes[0]
    obligations: list[ShapeObligation] = []
    for other in shapes[1:]:
        inferred = broadcast_shapes(current, other, solver=solver)
        obligations.extend(inferred.obligations)
        if inferred.shape is None:
            return ShapeInference(None, tuple(obligations))
        current = inferred.shape
    return ShapeInference(current, tuple(obligations))


def matmul_shape(left: Shape, right: Shape, *, solver: ShapeSolver | None = None) -> ShapeInference:
    if left.rank < 2 or right.rank < 2:
        raise ShapeError("matmul requires rank >= 2 inputs")
    solver = solver or ShapeSolver()
    batch = broadcast_shapes(Shape(left.dims[:-2]), Shape(right.dims[:-2]), solver=solver)
    obligations = list(batch.obligations)
    contract_obligation = solver.require_equal(left[-1], right[-2], reason="matmul contraction")
    if contract_obligation is not None:
        obligations.append(contract_obligation)
    if batch.shape is None:
        return ShapeInference(None, tuple(obligations))
    output = Shape(batch.shape.dims + (left[-2], right[-1]))
    return ShapeInference(output, tuple(obligations))


def _axis(axis: int, rank: int) -> int:
    normalized = axis + rank if axis < 0 else axis
    if normalized < 0 or normalized >= rank:
        raise ShapeError("contraction axis out of range", context={"axis": axis, "rank": rank})
    return normalized


def contract_shape(
    left: Shape,
    right: Shape,
    *,
    left_axis: int,
    right_axis: int,
    solver: ShapeSolver | None = None,
) -> ShapeInference:
    solver = solver or ShapeSolver()
    la = _axis(left_axis, left.rank)
    ra = _axis(right_axis, right.rank)
    obligation = solver.require_equal(left[la], right[ra], reason="tensor contraction")
    output = Shape(
        tuple(dim for i, dim in enumerate(left.dims) if i != la)
        + tuple(dim for i, dim in enumerate(right.dims) if i != ra)
    )
    return ShapeInference(output, () if obligation is None else (obligation,))


def _concrete_product(shape: Shape) -> int | None:
    values = [dim.concrete_value for dim in shape]
    if any(value is None for value in values):
        return None
    return prod(int(value) for value in values)


def reshape_shape(source: Shape, target: Shape) -> ShapeInference:
    if source == target:
        return ShapeInference(target, ())
    source_count = _concrete_product(source)
    target_count = _concrete_product(target)
    if source_count is not None and target_count is not None:
        if source_count != target_count:
            raise ShapeError(
                "reshape element count mismatch",
                context={"source_count": source_count, "target_count": target_count},
            )
        return ShapeInference(target, ())
    obligation = ShapeObligation(
        left=source,
        right=target,
        required_relation="element_count_equal",
        proof_status=ProofStatus.UNKNOWN,
        runtime_guard=True,
        reason="reshape element count",
    )
    return ShapeInference(target, (obligation,))


def transpose_shape(shape: Shape, axes: tuple[int, ...] | list[int]) -> ShapeInference:
    axes = tuple(int(axis) for axis in axes)
    if len(axes) != shape.rank or set(axes) != set(range(shape.rank)):
        raise ShapeError(
            "transpose axes must be a permutation of all axes",
            context={"axes": axes, "rank": shape.rank},
        )
    return ShapeInference(Shape(tuple(shape[index] for index in axes)), ())

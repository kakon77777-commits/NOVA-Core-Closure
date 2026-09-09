from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .errors import ValidationError


@dataclass(frozen=True)
class DimExpr:
    """Normalized affine integer dimension expression.

    The Round 02 decidable core intentionally represents only:
        constant + sum(integer_coefficient * symbol)
    """

    const: int = 0
    terms: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.const, int) or isinstance(self.const, bool):
            raise ValidationError("dimension constant must be an integer")
        merged: dict[str, int] = {}
        for name, coeff in self.terms:
            name = str(name)
            if not name:
                raise ValidationError("dimension symbol must not be empty")
            if not isinstance(coeff, int) or isinstance(coeff, bool):
                raise ValidationError("dimension coefficient must be an integer")
            merged[name] = merged.get(name, 0) + coeff
        normalized = tuple(sorted((name, coeff) for name, coeff in merged.items() if coeff != 0))
        object.__setattr__(self, "terms", normalized)

    @classmethod
    def constant(cls, value: int) -> "DimExpr":
        return cls(const=value)

    @classmethod
    def symbol(cls, name: str) -> "DimExpr":
        if not str(name):
            raise ValidationError("dimension symbol must not be empty")
        return cls(terms=((str(name), 1),))

    @property
    def is_concrete(self) -> bool:
        return not self.terms

    @property
    def concrete_value(self) -> int | None:
        return self.const if self.is_concrete else None

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(name for name, _ in self.terms)

    def to_record(self) -> dict[str, object]:
        return {
            "kind": "affine_dim",
            "const": self.const,
            "terms": [[name, coeff] for name, coeff in self.terms],
        }

    @classmethod
    def from_record(cls, value: Mapping[str, object]) -> "DimExpr":
        if value.get("kind") != "affine_dim":
            raise ValidationError("invalid affine dimension record")
        raw_terms = value.get("terms", ())
        if not isinstance(raw_terms, (list, tuple)):
            raise ValidationError("dimension terms must be a sequence")
        terms: list[tuple[str, int]] = []
        for term in raw_terms:
            if not isinstance(term, (list, tuple)) or len(term) != 2:
                raise ValidationError("dimension term must be [symbol, coefficient]")
            terms.append((str(term[0]), int(term[1])))
        return cls(const=int(value.get("const", 0)), terms=tuple(terms))

    def _coerce(self, other: object) -> "DimExpr":
        if isinstance(other, DimExpr):
            return other
        if isinstance(other, int) and not isinstance(other, bool):
            return DimExpr.constant(other)
        if isinstance(other, str):
            return DimExpr.symbol(other)
        return NotImplemented

    def __add__(self, other: object) -> "DimExpr":
        rhs = self._coerce(other)
        if rhs is NotImplemented:
            return NotImplemented
        return DimExpr(self.const + rhs.const, self.terms + rhs.terms)

    def __radd__(self, other: object) -> "DimExpr":
        return self.__add__(other)

    def __neg__(self) -> "DimExpr":
        return DimExpr(-self.const, tuple((name, -coeff) for name, coeff in self.terms))

    def __sub__(self, other: object) -> "DimExpr":
        rhs = self._coerce(other)
        if rhs is NotImplemented:
            return NotImplemented
        return self + (-rhs)

    def __rsub__(self, other: object) -> "DimExpr":
        lhs = self._coerce(other)
        if lhs is NotImplemented:
            return NotImplemented
        return lhs - self

    def __mul__(self, other: object) -> "DimExpr":
        if not isinstance(other, int) or isinstance(other, bool):
            raise TypeError("affine dimensions can only be multiplied by an integer scalar")
        return DimExpr(self.const * other, tuple((name, coeff * other) for name, coeff in self.terms))

    def __rmul__(self, other: object) -> "DimExpr":
        return self.__mul__(other)


def as_dim(value: DimExpr | int | str) -> DimExpr:
    if isinstance(value, DimExpr):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        if value < 0:
            raise ValidationError("dimension must be non-negative")
        return DimExpr.constant(value)
    if isinstance(value, str):
        return DimExpr.symbol(value)
    raise ValidationError(f"unsupported dimension value: {value!r}")


@dataclass(frozen=True)
class Shape:
    dims: tuple[DimExpr, ...] = ()

    def __post_init__(self) -> None:
        dims = tuple(v if isinstance(v, DimExpr) else as_dim(v) for v in self.dims)
        for dim in dims:
            if dim.is_concrete and dim.const < 0:
                raise ValidationError("dimension must be non-negative")
        object.__setattr__(self, "dims", dims)

    @classmethod
    def of(cls, *dims: DimExpr | int | str) -> "Shape":
        return cls(tuple(as_dim(v) for v in dims))

    @property
    def rank(self) -> int:
        return len(self.dims)

    def __iter__(self):
        return iter(self.dims)

    def __len__(self) -> int:
        return len(self.dims)

    def __getitem__(self, index):
        return self.dims[index]

    def to_record(self) -> dict[str, object]:
        return {"kind": "shape", "dims": [dim.to_record() for dim in self.dims]}

    @classmethod
    def from_record(cls, value: Mapping[str, object]) -> "Shape":
        if value.get("kind") != "shape":
            raise ValidationError("invalid shape record")
        raw_dims = value.get("dims", ())
        if not isinstance(raw_dims, (list, tuple)):
            raise ValidationError("shape dims must be a sequence")
        return cls(tuple(DimExpr.from_record(v) if isinstance(v, Mapping) else as_dim(v) for v in raw_dims))


from enum import Enum
from dataclasses import field

from .errors import ShapeError


class ProofStatus(str, Enum):
    PROVEN = "proven"
    DISPROVEN = "disproven"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ShapeConstraint:
    left: DimExpr
    right: DimExpr
    relation: str = "eq"
    reason: str = "shape equality"

    def __post_init__(self) -> None:
        object.__setattr__(self, "left", as_dim(self.left) if not isinstance(self.left, DimExpr) else self.left)
        object.__setattr__(self, "right", as_dim(self.right) if not isinstance(self.right, DimExpr) else self.right)
        if self.relation != "eq":
            raise ValidationError("Round 02 only supports equality shape constraints")

    def to_record(self) -> dict[str, object]:
        return {
            "kind": "shape_constraint",
            "relation": self.relation,
            "left": self.left.to_record(),
            "right": self.right.to_record(),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ShapeObligation:
    left: object
    right: object
    required_relation: str = "eq"
    proof_status: ProofStatus = ProofStatus.UNKNOWN
    runtime_guard: bool = True
    reason: str = "shape equality"

    def to_record(self) -> dict[str, object]:
        def record(value: object) -> object:
            method = getattr(value, "to_record", None)
            return method() if callable(method) else value
        return {
            "kind": "shape_obligation",
            "required_relation": self.required_relation,
            "left": record(self.left),
            "right": record(self.right),
            "proof_status": self.proof_status.value,
            "runtime_guard": self.runtime_guard,
            "reason": self.reason,
        }


class ShapeSolver:
    """Bounded deterministic equality solver for Round 02 affine dimensions.

    Supported deductions:
    - normalized expression identity;
    - concrete equality/inequality;
    - symbol aliases;
    - direct or single-symbol integral bindings.

    Relations outside this bounded subset remain explicit obligations.
    """

    def __init__(self) -> None:
        self._parent: dict[str, str] = {}
        self._value: dict[str, int] = {}
        self._constraints: list[ShapeConstraint] = []

    def _ensure(self, name: str) -> None:
        if name not in self._parent:
            self._parent[name] = name

    def _find(self, name: str) -> str:
        self._ensure(name)
        parent = self._parent[name]
        if parent != name:
            parent = self._find(parent)
            self._parent[name] = parent
        return parent

    def _bind_root(self, root: str, value: int) -> None:
        if value < 0:
            raise ShapeError(
                "contradictory shape equality: dimension would be negative",
                context={"symbol": root, "value": value},
            )
        current = self._value.get(root)
        if current is not None and current != value:
            raise ShapeError(
                "contradictory shape equality",
                context={"symbol": root, "existing": current, "received": value},
            )
        self._value[root] = value

    def _union(self, left: str, right: str) -> None:
        a = self._find(left)
        b = self._find(right)
        if a == b:
            return
        # Lexical root makes replay/canonical diagnostics deterministic.
        root, child = sorted((a, b))
        va = self._value.get(a)
        vb = self._value.get(b)
        if va is not None and vb is not None and va != vb:
            raise ShapeError(
                "contradictory shape equality",
                context={"left": left, "right": right, "left_value": va, "right_value": vb},
            )
        self._parent[child] = root
        if root not in self._value:
            chosen = va if a == child else vb
            if chosen is not None:
                self._value[root] = chosen
        if child in self._value:
            value = self._value.pop(child)
            self._bind_root(root, value)

    def substitute(self, value: DimExpr | int | str) -> DimExpr:
        expr = value if isinstance(value, DimExpr) else as_dim(value)
        const = expr.const
        terms: list[tuple[str, int]] = []
        for name, coeff in expr.terms:
            root = self._find(name)
            bound = self._value.get(root)
            if bound is None:
                terms.append((root, coeff))
            else:
                const += coeff * bound
        return DimExpr(const=const, terms=tuple(terms))

    @property
    def bindings(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for name in sorted(self._parent):
            root = self._find(name)
            if root in self._value:
                result[name] = self._value[root]
        return result

    @property
    def constraints(self) -> tuple[ShapeConstraint, ...]:
        return tuple(self._constraints)

    def prove_equal(self, left: DimExpr | int | str, right: DimExpr | int | str) -> ProofStatus:
        l = self.substitute(left)
        r = self.substitute(right)
        diff = l - r
        if not diff.terms:
            return ProofStatus.PROVEN if diff.const == 0 else ProofStatus.DISPROVEN
        return ProofStatus.UNKNOWN

    def add_equal(self, left: DimExpr | int | str, right: DimExpr | int | str, *, reason: str = "shape equality") -> ShapeConstraint:
        l = left if isinstance(left, DimExpr) else as_dim(left)
        r = right if isinstance(right, DimExpr) else as_dim(right)
        constraint = ShapeConstraint(l, r, reason=reason)

        reduced = self.substitute(l) - self.substitute(r)
        if not reduced.terms:
            if reduced.const != 0:
                raise ShapeError(
                    "contradictory shape equality",
                    violated_constraints=(reason,),
                    context={"left": l.to_record(), "right": r.to_record()},
                )
            self._constraints.append(constraint)
            return constraint

        if reduced.const == 0 and len(reduced.terms) == 2:
            (a, ca), (b, cb) = reduced.terms
            if {ca, cb} == {-1, 1}:
                self._union(a, b)
                self._constraints.append(constraint)
                return constraint

        if len(reduced.terms) == 1:
            name, coeff = reduced.terms[0]
            numerator = -reduced.const
            if coeff != 0 and numerator % coeff == 0:
                self._bind_root(self._find(name), numerator // coeff)

        self._constraints.append(constraint)
        return constraint

    def require_equal(
        self,
        left: DimExpr | int | str,
        right: DimExpr | int | str,
        *,
        reason: str = "shape equality",
    ) -> ShapeObligation | None:
        l = left if isinstance(left, DimExpr) else as_dim(left)
        r = right if isinstance(right, DimExpr) else as_dim(right)
        status = self.prove_equal(l, r)
        if status is ProofStatus.PROVEN:
            return None
        if status is ProofStatus.DISPROVEN:
            raise ShapeError(
                "shape equality disproven",
                violated_constraints=(reason,),
                context={"left": l.to_record(), "right": r.to_record()},
            )
        return ShapeObligation(
            left=l,
            right=r,
            proof_status=ProofStatus.UNKNOWN,
            runtime_guard=True,
            reason=reason,
        )

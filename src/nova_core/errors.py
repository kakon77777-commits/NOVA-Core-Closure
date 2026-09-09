from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ErrorDetail:
    category: str
    message: str
    path: tuple[str, ...] = ()
    source_nodes: tuple[str, ...] = ()
    violated_constraints: tuple[str, ...] = ()
    context: dict[str, Any] = field(default_factory=dict)
    repair_candidates: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "message": self.message,
            "path": list(self.path),
            "source_nodes": list(self.source_nodes),
            "violated_constraints": list(self.violated_constraints),
            "context": dict(self.context),
            "repair_candidates": list(self.repair_candidates),
        }


class NovaError(Exception):
    category = "NovaError"

    def __init__(
        self,
        message: str,
        *,
        path: tuple[str, ...] = (),
        source_nodes: tuple[str, ...] = (),
        violated_constraints: tuple[str, ...] = (),
        context: dict[str, Any] | None = None,
        repair_candidates: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message)
        self.detail = ErrorDetail(
            category=self.category,
            message=message,
            path=tuple(path),
            source_nodes=tuple(source_nodes),
            violated_constraints=tuple(violated_constraints),
            context=dict(context or {}),
            repair_candidates=tuple(repair_candidates),
        )

    def to_dict(self) -> dict[str, Any]:
        return self.detail.to_dict()


class ValidationError(NovaError):
    category = "ValidationError"


class ConflictError(NovaError):
    category = "ConflictError"


class PatchError(NovaError):
    category = "PatchError"


class DecodeError(NovaError):
    category = "DecodeError"


class MigrationError(NovaError):
    category = "MigrationError"


class ShapeError(NovaError):
    category = "ShapeError"

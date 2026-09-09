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


class ExecutionError(NovaError):
    category = "ExecutionError"


class MissingInputError(ExecutionError):
    category = "MissingInputError"


class RuntimeShapeError(ExecutionError):
    category = "RuntimeShapeError"


class UnsupportedOperationError(ExecutionError):
    category = "UnsupportedOperationError"


class DependencyError(ExecutionError):
    category = "DependencyError"


class BackendError(ExecutionError):
    category = "BackendError"


class ProjectionError(NovaError):
    category = "ProjectionError"


class ProjectionEditError(ProjectionError):
    category = "ProjectionEditError"


class FormulaEditError(ProjectionEditError):
    category = "FormulaEditError"


class DiffError(NovaError):
    category = "DiffError"


class TrainingError(NovaError):
    category = "TrainingError"


class NotebookError(NovaError):
    category = "NotebookError"


class ResourcePlanningError(NovaError):
    category = "ResourcePlanningError"


class ResourceVerificationError(NovaError):
    category = "ResourceVerificationError"


class InteropError(NovaError):
    category = "InteropError"


class DTypeInteropError(InteropError):
    category = "DTypeInteropError"


class DLPackInteropError(InteropError):
    category = "DLPackInteropError"

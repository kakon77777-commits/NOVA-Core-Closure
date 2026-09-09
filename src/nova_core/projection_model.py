from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class ProjectionSnapshot:
    semantic_hash: str
    text: str
    formula: str | None
    graph_view: Mapping[str, Any]
    editable_text: str
    reversibility: Mapping[str, str]
    formula_error: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_view", _freeze_mapping(self.graph_view))
        object.__setattr__(self, "reversibility", _freeze_mapping(self.reversibility))
        if self.formula_error is not None:
            object.__setattr__(self, "formula_error", _freeze_mapping(self.formula_error))

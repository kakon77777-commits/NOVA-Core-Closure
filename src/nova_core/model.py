from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, Mapping
import re

from .errors import ValidationError
from .shape import Shape
from .types import TensorType

_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    return value


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return _freeze(dict(value or {}))


def _tuple_str(value: Iterable[str] | None) -> tuple[str, ...]:
    return tuple(str(v) for v in (value or ()))


@dataclass(frozen=True)
class SchemaHeader:
    nova_core_version: str = "0.12.0"
    schema_version: str = "0.1.0"
    feature_flags: tuple[str, ...] = ()
    migration_history: tuple[str, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not _VERSION_RE.match(self.nova_core_version):
            raise ValidationError("invalid nova_core_version", path=("header", "nova_core_version"))
        if not _VERSION_RE.match(self.schema_version):
            raise ValidationError("invalid schema_version", path=("header", "schema_version"))
        object.__setattr__(self, "feature_flags", tuple(sorted(set(_tuple_str(self.feature_flags)))))
        object.__setattr__(self, "migration_history", _tuple_str(self.migration_history))
        object.__setattr__(self, "provenance", _freeze_mapping(self.provenance))
        object.__setattr__(self, "extensions", _freeze_mapping(self.extensions))


@dataclass(frozen=True)
class Node:
    id: str
    kind: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    value_type: Any = None
    shape_type: Any = None
    effect_type: Any = None
    differentiation_type: Any = None
    source_projection: Any = None
    constraints: tuple[Any, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("node id must not be empty")
        if not self.kind:
            raise ValidationError("node kind must not be empty", source_nodes=(self.id,))
        object.__setattr__(self, "inputs", _tuple_str(self.inputs))
        object.__setattr__(self, "outputs", _tuple_str(self.outputs))
        object.__setattr__(self, "constraints", tuple(_freeze(v) for v in self.constraints))
        object.__setattr__(self, "attributes", _freeze_mapping(self.attributes))
        object.__setattr__(self, "provenance", _freeze_mapping(self.provenance))
        object.__setattr__(self, "extensions", _freeze_mapping(self.extensions))
        object.__setattr__(self, "value_type", _freeze(self.value_type))
        object.__setattr__(self, "shape_type", _freeze(self.shape_type))
        object.__setattr__(self, "effect_type", _freeze(self.effect_type))
        object.__setattr__(self, "differentiation_type", _freeze(self.differentiation_type))
        object.__setattr__(self, "source_projection", _freeze(self.source_projection))
        if isinstance(self.value_type, TensorType) and isinstance(self.shape_type, Shape):
            if self.value_type.shape != self.shape_type:
                raise ValidationError(
                    "tensor value_type shape and shape_type disagree",
                    source_nodes=(self.id,),
                    context={
                        "value_type_shape": self.value_type.shape.to_record(),
                        "shape_type": self.shape_type.to_record(),
                    },
                )


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    kind: str = "value"
    constraints: tuple[Any, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source or not self.target:
            raise ValidationError("edge source and target must not be empty")
        object.__setattr__(self, "constraints", tuple(_freeze(v) for v in self.constraints))
        object.__setattr__(self, "attributes", _freeze_mapping(self.attributes))
        object.__setattr__(self, "provenance", _freeze_mapping(self.provenance))
        object.__setattr__(self, "extensions", _freeze_mapping(self.extensions))

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.source, self.target, self.kind)


@dataclass(frozen=True)
class Graph:
    id: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    nodes: tuple[Node, ...] = ()
    edges: tuple[Edge, ...] = ()
    constraints: tuple[Any, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("graph id must not be empty")
        object.__setattr__(self, "inputs", _tuple_str(self.inputs))
        object.__setattr__(self, "outputs", _tuple_str(self.outputs))
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "edges", tuple(self.edges))
        object.__setattr__(self, "constraints", tuple(_freeze(v) for v in self.constraints))
        object.__setattr__(self, "attributes", _freeze_mapping(self.attributes))
        object.__setattr__(self, "provenance", _freeze_mapping(self.provenance))
        object.__setattr__(self, "extensions", _freeze_mapping(self.extensions))


@dataclass(frozen=True)
class Module:
    id: str
    graphs: tuple[Graph, ...] = ()
    imports: tuple[str, ...] = ()
    exports: tuple[str, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("module id must not be empty")
        object.__setattr__(self, "graphs", tuple(self.graphs))
        object.__setattr__(self, "imports", _tuple_str(self.imports))
        object.__setattr__(self, "exports", _tuple_str(self.exports))
        object.__setattr__(self, "attributes", _freeze_mapping(self.attributes))
        object.__setattr__(self, "provenance", _freeze_mapping(self.provenance))
        object.__setattr__(self, "extensions", _freeze_mapping(self.extensions))


@dataclass(frozen=True)
class Project:
    header: SchemaHeader = field(default_factory=SchemaHeader)
    modules: tuple[Module, ...] = ()
    constraints: tuple[Any, ...] = ()
    artifacts: tuple[Any, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "modules", tuple(self.modules))
        object.__setattr__(self, "constraints", tuple(_freeze(v) for v in self.constraints))
        object.__setattr__(self, "artifacts", tuple(_freeze(v) for v in self.artifacts))
        object.__setattr__(self, "attributes", _freeze_mapping(self.attributes))
        object.__setattr__(self, "provenance", _freeze_mapping(self.provenance))
        object.__setattr__(self, "extensions", _freeze_mapping(self.extensions))
        validate_project(self)


def validate_graph(graph: Graph, *, module_id: str = "") -> None:
    node_ids: set[str] = set()
    produced: set[str] = set(graph.inputs)
    producer: dict[str, str] = {name: "<graph-input>" for name in graph.inputs}

    for node in graph.nodes:
        if node.id in node_ids:
            raise ValidationError(
                f"duplicate node id: {node.id}",
                path=("modules", module_id, "graphs", graph.id),
                source_nodes=(node.id,),
            )
        node_ids.add(node.id)
        for output in node.outputs:
            if output in produced:
                raise ValidationError(
                    f"duplicate output symbol: {output}",
                    path=("modules", module_id, "graphs", graph.id),
                    source_nodes=(node.id, producer.get(output, "")),
                )
            produced.add(output)
            producer[output] = node.id

    for node in graph.nodes:
        unresolved = tuple(name for name in node.inputs if name not in produced)
        if unresolved:
            raise ValidationError(
                f"unresolved node input(s): {', '.join(unresolved)}",
                path=("modules", module_id, "graphs", graph.id, "nodes", node.id),
                source_nodes=(node.id,),
                context={"unresolved": unresolved},
            )

    for edge in graph.edges:
        if edge.source not in node_ids or edge.target not in node_ids:
            raise ValidationError(
                f"edge endpoint does not exist: {edge.source}->{edge.target}",
                path=("modules", module_id, "graphs", graph.id, "edges"),
                source_nodes=(edge.source, edge.target),
            )

    unresolved_outputs = tuple(name for name in graph.outputs if name not in produced)
    if unresolved_outputs:
        raise ValidationError(
            f"unresolved graph output(s): {', '.join(unresolved_outputs)}",
            path=("modules", module_id, "graphs", graph.id, "outputs"),
            context={"unresolved": unresolved_outputs},
        )


def validate_module(module: Module) -> None:
    graph_ids: set[str] = set()
    for graph in module.graphs:
        if graph.id in graph_ids:
            raise ValidationError(
                f"duplicate graph id: {graph.id}",
                path=("modules", module.id),
            )
        graph_ids.add(graph.id)
        validate_graph(graph, module_id=module.id)


def validate_project(project: Project) -> None:
    module_ids: set[str] = set()
    for module in project.modules:
        if module.id in module_ids:
            raise ValidationError(f"duplicate module id: {module.id}", path=("modules",))
        module_ids.add(module.id)
        validate_module(module)

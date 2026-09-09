from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .model import Graph, Node


class BaseSpace(str, Enum):
    CONTINUOUS = "C"
    DISCRETE = "D"


class FillMode(str, Enum):
    SEQUENTIAL = "C"
    JUMP = "J"
    PARALLEL = "P"
    RECOGNITION = "R"


class ObservationMode(str, Enum):
    CONTINUOUS = "C"
    DISCRETE = "D"


@dataclass(frozen=True)
class ParadigmTag:
    index: int
    code: str
    name: str
    base: BaseSpace
    fill: FillMode
    observation: ObservationMode

    @property
    def triple(self) -> tuple[BaseSpace, FillMode, ObservationMode]:
        return (self.base, self.fill, self.observation)

    def to_record(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "code": self.code,
            "name": self.name,
            "base": self.base.value,
            "fill": self.fill.value,
            "observation": self.observation.value,
        }


_PARADIGM_ROWS = (
    (1, "CCC", "continuous sequential continuum"),
    (2, "CCD", "sampled continuous continuum"),
    (3, "DCC", "discrete sequential continuous observation"),
    (4, "DCD", "fully discrete sequential"),
    (5, "CJC", "continuous jump continuous observation"),
    (6, "CJD", "continuous jump discrete observation"),
    (7, "DJC", "discrete jump continuous reconstruction"),
    (8, "DJD", "fully discrete jump"),
    (9, "CPC", "parallel field evolution"),
    (10, "CPD", "parallel continuous-space discrete observation"),
    (11, "DPC", "discrete parallel continuous observation"),
    (12, "DPD", "fully discrete parallel"),
    (13, "CRC", "continuous recognition continuous observation"),
    (14, "CRD", "continuous recognition discrete observation"),
    (15, "DRC", "discrete recognition continuous observation"),
    (16, "DRD", "fully discrete recognition"),
)


def _tag(row: tuple[int, str, str]) -> ParadigmTag:
    index, code, name = row
    return ParadigmTag(
        index=index,
        code=code,
        name=name,
        base=BaseSpace(code[0]),
        fill=FillMode(code[1]),
        observation=ObservationMode(code[2]),
    )


PARADIGMS: tuple[ParadigmTag, ...] = tuple(_tag(row) for row in _PARADIGM_ROWS)
_BY_CODE = {item.code: item for item in PARADIGMS}
_BY_INDEX = {item.index: item for item in PARADIGMS}


def paradigm_by_code(code: str) -> ParadigmTag:
    return _BY_CODE[str(code).upper()]


def paradigm_by_index(index: int) -> ParadigmTag:
    return _BY_INDEX[int(index)]


def paradigm_for(base: BaseSpace, fill: FillMode, observation: ObservationMode) -> ParadigmTag:
    return _BY_CODE[f"{base.value}{fill.value}{observation.value}"]


@dataclass(frozen=True)
class PlannerProfile:
    parallelism: int = 8
    recognition_enabled: bool = True
    stable_cache: bool = False
    random_access_weight: float = 1.0
    synchronization_weight: float = 1.0
    precompute_weight: float = 1.0
    storage_weight: float = 1.0
    maintenance_weight: float = 1.0
    conversion_weight: float = 1.0
    risk_weight: float = 1.0

    def __post_init__(self) -> None:
        if self.parallelism < 1:
            raise ValueError("parallelism must be >= 1")
        for name in (
            "random_access_weight", "synchronization_weight", "precompute_weight",
            "storage_weight", "maintenance_weight", "conversion_weight", "risk_weight",
        ):
            if float(getattr(self, name)) < 0:
                raise ValueError(f"{name} must be nonnegative")


@dataclass(frozen=True)
class RegionEvidence:
    category: str
    detail: str

    def to_record(self) -> dict[str, str]:
        return {"category": self.category, "detail": self.detail}


@dataclass(frozen=True)
class StrategyRegion:
    region_id: str
    graph_id: str
    node_ids: tuple[str, ...]
    node_kinds: tuple[str, ...]
    base: BaseSpace = BaseSpace.DISCRETE
    observation: ObservationMode = ObservationMode.DISCRETE
    evidence: tuple[RegionEvidence, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))


@dataclass(frozen=True)
class ParadigmClassification:
    tag: ParadigmTag
    evidence: tuple[RegionEvidence, ...]
    confidence: str


_SOURCE_KINDS = {"Input", "Parameter", "Constant"}
_SEQUENTIAL_KINDS = {"BoundedLoop", "Loop", "Scan", "While"}
_SELECTIVE_KINDS = {"Gather", "Scatter", "Lookup", "Index", "SparseLookup"}
_PARALLEL_KINDS = {
    "Add", "Subtract", "Multiply", "Divide", "Negate", "MatMul", "Relu", "ReLU",
    "Sigmoid", "Tanh", "Softmax", "Reshape", "Transpose", "ReduceSum", "Mean",
    "Contraction", "Convolution",
}


def _axis_from_attrs(node: Node) -> tuple[BaseSpace, ObservationMode]:
    attrs = node.attributes
    try:
        base = BaseSpace(str(attrs.get("base_space", "D")).upper())
    except ValueError:
        base = BaseSpace.DISCRETE
    try:
        obs = ObservationMode(str(attrs.get("observation", "D")).upper())
    except ValueError:
        obs = ObservationMode.DISCRETE
    return base, obs


def _node_evidence(node: Node) -> tuple[RegionEvidence, ...]:
    attrs = node.attributes
    out: list[RegionEvidence] = []
    if node.kind in _SEQUENTIAL_KINDS or attrs.get("sequential_dependency") is True:
        out.append(RegionEvidence("sequential_dependency", f"{node.id}:{node.kind}"))
    if (
        node.kind in _SELECTIVE_KINDS
        or attrs.get("access_pattern") in {"selective", "sparse", "indexed"}
        or attrs.get("sparse") is True
    ):
        out.append(RegionEvidence("sparse_or_selective_access", f"{node.id}:{node.kind}"))
    if (
        node.kind in _PARALLEL_KINDS
        and not node.effect_type
        and attrs.get("sequential_dependency") is not True
    ) or attrs.get("parallel_independent") is True:
        out.append(RegionEvidence("parallel_independent", f"{node.id}:{node.kind}"))
    if attrs.get("stable_recognition") is True and attrs.get("precomputed") is True:
        out.append(RegionEvidence("stable_recognition", f"{node.id}:{node.kind}"))
    return tuple(out)


def extract_strategy_regions(graph: Graph) -> tuple[StrategyRegion, ...]:
    regions: list[StrategyRegion] = []
    for node in graph.nodes:
        if node.kind in _SOURCE_KINDS:
            continue
        base, obs = _axis_from_attrs(node)
        regions.append(
            StrategyRegion(
                region_id=f"{graph.id}:{node.id}",
                graph_id=graph.id,
                node_ids=(node.id,),
                node_kinds=(node.kind,),
                base=base,
                observation=obs,
                evidence=_node_evidence(node),
                attributes=node.attributes,
            )
        )
    if not regions:
        regions.append(
            StrategyRegion(
                region_id=f"{graph.id}:fallback",
                graph_id=graph.id,
                node_ids=(),
                node_kinds=(),
                evidence=(RegionEvidence("unknown", "no computational node evidence"),),
            )
        )
    return tuple(regions)


def classify_region(region: StrategyRegion, profile: PlannerProfile | None = None) -> tuple[ParadigmClassification, ...]:
    profile = profile or PlannerProfile()
    categories = {item.category for item in region.evidence}
    classifications: list[ParadigmClassification] = []

    def add(fill: FillMode, confidence: str, evidence: tuple[RegionEvidence, ...]) -> None:
        tag = paradigm_for(region.base, fill, region.observation)
        if all(existing.tag != tag for existing in classifications):
            classifications.append(ParadigmClassification(tag, evidence, confidence))

    # Conservative fallback is always representable.
    add(
        FillMode.SEQUENTIAL,
        "fallback" if "sequential_dependency" not in categories else "proven",
        tuple(item for item in region.evidence if item.category == "sequential_dependency")
        or (RegionEvidence("conservative_fallback", "sequential strategy remains available"),),
    )
    if "sparse_or_selective_access" in categories and "sequential_dependency" not in categories:
        add(FillMode.JUMP, "supported", tuple(item for item in region.evidence if item.category == "sparse_or_selective_access"))
    if "parallel_independent" in categories and "sequential_dependency" not in categories:
        add(FillMode.PARALLEL, "supported", tuple(item for item in region.evidence if item.category == "parallel_independent"))
    if "stable_recognition" in categories and profile.recognition_enabled:
        add(FillMode.RECOGNITION, "supported", tuple(item for item in region.evidence if item.category == "stable_recognition"))
    return tuple(classifications)

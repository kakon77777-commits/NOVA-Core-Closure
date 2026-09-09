from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any

from .autodiff import DifferentiationRequest
from .canonical import edge_record, node_record
from .codec import decode_edge, decode_node
from .model import Graph, Project
from .patch import GraphPatch
from .types import TensorType


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    to_record = getattr(value, "to_record", None)
    if callable(to_record):
        return _thaw(to_record())
    return value


_ALLOWED_CONSTRAINTS = {
    "require_graph_output",
    "require_node",
    "require_node_kind",
    "require_tensor_dtype",
    "require_tensor_shape",
    "forbid_effects",
}


class BuildStatus(str, Enum):
    READY = "ready"
    REJECTED = "rejected"


@dataclass(frozen=True)
class AIProvenance:
    request_id: str
    actor_id: str
    source: str = "ai"
    model_id: str | None = None
    session_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.request_id):
            raise ValueError("request_id must not be empty")
        if not str(self.actor_id):
            raise ValueError("actor_id must not be empty")
        if not str(self.source):
            raise ValueError("source must not be empty")
        object.__setattr__(self, "request_id", str(self.request_id))
        object.__setattr__(self, "actor_id", str(self.actor_id))
        object.__setattr__(self, "source", str(self.source))
        object.__setattr__(self, "model_id", None if self.model_id is None else str(self.model_id))
        object.__setattr__(self, "session_id", None if self.session_id is None else str(self.session_id))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))


@dataclass(frozen=True)
class AISandboxPolicy:
    max_added_nodes: int = 16
    max_replaced_nodes: int = 16
    max_removed_nodes: int = 0
    max_added_edges: int = 32
    max_replaced_edges: int = 32
    max_removed_edges: int = 0
    allowed_node_kinds: tuple[str, ...] | None = None
    allow_interface_change: bool = False
    allow_constraint_change: bool = True
    allow_node_removal: bool = False
    allow_effects: bool = False
    allow_test_execution: bool = True
    allow_differentiation: bool = True

    def __post_init__(self) -> None:
        for name in (
            "max_added_nodes",
            "max_replaced_nodes",
            "max_removed_nodes",
            "max_added_edges",
            "max_replaced_edges",
            "max_removed_edges",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.allowed_node_kinds is not None:
            object.__setattr__(
                self,
                "allowed_node_kinds",
                tuple(sorted({str(v) for v in self.allowed_node_kinds if str(v)})),
            )


@dataclass(frozen=True)
class BuildConstraint:
    kind: str
    subject: str
    expected: Any = None
    description: str = ""

    def __post_init__(self) -> None:
        kind = str(self.kind)
        subject = str(self.subject)
        if kind not in _ALLOWED_CONSTRAINTS:
            raise ValueError(f"unsupported build constraint kind: {kind}")
        if not subject:
            raise ValueError("constraint subject must not be empty")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "subject", subject)
        object.__setattr__(self, "expected", _freeze(self.expected))
        object.__setattr__(self, "description", str(self.description))


@dataclass(frozen=True)
class BuildTestCase:
    name: str
    inputs: Mapping[str, Any]
    expected_outputs: Mapping[str, Any]
    parameters: Mapping[str, Any] = field(default_factory=dict)
    backend: str = "interpreter"
    atol: float = 1e-8
    rtol: float = 1e-8

    def __post_init__(self) -> None:
        if not str(self.name):
            raise ValueError("test name must not be empty")
        if str(self.backend) not in {"interpreter", "numpy"}:
            raise ValueError("build test backend must be interpreter or numpy")
        if self.atol < 0 or self.rtol < 0:
            raise ValueError("test tolerances must be non-negative")
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "inputs", _freeze(dict(self.inputs or {})))
        object.__setattr__(self, "expected_outputs", _freeze(dict(self.expected_outputs or {})))
        object.__setattr__(self, "parameters", _freeze(dict(self.parameters or {})))
        object.__setattr__(self, "backend", str(self.backend))


@dataclass(frozen=True)
class SandboxViolation:
    kind: str
    message: str
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", _freeze(dict(self.evidence or {})))


@dataclass(frozen=True)
class SandboxReport:
    passed: bool
    violations: tuple[SandboxViolation, ...] = ()


@dataclass(frozen=True)
class ConstraintCheckResult:
    kind: str
    subject: str
    passed: bool
    message: str
    expected: Any = None
    observed: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "expected", _freeze(self.expected))
        object.__setattr__(self, "observed", _freeze(self.observed))


@dataclass(frozen=True)
class AIBuildRequest:
    provenance: AIProvenance
    patch: GraphPatch
    constraints: tuple[BuildConstraint, ...] = ()
    tests: tuple[BuildTestCase, ...] = ()
    differentiation_requests: tuple[DifferentiationRequest, ...] = ()
    sandbox: AISandboxPolicy = field(default_factory=AISandboxPolicy)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(self, "tests", tuple(self.tests))
        diffs: list[DifferentiationRequest] = []
        for item in self.differentiation_requests:
            if isinstance(item, DifferentiationRequest):
                diffs.append(item)
            elif isinstance(item, Mapping):
                diffs.append(
                    DifferentiationRequest(
                        target=str(item.get("target", "")),
                        wrt=tuple(str(v) for v in item.get("wrt", ())),
                        seed_input=None if item.get("seed_input") is None else str(item.get("seed_input")),
                        derivative_graph_id=None
                        if item.get("derivative_graph_id") is None
                        else str(item.get("derivative_graph_id")),
                    )
                )
            else:
                raise ValueError("differentiation request must be DifferentiationRequest or object")
        object.__setattr__(self, "differentiation_requests", tuple(diffs))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))


def _patch_record(patch: GraphPatch) -> dict[str, Any]:
    return {
        "base_hash": patch.base_hash,
        "base_record_hash": patch.base_record_hash,
        "module_id": patch.module_id,
        "graph_id": patch.graph_id,
        "added_nodes": [node_record(v, semantic=False) for v in patch.added_nodes],
        "removed_node_ids": list(patch.removed_node_ids),
        "replaced_nodes": [node_record(v, semantic=False) for v in patch.replaced_nodes],
        "added_edges": [edge_record(v, semantic=False) for v in patch.added_edges],
        "removed_edge_keys": [list(v) for v in patch.removed_edge_keys],
        "replaced_edges": [edge_record(v, semantic=False) for v in patch.replaced_edges],
        "changed_inputs": None if patch.changed_inputs is None else list(patch.changed_inputs),
        "changed_outputs": None if patch.changed_outputs is None else list(patch.changed_outputs),
        "changed_constraints": None if patch.changed_constraints is None else _thaw(patch.changed_constraints),
        "changed_attributes": None if patch.changed_attributes is None else _thaw(patch.changed_attributes),
        "changed_provenance": None if patch.changed_provenance is None else _thaw(patch.changed_provenance),
        "changed_extensions": None if patch.changed_extensions is None else _thaw(patch.changed_extensions),
        "proof_obligations": list(patch.proof_obligations),
        "tests": list(patch.tests),
        "rationale": patch.rationale,
        "provenance": _thaw(patch.provenance),
    }


def _decode_patch(value: Mapping[str, Any]) -> GraphPatch:
    def opt_tuple(name: str):
        raw = value.get(name)
        return None if raw is None else tuple(raw)

    return GraphPatch(
        base_hash=str(value.get("base_hash", "")),
        base_record_hash=None if value.get("base_record_hash") is None else str(value.get("base_record_hash")),
        module_id=str(value.get("module_id", "")),
        graph_id=str(value.get("graph_id", "")),
        added_nodes=tuple(decode_node(v) for v in value.get("added_nodes", ())),
        removed_node_ids=tuple(str(v) for v in value.get("removed_node_ids", ())),
        replaced_nodes=tuple(decode_node(v) for v in value.get("replaced_nodes", ())),
        added_edges=tuple(decode_edge(v) for v in value.get("added_edges", ())),
        removed_edge_keys=tuple(tuple(str(x) for x in v) for v in value.get("removed_edge_keys", ())),
        replaced_edges=tuple(decode_edge(v) for v in value.get("replaced_edges", ())),
        changed_inputs=opt_tuple("changed_inputs"),
        changed_outputs=opt_tuple("changed_outputs"),
        changed_constraints=opt_tuple("changed_constraints"),
        changed_attributes=value.get("changed_attributes"),
        changed_provenance=value.get("changed_provenance"),
        changed_extensions=value.get("changed_extensions"),
        proof_obligations=tuple(str(v) for v in value.get("proof_obligations", ())),
        tests=tuple(str(v) for v in value.get("tests", ())),
        rationale=str(value.get("rationale", "")),
        provenance=dict(value.get("provenance", {}) or {}),
    )


def _provenance_record(value: AIProvenance) -> dict[str, Any]:
    return {
        "request_id": value.request_id,
        "actor_id": value.actor_id,
        "source": value.source,
        "model_id": value.model_id,
        "session_id": value.session_id,
        "metadata": _thaw(value.metadata),
    }


def _sandbox_record(value: AISandboxPolicy) -> dict[str, Any]:
    return {
        "max_added_nodes": value.max_added_nodes,
        "max_replaced_nodes": value.max_replaced_nodes,
        "max_removed_nodes": value.max_removed_nodes,
        "max_added_edges": value.max_added_edges,
        "max_replaced_edges": value.max_replaced_edges,
        "max_removed_edges": value.max_removed_edges,
        "allowed_node_kinds": None if value.allowed_node_kinds is None else list(value.allowed_node_kinds),
        "allow_interface_change": value.allow_interface_change,
        "allow_constraint_change": value.allow_constraint_change,
        "allow_node_removal": value.allow_node_removal,
        "allow_effects": value.allow_effects,
        "allow_test_execution": value.allow_test_execution,
        "allow_differentiation": value.allow_differentiation,
    }


def ai_build_request_record(request: AIBuildRequest) -> dict[str, Any]:
    return {
        "version": "0.1.0",
        "provenance": _provenance_record(request.provenance),
        "patch": _patch_record(request.patch),
        "constraints": [
            {
                "kind": v.kind,
                "subject": v.subject,
                "expected": _thaw(v.expected),
                "description": v.description,
            }
            for v in request.constraints
        ],
        "tests": [
            {
                "name": v.name,
                "inputs": _thaw(v.inputs),
                "parameters": _thaw(v.parameters),
                "expected_outputs": _thaw(v.expected_outputs),
                "backend": v.backend,
                "atol": v.atol,
                "rtol": v.rtol,
            }
            for v in request.tests
        ],
        "differentiation_requests": [
            {
                "target": v.target,
                "wrt": list(v.wrt),
                "seed_input": v.seed_input,
                "derivative_graph_id": v.derivative_graph_id,
            }
            for v in request.differentiation_requests
        ],
        "sandbox": _sandbox_record(request.sandbox),
        "metadata": _thaw(request.metadata),
    }


def encode_ai_build_request(request: AIBuildRequest) -> str:
    return json.dumps(ai_build_request_record(request), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def decode_ai_build_request(value: str | bytes | Mapping[str, Any]) -> AIBuildRequest:
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, Mapping):
        raise ValueError("AI build request must be a JSON object")
    provenance = value.get("provenance", {})
    patch = value.get("patch", {})
    sandbox = value.get("sandbox", {})
    if not isinstance(provenance, Mapping) or not isinstance(patch, Mapping) or not isinstance(sandbox, Mapping):
        raise ValueError("invalid AI build request object")
    return AIBuildRequest(
        provenance=AIProvenance(
            request_id=str(provenance.get("request_id", "")),
            actor_id=str(provenance.get("actor_id", "")),
            source=str(provenance.get("source", "ai")),
            model_id=None if provenance.get("model_id") is None else str(provenance.get("model_id")),
            session_id=None if provenance.get("session_id") is None else str(provenance.get("session_id")),
            metadata=dict(provenance.get("metadata", {}) or {}),
        ),
        patch=_decode_patch(patch),
        constraints=tuple(
            BuildConstraint(
                kind=str(v.get("kind", "")),
                subject=str(v.get("subject", "")),
                expected=v.get("expected"),
                description=str(v.get("description", "")),
            )
            for v in value.get("constraints", ())
        ),
        tests=tuple(
            BuildTestCase(
                name=str(v.get("name", "")),
                inputs=dict(v.get("inputs", {}) or {}),
                parameters=dict(v.get("parameters", {}) or {}),
                expected_outputs=dict(v.get("expected_outputs", {}) or {}),
                backend=str(v.get("backend", "interpreter")),
                atol=float(v.get("atol", 1e-8)),
                rtol=float(v.get("rtol", 1e-8)),
            )
            for v in value.get("tests", ())
        ),
        differentiation_requests=tuple(value.get("differentiation_requests", ())),
        sandbox=AISandboxPolicy(**dict(sandbox)),
        metadata=dict(value.get("metadata", {}) or {}),
    )


def ai_build_request_hash(request: AIBuildRequest) -> str:
    return "sha256:" + hashlib.sha256(encode_ai_build_request(request).encode("utf-8")).hexdigest()


def _target_exists(project: Project, module_id: str, graph_id: str) -> bool:
    for module in project.modules:
        if module.id == module_id:
            return any(graph.id == graph_id for graph in module.graphs)
    return False


def _effect_nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, (tuple, list, set, frozenset, str)):
        return bool(value)
    return True


def check_ai_sandbox(project: Project, request: AIBuildRequest) -> SandboxReport:
    p = request.patch
    s = request.sandbox
    violations: list[SandboxViolation] = []
    if not _target_exists(project, p.module_id, p.graph_id):
        violations.append(SandboxViolation("target_not_found", "target module/graph does not exist"))

    checks = (
        ("added_node_budget", len(p.added_nodes), s.max_added_nodes),
        ("replaced_node_budget", len(p.replaced_nodes), s.max_replaced_nodes),
        ("removed_node_budget", len(p.removed_node_ids), s.max_removed_nodes),
        ("added_edge_budget", len(p.added_edges), s.max_added_edges),
        ("replaced_edge_budget", len(p.replaced_edges), s.max_replaced_edges),
        ("removed_edge_budget", len(p.removed_edge_keys), s.max_removed_edges),
    )
    for kind, observed, limit in checks:
        if observed > limit:
            violations.append(SandboxViolation(kind, f"patch exceeds {kind}", {"observed": observed, "limit": limit}))

    if p.removed_node_ids and not s.allow_node_removal:
        violations.append(SandboxViolation("node_removal_forbidden", "node removal is forbidden"))
    if (p.changed_inputs is not None or p.changed_outputs is not None) and not s.allow_interface_change:
        violations.append(SandboxViolation("interface_change_forbidden", "graph interface changes are forbidden"))
    if p.changed_constraints is not None and not s.allow_constraint_change:
        violations.append(SandboxViolation("constraint_change_forbidden", "graph constraint changes are forbidden"))

    changed_nodes = tuple(p.added_nodes) + tuple(p.replaced_nodes)
    if s.allowed_node_kinds is not None:
        allowed = set(s.allowed_node_kinds)
        for node in changed_nodes:
            if node.kind not in allowed:
                violations.append(
                    SandboxViolation(
                        "node_kind_forbidden",
                        "node kind is not allowed by sandbox",
                        {"node_id": node.id, "kind": node.kind},
                    )
                )
    if not s.allow_effects:
        for node in changed_nodes:
            if _effect_nonempty(node.effect_type):
                violations.append(
                    SandboxViolation(
                        "effects_forbidden",
                        "effectful node is forbidden by sandbox",
                        {"node_id": node.id, "effect_type": _thaw(node.effect_type)},
                    )
                )
    if request.tests and not s.allow_test_execution:
        violations.append(SandboxViolation("test_execution_forbidden", "sandbox forbids validation test execution"))
    if request.differentiation_requests and not s.allow_differentiation:
        violations.append(SandboxViolation("differentiation_forbidden", "sandbox forbids differentiation validation"))
    return SandboxReport(passed=not violations, violations=tuple(violations))


def _shape_observed(value: TensorType) -> list[Any]:
    out: list[Any] = []
    for dim in value.shape:
        if dim.is_concrete:
            out.append(dim.const)
        else:
            out.append(dim.to_record())
    return out


def evaluate_build_constraints(graph: Graph, constraints: tuple[BuildConstraint, ...]) -> tuple[ConstraintCheckResult, ...]:
    nodes = {node.id: node for node in graph.nodes}
    results: list[ConstraintCheckResult] = []
    for constraint in constraints:
        kind = constraint.kind
        subject = constraint.subject
        passed = False
        observed: Any = None
        message = "constraint failed"
        if kind == "require_graph_output":
            observed = list(graph.outputs)
            passed = subject in graph.outputs
            message = "graph output present" if passed else "required graph output missing"
        elif kind == "require_node":
            observed = sorted(nodes)
            passed = subject in nodes
            message = "node present" if passed else "required node missing"
        elif kind == "require_node_kind":
            node = nodes.get(subject)
            observed = None if node is None else node.kind
            passed = node is not None and observed == constraint.expected
            message = "node kind matches" if passed else "node kind mismatch"
        elif kind == "require_tensor_dtype":
            node = nodes.get(subject)
            observed = node.value_type.dtype if node is not None and isinstance(node.value_type, TensorType) else None
            passed = observed == constraint.expected
            message = "tensor dtype matches" if passed else "tensor dtype mismatch"
        elif kind == "require_tensor_shape":
            node = nodes.get(subject)
            observed = _shape_observed(node.value_type) if node is not None and isinstance(node.value_type, TensorType) else None
            expected = _thaw(constraint.expected)
            passed = observed == expected
            message = "tensor shape matches" if passed else "tensor shape mismatch"
        elif kind == "forbid_effects":
            effectful = [node.id for node in graph.nodes if _effect_nonempty(node.effect_type)]
            observed = effectful
            passed = not effectful
            message = "graph is effect-free" if passed else "graph contains effects"
        results.append(
            ConstraintCheckResult(
                kind=kind,
                subject=subject,
                passed=passed,
                message=message,
                expected=constraint.expected,
                observed=observed,
            )
        )
    return tuple(results)


@dataclass(frozen=True)
class BuildTestResult:
    name: str
    passed: bool
    backend: str
    message: str
    expected_outputs: Mapping[str, Any] = field(default_factory=dict)
    observed_outputs: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "expected_outputs", _freeze(dict(self.expected_outputs or {})))
        object.__setattr__(self, "observed_outputs", _freeze(dict(self.observed_outputs or {})))


@dataclass(frozen=True)
class DifferentiationEvidence:
    target: str
    wrt: tuple[str, ...]
    passed: bool
    derivative_semantic_hash: str | None = None
    gradients: Mapping[str, str] = field(default_factory=dict)
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "wrt", tuple(str(v) for v in self.wrt))
        object.__setattr__(self, "gradients", _freeze(dict(self.gradients or {})))


@dataclass(frozen=True)
class AIBuildCandidate:
    status: BuildStatus
    request: AIBuildRequest
    request_hash: str
    before_semantic_hash: str
    before_record_hash: str
    sandbox: SandboxReport
    constraints: tuple[ConstraintCheckResult, ...] = ()
    tests: tuple[BuildTestResult, ...] = ()
    differentiation: tuple[DifferentiationEvidence, ...] = ()
    candidate_project: Project | None = None
    candidate_semantic_hash: str | None = None
    candidate_record_hash: str | None = None
    diff: Any = None
    error: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(self, "tests", tuple(self.tests))
        object.__setattr__(self, "differentiation", tuple(self.differentiation))
        if self.error is not None:
            object.__setattr__(self, "error", _freeze(dict(self.error)))


def _find_target_graph(project: Project, module_id: str, graph_id: str):
    for module in project.modules:
        if module.id != module_id:
            continue
        graph = next((item for item in module.graphs if item.id == graph_id), None)
        if graph is None:
            break
        return module, graph, {item.id: item for item in module.graphs}
    raise ValueError(f"target graph not found: {module_id}/{graph_id}")


def _error_dict(exc: Exception) -> dict[str, Any]:
    to_dict = getattr(exc, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    return {"category": type(exc).__name__, "message": str(exc)}


def _run_build_test(project: Project, graph: Graph, graph_lookup: Mapping[str, Graph], case: BuildTestCase) -> BuildTestResult:
    import numpy as np

    from .backends import NumPyBackend
    from .interpreter import Interpreter

    backend = Interpreter() if case.backend == "interpreter" else NumPyBackend()
    try:
        result = backend.run_graph(
            graph,
            _thaw(case.inputs),
            parameters=_thaw(case.parameters),
            graph_lookup=graph_lookup,
        )
        observed = {str(k): v for k, v in result.outputs.items()}
        expected = _thaw(case.expected_outputs)
        missing = [name for name in expected if name not in observed]
        if missing:
            return BuildTestResult(
                name=case.name,
                passed=False,
                backend=case.backend,
                message=f"expected output missing: {', '.join(missing)}",
                expected_outputs=expected,
                observed_outputs={k: _thaw(v) for k, v in observed.items()},
            )
        for name, exp in expected.items():
            obs = observed[name]
            try:
                equal = bool(np.allclose(np.asarray(obs), np.asarray(exp), atol=case.atol, rtol=case.rtol, equal_nan=True))
            except Exception:
                equal = obs == exp
            if not equal:
                return BuildTestResult(
                    name=case.name,
                    passed=False,
                    backend=case.backend,
                    message=f"output mismatch: {name}",
                    expected_outputs=expected,
                    observed_outputs={k: _thaw(v) for k, v in observed.items()},
                )
        return BuildTestResult(
            name=case.name,
            passed=True,
            backend=case.backend,
            message="passed",
            expected_outputs=expected,
            observed_outputs={k: _thaw(v) for k, v in observed.items()},
        )
    except Exception as exc:
        return BuildTestResult(
            name=case.name,
            passed=False,
            backend=case.backend,
            message=f"{type(exc).__name__}: {exc}",
            expected_outputs=_thaw(case.expected_outputs),
            observed_outputs={},
        )


def _run_diff_request(graph: Graph, request: DifferentiationRequest) -> DifferentiationEvidence:
    from .autodiff import differentiate_graph
    from .canonical import semantic_hash

    try:
        result = differentiate_graph(graph, request)
        return DifferentiationEvidence(
            target=request.target,
            wrt=request.wrt,
            passed=True,
            derivative_semantic_hash=semantic_hash(result.graph),
            gradients=result.gradients,
            message="passed",
        )
    except Exception as exc:
        return DifferentiationEvidence(
            target=request.target,
            wrt=request.wrt,
            passed=False,
            message=f"{type(exc).__name__}: {exc}",
        )


def preview_ai_build(project: Project, request: AIBuildRequest) -> AIBuildCandidate:
    from .canonical import record_hash, semantic_hash
    from .diff import diff_graphs
    from .patch import apply_graph_patch

    before_sem = semantic_hash(project)
    before_rec = record_hash(project)
    req_hash = ai_build_request_hash(request)
    sandbox = check_ai_sandbox(project, request)
    if not sandbox.passed:
        return AIBuildCandidate(
            status=BuildStatus.REJECTED,
            request=request,
            request_hash=req_hash,
            before_semantic_hash=before_sem,
            before_record_hash=before_rec,
            sandbox=sandbox,
            error={"category": "AISandboxError", "message": "AI build request rejected by sandbox"},
        )

    try:
        _, before_graph, _ = _find_target_graph(project, request.patch.module_id, request.patch.graph_id)
        patch_result = apply_graph_patch(project, request.patch)
        candidate_project = patch_result.project
        _, candidate_graph, lookup = _find_target_graph(
            candidate_project, request.patch.module_id, request.patch.graph_id
        )
        diff = diff_graphs(before_graph, candidate_graph)
    except Exception as exc:
        return AIBuildCandidate(
            status=BuildStatus.REJECTED,
            request=request,
            request_hash=req_hash,
            before_semantic_hash=before_sem,
            before_record_hash=before_rec,
            sandbox=sandbox,
            error=_error_dict(exc),
        )

    constraint_results = evaluate_build_constraints(candidate_graph, request.constraints)
    test_results = tuple(_run_build_test(candidate_project, candidate_graph, lookup, case) for case in request.tests)
    diff_results = tuple(_run_diff_request(candidate_graph, item) for item in request.differentiation_requests)
    ready = (
        all(item.passed for item in constraint_results)
        and all(item.passed for item in test_results)
        and all(item.passed for item in diff_results)
    )
    return AIBuildCandidate(
        status=BuildStatus.READY if ready else BuildStatus.REJECTED,
        request=request,
        request_hash=req_hash,
        before_semantic_hash=before_sem,
        before_record_hash=before_rec,
        sandbox=sandbox,
        constraints=constraint_results,
        tests=test_results,
        differentiation=diff_results,
        candidate_project=candidate_project,
        candidate_semantic_hash=semantic_hash(candidate_project),
        candidate_record_hash=record_hash(candidate_project),
        diff=diff,
        error=None if ready else {"category": "AIBuildValidationError", "message": "one or more build obligations failed"},
    )


@dataclass(frozen=True)
class AIBuildCommitResult:
    project: Project
    request_id: str
    request_hash: str
    before_semantic_hash: str
    before_record_hash: str
    after_semantic_hash: str
    after_record_hash: str
    candidate_semantic_hash: str
    candidate_record_hash: str


class AIBuildTransaction:
    def __init__(self, project: Project) -> None:
        from .patch import GraphTransaction

        self._tx = GraphTransaction(project)

    @property
    def current(self) -> Project:
        return self._tx.current

    @property
    def semantic_hash(self) -> str:
        return self._tx.semantic_hash

    @property
    def record_hash(self) -> str:
        return self._tx.record_hash

    @property
    def history_depth(self) -> int:
        return self._tx.history_depth

    def preview(self, request: AIBuildRequest) -> AIBuildCandidate:
        return preview_ai_build(self.current, request)

    def commit(self, candidate: AIBuildCandidate) -> AIBuildCommitResult:
        from .errors import AIBuildConflictError, AIBuildError

        if candidate.status is not BuildStatus.READY:
            raise AIBuildError(
                "only READY AI build candidates may be committed",
                context={"status": candidate.status.value, "request_id": candidate.request.provenance.request_id},
            )
        actual_request_hash = ai_build_request_hash(candidate.request)
        if actual_request_hash != candidate.request_hash:
            raise AIBuildConflictError(
                "AI build request hash changed after preview",
                context={"expected": candidate.request_hash, "observed": actual_request_hash},
            )
        if self.semantic_hash != candidate.before_semantic_hash or self.record_hash != candidate.before_record_hash:
            raise AIBuildConflictError(
                "AI build candidate is stale for the current working project",
                context={
                    "expected_semantic_hash": candidate.before_semantic_hash,
                    "current_semantic_hash": self.semantic_hash,
                    "expected_record_hash": candidate.before_record_hash,
                    "current_record_hash": self.record_hash,
                },
            )
        fresh = preview_ai_build(self.current, candidate.request)
        if fresh.status is not BuildStatus.READY:
            raise AIBuildConflictError(
                "AI build candidate no longer passes preview validation",
                context={"status": fresh.status.value, "error": None if fresh.error is None else dict(fresh.error)},
            )
        if (
            fresh.candidate_semantic_hash != candidate.candidate_semantic_hash
            or fresh.candidate_record_hash != candidate.candidate_record_hash
        ):
            raise AIBuildConflictError(
                "AI build preview and commit candidate hashes diverged",
                context={
                    "preview_semantic_hash": candidate.candidate_semantic_hash,
                    "fresh_semantic_hash": fresh.candidate_semantic_hash,
                    "preview_record_hash": candidate.candidate_record_hash,
                    "fresh_record_hash": fresh.candidate_record_hash,
                },
            )
        patch_result = self._tx.apply(candidate.request.patch)
        if (
            patch_result.after_hash != candidate.candidate_semantic_hash
            or patch_result.after_record_hash != candidate.candidate_record_hash
        ):
            # This path should be unreachable after fresh preview. Roll back defensively.
            self._tx.rollback()
            raise AIBuildConflictError("committed GraphPatch did not reproduce preview identity")
        return AIBuildCommitResult(
            project=patch_result.project,
            request_id=candidate.request.provenance.request_id,
            request_hash=candidate.request_hash,
            before_semantic_hash=patch_result.before_hash,
            before_record_hash=patch_result.before_record_hash or candidate.before_record_hash,
            after_semantic_hash=patch_result.after_hash,
            after_record_hash=patch_result.after_record_hash or candidate.candidate_record_hash or "",
            candidate_semantic_hash=candidate.candidate_semantic_hash or "",
            candidate_record_hash=candidate.candidate_record_hash or "",
        )

    def rollback(self) -> Project:
        return self._tx.rollback()

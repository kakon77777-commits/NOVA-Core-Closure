from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .canonical import semantic_hash
from .core_norm import DEFAULT_CORE_NORM_PROFILE, CoreNormProfile, core_norm_bytes, core_norm_hash
from .errors import ValidationError
from .model import Project
from .surface_ai import lower_ai_surface
from .surface_graph import lower_graph_surface
from .surface_text import lower_text_surface

CROSS_RECONSTRUCTION_REVISION = 1


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _source_bytes(kind: str, source: Any) -> bytes:
    if kind == "text":
        if not isinstance(source, str):
            raise ValidationError("text reconstruction source must be a string")
        return source.encode("utf-8")
    if isinstance(source, str):
        return source.encode("utf-8")
    if isinstance(source, Mapping):
        return _stable_json(source).encode("utf-8")
    raise ValidationError("structured reconstruction source must be string or mapping")


def _hash_bytes(tag: bytes, payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(tag + payload).hexdigest()


@dataclass(frozen=True)
class ReconstructionResult:
    representation_kind: str
    adapter_revision: int
    source_hash: str
    lowered_semantic_hash: str
    core_norm_hash: str
    core_norm_size: int
    project: Project
    obligations: tuple[str, ...] = ()

    def to_record(self, *, include_project: bool = False) -> dict[str, Any]:
        record = {
            "representation_kind": self.representation_kind,
            "adapter_revision": self.adapter_revision,
            "source_hash": self.source_hash,
            "lowered_semantic_hash": self.lowered_semantic_hash,
            "core_norm_hash": self.core_norm_hash,
            "core_norm_size": self.core_norm_size,
            "obligations": list(self.obligations),
        }
        if include_project:
            from .canonical import project_record
            record["project"] = project_record(self.project, semantic=True)
        return record


@dataclass(frozen=True)
class CrossRepresentationCertificate:
    revision: int
    profile_hash: str
    reconstructions: tuple[ReconstructionResult, ...]
    converged: bool
    common_core_norm_hash: str | None
    claim_boundary: str = (
        "bounded adapter reconstruction plus CoreNorm profile equivalence; "
        "not global language or behavioral equivalence"
    )

    def to_record(self) -> dict[str, Any]:
        return {
            "revision": self.revision,
            "profile_hash": self.profile_hash,
            "reconstructions": [item.to_record() for item in self.reconstructions],
            "converged": self.converged,
            "common_core_norm_hash": self.common_core_norm_hash,
            "claim_boundary": self.claim_boundary,
        }


def _profile_hash(profile: CoreNormProfile) -> str:
    return _hash_bytes(b"NOVA-CROSS-REP-PROFILE-v0.8\0", _stable_json(profile.to_record()).encode("utf-8"))


def reconstruct_surface(
    kind: str,
    source: Any,
    *,
    profile: CoreNormProfile = DEFAULT_CORE_NORM_PROFILE,
) -> ReconstructionResult:
    normalized_kind = str(kind).strip().lower()
    if normalized_kind == "text":
        project = lower_text_surface(source)
    elif normalized_kind == "graph":
        project = lower_graph_surface(source)
    elif normalized_kind == "ai":
        project = lower_ai_surface(source)
    else:
        raise ValidationError("unknown reconstruction surface kind", context={"kind": kind})
    norm = core_norm_bytes(project, profile=profile)
    return ReconstructionResult(
        representation_kind=normalized_kind,
        adapter_revision=CROSS_RECONSTRUCTION_REVISION,
        source_hash=_hash_bytes(b"NOVA-CROSS-REP-SOURCE-v0.8\0" + normalized_kind.encode("ascii") + b"\0", _source_bytes(normalized_kind, source)),
        lowered_semantic_hash=semantic_hash(project),
        core_norm_hash=core_norm_hash(project, profile=profile),
        core_norm_size=len(norm),
        project=project,
        obligations=(),
    )


def certify_reconstructions(
    sources: Mapping[str, Any],
    *,
    profile: CoreNormProfile = DEFAULT_CORE_NORM_PROFILE,
) -> CrossRepresentationCertificate:
    if not sources:
        raise ValidationError("cross-representation certificate needs at least one source")
    results = tuple(reconstruct_surface(kind, source, profile=profile) for kind, source in sorted(sources.items()))
    hashes = {item.core_norm_hash for item in results}
    converged = len(hashes) == 1
    common = next(iter(hashes)) if converged else None
    return CrossRepresentationCertificate(
        revision=CROSS_RECONSTRUCTION_REVISION,
        profile_hash=_profile_hash(profile),
        reconstructions=results,
        converged=converged,
        common_core_norm_hash=common,
    )


def certify_triad(
    text_source: str,
    graph_source: str | Mapping[str, Any],
    ai_source: str | Mapping[str, Any],
    *,
    profile: CoreNormProfile = DEFAULT_CORE_NORM_PROFILE,
) -> CrossRepresentationCertificate:
    return certify_reconstructions({"text": text_source, "graph": graph_source, "ai": ai_source}, profile=profile)


__all__ = [
    "CROSS_RECONSTRUCTION_REVISION",
    "CrossRepresentationCertificate",
    "ReconstructionResult",
    "certify_reconstructions",
    "certify_triad",
    "reconstruct_surface",
]

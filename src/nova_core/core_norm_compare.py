from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .core_norm import CoreNormProfile, DEFAULT_CORE_NORM_PROFILE, core_norm_project
from .model import Project


def _stable_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def core_norm_profile_hash(profile: CoreNormProfile = DEFAULT_CORE_NORM_PROFILE) -> str:
    return "sha256:" + hashlib.sha256(
        b"NOVA-CORENORM-PROFILE-v0.7\0" + _stable_bytes(profile.to_record())
    ).hexdigest()


def _first_difference(left: Any, right: Any, path: tuple[Any, ...] = ()) -> tuple[tuple[Any, ...], Any, Any] | None:
    if type(left) is not type(right):
        return path, left, right
    if isinstance(left, dict):
        left_keys = sorted(left.keys(), key=str)
        right_keys = sorted(right.keys(), key=str)
        if left_keys != right_keys:
            return path + ("<keys>",), left_keys, right_keys
        for key in left_keys:
            hit = _first_difference(left[key], right[key], path + (key,))
            if hit is not None:
                return hit
        return None
    if isinstance(left, list):
        if len(left) != len(right):
            return path + ("<length>",), len(left), len(right)
        for index, (a, b) in enumerate(zip(left, right)):
            hit = _first_difference(a, b, path + (index,))
            if hit is not None:
                return hit
        return None
    if left != right:
        return path, left, right
    return None


@dataclass(frozen=True)
class CoreNormComparison:
    equivalent: bool
    left_source_hash: str
    right_source_hash: str
    left_core_norm_hash: str
    right_core_norm_hash: str
    profile_hash: str
    first_difference_path: tuple[Any, ...] = ()
    first_left_value: Any = None
    first_right_value: Any = None

    def to_record(self) -> dict[str, Any]:
        return {
            "format": "nova.corenorm-comparison/0.7",
            "equivalent": self.equivalent,
            "left_source_hash": self.left_source_hash,
            "right_source_hash": self.right_source_hash,
            "left_core_norm_hash": self.left_core_norm_hash,
            "right_core_norm_hash": self.right_core_norm_hash,
            "profile_hash": self.profile_hash,
            "first_difference_path": list(self.first_difference_path),
            "first_left_value": self.first_left_value,
            "first_right_value": self.first_right_value,
            "claim_boundary": "bounded CoreNorm profile equivalence; not global semantic equivalence",
        }


def compare_core_norm(
    left: Project,
    right: Project,
    *,
    profile: CoreNormProfile = DEFAULT_CORE_NORM_PROFILE,
) -> CoreNormComparison:
    a = core_norm_project(left, profile=profile)
    b = core_norm_project(right, profile=profile)
    equivalent = a.hash == b.hash and dict(a.record) == dict(b.record)
    diff = None if equivalent else _first_difference(dict(a.record), dict(b.record))
    path, left_value, right_value = ((), None, None) if diff is None else diff
    return CoreNormComparison(
        equivalent=equivalent,
        left_source_hash=a.witness.source_semantic_hash,
        right_source_hash=b.witness.source_semantic_hash,
        left_core_norm_hash=a.hash,
        right_core_norm_hash=b.hash,
        profile_hash=core_norm_profile_hash(profile),
        first_difference_path=path,
        first_left_value=left_value,
        first_right_value=right_value,
    )


__all__ = ["CoreNormComparison", "compare_core_norm", "core_norm_profile_hash"]

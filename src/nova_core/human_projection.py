from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .identity_model import IdentityManifest, StructuralID
from .symbol_domains import DomainText, SymbolDomain


PURIFICATION_REVISION = 1
_DROP = object()


def _jsonable(value: Any) -> Any:
    to_record = getattr(value, "to_record", None)
    if callable(to_record):
        return _jsonable(to_record())
    if isinstance(value, DomainText):
        return {"$domain": value.domain.value, "$text": value.text}
    if isinstance(value, StructuralID):
        return {"$sid": value.text}
    if isinstance(value, bytes):
        return {"$bytes": value.hex()}
    if isinstance(value, Mapping):
        pairs = [(_jsonable(key), _jsonable(item)) for key, item in value.items()]
        pairs.sort(key=lambda pair: json.dumps(pair[0], ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return {"$map": [[key, item] for key, item in pairs]}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _stable_blob(value: Any) -> bytes:
    return json.dumps(
        _jsonable(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def semantic_anchor(value: Any) -> str:
    return "sha256:" + hashlib.sha256(b"NOVA-PROJECTION-ANCHOR-v0.5\0" + _stable_blob(value)).hexdigest()


def _path_token(value: Any) -> str:
    if isinstance(value, DomainText):
        return f"domain:{value.domain.value}:{value.text}"
    if isinstance(value, bytes):
        return "sid-bytes:" + value.hex()
    return str(value)


@dataclass(frozen=True)
class HumanProjectionEntry:
    owner_sid: str
    semantic_anchor: str
    path_hint: tuple[str, ...]
    text: str
    role: str = "value"
    payload: Any = None

    def to_record(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "owner_sid": self.owner_sid,
            "semantic_anchor": self.semantic_anchor,
            "path_hint": list(self.path_hint),
            "text": self.text,
            "role": self.role,
        }
        if self.payload is not None:
            record["payload"] = _jsonable(self.payload)
        return record


@dataclass(frozen=True)
class PurificationResult:
    record: Any
    entries: tuple[HumanProjectionEntry, ...]

    @property
    def human_projection_count(self) -> int:
        return len(self.entries)

    @property
    def pure(self) -> bool:
        return not contains_human_projection(self.record)


def contains_human_projection(value: Any) -> bool:
    if isinstance(value, DomainText):
        return value.domain is SymbolDomain.HUMAN_PROJECTION
    if isinstance(value, Mapping):
        return any(contains_human_projection(key) or contains_human_projection(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(contains_human_projection(item) for item in value)
    return False


def _owner_from_mapping(mapping: Mapping[Any, Any], inherited: StructuralID) -> StructuralID:
    raw = mapping.get("id")
    if isinstance(raw, (bytes, bytearray)) and len(raw) == 16:
        try:
            return StructuralID(bytes(raw))
        except Exception:
            return inherited
    return inherited


def _sort_constraints_if_needed(mapping: dict[Any, Any]) -> None:
    constraints = mapping.get("constraints")
    if isinstance(constraints, list):
        constraints.sort(key=_stable_blob)


def _purify(
    value: Any,
    *,
    owner: StructuralID,
    path: tuple[str, ...],
) -> tuple[Any, list[HumanProjectionEntry]]:
    if isinstance(value, DomainText):
        if value.domain is SymbolDomain.HUMAN_PROJECTION:
            return _DROP, [
                HumanProjectionEntry(
                    owner_sid=owner.text,
                    semantic_anchor="",
                    path_hint=path,
                    text=value.text,
                )
            ]
        return value, []

    if isinstance(value, Mapping):
        local_owner = _owner_from_mapping(value, owner)
        out: dict[Any, Any] = {}
        nested: list[HumanProjectionEntry] = []
        direct: list[tuple[HumanProjectionEntry, Any | None]] = []

        for key, item in value.items():
            key_path = path + (_path_token(key),)
            if isinstance(key, DomainText) and key.domain is SymbolDomain.HUMAN_PROJECTION:
                direct.append((
                    HumanProjectionEntry(
                        owner_sid=local_owner.text,
                        semantic_anchor="",
                        path_hint=key_path,
                        text=key.text,
                        role="key",
                        payload=item,
                    ),
                    item,
                ))
                continue

            purified_key, key_entries = _purify(key, owner=local_owner, path=key_path + ("<key>",))
            if purified_key is _DROP:
                nested.extend(key_entries)
                continue

            purified_item, item_entries = _purify(item, owner=local_owner, path=key_path)
            if purified_item is _DROP:
                for entry in item_entries:
                    direct.append((entry, None))
                continue

            out[purified_key] = purified_item
            nested.extend(key_entries)
            nested.extend(item_entries)

        _sort_constraints_if_needed(out)
        anchor = semantic_anchor(out)
        for entry, _payload in direct:
            nested.append(
                HumanProjectionEntry(
                    owner_sid=entry.owner_sid,
                    semantic_anchor=anchor,
                    path_hint=entry.path_hint,
                    text=entry.text,
                    role=entry.role,
                    payload=entry.payload,
                )
            )
        return out, nested

    if isinstance(value, (list, tuple)):
        out: list[Any] = []
        nested: list[HumanProjectionEntry] = []
        direct: list[HumanProjectionEntry] = []
        for index, item in enumerate(value):
            purified, entries = _purify(item, owner=owner, path=path + (str(index),))
            if purified is _DROP:
                direct.extend(entries)
                continue
            out.append(purified)
            nested.extend(entries)
        anchor = semantic_anchor(out)
        for entry in direct:
            nested.append(
                HumanProjectionEntry(
                    owner_sid=entry.owner_sid,
                    semantic_anchor=anchor,
                    path_hint=entry.path_hint,
                    text=entry.text,
                    role=entry.role,
                    payload=entry.payload,
                )
            )
        return out, nested

    return value, []


def purify_domain_record(record: Any, manifest: IdentityManifest) -> PurificationResult:
    purified, entries = _purify(record, owner=manifest.project_sid, path=())
    if purified is _DROP:
        raise ValueError("NOVA semantic root cannot be a human projection")
    if contains_human_projection(purified):
        raise ValueError("NOVA purification left Human Projection inside semantic core")
    ordered = tuple(
        sorted(
            entries,
            key=lambda item: (
                item.owner_sid,
                item.semantic_anchor,
                item.path_hint,
                item.role,
                item.text,
            ),
        )
    )
    return PurificationResult(purified, ordered)


def projection_entries_record(entries: tuple[HumanProjectionEntry, ...]) -> list[dict[str, Any]]:
    return [entry.to_record() for entry in entries]


__all__ = [
    "PURIFICATION_REVISION",
    "HumanProjectionEntry",
    "PurificationResult",
    "contains_human_projection",
    "projection_entries_record",
    "purify_domain_record",
    "semantic_anchor",
]

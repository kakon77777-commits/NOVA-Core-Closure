from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .canonical import project_record
from .errors import ValidationError
from .model import Project


IDENTITY_REVISION = 1
_SID_SIZE = 16
_KINDS = frozenset({"module", "graph", "node", "value"})


@dataclass(frozen=True, order=True)
class StructuralID:
    """Persistent 128-bit machine identity; human labels are projections."""

    raw: bytes

    def __post_init__(self) -> None:
        raw = bytes(self.raw)
        if len(raw) != _SID_SIZE:
            raise ValidationError(
                "NOVA StructuralID must be exactly 128 bits",
                context={"length": len(raw)},
            )
        object.__setattr__(self, "raw", raw)

    @property
    def text(self) -> str:
        return "sid:" + self.raw.hex()

    @classmethod
    def parse(cls, value: str) -> "StructuralID":
        text = str(value)
        if text.startswith("sid:"):
            text = text[4:]
        try:
            return cls(bytes.fromhex(text))
        except ValueError as exc:
            raise ValidationError("invalid NOVA StructuralID text") from exc


@dataclass(frozen=True)
class IdentityEntry:
    sid: StructuralID
    kind: str
    label: str
    parent: StructuralID | None = None

    def __post_init__(self) -> None:
        if self.kind not in _KINDS:
            raise ValidationError(
                "unsupported NOVA identity entry kind",
                context={"kind": self.kind},
            )
        if not self.label:
            raise ValidationError("identity projection label must not be empty")

    def to_record(self) -> dict[str, Any]:
        return {
            "sid": self.sid.text,
            "kind": self.kind,
            "label": self.label,
            "parent": None if self.parent is None else self.parent.text,
        }

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> "IdentityEntry":
        parent = value.get("parent")
        return cls(
            sid=StructuralID.parse(str(value["sid"])),
            kind=str(value["kind"]),
            label=str(value["label"]),
            parent=None if parent is None else StructuralID.parse(str(parent)),
        )


@dataclass(frozen=True)
class IdentityManifest:
    project_sid: StructuralID
    entries: tuple[IdentityEntry, ...]
    revision: int = IDENTITY_REVISION

    def __post_init__(self) -> None:
        if self.revision != IDENTITY_REVISION:
            raise ValidationError(
                "unsupported NOVA identity manifest revision",
                context={"revision": self.revision, "supported": IDENTITY_REVISION},
            )
        entries = tuple(self.entries)
        object.__setattr__(self, "entries", entries)
        sid_set = {entry.sid.raw for entry in entries}
        if len(sid_set) != len(entries):
            raise ValidationError("duplicate NOVA structural identity")
        seen_scope: set[tuple[str, bytes | None, str]] = set()
        for entry in entries:
            if (
                entry.parent is not None
                and entry.parent != self.project_sid
                and entry.parent.raw not in sid_set
            ):
                raise ValidationError(
                    "identity entry parent is not present in manifest",
                    context={"sid": entry.sid.text, "parent": entry.parent.text},
                )
            scope = (
                entry.kind,
                None if entry.parent is None else entry.parent.raw,
                entry.label,
            )
            if scope in seen_scope:
                raise ValidationError(
                    "duplicate identity projection label in scope",
                    context={"kind": entry.kind, "label": entry.label},
                )
            seen_scope.add(scope)

    def to_record(self) -> dict[str, Any]:
        return {
            "format": "nova.identity-manifest/0.3",
            "identity_revision": self.revision,
            "project_sid": self.project_sid.text,
            "entries": [
                entry.to_record()
                for entry in sorted(self.entries, key=lambda item: item.sid.raw)
            ],
        }

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> "IdentityManifest":
        if value.get("format") != "nova.identity-manifest/0.3":
            raise ValidationError("invalid NOVA identity manifest format")
        raw_entries = value.get("entries", ())
        if not isinstance(raw_entries, (list, tuple)):
            raise ValidationError("identity manifest entries must be a sequence")
        return cls(
            project_sid=StructuralID.parse(str(value["project_sid"])),
            entries=tuple(IdentityEntry.from_record(item) for item in raw_entries),
            revision=int(value.get("identity_revision", 0)),
        )

    def entry_by_sid(self, sid: StructuralID | str | bytes) -> IdentityEntry:
        target = coerce_sid(sid)
        for entry in self.entries:
            if entry.sid == target:
                return entry
        raise KeyError(f"unknown NOVA StructuralID: {target.text}")

    def resolve(
        self,
        kind: str,
        label: str,
        *,
        parent: StructuralID | str | bytes | None,
    ) -> StructuralID:
        parent_sid = None if parent is None else coerce_sid(parent)
        hits = [
            entry.sid
            for entry in self.entries
            if entry.kind == kind and entry.label == label and entry.parent == parent_sid
        ]
        if len(hits) != 1:
            raise KeyError(
                f"NOVA identity lookup expected one {kind} label {label!r}, found {len(hits)}"
            )
        return hits[0]

    def with_labels(self, updates: Mapping[str | StructuralID, str]) -> "IdentityManifest":
        normalized: dict[bytes, str] = {}
        for key, label in updates.items():
            sid = key if isinstance(key, StructuralID) else StructuralID.parse(str(key))
            if not str(label):
                raise ValidationError("identity projection label must not be empty")
            normalized[sid.raw] = str(label)
        known = {entry.sid.raw for entry in self.entries}
        if not normalized.keys() <= known:
            raise ValidationError("label update references unknown StructuralID")
        return IdentityManifest(
            project_sid=self.project_sid,
            entries=tuple(
                IdentityEntry(
                    entry.sid,
                    entry.kind,
                    normalized.get(entry.sid.raw, entry.label),
                    entry.parent,
                )
                for entry in self.entries
            ),
            revision=self.revision,
        )


def coerce_sid(value: StructuralID | str | bytes) -> StructuralID:
    if isinstance(value, StructuralID):
        return value
    return StructuralID(value) if isinstance(value, bytes) else StructuralID.parse(str(value))


def _seed(project: Project) -> bytes:
    raw = json.dumps(
        project_record(project, semantic=True),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(b"NOVA-IDENTITY-BOOTSTRAP-v0.3\0" + raw).digest()


def _derive(
    project_sid: StructuralID,
    kind: str,
    label: str,
    parent: StructuralID | None,
) -> StructuralID:
    h = hashlib.sha256()
    for part in (
        b"NOVA-STRUCTURAL-ID-v0.3\0",
        project_sid.raw,
        kind.encode("ascii"),
        b"\0",
        b"" if parent is None else parent.raw,
        b"\0",
        label.encode("utf-8"),
    ):
        h.update(part)
    return StructuralID(h.digest()[:_SID_SIZE])


def _value_labels(graph: Mapping[str, Any]) -> tuple[str, ...]:
    labels = {
        str(value)
        for field in ("inputs", "outputs")
        for value in graph.get(field, ()) or ()
    }
    for node in graph.get("nodes", ()) or ():
        labels.update(
            str(value)
            for field in ("inputs", "outputs")
            for value in node.get(field, ()) or ()
        )
    return tuple(sorted(labels, key=lambda item: item.encode("utf-8")))


def bootstrap_identity_manifest(project: Project) -> IdentityManifest:
    """Deterministic one-time migration. Persist the returned manifest."""

    project_sid = StructuralID(
        hashlib.sha256(b"NOVA-PROJECT-ID-v0.3\0" + _seed(project)).digest()[:_SID_SIZE]
    )
    entries: list[IdentityEntry] = []
    for module in project_record(project, semantic=True).get("modules", ()) or ():
        m_label = str(module["id"])
        m_sid = _derive(project_sid, "module", m_label, project_sid)
        entries.append(IdentityEntry(m_sid, "module", m_label, project_sid))
        for graph in module.get("graphs", ()) or ():
            g_label = str(graph["id"])
            g_sid = _derive(project_sid, "graph", g_label, m_sid)
            entries.append(IdentityEntry(g_sid, "graph", g_label, m_sid))
            for node in graph.get("nodes", ()) or ():
                n_label = str(node["id"])
                entries.append(
                    IdentityEntry(
                        _derive(project_sid, "node", n_label, g_sid),
                        "node",
                        n_label,
                        g_sid,
                    )
                )
            for label in _value_labels(graph):
                entries.append(
                    IdentityEntry(
                        _derive(project_sid, "value", label, g_sid),
                        "value",
                        label,
                        g_sid,
                    )
                )
    return IdentityManifest(project_sid, tuple(entries))


__all__ = [
    "IDENTITY_REVISION",
    "IdentityEntry",
    "IdentityManifest",
    "StructuralID",
    "bootstrap_identity_manifest",
    "coerce_sid",
]

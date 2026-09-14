from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .errors import ValidationError
from .human_projection import semantic_anchor
from .identity_model import IdentityManifest, StructuralID
from .purified_identity import purified_core_record
from .symbol_domains import DomainText, SymbolDomain


SCOPED_SYMBOL_REVISION = 1
_SCOPED_ID_SIZE = 16
_SCOPE_FAMILY = "affine_dim"
_BINDER_TAG = b"NOVA-SCOPED-SYMBOL-ID-v0.6\0"


@dataclass(frozen=True, order=True)
class ScopedSymbolID:
    raw: bytes

    def __post_init__(self) -> None:
        raw = bytes(self.raw)
        if len(raw) != _SCOPED_ID_SIZE:
            raise ValidationError(
                "NOVA ScopedSymbolID must be exactly 128 bits",
                context={"length": len(raw)},
            )
        object.__setattr__(self, "raw", raw)

    @property
    def text(self) -> str:
        return "ssid:" + self.raw.hex()

    @classmethod
    def parse(cls, value: str) -> "ScopedSymbolID":
        text = str(value)
        if text.startswith("ssid:"):
            text = text[5:]
        try:
            return cls(bytes.fromhex(text))
        except ValueError as exc:
            raise ValidationError("invalid NOVA ScopedSymbolID text") from exc


@dataclass(frozen=True)
class ScopedSymbolEntry:
    symbol_id: ScopedSymbolID
    scope_sid: StructuralID
    label: str
    family: str = _SCOPE_FAMILY
    signature: str = ""

    def __post_init__(self) -> None:
        if not self.label:
            raise ValidationError("scoped symbol projection label must not be empty")
        if not self.family:
            raise ValidationError("scoped symbol family must not be empty")
        if self.signature and not self.signature.startswith("sha256:"):
            raise ValidationError("scoped symbol signature must be sha256-prefixed")

    def to_record(self) -> dict[str, Any]:
        return {
            "symbol_id": self.symbol_id.text,
            "scope_sid": self.scope_sid.text,
            "family": self.family,
            "label": self.label,
            "signature": self.signature,
        }

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> "ScopedSymbolEntry":
        return cls(
            symbol_id=ScopedSymbolID.parse(str(value["symbol_id"])),
            scope_sid=StructuralID.parse(str(value["scope_sid"])),
            family=str(value.get("family", _SCOPE_FAMILY)),
            label=str(value["label"]),
            signature=str(value.get("signature", "")),
        )


@dataclass(frozen=True)
class ScopedSymbolManifest:
    project_sid: StructuralID
    entries: tuple[ScopedSymbolEntry, ...]
    revision: int = SCOPED_SYMBOL_REVISION

    def __post_init__(self) -> None:
        if self.revision != SCOPED_SYMBOL_REVISION:
            raise ValidationError(
                "unsupported scoped symbol manifest revision",
                context={"revision": self.revision, "supported": SCOPED_SYMBOL_REVISION},
            )
        entries = tuple(self.entries)
        object.__setattr__(self, "entries", entries)
        ids = {entry.symbol_id.raw for entry in entries}
        if len(ids) != len(entries):
            raise ValidationError("duplicate NOVA scoped symbol identity")
        labels: set[tuple[bytes, str, str]] = set()
        for entry in entries:
            key = (entry.scope_sid.raw, entry.family, entry.label)
            if key in labels:
                raise ValidationError(
                    "duplicate scoped symbol projection label in scope",
                    context={
                        "scope_sid": entry.scope_sid.text,
                        "family": entry.family,
                        "label": entry.label,
                    },
                )
            labels.add(key)

    def to_record(self) -> dict[str, Any]:
        return {
            "format": "nova.scoped-symbol-manifest/0.6",
            "scoped_symbol_revision": self.revision,
            "project_sid": self.project_sid.text,
            "entries": [
                entry.to_record()
                for entry in sorted(self.entries, key=lambda item: item.symbol_id.raw)
            ],
        }

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> "ScopedSymbolManifest":
        if value.get("format") != "nova.scoped-symbol-manifest/0.6":
            raise ValidationError("invalid NOVA scoped symbol manifest format")
        raw_entries = value.get("entries", ())
        if not isinstance(raw_entries, (list, tuple)):
            raise ValidationError("scoped symbol manifest entries must be a sequence")
        return cls(
            project_sid=StructuralID.parse(str(value["project_sid"])),
            entries=tuple(ScopedSymbolEntry.from_record(item) for item in raw_entries),
            revision=int(value.get("scoped_symbol_revision", 0)),
        )

    def entry_by_id(self, value: ScopedSymbolID | str | bytes) -> ScopedSymbolEntry:
        target = coerce_scoped_symbol_id(value)
        for entry in self.entries:
            if entry.symbol_id == target:
                return entry
        raise KeyError(f"unknown NOVA ScopedSymbolID: {target.text}")

    def resolve(
        self,
        scope_sid: StructuralID | str | bytes,
        label: str,
        *,
        family: str = _SCOPE_FAMILY,
    ) -> ScopedSymbolID:
        scope = scope_sid if isinstance(scope_sid, StructuralID) else (
            StructuralID(scope_sid) if isinstance(scope_sid, bytes) else StructuralID.parse(str(scope_sid))
        )
        hits = [
            entry.symbol_id
            for entry in self.entries
            if entry.scope_sid == scope and entry.family == family and entry.label == str(label)
        ]
        if len(hits) != 1:
            raise KeyError(
                f"NOVA scoped symbol lookup expected one {family} label {label!r} in {scope.text}, found {len(hits)}"
            )
        return hits[0]

    def with_labels(
        self,
        updates: Mapping[ScopedSymbolID | str, str],
    ) -> "ScopedSymbolManifest":
        normalized: dict[bytes, str] = {}
        for key, label in updates.items():
            symbol_id = key if isinstance(key, ScopedSymbolID) else ScopedSymbolID.parse(str(key))
            if not str(label):
                raise ValidationError("scoped symbol projection label must not be empty")
            normalized[symbol_id.raw] = str(label)
        known = {entry.symbol_id.raw for entry in self.entries}
        if not normalized.keys() <= known:
            raise ValidationError("scoped symbol label update references unknown identity")
        return ScopedSymbolManifest(
            self.project_sid,
            tuple(
                ScopedSymbolEntry(
                    entry.symbol_id,
                    entry.scope_sid,
                    normalized.get(entry.symbol_id.raw, entry.label),
                    entry.family,
                    entry.signature,
                )
                for entry in self.entries
            ),
            self.revision,
        )


def coerce_scoped_symbol_id(value: ScopedSymbolID | str | bytes) -> ScopedSymbolID:
    if isinstance(value, ScopedSymbolID):
        return value
    return ScopedSymbolID(value) if isinstance(value, bytes) else ScopedSymbolID.parse(str(value))


def _stable_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _list_token(item: Any, index: int) -> str | int:
    if isinstance(item, Mapping):
        raw = item.get("id")
        if isinstance(raw, (bytes, bytearray)) and len(raw) == 16:
            return "id:" + bytes(raw).hex()
    return index


def _collect_occurrences(
    value: Any,
    path: tuple[str | int, ...],
    out: dict[str, list[tuple[tuple[str | int, ...], int]]],
) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = key.text if isinstance(key, DomainText) else str(key)
            if key_text == "terms" and isinstance(item, (list, tuple)):
                for term in item:
                    if (
                        isinstance(term, (list, tuple))
                        and len(term) >= 2
                        and isinstance(term[0], DomainText)
                        and term[0].domain is SymbolDomain.SCOPED_SEMANTIC_SYMBOL
                    ):
                        try:
                            coeff = int(term[1])
                        except Exception as exc:
                            raise ValidationError("affine scoped symbol coefficient must be an integer") from exc
                        out.setdefault(term[0].text, []).append((path + ("terms",), coeff))
                    else:
                        _collect_occurrences(term, path + ("terms",), out)
                continue
            _collect_occurrences(item, path + (key_text,), out)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _collect_occurrences(item, path + (_list_token(item, index),), out)


def _signature(
    occurrences: list[tuple[tuple[str | int, ...], int]],
) -> tuple[str, bytes]:
    normalized = sorted(
        [[str(token) for token in path] + [int(coeff)] for path, coeff in occurrences]
    )
    blob = _stable_json(normalized)
    digest = hashlib.sha256(b"NOVA-SCOPED-SYMBOL-SIGNATURE-v0.6\0" + blob).hexdigest()
    return "sha256:" + digest, blob


def _derive_symbol_id(scope_sid: StructuralID, signature_blob: bytes) -> ScopedSymbolID:
    digest = hashlib.sha256(_BINDER_TAG + scope_sid.raw + signature_blob).digest()
    return ScopedSymbolID(digest[:_SCOPED_ID_SIZE])


def bootstrap_scoped_symbol_manifest(
    project: Any,
    identity_manifest: IdentityManifest,
) -> ScopedSymbolManifest:
    """Create the one-time v0.6 binder manifest from structural occurrences.

    The caller must already possess and persist a Structural IdentityManifest.
    Human symbol spellings are projection metadata and never enter the symbol-ID seed.
    If two legacy names are structurally indistinguishable inside one graph scope,
    migration fails rather than using the names as a hidden tie-breaker.
    """

    if identity_manifest.project_sid is None:
        raise ValidationError("scoped symbol bootstrap requires a structural identity manifest")

    record = purified_core_record(project, identity_manifest, strict=True)
    entries: list[ScopedSymbolEntry] = []
    seen_ids: set[bytes] = set()

    for module in record.get("modules", ()) or ():
        for graph in module.get("graphs", ()) or ():
            raw_scope = graph.get("id")
            if not isinstance(raw_scope, (bytes, bytearray)) or len(raw_scope) != 16:
                raise ValidationError("scoped symbol bootstrap requires graph StructuralID scope")
            scope_sid = StructuralID(bytes(raw_scope))
            occurrence_map: dict[str, list[tuple[tuple[str | int, ...], int]]] = {}
            _collect_occurrences(graph, (), occurrence_map)

            signature_owner: dict[str, str] = {}
            pending: list[tuple[str, str, bytes]] = []
            for label, occurrences in occurrence_map.items():
                signature_text, signature_blob = _signature(occurrences)
                other = signature_owner.get(signature_text)
                if other is not None and other != label:
                    raise ValidationError(
                        "scoped symbol bootstrap is structurally ambiguous",
                        context={
                            "scope_sid": scope_sid.text,
                            "labels": sorted([other, label]),
                            "signature": signature_text,
                            "resolution": "provide an explicit persistent scoped-symbol manifest",
                        },
                    )
                signature_owner[signature_text] = label
                pending.append((label, signature_text, signature_blob))

            for label, signature_text, signature_blob in pending:
                symbol_id = _derive_symbol_id(scope_sid, signature_blob)
                if symbol_id.raw in seen_ids:
                    raise ValidationError("scoped symbol identity collision")
                seen_ids.add(symbol_id.raw)
                entries.append(
                    ScopedSymbolEntry(
                        symbol_id=symbol_id,
                        scope_sid=scope_sid,
                        label=label,
                        family=_SCOPE_FAMILY,
                        signature=signature_text,
                    )
                )

    return ScopedSymbolManifest(identity_manifest.project_sid, tuple(entries))


def scoped_symbol_manifest_hash(manifest: ScopedSymbolManifest, *, include_labels: bool = False) -> str:
    entries = []
    for entry in sorted(manifest.entries, key=lambda item: item.symbol_id.raw):
        record: dict[str, Any] = {
            "symbol_id": entry.symbol_id.text,
            "scope_sid": entry.scope_sid.text,
            "family": entry.family,
            "signature": entry.signature,
        }
        if include_labels:
            record["label"] = entry.label
        entries.append(record)
    payload = {
        "revision": manifest.revision,
        "project_sid": manifest.project_sid.text,
        "entries": entries,
    }
    return "sha256:" + hashlib.sha256(
        b"NOVA-SCOPED-SYMBOL-MANIFEST-HASH-v0.6\0" + _stable_json(payload)
    ).hexdigest()


def symbol_projection_anchor(entry: ScopedSymbolEntry) -> str:
    return semantic_anchor(
        {
            "symbol_id": entry.symbol_id.text,
            "scope_sid": entry.scope_sid.text,
            "family": entry.family,
            "signature": entry.signature,
        }
    )


__all__ = [
    "SCOPED_SYMBOL_REVISION",
    "ScopedSymbolEntry",
    "ScopedSymbolID",
    "ScopedSymbolManifest",
    "bootstrap_scoped_symbol_manifest",
    "coerce_scoped_symbol_id",
    "scoped_symbol_manifest_hash",
    "symbol_projection_anchor",
]

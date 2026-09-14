from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import Mapping


# Registry revision is monotonic. Codes inside a domain are append-only.
# A decoder may accept any revision <= its own because older codes retain
# their meaning. Reassignment or deletion requires a new wire-format epoch.
REGISTRY_REVISION = 1


@dataclass(frozen=True)
class RegistryDomain:
    code: int
    name: str
    atoms: tuple[str, ...]

    def code_for(self, atom: str) -> int | None:
        return _DOMAIN_FORWARD[self.name].get(atom)

    def atom_for(self, code: int) -> str:
        try:
            return _DOMAIN_REVERSE[self.name][code]
        except KeyError as exc:
            raise KeyError(f"unknown NOVA global atom code {self.name}:{code}") from exc


# Domain IDs are append-only too. Keep these numeric identities stable.
_DOMAIN_SPECS: tuple[RegistryDomain, ...] = (
    RegistryDomain(
        1,
        "record_kind",
        (
            "tensor_type",
            "shape",
            "affine_dim",
            "shape_constraint",
            "shape_obligation",
        ),
    ),
    RegistryDomain(
        2,
        "operator",
        (
            "Input",
            "Parameter",
            "Constant",
            "Identity",
            "Add",
            "Subtract",
            "Multiply",
            "Divide",
            "Negate",
            "MatMul",
            "Reshape",
            "Transpose",
            "ReduceSum",
            "Mean",
            "Relu",
            "Sigmoid",
            "Tanh",
            "Softmax",
            "StopGradient",
            "ADReduceToShape",
            "ADBroadcastLike",
            "ADReshapeLike",
            "ADTransposeLast2",
            "ADMeanGrad",
            "ADReluGrad",
            "ADZeroLike",
            "If",
            "BoundedLoop",
            "Call",
        ),
    ),
    RegistryDomain(
        3,
        "dtype",
        (
            "bool",
            "i8",
            "i16",
            "i32",
            "i64",
            "u8",
            "u16",
            "u32",
            "u64",
            "f16",
            "bf16",
            "f32",
            "f64",
            "c64",
            "c128",
        ),
    ),
    RegistryDomain(
        4,
        "device",
        (
            "cpu",
            "cuda",
            "rocm",
            "metal",
            "tpu",
            "external",
        ),
    ),
    RegistryDomain(
        5,
        "layout",
        (
            "dense",
            "row_major",
            "column_major",
            "contiguous",
            "strided",
            "sparse_coo",
            "sparse_csr",
        ),
    ),
    RegistryDomain(
        6,
        "edge_kind",
        (
            "value",
            "control",
            "type",
            "shape",
            "effect",
            "ownership",
            "differentiation",
            "resource",
            "validation",
        ),
    ),
    RegistryDomain(
        7,
        "effect_kind",
        (
            "Pure",
            "IO",
            "State",
            "Random",
            "Network",
            "File",
            "Device",
            "Unsafe",
            "NonDeterministic",
            "External",
        ),
    ),
    RegistryDomain(
        8,
        "differentiation_kind",
        (
            "Differentiable",
            "PiecewiseDifferentiable",
            "NonDifferentiable",
            "UnknownDifferentiability",
        ),
    ),
    RegistryDomain(
        9,
        "proof_status",
        (
            "proven",
            "disproven",
            "unknown",
        ),
    ),
    RegistryDomain(
        10,
        "relation",
        (
            "eq",
            "broadcast_compatible",
            "element_count_equal",
        ),
    ),
)


def _validate_registry() -> None:
    domain_codes: set[int] = set()
    domain_names: set[str] = set()
    for domain in _DOMAIN_SPECS:
        if domain.code <= 0:
            raise RuntimeError("NOVA registry domain codes must be positive")
        if domain.code in domain_codes:
            raise RuntimeError(f"duplicate NOVA registry domain code: {domain.code}")
        if domain.name in domain_names:
            raise RuntimeError(f"duplicate NOVA registry domain name: {domain.name}")
        domain_codes.add(domain.code)
        domain_names.add(domain.name)
        if any(not atom for atom in domain.atoms):
            raise RuntimeError(f"empty atom in NOVA registry domain: {domain.name}")
        if len(set(domain.atoms)) != len(domain.atoms):
            raise RuntimeError(f"duplicate atom in NOVA registry domain: {domain.name}")


_validate_registry()

_DOMAIN_BY_NAME: Mapping[str, RegistryDomain] = MappingProxyType(
    {domain.name: domain for domain in _DOMAIN_SPECS}
)
_DOMAIN_BY_CODE: Mapping[int, RegistryDomain] = MappingProxyType(
    {domain.code: domain for domain in _DOMAIN_SPECS}
)
_DOMAIN_FORWARD: Mapping[str, Mapping[str, int]] = MappingProxyType(
    {
        domain.name: MappingProxyType(
            {atom: index + 1 for index, atom in enumerate(domain.atoms)}
        )
        for domain in _DOMAIN_SPECS
    }
)
_DOMAIN_REVERSE: Mapping[str, Mapping[int, str]] = MappingProxyType(
    {
        domain.name: MappingProxyType(
            {index + 1: atom for index, atom in enumerate(domain.atoms)}
        )
        for domain in _DOMAIN_SPECS
    }
)


def domain_code(domain: str) -> int:
    try:
        return _DOMAIN_BY_NAME[domain].code
    except KeyError as exc:
        raise KeyError(f"unknown NOVA registry domain: {domain}") from exc


def domain_name(code: int) -> str:
    try:
        return _DOMAIN_BY_CODE[code].name
    except KeyError as exc:
        raise KeyError(f"unknown NOVA registry domain code: {code}") from exc


def global_code(domain: str, atom: str) -> tuple[int, int] | None:
    spec = _DOMAIN_BY_NAME.get(domain)
    if spec is None:
        return None
    atom_code = _DOMAIN_FORWARD[domain].get(atom)
    if atom_code is None:
        return None
    return spec.code, atom_code


def resolve_global(domain: int | str, atom_code: int) -> str:
    name = domain_name(domain) if isinstance(domain, int) else domain
    try:
        return _DOMAIN_REVERSE[name][atom_code]
    except KeyError as exc:
        raise KeyError(f"unknown NOVA global atom code {name}:{atom_code}") from exc


def registry_snapshot() -> dict[str, object]:
    return {
        "format": "nova.global-semantic-registry/0.2",
        "revision": REGISTRY_REVISION,
        "domains": [
            {
                "code": domain.code,
                "name": domain.name,
                "atoms": [
                    {"code": index + 1, "atom": atom}
                    for index, atom in enumerate(domain.atoms)
                ],
            }
            for domain in _DOMAIN_SPECS
        ],
    }


def registry_fingerprint() -> str:
    payload = json.dumps(
        registry_snapshot(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


__all__ = [
    "REGISTRY_REVISION",
    "RegistryDomain",
    "domain_code",
    "domain_name",
    "global_code",
    "resolve_global",
    "registry_fingerprint",
    "registry_snapshot",
]

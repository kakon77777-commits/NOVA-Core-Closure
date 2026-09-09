from __future__ import annotations

import json
import pytest

from nova_core import (
    ISQLCodecError,
    SemanticDimension,
    SemanticField,
    SemanticProvenance,
    SemanticRelation,
    SemanticTensor,
    SemanticTopology,
    decode_semantic_tensor,
    encode_semantic_tensor,
    semantic_tensor_hash,
)


def sample_tensor(*, metadata_order: str = "ab") -> SemanticTensor:
    metadata = {"a": 1, "b": 2} if metadata_order == "ab" else {"b": 2, "a": 1}
    return SemanticTensor(
        dimensions=(
            SemanticDimension("operation_family", "activation", weight=2.0),
            SemanticDimension("smoothness", "preferred", weight=1.0),
        ),
        phase=SemanticField("intent-phase", {"mode": "selection"}),
        spectrum=(
            SemanticField("activation", 0.9),
            SemanticField("bounded_output", 0.7),
        ),
        topology=SemanticTopology(kind="relation_graph", properties={"connected": True}),
        relations=(
            SemanticRelation("operation_family", "prefers", "smoothness"),
        ),
        confidence=0.8,
        provenance=SemanticProvenance(
            protocol_version="ISQL-Core/0.2",
            registry_id="ISQL-NOVA-G7",
            registry_version="1",
            domain="PROGRAM_INTENT",
            registry_hash="sha256:registry",
            encoder_version="manual-example/v1",
            decoder_contract="semantic-candidate-set/v1",
            model_id=None,
            resolution="R2",
            context_policy="explicit-only",
            source_id="intent-001",
            metadata=metadata,
        ),
        extensions={"future_field": {"x": 1}},
    )


def test_semantic_tensor_roundtrip_and_hash_ignore_mapping_order():
    a = sample_tensor(metadata_order="ab")
    b = sample_tensor(metadata_order="ba")
    assert semantic_tensor_hash(a) == semantic_tensor_hash(b)
    encoded = encode_semantic_tensor(a)
    decoded = decode_semantic_tensor(encoded)
    assert decoded == a
    assert semantic_tensor_hash(decoded) == semantic_tensor_hash(a)
    assert json.loads(encoded)["kind"] == "semantic_tensor"


def test_dimension_order_is_canonicalized_but_relation_sequence_is_stable():
    base = sample_tensor()
    reversed_dims = SemanticTensor(
        dimensions=tuple(reversed(base.dimensions)),
        phase=base.phase,
        spectrum=tuple(reversed(base.spectrum)),
        topology=base.topology,
        relations=base.relations,
        confidence=base.confidence,
        provenance=base.provenance,
        extensions=base.extensions,
    )
    assert semantic_tensor_hash(reversed_dims) == semantic_tensor_hash(base)


def test_confidence_must_be_bounded():
    base = sample_tensor()
    with pytest.raises(ValueError, match="confidence"):
        SemanticTensor(
            dimensions=base.dimensions,
            phase=base.phase,
            spectrum=base.spectrum,
            topology=base.topology,
            relations=base.relations,
            confidence=1.1,
            provenance=base.provenance,
        )


def test_dimension_weight_must_be_positive():
    with pytest.raises(ValueError, match="weight"):
        SemanticDimension("x", 1, weight=0.0)


def test_provenance_requires_protocol_registry_and_decoder_contract():
    for kwargs, message in (
        ({"protocol_version": ""}, "protocol"),
        ({"registry_id": ""}, "registry"),
        ({"registry_version": ""}, "registry"),
        ({"domain": ""}, "domain"),
        ({"decoder_contract": ""}, "decoder"),
    ):
        data = dict(
            protocol_version="ISQL-Core/0.2",
            registry_id="ISQL-NOVA-G7",
            registry_version="1",
            domain="PROGRAM_INTENT",
            decoder_contract="semantic-candidate-set/v1",
        )
        data.update(kwargs)
        with pytest.raises(ValueError, match=message):
            SemanticProvenance(**data)


def test_unknown_extensions_roundtrip_without_affecting_known_fields():
    tensor = sample_tensor()
    decoded = decode_semantic_tensor(encode_semantic_tensor(tensor))
    assert decoded.extensions["future_field"]["x"] == 1
    assert decoded.dimensions[0].name == "operation_family"


def test_non_json_semantic_value_is_rejected():
    tensor = sample_tensor()
    bad = SemanticTensor(
        dimensions=(SemanticDimension("bad", object()),),
        phase=tensor.phase,
        spectrum=tensor.spectrum,
        topology=tensor.topology,
        relations=tensor.relations,
        confidence=tensor.confidence,
        provenance=tensor.provenance,
    )
    with pytest.raises(ISQLCodecError):
        encode_semantic_tensor(bad)


def test_decode_rejects_wrong_kind():
    with pytest.raises(ISQLCodecError, match="kind"):
        decode_semantic_tensor('{"kind":"not_semantic_tensor"}')

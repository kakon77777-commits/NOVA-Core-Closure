import json
import pytest
from nova_core import DecodeError, decode_project, encode_project, semantic_hash


def raw():
    return {
        "header": {"nova_core_version":"0.1.0", "schema_version":"0.1.0", "feature_flags":["graph-kernel"], "future_header":{"x":1}},
        "modules": [{"id":"app", "graphs":[{"id":"main", "inputs":["x"], "outputs":["y"], "nodes":[{"id":"n", "kind":"Identity", "inputs":["x"], "outputs":["y"], "future_node":{"kept":True}}]}]}],
        "future_project": {"retained": True},
    }


def test_decode_encode_roundtrip_preserves_semantic_hash():
    p = decode_project(raw())
    assert semantic_hash(p) == semantic_hash(decode_project(encode_project(p)))


def test_unknown_fields_are_preserved_as_extensions():
    p = decode_project(raw())
    assert p.extensions["future_project"]["retained"] is True
    assert p.header.extensions["future_header"]["x"] == 1
    assert p.modules[0].graphs[0].nodes[0].extensions["future_node"]["kept"] is True


def test_encoded_json_reemits_unknown_fields():
    data = json.loads(encode_project(decode_project(raw())))
    assert data["future_project"] == {"retained": True}
    assert data["modules"][0]["graphs"][0]["nodes"][0]["future_node"] == {"kept": True}


def test_invalid_json_is_typed_decode_error():
    with pytest.raises(DecodeError):
        decode_project("{bad")

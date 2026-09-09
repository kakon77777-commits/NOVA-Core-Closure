import json
import pytest

from nova_core import (
    Graph,
    Module,
    Node,
    Project,
    Shape,
    TensorType,
    ValidationError,
    decode_project,
    encode_project,
    semantic_hash,
)


def tensor_project(*, value_type=None, shape_type=None):
    node = Node(
        id="x_id",
        kind="Identity",
        inputs=("x",),
        outputs=("y",),
        value_type=value_type,
        shape_type=shape_type,
    )
    return Project(modules=(Module(id="app", graphs=(Graph(id="main", inputs=("x",), outputs=("y",), nodes=(node,)),)),))


def test_tensor_type_is_canonical_json_not_python_repr():
    project = tensor_project(value_type=TensorType("f32", Shape.of("B", 4)))
    payload = json.loads(encode_project(project))
    record = payload["modules"][0]["graphs"][0]["nodes"][0]["value_type"]
    assert record["kind"] == "tensor_type"
    assert record["shape"]["kind"] == "shape"
    assert record["shape"]["dims"][1]["const"] == 4


def test_tensor_type_decode_round_trip_restores_semantic_objects_and_hash():
    project = tensor_project(
        value_type=TensorType("f32", Shape.of("B", 4), layout="row_major", device="cpu"),
        shape_type=Shape.of("B", 4),
    )
    encoded = encode_project(project)
    decoded = decode_project(encoded)
    node = decoded.modules[0].graphs[0].nodes[0]
    assert isinstance(node.value_type, TensorType)
    assert isinstance(node.shape_type, Shape)
    assert node.value_type == project.modules[0].graphs[0].nodes[0].value_type
    assert semantic_hash(decoded) == semantic_hash(project)


def test_tensor_type_unknown_fields_are_preserved_in_extensions():
    raw = json.loads(encode_project(tensor_project(value_type=TensorType("f32", Shape.of(2, 3)))))
    raw["modules"][0]["graphs"][0]["nodes"][0]["value_type"]["future_layout_rule"] = {"tile": 16}
    decoded = decode_project(raw)
    tensor = decoded.modules[0].graphs[0].nodes[0].value_type
    assert isinstance(tensor, TensorType)
    assert tensor.extensions["future_layout_rule"]["tile"] == 16
    encoded_again = json.loads(encode_project(decoded))
    assert encoded_again["modules"][0]["graphs"][0]["nodes"][0]["value_type"]["future_layout_rule"] == {"tile": 16}


def test_node_rejects_disagreement_between_tensor_type_shape_and_shape_type():
    with pytest.raises(ValidationError, match="tensor value_type shape and shape_type disagree"):
        Node(
            id="bad",
            kind="Identity",
            value_type=TensorType("f32", Shape.of(2, 3)),
            shape_type=Shape.of(2, 4),
        )

from dataclasses import replace
import json

import pytest
import nova_core
from nova_core import Edge, Graph, GraphTransaction, Module, Node, Project, ValidationError, record_hash, semantic_hash


def _api(name):
    return getattr(nova_core, name)


def base_project(*, with_edge: bool = False) -> Project:
    edges = (Edge(source="add", target="add", kind="trace", attributes={"level": 1}),) if with_edge else ()
    return Project(
        modules=(
            Module(
                id="app",
                graphs=(
                    Graph(
                        id="main",
                        inputs=("x", "b"),
                        outputs=("y",),
                        nodes=(Node(id="add", kind="Add", inputs=("x", "b"), outputs=("y",), attributes={"axis": 0}),),
                        edges=edges,
                    ),
                ),
            ),
        )
    )


def graph_of(project: Project) -> Graph:
    return project.modules[0].graphs[0]


def test_add_node_then_set_outputs_builds_valid_candidate_without_mutating_base():
    project = base_project()
    before_record = record_hash(project)
    ops = (
        _api("AddNodeEdit")(Node(id="relu", kind="Relu", inputs=("y",), outputs=("z",))),
        _api("SetGraphOutputsEdit")(("z",)),
    )
    candidate = _api("preview_node_graph_edit")(project, "app", "main", ops)
    assert record_hash(project) == before_record
    assert [n.id for n in graph_of(candidate.candidate_project).nodes] == ["add", "relu"]
    assert graph_of(candidate.candidate_project).outputs == ("z",)
    assert [n.id for n in candidate.patch.added_nodes] == ["relu"]
    assert candidate.patch.changed_outputs == ("z",)
    assert candidate.diff.semantic_changed is True


def test_replace_node_and_ordered_input_rewire_preserve_operand_order():
    project = base_project()
    ops = (
        _api("ReplaceNodeEdit")(
            "add", Node(id="add", kind="Subtract", inputs=("x", "b"), outputs=("y",), attributes={"axis": 0})
        ),
        _api("SetNodeInputsEdit")("add", ("b", "x")),
    )
    candidate = _api("preview_node_graph_edit")(project, "app", "main", ops)
    node = graph_of(candidate.candidate_project).nodes[0]
    assert node.kind == "Subtract"
    assert node.inputs == ("b", "x")
    assert semantic_hash(candidate.candidate_project) != semantic_hash(project)


def test_set_node_attributes_replaces_mapping_as_explicit_edit():
    project = base_project()
    candidate = _api("preview_node_graph_edit")(
        project,
        "app",
        "main",
        (_api("SetNodeAttributesEdit")("add", {"axis": 1, "reviewed": True}),),
    )
    assert dict(graph_of(candidate.candidate_project).nodes[0].attributes) == {"axis": 1, "reviewed": True}


def test_add_and_remove_edges_are_explicit_structural_operations():
    project = base_project()
    add_ops = (
        _api("AddNodeEdit")(Node(id="relu", kind="Relu", inputs=("y",), outputs=("z",))),
        _api("SetGraphOutputsEdit")(("z",)),
        _api("AddEdgeEdit")(Edge(source="add", target="relu", kind="value", attributes={"slot": 0})),
    )
    added = _api("preview_node_graph_edit")(project, "app", "main", add_ops)
    assert graph_of(added.candidate_project).edges[0].key == ("add", "relu", "value")

    base_with_edge = base_project(with_edge=True)
    removed = _api("preview_node_graph_edit")(
        base_with_edge,
        "app",
        "main",
        (_api("RemoveEdgeEdit")(("add", "add", "trace")),),
    )
    assert graph_of(removed.candidate_project).edges == ()


def test_remove_node_that_breaks_graph_is_rejected_and_base_remains_exact():
    project = base_project()
    before = record_hash(project)
    with pytest.raises(ValidationError):
        _api("preview_node_graph_edit")(
            project,
            "app",
            "main",
            (_api("RemoveNodeEdit")("add"),),
        )
    assert record_hash(project) == before


def test_edit_operations_are_applied_in_declared_order():
    project = base_project()
    node = Node(id="relu", kind="Relu", inputs=("y",), outputs=("z",))
    candidate = _api("preview_node_graph_edit")(
        project,
        "app",
        "main",
        (
            _api("AddNodeEdit")(node),
            _api("SetNodeAttributesEdit")("relu", {"label": "new"}),
            _api("SetGraphOutputsEdit")(("z",)),
        ),
    )
    relu = next(n for n in graph_of(candidate.candidate_project).nodes if n.id == "relu")
    assert dict(relu.attributes) == {"label": "new"}


def test_decode_node_graph_edits_is_strict_and_preserves_input_order():
    payload = [
        {
            "op": "set_node_inputs",
            "node_id": "add",
            "inputs": ["b", "x"],
        },
        {
            "op": "set_graph_outputs",
            "outputs": ["y"],
        },
    ]
    ops = _api("decode_node_graph_edits")(payload)
    assert ops[0].inputs == ("b", "x")
    assert ops[1].outputs == ("y",)
    with pytest.raises(nova_core.ProjectionEditError):
        _api("decode_node_graph_edits")([{"op": "teleport_node", "node_id": "add"}])


def test_preview_patch_keeps_record_hash_guard_for_later_commit_conflicts():
    project = base_project()
    candidate = _api("preview_node_graph_edit")(
        project,
        "app",
        "main",
        (_api("SetNodeAttributesEdit")("add", {"axis": 2}),),
    )
    assert candidate.patch.base_record_hash == record_hash(project)
    drifted = replace(project, provenance={"review": 2})
    assert semantic_hash(drifted) == semantic_hash(project)
    tx = GraphTransaction(drifted)
    with pytest.raises(nova_core.ConflictError):
        nova_core.commit_projection_edit(tx, candidate)

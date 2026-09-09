import json
from dataclasses import replace

import pytest

from nova_core import (
    ConflictError,
    Graph,
    GraphTransaction,
    Module,
    Node,
    Project,
    ValidationError,
    record_hash,
    semantic_hash,
)
from nova_core.editing import commit_projection_edit, interpret_structured_text_edit
from nova_core.errors import ProjectionEditError
from nova_core.projection import project_editable_text


def base_project() -> Project:
    graph = Graph(
        id="main",
        inputs=("x", "b"),
        outputs=("y",),
        nodes=(Node(id="op", kind="Add", inputs=("x", "b"), outputs=("y",), provenance={"source": "base"}),),
        attributes={"purpose": "edit-test"},
        provenance={"review": 1},
    )
    return Project(modules=(Module(id="app", graphs=(graph,)),), provenance={"project_review": 1})


def edited_payload(project: Project) -> dict:
    graph = project.modules[0].graphs[0]
    return json.loads(project_editable_text(graph))


def test_edit_preview_replaces_node_without_mutating_working_project():
    project = base_project()
    before_sem = semantic_hash(project)
    before_record = record_hash(project)
    payload = edited_payload(project)
    payload["nodes"][0]["kind"] = "Multiply"
    candidate = interpret_structured_text_edit(project, "app", "main", json.dumps(payload))

    assert semantic_hash(project) == before_sem
    assert record_hash(project) == before_record
    assert candidate.patch.replaced_nodes[0].id == "op"
    assert candidate.diff.modified_nodes[0].node_id == "op"
    assert candidate.diff.semantic_changed is True
    assert candidate.candidate_semantic_hash != before_sem
    assert candidate.validation == "passed"


def test_edit_preview_can_change_graph_interface_and_attributes():
    project = base_project()
    payload = edited_payload(project)
    payload["outputs"] = ["x"]
    payload["attributes"] = {"purpose": "changed"}
    candidate = interpret_structured_text_edit(project, "app", "main", json.dumps(payload))
    assert candidate.patch.changed_outputs == ("x",)
    assert dict(candidate.patch.changed_attributes or {}) == {"purpose": "changed"}
    graph = candidate.candidate_project.modules[0].graphs[0]
    assert graph.outputs == ("x",)
    assert dict(graph.attributes) == {"purpose": "changed"}


def test_invalid_edited_graph_fails_validation_and_leaves_project_unchanged():
    project = base_project()
    before = record_hash(project)
    payload = edited_payload(project)
    payload["nodes"][0]["inputs"] = ["missing", "b"]
    with pytest.raises(ValidationError):
        interpret_structured_text_edit(project, "app", "main", json.dumps(payload))
    assert record_hash(project) == before


def test_editing_graph_identity_is_rejected_as_typed_projection_edit_error():
    project = base_project()
    payload = edited_payload(project)
    payload["id"] = "renamed"
    with pytest.raises(ProjectionEditError):
        interpret_structured_text_edit(project, "app", "main", json.dumps(payload))


def test_commit_matches_preview_hash_and_transaction_can_rollback():
    project = base_project()
    payload = edited_payload(project)
    payload["nodes"][0]["kind"] = "Subtract"
    candidate = interpret_structured_text_edit(project, "app", "main", json.dumps(payload))
    tx = GraphTransaction(project)
    result = commit_projection_edit(tx, candidate)
    assert result.after_hash == candidate.candidate_semantic_hash
    assert record_hash(tx.current) == candidate.candidate_record_hash
    tx.rollback()
    assert record_hash(tx.current) == candidate.before_record_hash


def test_record_hash_conflict_rejected_even_if_semantic_hash_is_same():
    project = base_project()
    payload = edited_payload(project)
    payload["nodes"][0]["kind"] = "Multiply"
    candidate = interpret_structured_text_edit(project, "app", "main", json.dumps(payload))

    # provenance-only change: semantic identity is unchanged, record identity is not.
    drifted = replace(project, provenance={"project_review": 2})
    assert semantic_hash(drifted) == semantic_hash(project)
    assert record_hash(drifted) != record_hash(project)
    tx = GraphTransaction(drifted)
    with pytest.raises(ConflictError):
        commit_projection_edit(tx, candidate)
    assert record_hash(tx.current) == record_hash(drifted)


def test_unchanged_edit_produces_empty_diff_and_no_hash_drift():
    project = base_project()
    candidate = interpret_structured_text_edit(
        project,
        "app",
        "main",
        project_editable_text(project.modules[0].graphs[0]),
    )
    assert candidate.diff.is_empty is True
    assert candidate.no_change is True
    assert candidate.before_semantic_hash == candidate.candidate_semantic_hash
    assert candidate.before_record_hash == candidate.candidate_record_hash

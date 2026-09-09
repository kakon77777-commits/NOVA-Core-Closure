import pytest
from nova_core import ConflictError, Edge, Graph, GraphPatch, GraphTransaction, Module, Node, PatchError, Project, ValidationError, semantic_hash


def base_project():
    return Project(modules=(Module(id="app", graphs=(Graph(id="main", inputs=("x",), outputs=("y",), nodes=(Node(id="n1", kind="Identity", inputs=("x",), outputs=("y",)),)),)),))


def test_patch_adds_valid_node_and_changes_hash():
    p = base_project()
    tx = GraphTransaction(p)
    patch = GraphPatch(base_hash=semantic_hash(p), module_id="app", graph_id="main", added_nodes=(Node(id="n2", kind="Probe"),))
    result = tx.apply(patch)
    assert result.after_hash != result.before_hash
    assert tx.current.modules[0].graphs[0].nodes[-1].id == "n2"


def test_base_hash_conflict_rejected_without_mutation():
    p = base_project(); tx = GraphTransaction(p); before = tx.semantic_hash
    with pytest.raises(ConflictError):
        tx.apply(GraphPatch(base_hash="sha256:deadbeef", module_id="app", graph_id="main"))
    assert tx.semantic_hash == before


def test_invalid_candidate_edge_rejected_without_mutation():
    p = base_project(); tx = GraphTransaction(p); before = tx.semantic_hash
    patch = GraphPatch(base_hash=before, module_id="app", graph_id="main", added_edges=(Edge(source="n1", target="missing"),))
    with pytest.raises(ValidationError):
        tx.apply(patch)
    assert tx.semantic_hash == before
    assert tx.history_depth == 0


def test_rollback_restores_exact_base_hash():
    p = base_project(); tx = GraphTransaction(p); before = tx.semantic_hash
    tx.apply(GraphPatch(base_hash=before, module_id="app", graph_id="main", added_nodes=(Node(id="n2", kind="Probe"),)))
    tx.rollback()
    assert tx.semantic_hash == before


def test_rollback_without_history_is_typed_error():
    with pytest.raises(PatchError):
        GraphTransaction(base_project()).rollback()

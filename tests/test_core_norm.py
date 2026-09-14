from __future__ import annotations

import pytest

from nova_core.core_norm import core_norm_bytes, core_norm_equivalent, core_norm_hash, core_norm_project
from nova_core.errors import ValidationError
from nova_core.model import Graph, Module, Node, Project, SchemaHeader


def _tensor_type(symbol: str) -> dict:
    return {
        "kind": "tensor_type",
        "dtype": "f32",
        "shape": {
            "kind": "shape",
            "dims": [
                {"kind": "affine_dim", "const": 0, "terms": [[symbol, 1]]},
                {"kind": "affine_dim", "const": 8, "terms": []},
            ],
        },
        "layout": "dense",
        "device": "cpu",
    }


def _project_a() -> Project:
    add = Node(
        id="add_node",
        kind="Add",
        inputs=("x", "y"),
        outputs=("sum",),
        value_type=_tensor_type("B"),
        constraints=(
            {
                "kind": "shape_obligation",
                "required_relation": "eq",
                "proof_status": "unknown",
                "runtime_guard": True,
                "reason": "human explanation A",
            },
        ),
    )
    graph = Graph(id="main", inputs=("x", "y"), outputs=("sum",), nodes=(add,))
    return Project(header=SchemaHeader(), modules=(Module(id="app", graphs=(graph,)),))


def _project_b() -> Project:
    add = Node(
        id="plus",
        kind="Add",
        inputs=("right", "left"),
        outputs=("temporary",),
        value_type=_tensor_type("Batch"),
        constraints=(
            {
                "kind": "shape_obligation",
                "required_relation": "eq",
                "proof_status": "unknown",
                "runtime_guard": True,
                "reason": "human explanation B",
            },
        ),
    )
    identity = Node(id="surface_alias", kind="Identity", inputs=("temporary",), outputs=("answer",))
    graph = Graph(id="calculation", inputs=("left", "right"), outputs=("answer",), nodes=(identity, add))
    return Project(header=SchemaHeader(), modules=(Module(id="different_module_name", graphs=(graph,)),))


def test_cross_representation_core_norm_equivalence() -> None:
    left = _project_a()
    right = _project_b()
    assert core_norm_equivalent(left, right)
    assert core_norm_hash(left) == core_norm_hash(right)
    assert core_norm_bytes(left) == core_norm_bytes(right)


def test_legacy_hash_can_differ_while_core_norm_matches() -> None:
    from nova_core.canonical import semantic_hash
    left = _project_a(); right = _project_b()
    assert semantic_hash(left) != semantic_hash(right)
    assert core_norm_hash(left) == core_norm_hash(right)


def test_core_norm_witness_records_rewrites() -> None:
    result = core_norm_project(_project_b())
    assert result.witness.identity_nodes_eliminated >= 1
    assert result.witness.commutative_nodes_reordered >= 1
    assert result.witness.scoped_binders_alpha_normalized == 1


def test_semantic_operator_change_breaks_equivalence() -> None:
    base = _project_a()
    bad_node = Node(id="different", kind="Subtract", inputs=("x", "y"), outputs=("sum",), value_type=_tensor_type("Whatever"))
    bad = Project(header=SchemaHeader(), modules=(Module(id="m", graphs=(Graph(id="g", inputs=("x", "y"), outputs=("sum",), nodes=(bad_node,)),)),))
    assert not core_norm_equivalent(base, bad)


def test_noncommutative_input_order_remains_semantic() -> None:
    a = Node(id="n1", kind="Subtract", inputs=("x", "y"), outputs=("z",))
    b = Node(id="n2", kind="Subtract", inputs=("b", "a"), outputs=("out",))
    p1 = Project(modules=(Module(id="m1", graphs=(Graph(id="g1", inputs=("x", "y"), outputs=("z",), nodes=(a,)),)),))
    p2 = Project(modules=(Module(id="m2", graphs=(Graph(id="g2", inputs=("a", "b"), outputs=("out",), nodes=(b,)),)),))
    assert not core_norm_equivalent(p1, p2)


def test_structurally_ambiguous_binders_are_rejected() -> None:
    value_type = {
        "kind": "tensor_type",
        "dtype": "f32",
        "shape": {"kind": "shape", "dims": [{"kind": "affine_dim", "const": 0, "terms": [["B", 1], ["N", 1]]}]},
        "layout": "dense",
        "device": "cpu",
    }
    node = Node(id="n", kind="Identity", inputs=("x",), outputs=("y",), value_type=value_type)
    project = Project(modules=(Module(id="m", graphs=(Graph(id="g", inputs=("x",), outputs=("y",), nodes=(node,)),)),))
    with pytest.raises(ValidationError, match="symmetric scoped binders"):
        core_norm_hash(project)


def test_dead_nodes_are_rejected_by_bounded_profile() -> None:
    live = Node(id="live", kind="Add", inputs=("x", "y"), outputs=("z",))
    dead = Node(id="dead", kind="Multiply", inputs=("x", "y"), outputs=("unused",))
    project = Project(modules=(Module(id="m", graphs=(Graph(id="g", inputs=("x", "y"), outputs=("z",), nodes=(live, dead)),)),))
    with pytest.raises(ValidationError, match="dead nodes"):
        core_norm_hash(project)


def test_call_nodes_are_explicitly_outside_v07_bounded_domain() -> None:
    call = Node(id="c", kind="Call", inputs=("x",), outputs=("y",), attributes={"callee": "helper"})
    project = Project(modules=(Module(id="m", graphs=(Graph(id="g", inputs=("x",), outputs=("y",), nodes=(call,)),)),))
    with pytest.raises(ValidationError, match="Call nodes"):
        core_norm_hash(project)


def test_comparison_certificate_is_explicitly_bounded() -> None:
    from nova_core.core_norm_compare import compare_core_norm
    comparison = compare_core_norm(_project_a(), _project_b())
    assert comparison.equivalent
    assert comparison.left_source_hash != comparison.right_source_hash
    assert comparison.left_core_norm_hash == comparison.right_core_norm_hash
    assert "not global semantic equivalence" in comparison.to_record()["claim_boundary"]


def test_comparison_reports_first_difference() -> None:
    from nova_core.core_norm_compare import compare_core_norm
    base = _project_a()
    changed = Node(id="n", kind="Subtract", inputs=("x", "y"), outputs=("sum",), value_type=_tensor_type("B"))
    other = Project(header=SchemaHeader(), modules=(Module(id="m", graphs=(Graph(id="g", inputs=("x", "y"), outputs=("sum",), nodes=(changed,)),)),))
    comparison = compare_core_norm(base, other)
    assert not comparison.equivalent
    assert comparison.first_difference_path


def test_explicit_edge_identity_rewire_is_not_guessed() -> None:
    from nova_core.model import Edge
    add = Node(id="a", kind="Add", inputs=("x", "y"), outputs=("tmp",))
    identity = Node(id="i", kind="Identity", inputs=("tmp",), outputs=("z",))
    graph = Graph(id="g", inputs=("x", "y"), outputs=("z",), nodes=(add, identity), edges=(Edge(source="a", target="i"),))
    project = Project(modules=(Module(id="m", graphs=(graph,)),))
    with pytest.raises(ValidationError, match="explicit-edge rewiring"):
        core_norm_hash(project)

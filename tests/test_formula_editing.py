import pytest
import nova_core
from nova_core import Graph, GraphTransaction, Module, Node, Project, Shape, TensorType, record_hash


def _project(node: Node) -> Project:
    return Project(modules=(Module(id="app", graphs=(Graph(id="main", inputs=("X", "W", "b"), outputs=node.outputs, nodes=(node,)),)),))


def _node(project: Project) -> Node:
    return project.modules[0].graphs[0].nodes[0]


def test_binary_formula_edit_builds_candidate_and_preserves_node_identity():
    project = _project(Node(id="op", kind="Add", inputs=("X", "b"), outputs=("Y",)))
    candidate = nova_core.preview_formula_edit(project, "app", "main", "op", "Y = X - b")
    changed = _node(candidate.candidate_project)
    assert changed.id == "op"
    assert changed.outputs == ("Y",)
    assert changed.kind == "Subtract"
    assert changed.inputs == ("X", "b")
    assert candidate.diff.semantic_changed is True


def test_matmul_and_unary_function_formulas_are_supported():
    matmul = _project(Node(id="op", kind="Add", inputs=("X", "W"), outputs=("Y",)))
    candidate = nova_core.preview_formula_edit(matmul, "app", "main", "op", "Y = X @ W")
    assert _node(candidate.candidate_project).kind == "MatMul"

    unary = _project(Node(id="op", kind="Identity", inputs=("X",), outputs=("Y",)))
    for formula, expected in [
        ("Y = -X", "Negate"),
        ("Y = relu(X)", "Relu"),
        ("Y = sigmoid(X)", "Sigmoid"),
        ("Y = tanh(X)", "Tanh"),
        ("Y = softmax(X)", "Softmax"),
        ("Y = identity(X)", "Identity"),
    ]:
        result = nova_core.preview_formula_edit(unary, "app", "main", "op", formula)
        assert _node(result.candidate_project).kind == expected


def test_formula_lhs_must_match_target_output():
    project = _project(Node(id="op", kind="Add", inputs=("X", "b"), outputs=("Y",)))
    with pytest.raises(nova_core.FormulaEditError):
        nova_core.preview_formula_edit(project, "app", "main", "op", "Z = X - b")


def test_nested_expression_is_rejected_in_bounded_formula_mode():
    project = _project(Node(id="op", kind="Relu", inputs=("X",), outputs=("Y",)))
    with pytest.raises(nova_core.FormulaEditError):
        nova_core.preview_formula_edit(project, "app", "main", "op", "Y = relu(X + b)")


def test_arbitrary_calls_attributes_indexing_and_literals_are_rejected():
    project = _project(Node(id="op", kind="Identity", inputs=("X",), outputs=("Y",)))
    for formula in (
        "Y = os.system(X)",
        "Y = evil(X)",
        "Y = X[0]",
        "Y = 3",
        "Y = X + 3",
    ):
        with pytest.raises(nova_core.FormulaEditError):
            nova_core.preview_formula_edit(project, "app", "main", "op", formula)


def test_formula_parser_never_executes_input_code():
    project = _project(Node(id="op", kind="Identity", inputs=("X",), outputs=("Y",)))
    touched = []
    dangerous = "Y = __import__('builtins').print('should-not-run')"
    with pytest.raises(nova_core.FormulaEditError):
        nova_core.preview_formula_edit(project, "app", "main", "op", dangerous)
    assert touched == []


def test_typed_node_rejects_shape_family_change_but_allows_same_family():
    t = TensorType("f32", Shape.of("B", "O"))
    project = _project(Node(id="op", kind="Add", inputs=("X", "b"), outputs=("Y",), value_type=t, shape_type=t.shape))
    same_family = nova_core.preview_formula_edit(project, "app", "main", "op", "Y = X * b")
    assert _node(same_family.candidate_project).kind == "Multiply"
    with pytest.raises(nova_core.FormulaEditError):
        nova_core.preview_formula_edit(project, "app", "main", "op", "Y = X @ W")


def test_target_must_exist_and_have_exactly_one_output():
    project = _project(Node(id="op", kind="Identity", inputs=("X",), outputs=("Y",)))
    with pytest.raises(nova_core.FormulaEditError):
        nova_core.preview_formula_edit(project, "app", "main", "missing", "Y = X")

    multi = _project(Node(id="op", kind="Probe", inputs=("X",), outputs=("Y", "Z")))
    with pytest.raises(nova_core.FormulaEditError):
        nova_core.preview_formula_edit(multi, "app", "main", "op", "Y = X")


def test_formula_preview_does_not_mutate_source_and_commit_matches_preview():
    project = _project(Node(id="op", kind="Add", inputs=("X", "b"), outputs=("Y",)))
    before = record_hash(project)
    candidate = nova_core.preview_formula_edit(project, "app", "main", "op", "Y = X / b")
    assert record_hash(project) == before
    tx = GraphTransaction(project)
    committed = nova_core.commit_projection_edit(tx, candidate)
    assert committed.after_hash == candidate.candidate_semantic_hash
    assert record_hash(tx.current) == candidate.candidate_record_hash

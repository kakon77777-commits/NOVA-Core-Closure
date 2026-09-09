import pytest
from nova_core import Edge, Graph, Module, Node, Project, SchemaHeader, ValidationError


def project_with_graph(graph):
    return Project(header=SchemaHeader(), modules=(Module(id="app", graphs=(graph,)),))


def test_valid_minimal_project_constructs():
    p = project_with_graph(Graph(id="main", inputs=("x",), outputs=("y",), nodes=(Node(id="n", kind="Identity", inputs=("x",), outputs=("y",)),)))
    assert p.modules[0].graphs[0].id == "main"


def test_duplicate_module_id_rejected():
    with pytest.raises(ValidationError, match="duplicate module id"):
        Project(modules=(Module(id="m"), Module(id="m")))


def test_duplicate_graph_id_rejected():
    with pytest.raises(ValidationError, match="duplicate graph id"):
        Project(modules=(Module(id="m", graphs=(Graph(id="g"), Graph(id="g"))),))


def test_duplicate_node_id_rejected():
    g = Graph(id="g", nodes=(Node(id="n", kind="A"), Node(id="n", kind="B")))
    with pytest.raises(ValidationError, match="duplicate node id"):
        project_with_graph(g)


def test_duplicate_output_symbol_rejected():
    g = Graph(id="g", nodes=(Node(id="a", kind="A", outputs=("z",)), Node(id="b", kind="B", outputs=("z",))))
    with pytest.raises(ValidationError, match="duplicate output symbol"):
        project_with_graph(g)


def test_unresolved_graph_output_rejected():
    with pytest.raises(ValidationError, match="unresolved graph output"):
        project_with_graph(Graph(id="g", outputs=("missing",)))


def test_unknown_edge_endpoint_rejected():
    g = Graph(id="g", nodes=(Node(id="a", kind="A"),), edges=(Edge(source="a", target="missing"),))
    with pytest.raises(ValidationError, match="edge endpoint does not exist"):
        project_with_graph(g)


def test_unresolved_node_input_rejected():
    g = Graph(id="g", nodes=(Node(id="a", kind="A", inputs=("missing",)),))
    with pytest.raises(ValidationError, match="unresolved node input"):
        project_with_graph(g)

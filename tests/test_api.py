import json
from pathlib import Path

import numpy as np

from nova_core import Graph, Module, Node, Project
from nova_core.api import load_project, run_graph, run_project
from nova_core.codec import encode_project


def make_project():
    graph = Graph(
        id="main",
        inputs=("x", "y"),
        outputs=("z",),
        nodes=(Node(id="add", kind="Add", inputs=("x", "y"), outputs=("z",)),),
    )
    return Project(modules=(Module(id="app", graphs=(graph,)),))


def test_load_project_accepts_project_json_and_path(tmp_path):
    project = make_project()
    encoded = encode_project(project)
    assert load_project(project) is project
    assert load_project(encoded) == project
    path = tmp_path / "program.json"
    path.write_text(encoded, encoding="utf-8")
    assert load_project(path) == project


def test_run_graph_selects_reference_or_numpy_backend():
    graph = make_project().modules[0].graphs[0]
    inputs = {"x": np.array([1.0, 2.0]), "y": np.array([3.0, 4.0])}
    a = run_graph(graph, inputs, backend="interpreter")
    b = run_graph(graph, inputs, backend="numpy")
    np.testing.assert_allclose(a.outputs["z"], [4.0, 6.0])
    np.testing.assert_allclose(b.outputs["z"], [4.0, 6.0])


def test_run_project_resolves_module_and_graph():
    result = run_project(make_project(), "app", "main", {"x": 2, "y": 5})
    assert result.outputs["z"] == 7

import json
import numpy as np
import pytest
import nova_core
from nova_core import Graph, Module, Node, Project, semantic_hash


def project() -> Project:
    g1 = Graph(
        id="add",
        inputs=("x", "b"),
        outputs=("y",),
        nodes=(Node(id="add", kind="Add", inputs=("x", "b"), outputs=("y",)),),
    )
    g2 = Graph(
        id="relu",
        inputs=("y",),
        outputs=("z",),
        nodes=(Node(id="relu", kind="Relu", inputs=("y",), outputs=("z",)),),
    )
    return Project(modules=(Module(id="app", graphs=(g1, g2)),))


def notebook():
    return nova_core.Notebook(
        cells=(
            nova_core.NotebookCell(
                id="c1",
                module_id="app",
                graph_id="add",
                bindings={
                    "x": nova_core.ExternalInput("x"),
                    "b": nova_core.ExternalInput("b"),
                },
            ),
            nova_core.NotebookCell(
                id="c2",
                module_id="app",
                graph_id="relu",
                bindings={"y": nova_core.CellOutput("c1", "y")},
            ),
        )
    )


def test_graph_cells_chain_external_and_prior_cell_outputs():
    result = nova_core.run_notebook(
        project(),
        notebook(),
        {"x": np.array([-1.0, 2.0]), "b": np.array([0.5, 0.5])},
        backend="numpy",
    )
    assert len(result.cells) == 2
    np.testing.assert_allclose(result.cells[0].outputs["y"], [-0.5, 2.5])
    np.testing.assert_allclose(result.cells[1].outputs["z"], [0.0, 2.5])
    assert result.cells[1].dependency_cells == ("c1",)
    assert result.cells[1].graph_semantic_hash.startswith("sha256:")


def test_forward_cell_reference_is_rejected():
    with pytest.raises(nova_core.NotebookError):
        nova_core.Notebook(
            cells=(
                nova_core.NotebookCell(
                    id="c1",
                    module_id="app",
                    graph_id="add",
                    bindings={"x": nova_core.CellOutput("later", "z"), "b": nova_core.ExternalInput("b")},
                ),
                nova_core.NotebookCell(id="later", module_id="app", graph_id="relu", bindings={"y": nova_core.ExternalInput("y")}),
            )
        )


def test_missing_or_extra_graph_input_bindings_are_rejected():
    nb = nova_core.Notebook(
        cells=(
            nova_core.NotebookCell(id="c1", module_id="app", graph_id="add", bindings={"x": nova_core.ExternalInput("x")}),
        )
    )
    with pytest.raises(nova_core.NotebookError):
        nova_core.run_notebook(project(), nb, {"x": np.array([1.0])}, backend="numpy")

    extra = nova_core.Notebook(
        cells=(
            nova_core.NotebookCell(
                id="c1",
                module_id="app",
                graph_id="add",
                bindings={"x": nova_core.ExternalInput("x"), "b": nova_core.ExternalInput("b"), "ghost": nova_core.ExternalInput("g")},
            ),
        )
    )
    with pytest.raises(nova_core.NotebookError):
        nova_core.run_notebook(project(), extra, {"x": np.array([1.0]), "b": np.array([2.0]), "g": 0}, backend="numpy")


def test_missing_external_input_and_missing_prior_output_are_typed_failures():
    with pytest.raises(nova_core.NotebookError):
        nova_core.run_notebook(project(), notebook(), {"x": np.array([1.0])}, backend="numpy")

    bad = nova_core.Notebook(
        cells=(
            notebook().cells[0],
            nova_core.NotebookCell(id="c2", module_id="app", graph_id="relu", bindings={"y": nova_core.CellOutput("c1", "missing")}),
        )
    )
    with pytest.raises(nova_core.NotebookError):
        nova_core.run_notebook(
            project(), bad, {"x": np.array([1.0]), "b": np.array([2.0])}, backend="numpy"
        )


def test_cell_result_digests_are_deterministic_and_source_graphs_do_not_mutate():
    p = project()
    before = tuple(semantic_hash(g) for g in p.modules[0].graphs)
    inputs = {"x": np.array([-1.0, 2.0]), "b": np.array([0.5, 0.5])}
    first = nova_core.run_notebook(p, notebook(), inputs, backend="numpy")
    second = nova_core.run_notebook(p, notebook(), inputs, backend="numpy")
    assert [c.output_digest for c in first.cells] == [c.output_digest for c in second.cells]
    assert first.notebook_hash == second.notebook_hash
    assert tuple(semantic_hash(g) for g in p.modules[0].graphs) == before
    assert first.cells[0].output_summaries["y"]["shape"] == [2]
    assert first.cells[0].output_summaries["y"]["dtype"] == "float64"


def test_interpreter_and_numpy_notebook_results_are_equivalent():
    p = project()
    inputs = {"x": np.array([-1.0, 2.0]), "b": np.array([0.5, 0.5])}
    left = nova_core.run_notebook(p, notebook(), inputs, backend="interpreter")
    right = nova_core.run_notebook(p, notebook(), inputs, backend="numpy")
    np.testing.assert_allclose(left.cells[-1].outputs["z"], right.cells[-1].outputs["z"])
    assert left.cells[-1].output_digest == right.cells[-1].output_digest


def test_notebook_json_decoder_is_strict_and_round_trip_hash_stable():
    payload = {
        "version": "0.1",
        "cells": [
            {
                "id": "c1",
                "module_id": "app",
                "graph_id": "add",
                "bindings": {
                    "x": {"kind": "external", "name": "x"},
                    "b": {"kind": "external", "name": "b"},
                },
            },
            {
                "id": "c2",
                "module_id": "app",
                "graph_id": "relu",
                "bindings": {"y": {"kind": "cell_output", "cell_id": "c1", "output": "y"}},
            },
        ],
    }
    decoded = nova_core.decode_notebook(json.dumps(payload))
    assert decoded == notebook()
    assert nova_core.notebook_hash(decoded) == nova_core.notebook_hash(notebook())
    payload["cells"][0]["bindings"]["x"] = {"kind": "magic", "name": "x"}
    with pytest.raises(nova_core.NotebookError):
        nova_core.decode_notebook(payload)

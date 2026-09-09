import pytest

from nova_core import Graph
from nova_core.errors import ValidationError


def test_differentiation_request_requires_target_and_wrt():
    from nova_core.autodiff import DifferentiationRequest

    with pytest.raises(ValidationError):
        DifferentiationRequest(target="", wrt=("x",))
    with pytest.raises(ValidationError):
        DifferentiationRequest(target="loss", wrt=())


def test_differentiation_request_rejects_duplicate_wrt_symbols():
    from nova_core.autodiff import DifferentiationRequest

    with pytest.raises(ValidationError):
        DifferentiationRequest(target="loss", wrt=("x", "x"))


def test_gradient_symbol_is_stable_and_preserves_source_name():
    from nova_core.autodiff import gradient_symbol

    assert gradient_symbol("W") == "__nova_grad__W"
    assert gradient_symbol("layer/weight:0") == "__nova_grad__layer/weight:0"


def test_derivative_graph_id_is_deterministic_for_request():
    from nova_core.autodiff import DifferentiationRequest, derivative_graph_id

    graph = Graph(id="main")
    request = DifferentiationRequest(target="loss", wrt=("W", "b"))
    first = derivative_graph_id(graph, request)
    second = derivative_graph_id(graph, request)

    assert first == second
    assert first.startswith("main__rev__loss__")
    assert derivative_graph_id(graph, DifferentiationRequest(target="loss", wrt=("b", "W"))) != first


def test_explicit_derivative_graph_id_overrides_generated_id():
    from nova_core.autodiff import DifferentiationRequest, derivative_graph_id

    graph = Graph(id="main")
    request = DifferentiationRequest(target="loss", wrt=("W",), derivative_graph_id="custom_grad")
    assert derivative_graph_id(graph, request) == "custom_grad"


def test_diff_error_is_typed_nova_error():
    from nova_core.errors import DiffError, NovaError

    error = DiffError("cannot differentiate", source_nodes=("n1",), context={"kind": "Magic"})
    assert isinstance(error, NovaError)
    assert error.to_dict()["category"] == "DiffError"
    assert error.to_dict()["source_nodes"] == ["n1"]


def test_derivative_graph_result_freezes_gradient_mapping():
    from nova_core.autodiff import DerivativeGraphResult

    result = DerivativeGraphResult(graph=Graph(id="g"), target="loss", gradients={"x": "dx"})
    assert dict(result.gradients) == {"x": "dx"}
    with pytest.raises(TypeError):
        result.gradients["x"] = "other"

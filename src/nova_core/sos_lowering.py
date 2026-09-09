from __future__ import annotations

from .errors import OperatorDescriptorError
from .model import Graph, Module, Node, Project, SchemaHeader, validate_project
from .sos import BrokenOperator, OperatorClosure, closure_hash

_SUPPORTED_UNARY_KINDS = {"Identity", "Negate", "Relu", "Sigmoid", "Tanh", "Softmax"}


def lower_closure_to_project(
    closure: OperatorClosure | BrokenOperator,
    *,
    input_symbol: str = "x",
    output_symbol: str = "y",
    module_id: str = "sos",
    graph_id: str = "sos_closure",
) -> Project:
    if not isinstance(closure, OperatorClosure):
        raise OperatorDescriptorError("lowering requires a safe OperatorClosure")
    if not input_symbol or not output_symbol:
        raise OperatorDescriptorError("input_symbol and output_symbol must not be empty")

    # Mathematical A o B executes B first, then A.
    execution_members = tuple(reversed(closure.members))
    nodes: list[Node] = []
    current = input_symbol
    for index, descriptor in enumerate(execution_members):
        slot = descriptor.composition_slot
        if slot.input_arity != 1 or slot.output_arity != 1:
            raise OperatorDescriptorError(
                "Round 11 lowering supports only unary single-output operator descriptors",
                context={"operator_id": descriptor.operator_id, "input_arity": slot.input_arity, "output_arity": slot.output_arity},
            )
        if descriptor.nova_kind not in _SUPPORTED_UNARY_KINDS:
            raise OperatorDescriptorError(
                "operator kind is not supported by Round 11 SOS lowering",
                context={"operator_id": descriptor.operator_id, "nova_kind": descriptor.nova_kind},
            )
        is_last = index == len(execution_members) - 1
        produced = output_symbol if is_last else f"__sos_{index}"
        attributes = {"axis": -1} if descriptor.nova_kind == "Softmax" else {}
        nodes.append(
            Node(
                id=f"sos_{index:03d}_{descriptor.operator_id}",
                kind=descriptor.nova_kind,
                inputs=(current,),
                outputs=(produced,),
                attributes=attributes,
                provenance={"sos_operator_id": descriptor.operator_id, "sos_closure_hash": closure_hash(closure)},
            )
        )
        current = produced

    graph = Graph(
        id=graph_id,
        inputs=(input_symbol,),
        outputs=(output_symbol,),
        nodes=tuple(nodes),
        provenance={"sos_closure_hash": closure_hash(closure), "sos_member_ids": list(closure.member_ids)},
    )
    project = Project(
        header=SchemaHeader(
            nova_core_version="0.11.0",
            schema_version="0.1.0",
            feature_flags=("sos-clsafe",),
        ),
        modules=(Module(id=module_id, graphs=(graph,), exports=(graph_id,)),),
        provenance={"source": "SOS closure lowering"},
    )
    validate_project(project)
    return project

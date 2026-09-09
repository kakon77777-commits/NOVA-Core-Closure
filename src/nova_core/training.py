from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np

from .errors import TrainingError
from .model import Graph


def _readonly_array(value: Any) -> np.ndarray:
    array = np.array(value, copy=True)
    if array.dtype.kind not in "biufc":
        raise TrainingError(
            "training parameters must use numeric dtypes",
            context={"dtype": str(array.dtype)},
        )
    array.setflags(write=False)
    return array


def _freeze_parameters(parameters: Mapping[str, Any]) -> Mapping[str, np.ndarray]:
    return MappingProxyType({str(name): _readonly_array(value) for name, value in parameters.items()})


def parameter_state_hash(parameters: Mapping[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update(b"NOVA-TRAINING-STATE-v1\0")
    for name in sorted(str(key) for key in parameters):
        array = np.asarray(parameters[name])
        if array.dtype.kind not in "biufc":
            raise TrainingError(
                "training parameters must use numeric dtypes",
                context={"parameter": name, "dtype": str(array.dtype)},
            )
        normalized_dtype = array.dtype.newbyteorder("<")
        normalized = np.ascontiguousarray(array.astype(normalized_dtype, copy=False))
        header = json.dumps(
            {
                "name": name,
                "dtype": normalized.dtype.str,
                "shape": list(normalized.shape),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest.update(len(header).to_bytes(8, "big"))
        digest.update(header)
        raw = normalized.tobytes(order="C")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return "sha256:" + digest.hexdigest()


def parameter_bindings(graph: Graph) -> dict[str, str]:
    bindings: dict[str, str] = {}
    runtime_names: set[str] = set()
    for node in graph.nodes:
        if node.kind != "Parameter":
            continue
        if len(node.outputs) != 1:
            raise TrainingError(
                "Parameter node must have exactly one output",
                source_nodes=(node.id,),
                context={"outputs": list(node.outputs)},
            )
        symbol = node.outputs[0]
        runtime_name = str(node.attributes.get("name", symbol))
        if not runtime_name:
            raise TrainingError(
                "Parameter runtime binding name must not be empty",
                source_nodes=(node.id,),
            )
        if runtime_name in runtime_names:
            raise TrainingError(
                "duplicate Parameter runtime binding name",
                source_nodes=(node.id,),
                context={"runtime_name": runtime_name},
            )
        runtime_names.add(runtime_name)
        bindings[symbol] = runtime_name
    return bindings


@dataclass(frozen=True)
class TrainingConfig:
    target: str
    wrt: tuple[str, ...]
    steps: int
    learning_rate: float
    backend: str = "numpy"

    def __post_init__(self) -> None:
        if not self.target:
            raise TrainingError("training target must not be empty")
        wrt = tuple(str(symbol) for symbol in self.wrt)
        if not wrt or len(set(wrt)) != len(wrt):
            raise TrainingError("training wrt must contain unique Parameter symbols")
        if not isinstance(self.steps, int) or isinstance(self.steps, bool) or self.steps <= 0:
            raise TrainingError("training steps must be a positive integer", context={"steps": self.steps})
        if self.steps > 1_000_000:
            raise TrainingError("training steps exceed Round 05 safety bound", context={"steps": self.steps})
        if not math.isfinite(float(self.learning_rate)) or float(self.learning_rate) <= 0:
            raise TrainingError(
                "learning_rate must be positive and finite",
                context={"learning_rate": self.learning_rate},
            )
        if self.backend not in {"interpreter", "numpy"}:
            raise TrainingError("unsupported training backend", context={"backend": self.backend})
        object.__setattr__(self, "wrt", wrt)
        object.__setattr__(self, "learning_rate", float(self.learning_rate))


@dataclass(frozen=True)
class TrainingState:
    step: int
    parameters: Mapping[str, Any]
    loss_history: tuple[float, ...]
    graph_semantic_hash: str
    parameter_state_hash: str = field(init=False)

    def __post_init__(self) -> None:
        if self.step < 0:
            raise TrainingError("training state step must be non-negative")
        frozen = _freeze_parameters(self.parameters)
        losses = tuple(float(loss) for loss in self.loss_history)
        if any(not math.isfinite(loss) for loss in losses):
            raise TrainingError("training loss history contains a non-finite value")
        object.__setattr__(self, "parameters", frozen)
        object.__setattr__(self, "loss_history", losses)
        object.__setattr__(self, "parameter_state_hash", parameter_state_hash(frozen))


@dataclass(frozen=True)
class TrainingStepRecord:
    step: int
    loss_before: float
    loss_after: float
    gradient_l2_norm: float
    parameter_state_hash_before: str
    parameter_state_hash_after: str


@dataclass(frozen=True)
class TrainingResult:
    state: TrainingState
    records: tuple[TrainingStepRecord, ...]
    derivative_graph_id: str
    derivative_semantic_hash: str

    @property
    def initial_loss(self) -> float:
        return self.state.loss_history[0]

    @property
    def final_loss(self) -> float:
        return self.state.loss_history[-1]


def sgd_update(
    parameters: Mapping[str, Any],
    gradients: Mapping[str, Any],
    bindings: Mapping[str, str],
    learning_rate: float,
) -> Mapping[str, np.ndarray]:
    if not math.isfinite(float(learning_rate)) or float(learning_rate) <= 0:
        raise TrainingError("learning_rate must be positive and finite")
    updated = {str(name): np.array(value, copy=True) for name, value in parameters.items()}
    for symbol, runtime_name in bindings.items():
        if runtime_name not in updated:
            raise TrainingError(
                "missing runtime parameter binding",
                context={"symbol": symbol, "runtime_name": runtime_name},
            )
        if symbol not in gradients:
            raise TrainingError("missing gradient for trainable symbol", context={"symbol": symbol})
        parameter = np.asarray(updated[runtime_name])
        gradient = np.asarray(gradients[symbol])
        if parameter.shape != gradient.shape:
            raise TrainingError(
                "gradient shape mismatch",
                context={"symbol": symbol, "parameter_shape": list(parameter.shape), "gradient_shape": list(gradient.shape)},
            )
        if not np.all(np.isfinite(gradient)):
            raise TrainingError("non-finite gradient", context={"symbol": symbol})
        result = parameter - float(learning_rate) * gradient
        if not np.all(np.isfinite(result)):
            raise TrainingError("SGD update produced non-finite parameter", context={"symbol": symbol})
        updated[runtime_name] = result
    return _freeze_parameters(updated)


def _training_backend(name: str):
    from .backends import NumPyBackend
    from .interpreter import Interpreter

    if name == "numpy":
        return NumPyBackend()
    if name == "interpreter":
        return Interpreter()
    raise TrainingError("unsupported training backend", context={"backend": name})


def _scalar_loss(value: Any, *, target: str) -> float:
    array = np.asarray(value)
    if array.shape != ():
        raise TrainingError(
            "training target must be scalar at runtime",
            context={"target": target, "shape": list(array.shape)},
        )
    loss = float(array)
    if not math.isfinite(loss):
        raise TrainingError("training loss is non-finite", context={"target": target, "loss": loss})
    return loss


def train_graph(
    graph: Graph,
    inputs: Mapping[str, Any],
    initial_parameters: Mapping[str, Any],
    config: TrainingConfig,
) -> TrainingResult:
    from .autodiff import DifferentiationRequest, differentiate_graph, gradient_symbol
    from .canonical import semantic_hash

    if config.target not in graph.outputs:
        raise TrainingError(
            "training target must be a graph output in Round 05",
            context={"target": config.target, "graph_outputs": list(graph.outputs)},
        )

    all_bindings = parameter_bindings(graph)
    missing_symbols = [symbol for symbol in config.wrt if symbol not in all_bindings]
    if missing_symbols:
        raise TrainingError(
            "optimizer target is not a Parameter output",
            context={"symbols": missing_symbols},
        )
    selected_bindings = {symbol: all_bindings[symbol] for symbol in config.wrt}
    for symbol, runtime_name in selected_bindings.items():
        if runtime_name not in initial_parameters:
            raise TrainingError(
                "missing runtime parameter binding",
                context={"symbol": symbol, "runtime_name": runtime_name},
            )

    graph_hash = semantic_hash(graph)
    runtime = _training_backend(config.backend)

    initial_state = TrainingState(
        step=0,
        parameters=initial_parameters,
        loss_history=(),
        graph_semantic_hash=graph_hash,
    )
    primal = runtime.run_graph(graph, inputs, parameters=initial_state.parameters)
    initial_loss = _scalar_loss(primal.outputs[config.target], target=config.target)

    occupied = set(graph.inputs)
    for node in graph.nodes:
        occupied.update(node.outputs)
    seed_input = "__nova_training_seed__"
    suffix = 0
    while seed_input in occupied:
        suffix += 1
        seed_input = f"__nova_training_seed__{suffix}"
    request = DifferentiationRequest(target=config.target, wrt=config.wrt, seed_input=seed_input)
    derivative = differentiate_graph(graph, request)
    derivative_hash = semantic_hash(derivative.graph)
    derivative_inputs = dict(inputs)
    derivative_inputs[seed_input] = np.asarray(1.0)

    state = TrainingState(
        step=0,
        parameters=initial_state.parameters,
        loss_history=(initial_loss,),
        graph_semantic_hash=graph_hash,
    )
    records: list[TrainingStepRecord] = []

    for step_index in range(1, config.steps + 1):
        if semantic_hash(graph) != graph_hash:
            raise TrainingError("canonical graph semantic hash drifted during training")

        gradient_run = runtime.run_graph(
            derivative.graph,
            derivative_inputs,
            parameters=state.parameters,
        )
        gradients: dict[str, np.ndarray] = {}
        norm_sq = 0.0
        for symbol in config.wrt:
            output = gradient_symbol(symbol)
            gradient = np.asarray(gradient_run.outputs[output])
            if not np.all(np.isfinite(gradient)):
                raise TrainingError("non-finite gradient", context={"symbol": symbol})
            gradients[symbol] = gradient
            norm_sq += float(np.sum(np.square(np.asarray(gradient, dtype=np.float64))))

        before_hash = state.parameter_state_hash
        updated = sgd_update(
            state.parameters,
            gradients,
            selected_bindings,
            config.learning_rate,
        )
        primal_after = runtime.run_graph(graph, inputs, parameters=updated)
        loss_after = _scalar_loss(primal_after.outputs[config.target], target=config.target)
        history = state.loss_history + (loss_after,)
        next_state = TrainingState(
            step=step_index,
            parameters=updated,
            loss_history=history,
            graph_semantic_hash=graph_hash,
        )
        records.append(
            TrainingStepRecord(
                step=step_index,
                loss_before=state.loss_history[-1],
                loss_after=loss_after,
                gradient_l2_norm=math.sqrt(norm_sq),
                parameter_state_hash_before=before_hash,
                parameter_state_hash_after=next_state.parameter_state_hash,
            )
        )
        state = next_state

    if semantic_hash(graph) != graph_hash:
        raise TrainingError("canonical graph semantic hash drifted during training")

    return TrainingResult(
        state=state,
        records=tuple(records),
        derivative_graph_id=derivative.graph.id,
        derivative_semantic_hash=derivative_hash,
    )

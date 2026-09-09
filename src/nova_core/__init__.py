from .canonical import canonical_bytes, canonical_json, project_record, record_hash, semantic_hash
from .codec import decode_project, encode_project
from .errors import BackendError, ConflictError, DecodeError, DependencyError, DiffError, DLPackInteropError, DTypeInteropError, ErrorDetail, ExecutionError, InteropError, MigrationError, MissingInputError, NovaError, PatchError, ProjectionEditError, ProjectionError, RuntimeShapeError, ShapeError, TrainingError, UnsupportedOperationError, ValidationError
from .model import Edge, Graph, Module, Node, Project, SchemaHeader, validate_graph, validate_module, validate_project
from .patch import GraphPatch, GraphTransaction, PatchResult, apply_graph_patch
from .shape import DimExpr, ProofStatus, Shape, ShapeConstraint, ShapeObligation, ShapeSolver, as_dim
from .types import TensorType
from .ops import ShapeInference, broadcast_shapes, contract_shape, elementwise_shape, matmul_shape, reshape_shape, transpose_shape
from .runtime import ExecutionEnvironment, ExecutionResult, ExecutionTrace, TraceRecord, validate_runtime_value
from .interpreter import Interpreter
from .backends import NumPyBackend
from .projection import parse_editable_text, project_editable_text, project_formula, project_graph_view, project_snapshot, project_text
from .projection_model import ProjectionSnapshot
from .diff import EdgeDelta, FieldChange, GraphDiff, NodeDelta, diff_graphs
from .editing import ProjectionEditCandidate, commit_projection_edit, interpret_structured_text_edit
from .audit import project_audit_view, project_error_view
from .api import GradientExecutionResult, differentiate_project, diff_project_graphs, find_graph, interop_from_dlpack, interop_to_dlpack, interop_to_numpy, load_project, preview_structured_edit, run_gradient, run_graph, run_project, run_project_gradient, train_project
from .autodiff import DerivativeGraphResult, DifferentiationRequest, VJP_RULES, derivative_graph_id, differentiate_graph, gradient_symbol
from .gradcheck import GradientCheckResult, check_gradient, finite_difference_gradient
from .training import TrainingConfig, TrainingResult, TrainingState, TrainingStepRecord, parameter_bindings, parameter_state_hash, sgd_update, train_graph
from .interop import dlpack_device, from_dlpack, from_numpy, numpy_dtype, to_dlpack, to_numpy, to_python

__version__ = "0.7.0"

__all__ = [
    "__version__",
    "SchemaHeader", "Node", "Edge", "Graph", "Module", "Project",
    "validate_graph", "validate_module", "validate_project",
    "canonical_json", "canonical_bytes", "project_record", "semantic_hash", "record_hash",
    "decode_project", "encode_project",
    "GraphPatch", "PatchResult", "GraphTransaction", "apply_graph_patch",
    "DimExpr", "Shape", "as_dim", "TensorType",
    "ProofStatus", "ShapeConstraint", "ShapeObligation", "ShapeSolver",
    "ShapeInference", "broadcast_shapes", "elementwise_shape", "matmul_shape", "contract_shape", "reshape_shape", "transpose_shape",
    "FieldChange", "NodeDelta", "EdgeDelta", "GraphDiff", "diff_graphs", "ProjectionEditCandidate", "interpret_structured_text_edit", "commit_projection_edit", "project_audit_view", "project_error_view", "diff_project_graphs", "preview_structured_edit",
    "ExecutionEnvironment", "ExecutionResult", "ExecutionTrace", "TraceRecord", "validate_runtime_value", "Interpreter", "NumPyBackend", "ProjectionSnapshot", "project_text", "project_formula", "project_graph_view", "project_editable_text", "parse_editable_text", "project_snapshot", "load_project", "run_graph", "run_project", "find_graph", "GradientExecutionResult", "differentiate_project", "run_gradient", "run_project_gradient", "train_project", "interop_to_numpy", "interop_to_dlpack", "interop_from_dlpack",
    "ErrorDetail", "NovaError", "ValidationError", "ShapeError", "ConflictError", "PatchError", "DecodeError", "MigrationError", "DiffError",
    "ExecutionError", "MissingInputError", "RuntimeShapeError", "UnsupportedOperationError", "DependencyError", "BackendError", "ProjectionError", "ProjectionEditError", "TrainingError", "InteropError", "DTypeInteropError", "DLPackInteropError",
    "DerivativeGraphResult", "DifferentiationRequest", "VJP_RULES", "derivative_graph_id", "differentiate_graph", "gradient_symbol",
    "GradientCheckResult", "check_gradient", "finite_difference_gradient",
    "TrainingConfig", "TrainingState", "TrainingStepRecord", "TrainingResult", "parameter_bindings", "parameter_state_hash", "sgd_update", "train_graph",
    "numpy_dtype", "to_numpy", "from_numpy", "to_python", "to_dlpack", "from_dlpack", "dlpack_device",
]

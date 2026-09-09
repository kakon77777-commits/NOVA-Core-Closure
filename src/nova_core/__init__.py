from .canonical import canonical_bytes, canonical_json, project_record, record_hash, semantic_hash
from .codec import decode_project, encode_project
from .errors import BackendError, ConflictError, DecodeError, DependencyError, ErrorDetail, ExecutionError, MigrationError, MissingInputError, NovaError, PatchError, ProjectionError, RuntimeShapeError, ShapeError, UnsupportedOperationError, ValidationError
from .model import Edge, Graph, Module, Node, Project, SchemaHeader, validate_graph, validate_module, validate_project
from .patch import GraphPatch, GraphTransaction, PatchResult, apply_graph_patch
from .shape import DimExpr, ProofStatus, Shape, ShapeConstraint, ShapeObligation, ShapeSolver, as_dim
from .types import TensorType
from .ops import ShapeInference, broadcast_shapes, contract_shape, elementwise_shape, matmul_shape, reshape_shape, transpose_shape
from .runtime import ExecutionEnvironment, ExecutionResult, ExecutionTrace, TraceRecord, validate_runtime_value
from .interpreter import Interpreter
from .backends import NumPyBackend
from .projection import project_formula, project_text
from .api import find_graph, load_project, run_graph, run_project

__version__ = "0.3.0"

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
    "ExecutionEnvironment", "ExecutionResult", "ExecutionTrace", "TraceRecord", "validate_runtime_value", "Interpreter", "NumPyBackend", "project_text", "project_formula", "load_project", "run_graph", "run_project", "find_graph",
    "ErrorDetail", "NovaError", "ValidationError", "ShapeError", "ConflictError", "PatchError", "DecodeError", "MigrationError",
    "ExecutionError", "MissingInputError", "RuntimeShapeError", "UnsupportedOperationError", "DependencyError", "BackendError", "ProjectionError",
]

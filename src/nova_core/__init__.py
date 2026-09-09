from .canonical import canonical_bytes, canonical_json, project_record, record_hash, semantic_hash
from .codec import decode_project, encode_project
from .errors import ConflictError, DecodeError, ErrorDetail, MigrationError, NovaError, PatchError, ShapeError, ValidationError
from .model import Edge, Graph, Module, Node, Project, SchemaHeader, validate_graph, validate_module, validate_project
from .patch import GraphPatch, GraphTransaction, PatchResult, apply_graph_patch
from .shape import DimExpr, ProofStatus, Shape, ShapeConstraint, ShapeObligation, ShapeSolver, as_dim
from .types import TensorType
from .ops import ShapeInference, broadcast_shapes, contract_shape, elementwise_shape, matmul_shape, reshape_shape, transpose_shape

__version__ = "0.2.0"

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
    "ErrorDetail", "NovaError", "ValidationError", "ShapeError", "ConflictError", "PatchError", "DecodeError", "MigrationError",
]

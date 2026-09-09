from nova_core import Graph, Module, Node, Project, SchemaHeader


def make_project(*, nodes=None, provenance=None, migration_history=()):
    nodes = nodes or (
        Node(id="n1", kind="Identity", inputs=("x",), outputs=("y",)),
    )
    return Project(
        header=SchemaHeader(
            nova_core_version="0.1.0",
            schema_version="0.1.0",
            feature_flags=("graph-kernel",),
            migration_history=migration_history,
        ),
        modules=(
            Module(
                id="app",
                graphs=(
                    Graph(id="main", inputs=("x",), outputs=("y",), nodes=tuple(nodes)),
                ),
            ),
        ),
        provenance=provenance or {},
    )

# Round 01 Release Notes — Canonical Graph Kernel

NOVA now has its first executable authoritative program object.

The release turns the structure-first claim into concrete software:

$$
\boxed{
\text{Program Identity}
\rightarrow
\text{Canonical Typed Structural Graph}
}
$$

The core can now serialize deterministically, compute semantic identity, reject structurally invalid graphs, preserve unknown future fields, apply validated graph patches transactionally, detect stale patch bases, and roll back committed graph changes.

This release does not yet assign tensor meaning to `value_type` or `shape_type`. Those fields are preserved structurally so Round 02 can add native Tensor/Shape semantics without replacing the graph kernel.

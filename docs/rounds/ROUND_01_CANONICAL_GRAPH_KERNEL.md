# Round 01 — Canonical Graph Kernel

Round 01 makes NOVA's first core claim executable:

$$
\boxed{
\text{Authoritative Program Identity}
=
\text{Versioned Typed Structural Graph}
}
$$

Implemented in this round:

- immutable `SchemaHeader`, `Project`, `Module`, `Graph`, `Node`, and `Edge` objects;
- structural validation;
- deterministic canonical UTF-8 JSON;
- semantic hashing separated from provenance/migration history;
- forward-compatible unknown-field preservation;
- JSON decode/encode round-trip;
- typed `NovaError` family;
- transactional `GraphPatch` with base-hash conflict detection;
- candidate validation before working-state mutation;
- exact rollback to the prior semantic hash.

Round 01 deliberately does **not** implement Tensor/Shape inference. That begins in Round 02.

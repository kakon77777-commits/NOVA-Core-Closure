# NOVA Stable Structural Identity v0.3

**Status:** Experimental implementation specification  
**Branch:** `experiment/stable-structural-identity-v0.3`  
**Wire projection:** NSM3  
**Identity revision:** 1  
**Canonical math delimiter:** `$...$` and `$$...$$`

## 1. Purpose

NOVA already separates the authoritative typed structural graph from source text. NSM2 additionally replaces known semantic words such as operator, dtype, device, layout, effect, and differentiation names with global numeric semantic atoms.

v0.3 addresses the next remaining dependency on human-readable text: structural objects are still identified by labels such as module names, graph names, node names, and value symbols.

The v0.3 target is:

$$
\boxed{
\text{Object Identity}
\neq
\text{Human Label}
\neq
\text{Semantic State}
}
$$

For a structural object $x$, define:

$$
I(x)\in\{0,1\}^{128}
$$

as its persistent machine identity, $L(x)$ as its human-facing label, and $S(x)$ as its semantic state.

A label-only rename $\rho$ must satisfy:

$$
I(\rho(x))=I(x)
$$

and

$$
S(\rho(x))=S(x).
$$

The machine projection therefore requires:

$$
\boxed{
H_{\mathrm{MID}}(P,M)
=
H_{\mathrm{MID}}(\rho(P),\rho(M))
}
$$

where $P$ is a NOVA project and $M$ is its persistent identity manifest.

By contrast, a real semantic state mutation must change the machine identity hash:

$$
S(P')\neq S(P)
\Rightarrow
H_{\mathrm{MID}}(P',M)\neq H_{\mathrm{MID}}(P,M).
$$

## 2. Scope

v0.3 assigns persistent 128-bit `StructuralID` values to four structural identity classes:

- module;
- graph;
- node;
- graph-local value.

The existing NOVA Core schema is not changed. The legacy `str` identifiers remain the current runtime/API projection. v0.3 is an additive identity layer above the frozen Core contract.

This is deliberate: the experiment can be validated without silently redefining G1–G7.

## 3. StructuralID

A `StructuralID` is exactly 128 bits.

Human-readable diagnostic form:

```text
sid:<32 hexadecimal digits>
```

The binary machine projection stores the 16 raw bytes, not the diagnostic text form.

The v0.3 bootstrap derives IDs from a domain-separated SHA-256 construction and truncates to 128 bits. The manifest rejects duplicate IDs.

The 256-bit `machine_identity_hash` remains distinct from the 128-bit persistent object IDs.

## 4. Bootstrap is a migration event

Existing NOVA projects already use textual identifiers. v0.3 therefore defines a one-time bootstrap:

$$
P_{legacy}
\xrightarrow{\operatorname{Bootstrap}}
M_0.
$$

For an unchanged legacy project, bootstrap is deterministic.

However, bootstrap is **not** intended to infer an eternal identity again after every edit. Once produced, $M_0$ must be persisted.

This distinction is essential. The initial migration may use legacy labels while minting IDs, but after migration:

$$
\boxed{
\text{rename label}
\not\Rightarrow
\text{mint new identity}
}
$$

Re-running bootstrap after an arbitrary rename is treated as a new import/migration event, not as identity preservation.

## 5. IdentityManifest

The manifest contains:

- project root `StructuralID`;
- identity revision;
- entity `StructuralID`;
- entity kind;
- parent `StructuralID`;
- current human-facing label.

Its role is transitional and projectional. The stable ID is authoritative for machine identity. The label is replaceable.

The hierarchy is:

$$
I_P
\rightarrow
I_M
\rightarrow
I_G
\rightarrow
\{I_N,I_V\}.
$$

Labels are unique only inside the relevant scoped identity namespace.

## 6. Identity-normalized project record

The v0.3 projection replaces mutable labels in the canonical semantic record:

$$
\text{module.id}
\rightarrow
I_M
$$

$$
\text{graph.id}
\rightarrow
I_G
$$

$$
\text{node.id}
\rightarrow
I_N
$$

and graph/node value references:

$$
\text{value label}
\rightarrow
I_V.
$$

Explicit edge endpoints are similarly rewritten from node labels to node IDs.

After replacement, modules, graphs, nodes, and explicit edges are ordered by stable machine identity rather than mutable label spelling. This prevents a rename from changing the serialized order.

## 7. NSM3

NSM3 reuses the deterministic field coding and Global Semantic Registry from NSM2, but its payload is the identity-normalized project projection.

The envelope is positional rather than text-keyed:

$$
[\,r_I,\ I_P,\ P_I\,]
$$

where:

- $r_I$ is the identity revision;
- $I_P$ is the project root identity;
- $P_I$ is the identity-normalized project record.

Therefore the envelope does not need textual keys such as `identity_root` or `project` in the binary representation.

Known semantic atoms remain numeric through the v0.2 Global Semantic Registry.

For the v0.3 validation graph, the following strings are absent from the NSM3 payload:

```text
app
main
add_node
left
right
sum
Add
Pure
Differentiable
```

The absence of these strings is an implementation property, not a claim that NSM3 contains no UTF-8 anywhere. Extension data and semantic domains not yet migrated may still use local symbols.

## 8. Human projection and sidecar

Human-readable names and documentation move to an identity-keyed sidecar:

$$
I_x
\leftrightarrow
\operatorname{Label}(x).
$$

`identity_sidecar()` also attaches non-authoritative `source_projection` and provenance data to stable node/graph/module identities.

This directly supports the intended model:

$$
\boxed{
\text{Machine Core}
\oplus
\text{Human Projection Sidecar}
}
$$

rather than embedding human documentation into execution authority.

## 9. Alpha-renaming transition

Given a project $P$, manifest $M$, and a set of label updates $R$, v0.3 defines:

$$
(P',M')
=
\operatorname{ApplyLabelProjection}(P,M,R).
$$

The operation first preserves the identity-normalized core, then changes only labels in the manifest, and finally reprojects a legacy-compatible NOVA `Project`.

The expected result is:

$$
H_{sem}(P')\neq H_{sem}(P)
$$

under the current legacy Core hash, because current Core semantics still include textual IDs, while:

$$
\boxed{
H_{MID}(P',M')=H_{MID}(P,M)
}
$$

and:

$$
\operatorname{NSM3}(P',M')
=
\operatorname{NSM3}(P,M).
$$

This difference is intentional. v0.3 demonstrates the migration path from label-sensitive legacy identity to label-independent machine identity without changing the frozen Core schema in place.

## 10. Identity versus state

Stable identity must survive an edit, but the machine state hash must not hide semantic mutation.

If one node keeps the same `StructuralID` but changes:

```text
Add -> Subtract
```

then:

$$
I_N'=I_N
$$

while:

$$
S_N'\neq S_N
$$

and therefore:

$$
H_{MID}'\neq H_{MID}.
$$

This prevents the identity layer from becoming a semantic-equivalence shortcut.

## 11. Compatibility

v0.3 is additive:

- NSM1 remains unchanged;
- NSM2 remains unchanged;
- Global Semantic Registry revision remains unchanged;
- the frozen NOVA Core graph schema remains unchanged;
- no existing runtime or interpreter is required to accept raw 128-bit IDs yet;
- NSM3 is decoded through an `IdentityManifest` back into the current legacy-compatible `Project` projection.

A future integration gate may move stable IDs into the Core schema itself, but v0.3 does not make that decision.

## 12. Explicit non-goals and remaining textual domains

v0.3 does **not** yet claim that every remaining string is a human label.

The following remain outside this migration boundary:

- arbitrary attribute keys and values;
- external ABI / runtime binding names;
- module import/export conventions not proven to be internal identity references;
- symbolic shape/dimension names such as `B`;
- arbitrary extension payloads;
- free-form constraint reasons and diagnostics;
- semantic references hidden inside extension-defined records.

These must not be blindly replaced by IDs because some strings are semantic payload, external protocol names, or extension-owned data.

A later revision should classify these domains explicitly before further symbol removal.

## 13. Validation conditions

v0.3 acceptance requires at least:

1. deterministic bootstrap for an unchanged legacy project;
2. deterministic NSM3 encoding;
3. semantic round-trip through the same manifest;
4. structural human labels absent from the tested NSM3 payload;
5. label-only rename changes legacy `semantic_hash` but not `machine_identity_hash`;
6. label-only rename produces byte-identical NSM3;
7. the same NSM3 blob can be reprojected with a renamed manifest;
8. a real semantic mutation changes `machine_identity_hash`;
9. sidecar annotations are keyed by stable IDs;
10. NSM1/NSM2 experimental behavior remains intact.

## 14. Current validation result

The isolated compatibility harness executed the v0.2 registry/codec tests and the new v0.3 structural-identity tests together:

```text
16 passed
```

A separate NSM3 harness verified:

- legacy semantic hash changes under complete label rename;
- machine identity hash remains unchanged;
- NSM3 bytes remain unchanged;
- `Add -> Subtract` changes machine identity hash.

The complete repository regression suite has not been re-executed in the current remote environment because the execution container cannot clone/download GitHub. This limitation must remain explicit until a full local or CI run is performed.

## 15. Next likely boundary

v0.3 removes structural human labels from machine identity. The next useful experiment should not blindly remove every remaining string. It should classify the remaining symbol domains into:

$$
\text{Identity}
\cup
\text{Semantic Atom}
\cup
\text{External Contract}
\cup
\text{Human Projection}
\cup
\text{Extension-Owned Payload}.
$$

Only after this classification should NOVA continue toward a more completely symbol-minimal / tensor-native machine representation.

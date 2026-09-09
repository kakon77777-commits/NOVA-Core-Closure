# NOVA Core Closure Round 07 — Projection Integrity & Structured Editing Design

## Status
Approved continuation of G2 Projection & Editing.

## Source constraints
Round 07 follows the recovered NOVA specifications:

- G2 requires mathematical projection, structured-text projection, node-graph projection, structured diff, error view, and semantic-hash invariance across projections.
- Projection edits must become candidate graph patches before commit.
- A candidate may enter the authoritative graph only after validation.
- Projection differences are not automatically semantic differences.
- Full projectional IDE and Notebook UI are outside this round; the roadmap explicitly permits a structured-text-first fallback.

## Goal
Build the machine-verifiable G2 core without creating a second source of truth.

$$
\boxed{
G^*
\xrightarrow{\Pi}
(V_{text},V_{math},V_{graph},V_{editable})
}
$$

All views must preserve the same semantic identity unless an edit is explicitly interpreted as a candidate patch.

## Architecture

### 1. Projection snapshot
`ProjectionSnapshot` records:

- base semantic hash;
- concise structured text;
- formula projection when supported;
- machine node-graph projection;
- lossless editable structured text;
- explicit reversibility metadata.

Calling projection code must not mutate the canonical graph.

### 2. Lossless editable structured text
Round 07 does not attempt a full human language parser. The editable projection is deterministic pretty JSON of the complete graph record. It is still a structured text projection, but unlike the concise formula/text views it is lossless and parseable.

$$
\operatorname{Parse}(T_{edit}) = G'
$$

and for an unedited projection:

$$
H_{sem}(G') = H_{sem}(G).
$$

### 3. Structural and semantic diff
`GraphDiff` compares two canonical graphs and classifies:

- node additions/removals/modifications;
- edge additions/removals;
- graph interface changes;
- constraint changes;
- graph attribute changes;
- semantic-hash change.

Node modifications retain field-level before/after values for type, shape, effect, differentiation, inputs, outputs, kind, attributes, constraints, and extensions.

### 4. Patch extension
Existing `GraphPatch` gains explicit replacement/interface fields rather than simulating replacement as unsafe remove+add ordering:

- `replaced_nodes`;
- `changed_inputs`;
- `changed_outputs`;
- `changed_attributes`.

Patch application continues to build and validate a complete candidate project before commit.

### 5. Projection edit candidate
`interpret_structured_text_edit(...)` performs:

1. parse edited structured text;
2. require the graph identity to remain targeted;
3. derive `GraphDiff`;
4. derive `GraphPatch`;
5. apply it to a candidate copy;
6. run existing full project validation;
7. produce preview/audit objects;
8. leave working state unchanged.

Commit is explicit through a transaction or output file.

### 6. Error and audit views
Errors are projected from existing typed `NovaError` data. Audit view includes base/candidate hashes, semantic-change flag, patch summary, diff summary, validation result, and provenance/rationale.

## CLI/API surface
Add:

- `nova project --view graph`
- `nova project --view editable`
- `nova diff <base> <target>`
- `nova edit-preview <project> --edited <graph.txt>`
- `nova edit-commit <project> --edited <graph.txt> --output <project.json>`

The commit command writes a new canonical project file and does not silently overwrite its input.

## Non-goals

- full graphical IDE;
- free-form natural-language editing;
- general formula parser;
- drag-and-drop node editor;
- Notebook execution model;
- three-way merge;
- G3 memory/resource planning.

## Exit criteria

1. text/formula/graph/editable projections leave semantic hash unchanged;
2. editable projection round-trips losslessly for tested graphs;
3. structural diff deterministically distinguishes semantic vs non-semantic changes;
4. a text edit produces a candidate GraphPatch, not direct mutation;
5. invalid edits fail with typed errors and leave working state unchanged;
6. preview and commit hashes match;
7. CLI/API smoke tests pass;
8. full inherited suite remains green.

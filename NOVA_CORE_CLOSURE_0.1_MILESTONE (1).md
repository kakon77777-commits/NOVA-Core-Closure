# NOVA Core Closure 0.1 — Milestone Decision

## 決策

第一個正式實作 milestone 採：

$$
\boxed{
\text{G1 Core Closure}
+
\text{G4 GraphPatch Preparation}
}
$$

而不是完整統合 G0–G8。

## 第一階段 deliverables

### A. Canonical Graph
- Project / Module / Graph / Node / Edge schema
- deterministic serializer
- semantic hash
- schema version
- migration header
- structured diff
- GraphPatch transaction

### B. Type / Tensor / Shape
- scalar/tensor values
- shape expressions
- broadcast
- contraction
- ShapeObligation
- minimal decidable constraint solver

### C. Execution
- pure function
- if
- bounded loop
- interpreter
- NumPy/CPU reference backend
- CLI

### D. Differentiation
- reverse-mode AD
- finite difference check
- stop-gradient
- explicit nondifferentiable failure

### E. AI-native preparation
- GraphPatch validator
- base hash
- proof obligations
- tests
- provenance
- rollback

## Exit criteria

至少三個模型可執行：

1. Linear Regression
2. MLP
3. Small Attention

並通過：

- shape rejection
- gradient check
- deterministic serialization
- semantic hash stability
- Python reference equivalence
- GraphPatch rollback
- no silent failure

## Implementation recommendation

Reference implementation 先使用 Python。

原因不是把 NOVA 定義成 Python，而是讓：

$$
\text{formal semantics}
\rightarrow
\text{reference executable model}
$$

最短路徑成立。

Reference backend 建議使用 NumPy；自動微分核心應保留 NOVA graph-level reverse transform，而不是只把 correctness 委託給外部 autograd。

下一階段才考慮 MLIR / LLVM / GPU lowering。

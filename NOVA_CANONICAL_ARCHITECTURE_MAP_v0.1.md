# NOVA Canonical Architecture Map v0.1

**日期：** 2026-08-18  
**定位：** NOVA 正式實作前的 Recover → Reconcile → Freeze Core 架構圖  
**狀態：** Implementation-preparation baseline  
**Canonical math delimiter：** `$...$` 與 `$$...$$`

---

## 0. 結論先行

NOVA 不需要重新設計。

現有五份主幹文件已經形成足夠穩定的權威層次：

$$
\boxed{
\text{Core Baseline}
\rightarrow
\text{Unified Roadmap}
\rightarrow
\text{Extension Contracts}
\rightarrow
\text{Vertical Slices}
}
$$

本次重新檢視後，建議凍結：

$$
\boxed{
\mathcal N_{\mathrm{Core}}
=
(
\mathcal G,
\mathcal T,
\mathcal S,
\mathcal E,
\mathcal M,
\mathcal D,
\mathcal R
)
}
$$

作為 NOVA 的核心本體模型。

NOVA 不是文字語法、不是 Tensor DSL、不是 Python 的預處理器，也不是 HSO 的另一個名字。

NOVA 的權威程式本體是：

$$
\boxed{
\text{typed structural program graph}
}
$$

文字、數學公式、節點圖、文件、AI 操作視圖都只是 projection。

---

# 1. 文件權威層級

## 1.1 Tier A：Nova Core Baseline v3.0

**角色：核心語言憲法。**

負責定義：

- 程式本體；
- Node / Edge model；
- 型別；
- Tensor / Shape；
- Effects；
- Ownership / Resource；
- Automatic Differentiation；
- Compiler pipeline；
- Runtime；
- CLI；
- FFI；
- Core MVP；
- Extension interfaces。

任何新版實作都不得因其他外層理論而默默改寫 Core semantic contract。

---

## 1.2 Tier B：Nova Unified Roadmap v1.0

**角色：Gate-based 工程統合路線。**

核心原則：

1. Core 穩定、外層可替換；
2. 一個問題只有一個權威層；
3. 高維本體與人類 projection 分離；
4. 壓縮不等於資訊消失；
5. 顯性失敗優於靜默損壞；
6. 每層必須可單獨運作。

Roadmap 定義 G0–G8，不用年份驅動，而使用可重現驗收 Gate。

---

## 1.3 Tier C：ISWP-05「結構先於文字」

**角色：後文本程式本體論與可證偽原則。**

它不是新增一套 Core schema，而是規定：

$$
\text{Text}
\neq
\text{Authoritative Program Identity}.
$$

並要求：

- 多 projection；
- semantic hash；
- structured diff / merge；
- GraphPatch；
- projection loss 可追蹤；
- AI 直接改圖但不可越過 validator。

---

## 1.4 Tier D：EML–APL / Operator IR Bridge

**角色：前置 operator bridge，不是 Nova Core dependency。**

資料流：

$$
S
\xrightarrow{\operatorname{parse}}
A
\xrightarrow{\operatorname{normalize}}
O
\xrightarrow{\operatorname{verify}}
O^{\checkmark}
\xrightarrow{\operatorname{lower}}
\mathcal N.
$$

它負責把 EML / APL-like operator semantics 穩定轉成 Nova tensor graph。

Core 不依賴它才能存在。

---

## 1.5 Tier E：Dynamic Revealing Vertical Slice

**角色：高價值垂直驗證案例。**

它測試 NOVA 是否真的能承載：

- semantic identity；
- operator control；
- source provenance；
- permission；
- sparse tensor state；
- reversible operations；
- multi-projection consistency。

它不是 NOVA Core 的定義來源。

---

# 2. 不可動核心

## 2.1 Structure-first authority

NOVA canonical program identity：

$$
\boxed{
G^\ast
}
$$

而不是 source string。

Human view：

$$
V_H=\pi_H(G^\ast)
$$

AI view：

$$
V_A=\pi_A(G^\ast)
$$

Formula view：

$$
V_F=\pi_F(G^\ast)
$$

任何 projection 編輯最後都必須轉成 graph patch。

---

## 2.2 Project object

一個 Nova project：

$$
\mathcal P
=
(
\mathcal{Mod},
\mathcal{Sym},
\mathcal{Graph},
\mathcal{Constraint},
\mathcal{Artifact}
).
$$

### Node 最小權威欄位

```text
Node {
  id
  kind
  inputs[]
  outputs[]
  value_type
  shape_type
  effect_type
  differentiation_type
  source_projection
  constraints[]
  attributes{}
}
```

### Edge

$$
e=(u,v,k,\chi)
$$

Edge kind 至少允許：

- value dependency；
- control dependency；
- type / shape dependency；
- effect dependency；
- ownership transfer；
- differentiation dependency；
- resource dependency；
- validation dependency。

因此 NOVA canonical structure 是 graph，而不是純 AST tree。

---

# 3. Tensor-native type system

NOVA 中 Tensor 是基本值族：

$$
\operatorname{Tensor}
[
\tau;
(d_1,\ldots,d_r);
\ell;
\delta
].
$$

其中：

- $\tau$：element type；
- $(d_1,\ldots,d_r)$：shape；
- $\ell$：layout；
- $\delta$：device / placement。

Scalar 是 rank-0 tensor，而不是 Tensor library 的特殊例外。

## 3.1 Dimension expression

至少允許：

- constant；
- symbol；
- affine expression；
- constrained nonlinear expression；
- runtime dimension。

Core solver 第一階段至少保證 Presburger-decidable subset。

超出可判定域時：

$$
\boxed{
\text{runtime guard}
\;\text{or}\;
\text{proof obligation}
}
$$

而不是默認相容。

---

# 4. Core semantic systems

## 4.1 Shape

Shape compatibility 是 Core authority。

不交給：

- AI intuition；
- EML；
- ISQL；
- SOS；
- backend。

---

## 4.2 Effects

至少包含：

```text
IO
State
Random
Network
File
Device
Unsafe
NonDeterministic
External
```

Pure node 可以合法重排；effect node 不得越過未證明可交換的 effect edge。

---

## 4.3 Differentiability

節點至少具有：

```text
Differentiable
PiecewiseDifferentiable
NonDifferentiable
UnknownDifferentiability
```

Language-level transforms：

$$
\operatorname{grad},
\quad
\operatorname{jacobian},
\quad
\operatorname{jvp},
\quad
\operatorname{vjp}.
$$

Reverse / forward AD 是 graph transformation，不是表面 library trick。

---

## 4.4 Resource / ownership

記憶體與 device placement 最終是 Core / compiler responsibility。

AI 可以提出 proposal，但：

$$
\boxed{
\text{AI proposal}
\neq
\text{memory-safety proof}
}
$$

必須存在 deterministic validator 與 conservative fallback。

---

# 5. Compiler canonical pipeline

正式 pipeline：

$$
\mathcal G_{\mathrm{source}}
\rightarrow
\mathcal G_{\mathrm{typed}}
\rightarrow
\mathcal G_{\mathrm{effect}}
\rightarrow
\mathcal G_{\mathrm{diff}}
\rightarrow
\mathcal G_{\mathrm{memory}}
\rightarrow
\mathcal G_{\mathrm{opt}}
\rightarrow
IR_H
\rightarrow
P_H.
$$

Core IR 必須顯式保存：

- tensor type；
- shape；
- effects；
- device；
- ownership / resource token；
- control flow；
- AD transform；
- stable version。

第一階段不應重造整個低階編譯宇宙。

優先採：

- Interpreter reference；
- CPU reference backend；
- Python interoperability；
- 後續 MLIR / LLVM / GPU lowering。

---

# 6. NOVA-A：AI-native 的真正含義

AI-native NOVA 不是：

$$
\text{AI}
\rightarrow
\text{source code text}.
$$

而是：

$$
\boxed{
\text{Intent}
\rightarrow
\text{Candidate Graph}
\rightarrow
\text{Constraint Validation}
\rightarrow
G^\ast
}
$$

AI 修改 canonical program 必須提交 GraphPatch：

```text
GraphPatch {
  base_hash
  added_nodes[]
  removed_nodes[]
  changed_edges[]
  changed_constraints[]
  proof_obligations[]
  tests[]
  rationale
}
```

這與 2026-08 HSO machine-native runtime 經驗高度相容，但 HSO 只提供工程信心，不修改 Nova Core 定義。

---

# 7. Extension boundary

## 7.1 ISQL

提供：

```text
SemanticPayload
```

角色：

$$
\text{high-dimensional semantic state}
\rightarrow
\text{Nova construction input}.
$$

ISQL 不負責 Nova execution semantics。

---

## 7.2 EML / EML-OIR

角色：

$$
\text{human / AI dense intent surface}
\rightarrow
\text{operator IR}
\rightarrow
\text{Nova lowering}.
$$

EML-OIR 第一批 operator 可以保持：

```text
shape
reshape
transpose
iota
each
reduce
scan
outer
compose
fork
commute
```

不要把完整 APL glyph set 併入 Nova Core。

---

## 7.3 SOS

SOS 負責 operator closure / composition algebra。

Nova 負責：

- typing；
- shape；
- effects；
- executable structure。

---

## 7.4 Cl-safe

Cl-safe 驗證高階 operator composition。

它不能取代 Nova Core type checker。

---

## 7.5 SNTME / Dynamic Revealing

屬於高價值 vertical slice。

第一版允許 Python / SQLite / graph structures / existing tensor libraries 當 implementation backend，只要 canonical semantic contract 已落在 EML-U / OIR / Nova structure 中。

---

# 8. 現在與 2026-07 roadmap 的差異

以下是本次 **2026-08-18 inference**，不是原文件內容。

HSO v1.0 的完成證明 AI 現在可以有效協助：

- machine-native canonical state；
- structured patches；
- deterministic serialization；
- append-only audit；
- rollback / replay；
- hash-chain verification；
- sparse operator/tensor state；
- machine-only observatory。

因此部分原本較晚的 Gate 可以提前。

但這不是所有 Gate 都可以壓縮。

---

# 9. Gate acceleration matrix

| Gate | 原定位 | 2026-08-18 判定 |
|---|---|---|
| G0 | 規格凍結 | **基本完成，可立即 formal freeze** |
| G1 | Core executable closure | **現在立刻實作** |
| G2 | Human projection/editing | **Projection 可與 G1 並行；完整 IDE 延後** |
| G3 | Memory/resource safety | **不可跳過；維持獨立 Gate** |
| G4 | AI-native GraphPatch | **可提前至 G1 後半部** |
| G5 | SOS + Cl-safe | **等 G1 semantic contract 穩定再接** |
| G6 | Execution paradigm planner | **延後** |
| G7 | ISQL semantic tensor | **接口先凍結，完整統合延後** |
| G8 | Minimal sufficient control / real-world execution | **延後** |

---

# 10. 新版實作順序

建議把原 G1 與 G4-preparation 拆成新的 Phase A–D。

## Phase A — Canonical Graph Kernel

完成：

1. deterministic Project / Module / Graph schema；
2. Node / Edge canonical IDs；
3. canonical serialization；
4. semantic hash；
5. structured error object；
6. GraphPatch transaction；
7. rollback；
8. migration/version header。

驗收：

$$
\operatorname{Hash}(\operatorname{Canon}(G))
$$

對相同 semantic graph 穩定。

---

## Phase B — Tensor / Shape Semantic Kernel

完成：

1. scalar + tensor type；
2. symbolic shape expression；
3. broadcast；
4. contraction；
5. ShapeObligation；
6. minimal decidable constraint solver；
7. elementwise ops；
8. matmul；
9. reshape / transpose。

驗收：

- 合法 shape 正確推導；
- 非法 shape 顯性拒絕；
- unknown shape 不被靜默接受。

---

## Phase C — Executable Closure

完成：

1. pure function；
2. `if`；
3. bounded loop；
4. interpreter；
5. CPU / NumPy reference backend；
6. structured text projection；
7. formula projection；
8. CLI；
9. Python interop。

驗收模型：

$$
Y=W X+b
$$

以及：

- linear regression；
- MLP；
- small attention。

---

## Phase D — Language-Level AD + AI Graph Construction

完成：

1. reverse-mode AD；
2. finite-difference gradient checker；
3. GraphPatch AI adapter；
4. build transaction；
5. provenance；
6. AI sandbox；
7. patch diff；
8. deterministic validator。

AI 必須能：

- 增加 node/layer；
- change shape；
- repair type error；
- add test；
- submit differentiation request；

而不必產生完整 text source。

---

# 11. 第一個正式實作 milestone

建議名稱：

# **NOVA Core Closure 0.1**

它不是完整 NOVA 1.0。

它是第一個不可逆的工程錨點：

$$
\boxed{
\text{Canonical Program Graph}
+
\text{Tensor/Shape Semantics}
+
\text{Interpreter}
+
\text{Reverse AD}
+
\text{GraphPatch}
}
$$

如果這一層成功，後面的：

- Nova-H；
- Nova-A；
- EML-OIR；
- ISQL；
- SOS；
- Cl-safe；
- SNTME；

都可以在不改 core ontology 的前提下逐步接入。

---

# 12. 第一輪禁止事項

NOVA Core Closure 0.1 不做：

- 完整 visual IDE；
- GPU optimizer；
- distributed runtime；
- arbitrary effect system 完整版；
- full MSSP-AISMBI AI memory planner；
- SOS 全量統合；
- ISQL 全量統合；
- SNTME 全量統合；
- 16-paradigm planner；
- single-symbol control；
- arbitrary AI-created Core operators；
- 任何需要重新定義 Core ontology 的 HSO feature。

---

# 13. 最終架構判定

NOVA 的核心邊界：

$$
\boxed{
\text{NOVA Core}
=
\text{typed tensor/operator program ontology + executable semantics}
}
$$

不是：

$$
\text{NOVA}
=
\text{所有 EveMissLab 理論的超級集合}.
$$

AI 時代真正使 NOVA 提前可行的地方，是：

$$
\boxed{
\text{AI can now operate the canonical structure directly}
}
$$

而不是：

$$
\boxed{
\text{AI can replace formal semantics}
}
$$

這兩者必須永久區分。

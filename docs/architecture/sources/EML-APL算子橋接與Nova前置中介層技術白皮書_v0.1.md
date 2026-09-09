# EML–APL 算子橋接與 Nova 前置中介層技術白皮書

## ——以改良 APL 算子代數建立 EML Operator IR

**版本：** v0.1  
**狀態：** INTERNAL TECHNICAL DRAFT／暫不公開  
**作者：** Neo.K（許筌崴）／EveMissLab  
**協作整理：** GPT-5.6 Thinking  
**日期：** 2026-07-18  
**文件定位：** EML 擴展規格、APL 系列續接文件、Nova 前置架構草案  

---

## 摘要

EML（Efficient New Language）目前已具備語義壓縮、結構化表示、可逆展開與 AI 操作導向等基本特徵；Nova 則被規劃為更接近張量、圖、形狀約束、自動微分與 AI 原生計算本體的後續語言。兩者之間仍缺少一個明確的中介層：它既不能只是自然語言的縮寫，也不能過早要求完整的張量程式本體，而應能穩定表示高階算子、陣列結構、型別升遷、軸運算、廣播、組合與微分資訊。

本文提出以既有的改良 APL 算子代數為基礎，建立：

1. **EML-APL Experimental Profile**：供 AI 使用的高密度陣列與算子表面層；
2. **EML Operator IR（EML-OIR）**：與字形無關、可型別化、可驗證、可下降至多後端的算子中介表示；
3. **Nova Lowering Contract**：未來將 EML-OIR 映射為 Nova 張量圖與程式本體的橋接契約。

本文不主張將古典 APL 的完整符號集直接併入 EML Core。相反地，本文主張吸收 APL 的算子智慧，保留 EML 的 ASCII canonical form 與可逆語義，並把特殊字形降為可選顯示投影。如此可避免核心語法膨脹、Tokenizer 不穩定、歷史語義綁定與未來 Nova 重寫成本。

核心架構為：

$$
\text{Natural Language / EML Surface / APL-like Surface}
\longrightarrow
\text{EML Operator IR}
\longrightarrow
\begin{cases}
\text{Python / NumPy}\\
\text{JAX / PyTorch}\\
\text{Rust}\\
\text{Nova}
\end{cases}
$$

---

## 關鍵詞

EML、APL、算子代數、Operator IR、Nova、陣列程式設計、張量語言、自動微分、AI 原生語言、型別多態、語義壓縮

---

# 1. 問題定義

## 1.1 EML 現階段的缺口

EML 的主要優勢是將意圖、關係與程序壓縮為 AI 可操作的符號結構。然而，當任務進入以下範圍時，只依靠一般函式呼叫與語義縮寫會迅速變得不足：

- 對陣列逐元素套用函式；
- 沿特定軸進行聚合；
- 對序列保留中間累積狀態；
- 生成笛卡兒積或外積關係；
- 對函式進行組合、交換、分叉與綁定；
- 顯式描述 rank、shape、axis 與 broadcasting；
- 將同一算子作用於實數、雙數、複數或其他代數結構；
- 保留自動微分與後端最佳化所需資訊。

若 EML 未建立這一層，未來通往 Nova 時將面臨兩種不理想選擇：

1. EML 直接生成低階 Python／框架程式碼，導致語義結構提前消失；
2. EML 直接生成完整 Nova 張量圖，使 EML 與尚未穩定的 Nova 本體過度耦合。

因此需要一個中間表示。

---

## 1.2 APL 的位置

APL 是典型的陣列導向語言，其歷史價值在於將 `fold`、`scan`、`outer`、`each` 等結構提升為語言核心。既有改良實驗進一步將這些算子解除數值型別綁定，使同一算子可以透明作用於：

- 實數；
- 雙數；
- 複數；
- 網格；
- 函式；
- 其他滿足必要運算公理的代數物件。

本文需要作出一個精確區分：

> APL 是陣列原生語言，但不是本文所稱的「現代張量圖原生語言」。

現代張量圖原生語言通常還要求：

- 明確 dtype；
- symbolic shape；
- rank polymorphism；
- device placement；
- broadcasting contract；
- automatic differentiation graph；
- sparse／dense layout；
- effect system；
- memory planning；
- graph patch 與版本治理。

APL 位於自然語言／一般程式語言與 Nova 之間，正適合作為中介設計來源。

---

# 2. 既有 APL 改良實驗

既有 APL 系列已建立三層論證。

## 2.1 基礎算子層

`apl_sim.py` 被記載為核心算子代數，包含：

```text
fold
scan
outer
each
fork
compose
commute
iota
rho
grade_up
grade_down
```

其核心意義不是重製 APL 字形，而是將算子實作成對輸入型別保持無知的高階結構。

例如：

```python
def fold(f):
    return lambda seq: reduce(f, seq)

def outer(f):
    return lambda a, b: [[f(x, y) for y in b] for x in a]
```

在此設計中，算子不宣告「值必須是浮點數」，只宣告它需要的運算能力。

---

## 2.2 代數升遷與自動微分層

`apl_ad.py` 被記載為 Dual Number 自動微分系統，包含：

```text
Dual
diff
gradient
d_exp
d_sin
d_cos
d_log
d_sqrt
```

當 `Dual(x, 1)` 被注入既有算子鏈時，`fold`、`each`、`compose` 等算子無需改寫，導數資訊可由代數規則自然傳遞。

這支持以下工程原則：

$$
\boxed{
\text{型別不是算子的固定屬性，而是算子部署時的參數。}
}
$$

---

## 2.3 應用驗證層

既有計畫記載四個應用：

1. `apl_nn.py`：迷你神經網路；
2. `apl_life.py`：Conway's Game of Life；
3. `apl_optimizer.py`：SGD、Momentum、Adam 最佳化器；
4. `apl_fractal.py`：Mandelbrot／Julia Set。

另有 Rust 實驗將 `outer` 分為：

- `outer_seq`；
- `outer_par`。

並以 Rayon 對 Mandelbrot 逃逸時間進行平行化，用以檢查算子在不同工作粒度下的平行收益。

---

# 3. 設計目標與非目標

## 3.1 設計目標

本計畫的目標是：

1. 讓 EML 能表達陣列與高階算子；
2. 保持 AI 可生成、可閱讀與可修正；
3. 保留 ASCII canonical form；
4. 允許 APL-like Unicode 投影；
5. 建立明確的型別、形狀、軸與廣播語義；
6. 支援多後端 lowering；
7. 為 Nova 提供穩定前置介面；
8. 保留 round-trip、trace 與版本治理；
9. 允許未來由 AI 主動發現新算子，但不直接污染核心；
10. 能量化 Token 效率與執行正確率。

---

## 3.2 非目標

v0.x 階段不追求：

- 完整相容所有 APL 方言；
- 複製古典 APL 的全部字形；
- 立即建立完整 Nova runtime；
- 將 EML Core 改造成單一大型陣列語言；
- 在沒有型別與形狀證明的情況下自動接受 AI 新算子；
- 以最短字串取代語義可讀性；
- 將 Unicode 字形設為唯一權威形式。

---

# 4. 路線比較

## 4.1 路線 A：APL 語法直接併入 EML Core

### 優點

- 表達密度高；
- 展示效果強；
- 可直接重用 APL 慣例。

### 主要問題

- EML Core 急速膨脹；
- 特殊字元 Token 成本不穩定；
- 存在傳統 APL 語義包袱；
- 人類與不同模型的可讀性差異大；
- 未來 Nova 語義成熟後可能再次重寫；
- Core 與實驗性功能難以分離。

### 判定

**不採用為主路線。**

---

## 4.2 路線 B：只吸收 APL 算子語義

例如使用：

```text
reduce(add, x)
scan(mul, x)
outer(mul, a, b)
each(f, x)
```

而不是要求：

```apl
+/x
×\x
a∘.×b
f¨x
```

### 判定

**採用，作為 EML canonical surface。**

---

## 4.3 路線 C：建立 EML Operator IR

不同表面表示統一下降為相同 AST／IR 節點：

```text
SUM(x)
reduce(add, x)
+/x
```

都可下降為：

```json
{
  "kind": "operator",
  "op": "reduce",
  "fn": "add",
  "args": ["x"],
  "axis": null
}
```

### 判定

**採用，作為主要架構。**

---

## 4.4 路線 D：建立 EML-APL Experimental Profile

將 APL-like 語法、陣列操作與實驗算子置於獨立 Profile，不直接承諾為 Core。

### 判定

**採用，作為實驗入口。**

---

# 5. 建議總架構

```text
EML Core
│
├── EML-APL Experimental Profile
│   ├── ASCII canonical syntax
│   ├── optional APL-like glyph projection
│   └── profile-specific diagnostics
│
├── EML Operator IR
│   ├── typed operator nodes
│   ├── shape / rank / axis constraints
│   ├── broadcasting contract
│   ├── algebra requirements
│   ├── effect / purity metadata
│   ├── differentiation metadata
│   └── provenance / source map
│
├── Current Backends
│   ├── Python
│   ├── NumPy
│   ├── JAX / PyTorch
│   └── Rust
│
└── Future Backend
    └── Nova tensor graph / program ontology
```

正式資料流：

$$
S
\xrightarrow{\operatorname{parse}}
A
\xrightarrow{\operatorname{normalize}}
O
\xrightarrow{\operatorname{verify}}
O^{\checkmark}
\xrightarrow{\operatorname{lower}_b}
P_b
$$

其中：

- $S$：表面語法；
- $A$：語法 AST；
- $O$：EML Operator IR；
- $O^{\checkmark}$：通過型別、形狀與效果檢查的 IR；
- $P_b$：目標後端程式。

---

# 6. EML-APL Profile

## 6.1 Canonical ASCII 形式

建議第一版採用顯式函式形態：

```text
shape(x)
reshape(shape=[2,3], input=x)
transpose(x, axes=[1,0])
each(fn=f, input=x)
reduce(fn=add, input=x, axis=1)
scan(fn=mul, input=x, axis=0)
outer(fn=mul, left=a, right=b)
compose(f, g, h)
fork(left=f, combine=g, right=h)
commute(f)
```

簡寫可以存在，但必須可正規化回 canonical form。

---

## 6.2 可選 Unicode／APL-like 投影

| Canonical | 顯示投影示例 |
|---|---|
| `shape(x)` | `⍴x` |
| `reshape(s, x)` | `s⍴x` |
| `reduce(add, x)` | `+/x` |
| `scan(add, x)` | `+\x` |
| `outer(mul, a, b)` | `a∘.×b` |
| `each(f, x)` | `f¨x` |

投影層只負責輸入便利與顯示，不作為唯一語義來源。

---

## 6.3 Profile 啟用方式

建議：

```text
use profile eml-apl@0.1
```

或檔頭：

```yaml
profiles:
  - eml-apl@0.1
```

未啟用 Profile 時，APL-like glyph 不應自動改變 EML Core 語義。

---

# 7. EML Operator IR

## 7.1 節點最小結構

```json
{
  "kind": "operator",
  "op": "reduce",
  "fn": {
    "ref": "add"
  },
  "args": [
    {"ref": "x"}
  ],
  "type": {
    "input": "Tensor<T, S>",
    "output": "Tensor<T, S'>"
  },
  "shape": {
    "input": ["N", "M"],
    "output": ["N"]
  },
  "axis": 1,
  "broadcast": "none",
  "algebra": {
    "requires": ["Semigroup<T>"],
    "identity": null
  },
  "laws": {
    "associative": true,
    "commutative": true
  },
  "effects": [],
  "differentiation": {
    "mode": "backend",
    "rule": null
  },
  "source": {
    "profile": "eml-apl@0.1",
    "span": [120, 142]
  }
}
```

---

## 7.2 必要欄位

第一版至少應保存：

- `kind`
- `op`
- `fn`
- `args`
- `axis`
- `shape`
- `rank`
- `dtype`
- `broadcast`
- `algebra.requires`
- `effects`
- `differentiation`
- `source`

---

## 7.3 為什麼要保存代數要求

`reduce(add, x)` 並不必然要求 $x$ 為浮點數。

它真正需要的是：

- 元素型別存在 `add`；
- `add` 至少滿足所宣告的結合條件；
- 若允許空序列，必須存在 identity。

因此可表達為：

$$
\operatorname{reduce}_{\oplus}:
\operatorname{Array}(T)
\rightarrow T
$$

其中：

$$
(T,\oplus)
\in
\operatorname{Semigroup}
$$

若有單位元：

$$
(T,\oplus,e)
\in
\operatorname{Monoid}
$$

這正是改良 APL 與 Nova 之間的重要橋接：算子依賴公理，不依賴固定數值型別。

---

# 8. 第一批算子集合

## 8.1 結構算子

```text
shape
rank
reshape
transpose
axis_move
iota
```

## 8.2 映射與廣播算子

```text
each
map
zip
broadcast
```

## 8.3 聚合與前綴算子

```text
reduce
fold
scan
```

## 8.4 關係生成與收縮算子

```text
outer
inner
contract
```

## 8.5 函式組合算子

```text
compose
fork
commute
bind
```

## 8.6 排序與索引算子

```text
grade_up
grade_down
gather
scatter
mask
```

## 8.7 微分與追蹤標記

```text
diff
gradient
jvp
vjp
trace
pure
effect
```

其中 `jvp`、`vjp` 可先只作 IR metadata，不要求 EML runtime 立即實作。

---

# 9. Shape、Rank、Axis 與 Broadcasting

## 9.1 Shape

令：

$$
x : \operatorname{Tensor}[T; s_1,\ldots,s_n]
$$

則：

```text
shape(x)
```

回傳：

$$
[s_1,\ldots,s_n]
$$

---

## 9.2 Rank

$$
\operatorname{rank}(x)=n
$$

Rank 應成為型別檢查的一部分，而不是只在 runtime 臨時查詢。

---

## 9.3 Axis

所有會改變維度的算子必須明確處理 `axis`：

```text
reduce(add, x, axis=1)
scan(add, x, axis=0)
```

省略 `axis` 時的預設值必須由 Profile 版本固定，不能依後端自行猜測。

---

## 9.4 Broadcasting

廣播不可只依賴 NumPy 隱含規則。IR 必須保存：

```json
"broadcast": {
  "mode": "numpy",
  "left": ["N", 1],
  "right": [1, "M"],
  "result": ["N", "M"]
}
```

未來 Nova 可選擇：

- 靜態證明；
- runtime guard；
- 拒絕不確定廣播；
- 生成 symbolic constraint。

---

# 10. 自動微分橋接

## 10.1 EML 階段

EML 表面層只需表達意圖：

```text
gradient(fn=loss, wrt=params)
```

## 10.2 EML-OIR 階段

IR 保存：

- 微分目標；
- 自變數；
- JVP／VJP 偏好；
- 可微分性；
- 不可微分節點；
- subgradient policy；
- stop-gradient 邊界。

## 10.3 Nova 階段

Nova 將其實體化為：

- 張量計算圖；
- primal graph；
- derivative graph；
- device placement；
- memory schedule。

因此 Dual Number 實驗是概念證據，不必限制未來只能採用 forward-mode AD。

---

# 11. 後端 Lowering

## 11.1 Python

適用於：

- 基本正確性；
- 小型 list；
- 教學與 trace；
- 自訂代數物件。

## 11.2 NumPy

適用於：

- dense array；
- 基本 broadcasting；
- CPU 向量化。

## 11.3 JAX／PyTorch

適用於：

- 自動微分；
- GPU；
- JIT；
- 神經網路與張量圖。

## 11.4 Rust

適用於：

- 型別化 runtime；
- 平行算子；
- 可控記憶體；
- 原生部署；
- 算子成本實驗。

## 11.5 Nova

未來 Nova lowering 不應重新解析 EML 表面字串，而應直接接收已驗證的 EML-OIR。

---

# 12. AI 操作模型

EML 的主要操作者預期是 AI，因此語言需要優先支援以下流程：

$$
\text{Intent}
\rightarrow
\text{Operator Proposal}
\rightarrow
\text{IR Validation}
\rightarrow
\text{Backend Selection}
\rightarrow
\text{Execution}
\rightarrow
\text{Trace}
\rightarrow
\text{Revision}
$$

AI 可以提出新算子，但新算子必須附帶：

1. canonical name；
2. 展開定義；
3. 輸入／輸出型別；
4. shape rule；
5. algebra requirements；
6. effects；
7. differentiation rule；
8. reference implementation；
9. property tests；
10. migration rule。

未完整提供者只能作為 local macro，不能直接升為 Core operator。

---

# 13. 算子晉升機制

## 13.1 Local Macro

只在單一任務內有效。

## 13.2 Profile Operator

在 `eml-apl` 等 Profile 中被標準化。

## 13.3 Shared OIR Operator

多個 Profile 與後端都能使用。

## 13.4 Core Operator

符合以下條件後才可晉升：

- 高使用頻率；
- 跨領域；
- 語義穩定；
- 跨後端；
- Token 收益明確；
- 無重大歧義；
- 可逆展開；
- 有正式測試；
- 有版本遷移策略。

---

# 14. 編譯與驗證管線

```text
1. Parse
2. Normalize glyphs to canonical ASCII
3. Resolve profile and operator names
4. Build surface AST
5. Lower to EML-OIR
6. Infer dtype / shape / rank
7. Solve axis and broadcast constraints
8. Check algebra requirements
9. Check effects and purity
10. Attach AD metadata
11. Optimize
12. Lower to backend
13. Execute
14. Capture trace
15. Round-trip / equivalence validation
```

---

# 15. 最佳化規則

第一版可加入保守規則：

## 15.1 Map Fusion

$$
\operatorname{each}(f,\operatorname{each}(g,x))
\Rightarrow
\operatorname{each}(f\circ g,x)
$$

條件：

- $f,g$ 純函式；
- 無 trace barrier；
- 無例外順序要求。

## 15.2 Reduce Fusion

只在已證明結合律、型別穩定與後端支援時執行。

## 15.3 Transpose Cancellation

$$
\operatorname{transpose}(\operatorname{transpose}(x,p),p^{-1})
\Rightarrow x
$$

## 15.4 Constant Shape Folding

可在編譯期確定的 `shape`、`rank`、`iota` 應提前計算。

## 15.5 Parallel Outer

`outer` 可根據：

- 輸入大小；
- 單格計算成本；
- 記憶體；
- 裝置；

選擇 sequential、SIMD、threaded 或 GPU lowering。

既有 Rust Mandelbrot 實驗即屬於此類成本驗證。

---

# 16. Token 與語義測試

EML-APL 不應只比較字串長度。

應同時測量：

$$
Q=
\rho_T
\cdot
A_{\mathrm{sem}}
\cdot
A_{\mathrm{exec}}
\cdot
S_{\mathrm{cross}}
\cdot
R_{\mathrm{roundtrip}}
$$

其中：

- $\rho_T$：Token 壓縮率；
- $A_{\mathrm{sem}}$：語義正確率；
- $A_{\mathrm{exec}}$：執行正確率；
- $S_{\mathrm{cross}}$：跨模型穩定性；
- $R_{\mathrm{roundtrip}}$：往返重建率。

測試組至少比較：

1. 自然語言；
2. Python；
3. NumPy／JAX；
4. APL-like glyph；
5. EML canonical；
6. EML-OIR JSON；
7. Nova 表示（完成後）。

---

# 17. 測試類型

## 17.1 單算子測試

- `reduce`
- `scan`
- `outer`
- `each`
- `reshape`
- `transpose`

## 17.2 組合測試

- `compose(each(...), reduce(...))`
- `fork`
- `outer + reduce`
- shape polymorphism；
- nested axes。

## 17.3 代數多態測試

同一 IR 分別作用於：

- `float`；
- `int`；
- `Dual`；
- `Complex`；
- Boolean semiring；
- symbolic expressions。

## 17.4 後端一致性測試

$$
\operatorname{run}_{Python}(O)
\simeq
\operatorname{run}_{Rust}(O)
\simeq
\operatorname{run}_{Nova}(O)
$$

## 17.5 錯誤測試

- 不相容 shape；
- 無效 axis；
- 缺少 identity 的空 reduce；
- 不可微分算子；
- effect reorder；
- Unicode 正規化衝突。

---

# 18. 版本治理

建議分為：

```text
EML Core v1.x
EML-APL Profile v0.x
EML-OIR v0.x
Nova Lowering Contract v0.x
```

四者獨立版本化。

相容性原則：

1. Surface syntax 可改，但 OIR 需提供 migration；
2. Glyph projection 不得改變 canonical semantics；
3. Profile operator 不自動進入 Core；
4. OIR breaking change 必須提升 major version；
5. Nova 可擴充 OIR metadata，但不得無聲改寫既有語義；
6. 所有 AI 自動提案都先進 candidate namespace。

---

# 19. 實作路線圖

## Phase 0：封存與重新接軌

- 整理既有 APL 論文、計畫與 Rust 實驗；
- 建立檔案清單；
- 確認遺失的 Python 原始碼；
- 將本白皮書納入 EML 內部規劃。

## Phase 1：EML-APL Profile Parser

- canonical ASCII syntax；
- glyph normalizer；
- AST；
- 診斷訊息；
- 10–15 個核心算子。

## Phase 2：EML-OIR v0.1

- OperatorNode；
- shape／rank／axis；
- algebra requirements；
- source map；
- JSON serialization。

## Phase 3：Python Reference Backend

- list backend；
- Dual／Complex 測試；
- round-trip；
- property tests。

## Phase 4：NumPy／Rust Backend

- broadcasting；
- parallel outer；
- benchmark；
- backend equivalence。

## Phase 5：AD 與張量橋接

- JAX／PyTorch lowering；
- JVP／VJP metadata；
- symbolic shapes；
- graph export。

## Phase 6：Nova Contract

- OIR → Nova graph；
- dtype／device／memory；
- effect system；
- graph patch；
- provenance；
- rollback。

---

# 20. 最小可行規格

v0.1 建議只要求：

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

以及：

- ASCII canonical；
- Unicode normalizer；
- OperatorNode；
- shape／axis；
- Python backend；
- Rust `outer` backend prototype；
- 100 組單元測試；
- 30 組跨表示 round-trip；
- 20 組 AI 零樣本生成測試。

不要在 v0.1 同時加入完整 sparse、device、memory planner 與 attention。

---

# 21. 核心決策

本文正式建議：

> **EML 不直接吞併古典 APL，而是吸收改良 APL 的算子代數，建立獨立的 EML-APL Profile 與 EML Operator IR。**

架構可濃縮為：

$$
\boxed{
\text{APL 的算子智慧}
+
\text{EML 的壓縮與可逆表示}
=
\text{Nova 的前置算子中介層}
}
$$

其中：

- APL 提供高階陣列與函式算子；
- EML 提供 AI 可操作的 canonical 表示與展開規則；
- EML-OIR 提供型別、形狀、軸、代數與微分資訊；
- Nova 提供現代張量圖與程式本體。

---

# 22. 結論

APL 系列不應被視為已完成後被遺忘的旁支。它實際上已經提前驗證了 EML 通往 Nova 時最需要的一項能力：

> **同一個算子可以先於具體值、具體型別與具體後端而存在。**

EML 若吸收這項成果，便不再只是符號壓縮與語義表示系統，而開始具備：

$$
\text{語義壓縮}
+
\text{算子組合}
+
\text{型別多態}
+
\text{陣列結構}
+
\text{可驗證 lowering}
$$

這使 EML 能在不提前取代 Nova 的前提下，成為 Nova 的可行準備層。

因此，建議接下來的正式工程名稱為：

> **EML Operator Bridge（EOB）**

其核心中介表示為：

> **EML Operator IR（EML-OIR）**

其第一個實驗 Profile 為：

> **EML-APL Experimental Profile**

三者共同構成 EML 由語義壓縮層走向 AI 原生張量計算的第一座正式橋梁。

---

# 附錄 A：Canonical 示例

```text
use profile eml-apl@0.1

x = iota(8)
s = reduce(fn=add, input=x)
p = scan(fn=mul, input=x)
m = outer(fn=mul, left=x, right=x)
y = each(fn=square, input=x)
```

---

# 附錄 B：OIR 示例

```json
{
  "oir_version": "0.1",
  "nodes": [
    {
      "id": "n1",
      "kind": "operator",
      "op": "iota",
      "args": [8],
      "dtype": "int64",
      "shape": [8],
      "effects": []
    },
    {
      "id": "n2",
      "kind": "operator",
      "op": "reduce",
      "fn": {"ref": "add"},
      "args": [{"ref": "n1"}],
      "axis": 0,
      "algebra": {
        "requires": ["Monoid<int64>"],
        "identity": 0
      },
      "effects": []
    }
  ]
}
```

---

# 附錄 C：目前封存狀態

本次資料庫整理確認存在：

- 《算子先於值：APL 算子代數的類型多態重建與算子本體論的實驗性確認》；
- 《APL Operator Algebra — Four Mini-Apps Plan》；
- `apl_maze_rust`：
  - `Cargo.toml`
  - `Cargo.lock`
  - `src/main.rs`
  - `mandelbrot_rust.png`

既有文件另記載下列 Python 檔案，但本次資料庫搜尋未取得其獨立原始檔：

- `apl_sim.py`
- `apl_ad.py`
- `apl_nn.py`
- `apl_life.py`
- `apl_optimizer.py`
- `apl_fractal.py`

這些檔案不得在封存時假裝已找到；後續可從舊工作目錄、壓縮檔或歷史備份繼續追查。

---
title: "結構先於文字：Nova 與後文本程式語言本體論"
english_title: "Structure Before Text: Nova and the Ontology of Post-Textual Programming Languages"
series: "意圖—結構—世界程式論"
series_english: "Intent–Structure–World Programming"
series_number: "05/12"
part: "第二部：後文本語言與結構表示"
author: "Neo.K with Aletheia"
institution: "EveMissLab／一言諾科技有限公司"
version: "v0.1"
date: "2026-07-25"
language: "zh-TW"
document_type: "理論論文／程式本體論"
status: "初版完成"
---

# 結構先於文字：Nova 與後文本程式語言本體論

## Structure Before Text: Nova and the Ontology of Post-Textual Programming Languages

**系列：**《意圖—結構—世界程式論》第五篇  
**部別：**第二部「後文本語言與結構表示」  
**作者：** Neo.K with Aletheia  
**機構：** EveMissLab／一言諾科技有限公司  
**版本：** v0.1  
**日期：** 2026 年 7 月 25 日  

---

## 摘要

傳統程式語言多以文字序列作為權威來源：人類先撰寫字串，解析器再從字串重建抽象語法樹，編譯器則以該樹作為後續分析與執行基礎。這個模型簡潔、可攜、容易版本控制，並已形成成熟的工具與文化。然而，它也把程式身分、結構、依賴、型別、形狀、效果與執行語義，長期綁定於線性文字的表面秩序。

本文提出「結構先於文字」命題：程式的權威本體可以直接是具型別、形狀、效果、記憶、微分、資源與後端義務的結構化程式圖；文字、數學公式、節點圖、文件、除錯介面與人類摘要則是同一程式物件的不同投影。Nova 作為主要實例，其核心可表示為：

$$
\mathcal N_{\mathrm{Core}}
=
\left(
\mathcal G,
\mathcal T,
\mathcal S,
\mathcal E,
\mathcal M,
\mathcal D,
\mathcal R
\right)
$$

其中依序代表結構化程式圖、值與張量型別、形狀及約束求解、效果與可重現性、記憶體與資源規劃、自動微分，以及多後端實現。

本文區分文字先行與結構先行兩種程式生成模式。前者為：

$$
\text{Text}
\rightarrow
\text{Parse}
\rightarrow
\text{Structure}
$$

後者為：

$$
\text{Structure}
\rightarrow
\left\{
\text{Text},
\text{Formula},
\text{Graph},
\text{Document},
\text{Debug View}
\right\}
$$

結構先行不等於取消文字，也不等於視覺化編程。它要求程式身分由正規化結構與語義雜湊決定，而非由某個排版或編輯器私有格式決定；所有投影都必須聲明其可逆性、語意保持與投影損失；AI 可以直接產生結構補丁與規劃，但不能越過型別、效果、記憶體、微分、資源與後端驗證。

本文並提出後文本程式語言的七項最低判準：結構權威性、多投影性、語義身分穩定、投影可追蹤、結構化差分、確定性驗證邊界與開放交換格式。本文分析結構原生程式的主要收益，包括消除解析歧義、提高 AI 直接操作能力、支援高維依賴、改善型別與效果追蹤、建立結構化 diff、容納多閱讀者投影，以及使程式與執行證書形成同一可驗證物件。本文也分析其風險：IDE 綁定、圖規模爆炸、結構化 merge、無障礙問題、跨工具交換、投影不一致、隱藏結構與人類失控。

本文最後提出可證偽研究綱領，包括多投影不動點、語義雜湊穩定性、結構化 merge 成功率、AI 圖補丁正確率、投影編輯認知成本、張量形狀錯誤阻止率、效果衝突偵測、後端語義保持及大規模圖導航效率。本文的核心結論是：後文本程式設計不是文字終結論，而是程式本體與文字表面的解耦；文字繼續存在，但不再必然壟斷程式的存在形式。

**關鍵詞：** Nova、後文本程式設計、結構原生、型別化程式圖、投影式編輯、張量原生、自動微分、效果系統、結構化差分、AI 原生程式語言

---

## Abstract

Traditional programming languages generally treat textual sequences as authoritative sources. Humans write strings, parsers reconstruct abstract syntax trees, and compilers use those trees for later analysis and execution. This model is portable, versionable, and supported by mature tools, yet it binds program identity, structure, dependencies, types, shapes, effects, and semantics to the surface order of linear text.

This paper proposes the principle of structure before text. The authoritative program object may be a typed graph carrying shape constraints, effects, memory obligations, differentiation information, resource plans, and backend requirements. Text, mathematical notation, node graphs, documentation, debugging views, and human summaries become projections of the same program object.

Nova is developed as the primary instance:

$$
\mathcal N_{\mathrm{Core}}
=
\left(
\mathcal G,
\mathcal T,
\mathcal S,
\mathcal E,
\mathcal M,
\mathcal D,
\mathcal R
\right)
$$

The paper distinguishes text-first construction from structure-first construction, defines minimum criteria for post-textual programming languages, and specifies identity, projection, editing, diff, merge, validation, and backend-lowering principles. Structure-first programming does not abolish text or reduce programming to visual diagrams. It relocates authority from one textual surface to a normalized, versioned, and verifiable structural object.

The paper also examines risks: IDE lock-in, graph-scale explosion, structural merge complexity, accessibility, interchange formats, projection inconsistency, hidden structure, and loss of human control. It concludes with a falsifiable research program covering multi-projection fixed points, semantic-hash stability, structural merge, AI graph patches, cognitive cost, shape error prevention, effect-conflict detection, and backend semantic preservation.

**Keywords:** Nova, post-textual programming, structure-native language, typed program graph, projectional editing, tensor-native programming, automatic differentiation, effect systems

---

# 一、問題的提出：為什麼程式必須先成為文字？

大部分程式語言的基本流程是：

$$
\text{Human Thought}
\rightarrow
\text{Source Text}
\rightarrow
\text{Parser}
\rightarrow
\text{AST}
\rightarrow
\text{IR}
\rightarrow
\text{Execution}
$$

程式真正用於型別檢查、最佳化與執行的結構，通常不是原始字串，而是解析後形成的結構表示。然而，人類仍以字串作為主要編輯、儲存與版本控制介面。

這形成一個長期被視為理所當然的制度：

> 程式必須先被寫成文字，才能成為結構。

但這不是計算的邏輯必然，而是歷史上最成功、最便於交換的人機介面選擇。

如果編譯器最終需要的是：

- 節點；
- 邊；
- 型別；
- 依賴；
- 作用域；
- 效果；
- 控制流；
- 資源；
- 記憶體；
- 後端義務；

那麼可以反問：

> **程式能否直接以這些結構存在，再依不同主體需求生成文字與其他視圖？**

本文的回答是肯定的，但附帶嚴格條件。

結構先於文字不是把文字拿掉，也不是把所有程式改成節點圖。它真正改變的是：

$$
\boxed{
\text{Authoritative Program Identity}
:
\text{Text File}
\rightarrow
\text{Structured Program Object}
}
$$

---

# 二、文字先行與結構先行

## 2.1 文字先行模式

定義文字先行程式：

$$
p_T
=
\left(
s,
\operatorname{Parse},
G
\right)
$$

其中：

- $s$：來源字串；
- $\operatorname{Parse}$：解析器；
- $G$：解析所得結構。

其基本關係為：

$$
G
=
\operatorname{Parse}(s)
$$

文字通常是權威來源；AST 可以重新生成。

## 2.2 結構先行模式

定義結構先行程式：

$$
p_S
=
\left(
G^\ast,
\Pi,
\mathcal V
\right)
$$

其中：

- $G^\ast$：權威結構；
- $\Pi$：投影集合；
- $\mathcal V$：驗證與遷移規則。

各種視圖由：

$$
\pi_i(G^\ast)=v_i
$$

產生。

## 2.3 兩者不是互斥

文字仍可作為一種輸入：

$$
s
\xrightarrow{\operatorname{Import}}
G^\ast
$$

但匯入後的權威身分轉移到結構。

同樣地，結構可投影回文字：

$$
G^\ast
\xrightarrow{\pi_{\mathrm{text}}}
s'
$$

因此：

$$
\boxed{
\text{Structure-First}
\neq
\text{Text-Prohibited}
}
$$

它只是拒絕把文字視為唯一合法程式本體。

---

# 三、Nova Core 的七元本體

本文採用：

$$
\boxed{
\mathcal N_{\mathrm{Core}}
=
\left(
\mathcal G,
\mathcal T,
\mathcal S,
\mathcal E,
\mathcal M,
\mathcal D,
\mathcal R
\right)
}
$$

## 3.1 結構化程式圖 $\mathcal G$

程式圖：

$$
\mathcal G
=
(V,E)
$$

其中節點可表示：

- 常數；
- 變數；
- 算子；
- 函式；
- 控制節點；
- 張量；
- 外部能力；
- 效果；
- 斷言；
- 測試；
- 子圖引用。

邊不只表示資料流，也可表示：

- 值依賴；
- 控制依賴；
- 型別依賴；
- 形狀依賴；
- 效果依賴；
- 所有權轉移；
- 微分依賴；
- 資源依賴；
- 驗證依賴。

因此：

$$
e
=
(u,v,k,\chi)
$$

其中：

- $u,v$：節點；
- $k$：邊類型；
- $\chi$：附加約束。

## 3.2 型別系統 $\mathcal T$

Nova 不只記錄值類型，也把張量階數、元素型別與維度結構納入語義。

例如：

$$
X:
\operatorname{Tensor}
\left[
f32;
(B,I)
\right]
$$

$$
W:
\operatorname{Tensor}
\left[
f32;
(I,O)
\right]
$$

則：

$$
XW:
\operatorname{Tensor}
\left[
f32;
(B,O)
\right]
$$

## 3.3 形狀與約束 $\mathcal S$

形狀不是註解，而是可求解約束。

令：

$$
\mathcal C_S
=
\{
I_X=I_W,
B>0,
O>0
\}
$$

若約束不可滿足，系統必須輸出結構化 `ShapeError`，不得等到後端崩潰。

## 3.4 效果與可重現性 $\mathcal E$

效果描述：

- 外部寫入；
- 網路；
- 時間；
- 隨機；
- 全域狀態；
- 裝置；
- 檔案；
- 非確定性；
- 例外；
- 並行。

令節點效果為：

$$
\operatorname{Eff}(v)
$$

子圖效果則依組合規則形成：

$$
\operatorname{Eff}(G')
=
\bigoplus_{v\in G'}
\operatorname{Eff}(v)
$$

## 3.5 記憶體與資源 $\mathcal M$

Nova 將記憶體、生命週期、所有權、配置與裝置位置視為編譯器與驗證系統共同責任。

資源計畫：

$$
M_P
=
\operatorname{Plan}
\left(
G,
T,
S,
E,
H
\right)
$$

其中 $H$ 是硬體條件。

AI 可以建議 $M_P$，但必須經靜態分析、執行檢查或證明義務驗證。

## 3.6 自動微分 $\mathcal D$

微分是語言級圖變換：

$$
\mathcal D:
G
\mapsto
G_{\nabla}
$$

而不是只由函式庫在執行期動態記錄。

系統必須知道：

- 哪些節點可微；
- 哪些節點不可微；
- 哪些需要次梯度；
- 哪些具有自訂規則；
- 哪些微分路徑被阻斷。

## 3.7 多後端實現 $\mathcal R$

語義圖可降低到：

$$
\operatorname{Lower}_H(G)
=
P_H
$$

其中 $H$ 可是：

- CPU；
- GPU；
- NPU；
- WebGPU；
- 分散式叢集；
- 其他專用硬體。

後端只負責實現語義，不得反過來改寫核心語義而不回報。

---

# 四、Nova 的程式物件模型

一個 Nova 專案可表示為：

$$
\mathcal P
=
\left(
\mathcal{Mod},
\mathcal{Sym},
\mathcal{Graph},
\mathcal{Constraint},
\mathcal{Artifact}
\right)
$$

## 4.1 模組

模組保存：

- 導入；
- 導出；
- 命名空間；
- 能力依賴；
- 版本；
- 後端要求；
- 測試。

## 4.2 符號表

符號表不只是名稱到位址，而是：

$$
\operatorname{Symbol}
\mapsto
\left(
\operatorname{NodeID},
\operatorname{Type},
\operatorname{Scope},
\operatorname{Version}
\right)
$$

## 4.3 節點

最小節點：

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
  ownership_type
  constraints[]
  attributes{}
  provenance
}
```

## 4.4 Artifact

Artifact 包含：

- 編譯產物；
- 測試結果；
- 證明義務；
- 執行 trace；
- 文件投影；
- 效能資料；
- 後端差分；
- 錯誤記錄。

這表示程式不只是一個可執行圖，也包含其可驗證歷史。

---

# 五、程式身分：什麼使兩個投影是同一個程式？

## 5.1 表面等價不足

兩段文字完全相同，若其：

- 匯入版本；
- 型別註冊表；
- 效果政策；
- 後端語義；
- 外部能力；

不同，可能不是同一個程式。

反之，數學公式與節點圖表面完全不同，卻可能對應同一結構。

## 5.2 正規化結構

定義正規化：

$$
\operatorname{Norm}
:
G
\mapsto
G_N
$$

處理：

- 無關節點排序；
- 穩定 ID；
- 型別展開；
- 約束排序；
- 引用正規化；
- schema 版本；
- 未知欄位保留。

## 5.3 語義雜湊

定義：

$$
H_{\mathrm{sem}}(G)
=
h
\left(
\operatorname{Norm}(G)
\right)
$$

如果投影切換沒有改變程式：

$$
H_{\mathrm{sem}}(G_t)
=
H_{\mathrm{sem}}(G_{t+1})
$$

## 5.4 觀察等價

對指定觀察集合 $\mathcal O$：

$$
G_1
\equiv_{\mathcal O}
G_2
$$

若：

$$
\forall x\in D,
\quad
\mathcal O
\left(
\operatorname{Run}(G_1,x)
\right)
=
\mathcal O
\left(
\operatorname{Run}(G_2,x)
\right)
$$

且效果、資源與失敗義務符合契約。

結構相同與語義等價是不同層次，不應混淆。

---

# 六、多投影系統

## 6.1 投影集合

Nova 可有：

$$
\Pi(G)
=
\left\{
\pi_{\mathrm{text}},
\pi_{\mathrm{math}},
\pi_{\mathrm{graph}},
\pi_{\mathrm{doc}},
\pi_{\mathrm{debug}},
\pi_{\mathrm{audit}},
\pi_{\mathrm{AI}}
\right\}
$$

## 6.2 結構化文字投影

文字仍然重要，應具備：

- 可讀；
- 可搜尋；
- 可 diff；
- 可在一般編輯器中查看；
- 可用於 code review；
- 可離線交換。

但文字中的排版不再自動決定程式身分。

## 6.3 數學投影

對張量與可微分運算，數學視圖可直接顯示：

$$
Y=XW+b
$$

但背後必須明確保存：

- $X,W,b$ 的型別；
- 維度；
- 廣播規則；
- 裝置；
- 效果；
- 微分策略。

漂亮公式不能取代完整語義。

## 6.4 節點圖

節點圖適合顯示：

- 資料流；
- 分支；
- 循環；
- 共享子圖；
- 資源；
- 依賴。

但大型程式不能只靠拖拉節點維護。

## 6.5 文件投影

文件投影可把：

- 目的；
- 型別；
- 效果；
- 不變量；
- 測試；
- 範例；
- 失敗；

生成為可讀文件。

## 6.6 AI 操作投影

AI 不必閱讀人類排版，而可操作：

```text
GraphPatch
ConstraintPatch
ProofObligation
ExecutionPlan
EvidenceBundle
```

這是 AI 原生性的重要條件。

---

# 七、投影編輯與編輯語義

## 7.1 表面編輯轉為圖補丁

使用者在文字或公式視圖中修改：

$$
v_i
\rightarrow
v_i'
$$

系統需要產生：

$$
\Delta G
=
\operatorname{InterpretEdit}
\left(
v_i,v_i'
\right)
$$

只有當 $\Delta G$ 可驗證時，才能提交至權威圖。

## 7.2 編輯不是直接修改畫面

合理流程：

```text
Projection Edit
→ Candidate Graph Patch
→ Type and Shape Check
→ Effect Check
→ Memory and Resource Obligations
→ Preview
→ Commit
```

## 7.3 多義編輯

若一次表面修改可對應多個結構補丁：

$$
\{
\Delta G_1,\ldots,\Delta G_k
\}
$$

系統應顯示候選，不得靜默選擇高風險修改。

## 7.4 局部可逆性

某些投影只保留部分結構。令：

$$
\pi_i
:
G
\rightarrow
V_i
$$

若不存在完整逆映射，則需標記：

$$
\rho_i
:
V_i
\rightarrow
\Delta(G)
$$

為多候選或有損編輯。

---

# 八、結構化 diff、merge 與版本控制

## 8.1 文字 diff 的限制

文字 diff 主要比較：

- 行；
- 字元；
- 區塊。

但結構修改可能包括：

- 節點移動；
- 子圖抽取；
- 名稱改變；
- 型別改變；
- 邊重新連接；
- 效果擴張；
- 資源策略改變。

## 8.2 結構化 diff

定義：

$$
\Delta G
=
\left(
\Delta V,
\Delta E,
\Delta T,
\Delta S,
\Delta E_f,
\Delta M,
\Delta D
\right)
$$

其中分別表示節點、邊、型別、形狀、效果、記憶體與微分差分。

## 8.3 語意 diff

人類可見摘要應顯示：

```text
Function renamed: unchanged semantics
Tensor shape changed: [B,I] → [B,2I]
External network effect added
Gradient path detached
Memory plan moved from CPU to GPU
```

## 8.4 三方合併

給定基線 $G_0$、分支 $G_A,G_B$：

$$
\operatorname{Merge}
\left(
G_0,G_A,G_B
\right)
\rightarrow
G_M
\cup
\mathcal C_{\mathrm{conflict}}
$$

衝突可包含：

- 同節點不同修改；
- 型別衝突；
- 邊衝突；
- 效果衝突；
- 資源衝突；
- 版本遷移衝突。

## 8.5 結構化 merge 不是自動正確

即使節點 ID 不衝突，兩個修改合併後仍可能破壞全域約束。因此：

$$
\operatorname{MergeSuccess}
\Rightarrow
\operatorname{Revalidate}(G_M)
$$

---

# 九、張量原生與後文本本體的關係

## 9.1 張量不是唯一資料類型

Nova 以張量作為重要一級值，但不應宣稱所有現實物件都必須被強制壓成張量。

核心可以包含：

- 標量；
- 張量；
- 代數資料型別；
- 記錄；
- 事件；
- 資源句柄；
- 能力；
- 外部物件。

## 9.2 形狀一級化

張量原生的真正價值不是少寫矩陣迴圈，而是把：

- 軸；
- 批次；
- 廣播；
- 維度；
- 裝置；
- 分片；

提升為可分析語義。

## 9.3 後端最佳化

對語義等價實現集合：

$$
[G]_{\mathrm{sem}}
$$

可搜尋：

$$
P_H^\ast
=
\arg\min_{P_H\in[G]_{\mathrm{sem}}}
C_H(P_H)
$$

但只有在等價性經證明、差分測試或受控近似確認時才可替換。

## 9.4 不承諾自動全局最優

後端最佳化通常是：

- 啟發式；
- 成本模型相對；
- 硬體相對；
- 工作負載相對。

因此 Nova 不應把「AI 最佳化」描述為必然找到全局最優。

---

# 十、自動微分作為圖變換

## 10.1 語言級微分

令程式圖為：

$$
G
$$

反向微分：

$$
\mathcal D_{\mathrm{rev}}(G)
=
G'
$$

其中 $G'$ 包含：

- 原始前向圖；
- 梯度節點；
- 反向依賴；
- 中間值保存；
- 不可微錯誤；
- 自訂微分規則。

## 10.2 微分身分

微分後程式不是一段臨時執行記錄，而是可版本化的新結構：

$$
G_{\nabla}
$$

## 10.3 效果與微分

具有外部效果的節點，不能自動被視為可微。

例如：

$$
\operatorname{WriteFile}
$$

或：

$$
\operatorname{RandomSample}
$$

需有明確微分規則、停止梯度或錯誤。

## 10.4 微分驗證

可使用：

- 有限差分；
- 符號檢查；
- 已知導數；
- 交叉後端比較；
- 性質測試。

AI 不能只因圖看起來合理而宣告梯度正確。

---

# 十一、記憶體、資源與所有權

## 11.1 AI 建議與可驗證計畫

Nova 可以讓 AI 建議：

- 配置位置；
- 生命週期；
- 緩衝重用；
- 裝置遷移；
- 分片；
- 並行。

但最終需要形成：

$$
M_P
=
\left(
\operatorname{Alloc},
\operatorname{Lifetime},
\operatorname{Ownership},
\operatorname{Placement},
\operatorname{Sync}
\right)
$$

## 11.2 安全義務

需驗證：

- 無懸空引用；
- 無非法別名；
- 無未同步競態；
- 記憶體上限；
- 裝置相容；
- 回收正確；
- 失敗時釋放。

## 11.3 不把記憶體責任神秘化

「由 AI 管理記憶體」不是安全模型。安全模型是：

$$
\text{AI Candidate}
\rightarrow
\text{Formal Resource Plan}
\rightarrow
\text{Static and Runtime Validation}
$$

---

# 十二、效果、能力與外部世界

## 12.1 純計算與外部效果

純節點：

$$
y=f(x)
$$

不改變外部世界。

效果節點則可能：

$$
W_{t+1}
=
T(W_t,a)
$$

## 12.2 能力句柄

外部能力應以顯式句柄存在：

```text
Capability {
  id
  type
  scope
  permissions
  expiry
  provenance
}
```

## 12.3 效果重排

兩個節點可重排，必須滿足：

$$
\operatorname{Commute}(O_1,O_2)
$$

而不能只依資料流看似獨立。

## 12.4 世界狀態仍不屬於 Nova Core 全部責任

Nova 可以表示與執行效果，但長期 Agent 的時間、等待、恢復、批准與世界治理，仍屬後續 Runtime 與 CompilableWorld 層。

---

# 十三、失敗必須型別化

Nova 不應只輸出：

```text
Compilation failed
```

而需有：

```text
ShapeError
TypeError
EffectError
DiffError
MemoryPlanError
BackendError
CapabilityError
ReproducibilityError
MigrationError
ProjectionError
```

## 13.1 錯誤物件

```text
Error {
  kind
  source_nodes[]
  violated_constraints[]
  affected_projections[]
  backend
  evidence
  repair_candidates[]
}
```

## 13.2 不允許靜默猜測

若型別或後端推斷無法確定：

$$
\operatorname{Unknown}
$$

必須保留為一級結果，而不是選擇最常見答案。

---

# 十四、後文本程式語言的七項最低判準

## 判準一：結構權威性

存在：

$$
G^\ast
$$

作為權威程式物件。

## 判準二：多投影性

至少兩種以上人類或機器投影，指向同一程式身分。

## 判準三：語義身分穩定

投影排版改變不自動改變：

$$
H_{\mathrm{sem}}(G^\ast)
$$

## 判準四：投影可追蹤

每一投影能追溯到來源節點與結構版本。

## 判準五：結構化差分

系統能表示節點、邊、型別、形狀、效果與資源差分。

## 判準六：確定性驗證邊界

AI 建議不得越過：

- 型別；
- 形狀；
- 效果；
- 記憶體；
- 微分；
- 後端；
- 權限；

驗證。

## 判準七：開放交換格式

權威程式不得只能存在於單一 IDE 私有資料庫。

---

# 十五、Nova 不是什麼

## 15.1 不是視覺化編程

節點圖只是投影之一。

## 15.2 不是數學符號取代英文

數學公式若沒有型別、形狀、效果與資源語義，只是漂亮表面。

## 15.3 不是張量版 Python

Python 可作匯入與過渡介面，但 Nova 的權威本體與型別系統不同。

## 15.4 不是所有程式都可微

不可微分必須被顯式表示。

## 15.5 不是 AI 猜測語言

AI 是生成與規劃層，不是正確性本體。

## 15.6 不是立即取代所有語言

Nova Core 應先聚焦：

- 張量；
- 科學計算；
- 可微分模型；
- 高效資料流；
- 多後端。

## 15.7 不是私有 IDE 格式

沒有開放 schema、序列化、CLI 與文字投影，就不能稱為可治理的後文本語言。

---

# 十六、AI 原生程式操作

## 16.1 直接建構圖

傳統 AI coding：

$$
\text{Intent}
\rightarrow
\text{Text}
\rightarrow
\text{Parse}
\rightarrow
G
$$

AI 原生 Nova：

$$
\text{Intent}
\rightarrow
\text{Candidate Graph}
\rightarrow
\text{Constraint Validation}
\rightarrow
G^\ast
$$

## 16.2 GraphPatch

AI 修改應提交：

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

## 16.3 最小授權單位

人類可批准：

- 單節點；
- 子圖；
- 效果集合；
- 後端計畫；
- 完整 ProgramHandle。

這比批准一大段不透明文字更可治理。

## 16.4 人類仍需投影

AI 原生不等於人類退出。人類應能查看：

- 結構摘要；
- 語意 diff；
- 風險；
- 測試；
- 未解義務；
- 回復方法。

---

# 十七、與 EML、SOS、Intent IR 的邊界

## 17.1 EML → Nova

EML 負責將人類高密度語意附加降級為 Nova 節點或約束：

$$
T_{\mathrm{EML}}
\xrightarrow{\operatorname{Lower}_{\mathrm{EML}}}
\mathcal N
$$

EML 不直接決定 Nova 的底層記憶體與 kernel。

## 17.2 SOS ↔ Nova

Nova 節點可掛載：

```text
OperatorDescriptor {
  semantic_slot
  composition_slot
  projection_slot
  state_schema
  effect_schema
  version
}
```

SOS 負責更一般的算子閉包與組合代數；Nova 負責可執行結構本體。

## 17.3 Intent IR → Nova

Intent IR 可產生：

- 目標子圖；
- 約束；
- 成功條件；
- 能力需求；
- 證明義務。

但 Nova 不直接決定人類目的是否合法或是否充分。

## 17.4 Runtime

Runtime 負責：

- 工具；
- 事件；
- 暫停；
- 恢復；
- 長時程執行；
- 世界狀態。

Nova Core 則提供可執行且可驗證的程式結構。

---

# 十八、主要風險

## 18.1 IDE 綁定

若程式只能由某個編輯器理解，使用者失去主權。

## 18.2 圖規模爆炸

大型程式圖可能包含數百萬節點，需要：

- 分層；
- 摘要；
- 子圖；
- 查詢；
- 局部視圖；
- 語意導航。

## 18.3 結構化 merge 困難

圖合併比行合併更接近語意，但演算法與 UI 成本更高。

## 18.4 投影不一致

多投影可能不同步或以不同方式隱藏資訊。

## 18.5 隱藏結構

畫面簡潔可能掩蓋大量效果、資源與依賴。

## 18.6 無障礙

若高度依賴圖形介面，可能排除使用螢幕閱讀器、鍵盤或純文字工具的使用者。

## 18.7 格式碎裂

不同工具可能各自擴充 schema，形成不相容方言。

## 18.8 AI 補丁權力過大

結構補丁可能一次改變大量隱藏節點，需要差分、限制與批准。

## 18.9 語意雜湊迷信

相同雜湊只能說明正規化結構相同，不能自行證明其倫理、目的或外部效果正確。

---

# 十九、可證偽研究綱領

## 19.1 多投影不動點

對同一程式：

$$
G
\rightarrow
V_1
\rightarrow
G_1
\rightarrow
V_2
\rightarrow
G_2
$$

測量：

$$
d(G,G_2)
$$

## 19.2 語義雜湊穩定

對排版、節點位置與非語義 UI 修改，檢查：

$$
H_{\mathrm{sem}}
$$

是否保持。

## 19.3 結構化 merge

比較：

- 行 diff；
- AST diff；
- Nova 圖 diff；

在重命名、子圖抽取、型別改變與效果增加下的合併成功率與錯誤率。

## 19.4 AI GraphPatch 正確率

測量：

- 目標保持；
- 型別通過；
- 形狀通過；
- 效果未越界；
- 測試通過；
- 人類接受率；
- 回復成功率。

## 19.5 認知成本

比較人類使用：

- 純文字；
- 數學投影；
- 節點圖；
- 混合投影；

完成理解、修改與除錯的時間。

## 19.6 形狀錯誤阻止率

$$
\eta_S
=
\frac{
\text{shape errors detected before backend execution}
}{
\text{all injected shape errors}
}
$$

## 19.7 效果衝突偵測

注入外部寫入、時間、隨機、網路與並行衝突，測量靜態及受控執行期偵測率。

## 19.8 後端語義保持

比較 CPU、GPU、NPU 結果：

$$
d
\left(
\operatorname{Run}_{H_1}(G),
\operatorname{Run}_{H_2}(G)
\right)
$$

並納入數值容差與非確定性契約。

## 19.9 大圖導航

測量在大規模程式圖中定位：

- 錯誤來源；
- 效果路徑；
- 型別衝突；
- 資源瓶頸；
- 梯度路徑；

所需時間。

---

# 二十、工程路線與階段門

## G0：核心規格凍結

產物：

- schema；
- 術語；
- 錯誤類型；
- 正規化；
- 版本政策；
- ADR。

## G1：Nova Core 閉環

完成：

- 圖 schema；
- 型別；
- 形狀求解；
- CPU 後端；
- reverse-mode AD；
- CLI；
- 文字投影；
- Python／DLPack FFI。

最低案例：

$$
Y=XW+b
$$

及小型訓練迴圈。

## G2：投影與編輯

完成：

- 數學；
- 文字；
- 節點；
- 結構化 diff；
- 錯誤視圖。

驗收：

$$
H_{\mathrm{sem}}(G)=\text{constant}
$$

在不改變語義的投影切換中保持。

## G3：資源安全

完成可驗證記憶體與裝置計畫。

## G4：AI 直接建構

AI 只透過 GraphPatch 修改權威結構。

## G5：外部擴充

再接入：

- EML；
- SOS；
- 安全組合；
- 多範式；
- ProgramHandle。

這個順序避免尚未完成核心，就把所有理論塞入同一語言。

---

# 二十一、本文的十五項命題

## 命題一

$$
\boxed{
\text{Program Structure}
\text{ need not originate from text}
}
$$

## 命題二

$$
\boxed{
\text{Structure-First}
\neq
\text{Text-Free}
}
$$

## 命題三

程式的權威身分可以由正規化結構與版本化 schema 決定。

## 命題四

文字、公式、節點圖與文件可以是同一程式本體的不同投影。

## 命題五

$$
\boxed{
\text{Projection Difference}
\not\Rightarrow
\text{Semantic Difference}
}
$$

## 命題六

多投影系統必須標記可逆性與投影損失。

## 命題七

結構化 diff 比文字 diff 更接近程式語意，但不保證自動正確。

## 命題八

張量原生的核心價值是把形狀、軸、廣播與裝置提升為可驗證語意。

## 命題九

自動微分應是可追蹤的圖變換，而不是不可見的執行技巧。

## 命題十

AI 可以提出程式圖，但不得越過型別、效果、記憶體、微分與後端驗證。

## 命題十一

後端最佳化必須在語意等價類中進行。

## 命題十二

失敗必須型別化、可追蹤且可回復。

## 命題十三

開放交換格式是後文本程式主權的必要條件。

## 命題十四

Nova、EML、SOS、Intent IR 與 Runtime 必須保持分層責任。

## 命題十五

$$
\boxed{
\text{後文本程式設計}
=
\text{程式本體與單一文字表面的解耦}
}
$$

---

# 二十二、與第四篇的銜接

第四篇提出：

$$
\text{Host}
+
\text{Semantic Overlay}
\rightarrow
\text{Host-Neutral Semantic IR}
$$

其目的是讓語意能離開單一宿主表面。

本文再向前一步：

$$
\text{Semantic IR}
\rightarrow
\text{Structure-Native Program Object}
$$

EML 的策略是漸進附加；Nova 的策略是直接讓結構成為本體。

因此：

$$
\boxed{
\text{EML}
=
\text{從既有表面向結構過渡的橋}
}
$$

$$
\boxed{
\text{Nova}
=
\text{結構本身成為權威程式的核心}
}
$$

下一篇將進一步處理：

> 結構中的節點與符號，是否能不只是靜態標記，而成為具有語義、組合與狀態槽的算子閉包？

這將進入 SOS 與「符號作為算子」。

---

# 二十三、結論：文字仍在，但不再是唯一世界

程式文字之所以成功，不只是因為它適合機器，也因為它適合人類：

- 可閱讀；
- 可複製；
- 可搜尋；
- 可版本控制；
- 可跨工具；
- 可長期保存。

因此，後文本程式設計若企圖消滅文字，反而會摧毀重要的工程公共基礎。

真正需要改變的不是文字是否存在，而是：

> **程式的權威結構是否必須永遠被某一種文字排版壟斷。**

Nova 的答案是：

$$
\boxed{
\text{No}
}
$$

程式可以先以結構存在。

人類可以看文字。

數學家可以看公式。

工程師可以看依賴與效果。

除錯者可以看錯誤路徑。

AI 可以看圖補丁、約束與證據。

編譯器可以看型別、形狀、記憶體與後端義務。

這些視圖不必互相競爭誰才是真正程式；它們共同投影自同一個可版本化、可驗證、可遷移的結構本體。

因此，本文的最終命題是：

$$
\boxed{
\text{結構先於文字，不代表文字消失。}
}
$$

$$
\boxed{
\text{它代表文字終於可以從程式本體的唯一容器，}
}
$$

$$
\boxed{
\text{轉變為多種可靠人機投影之一。}
}
$$

當程式身分不再依賴單一表面，後文本程式語言才真正成立。

---

# 附錄 A：Nova 最小結構範例

```json
{
  "nova_version": "0.1",
  "module": "linear_model",
  "nodes": [
    {
      "id": "input_x",
      "kind": "Input",
      "outputs": ["X"],
      "value_type": {
        "element": "f32",
        "shape": ["B", "I"]
      },
      "effects": [],
      "diff": "Differentiable"
    },
    {
      "id": "weight_w",
      "kind": "Parameter",
      "outputs": ["W"],
      "value_type": {
        "element": "f32",
        "shape": ["I", "O"]
      },
      "effects": [],
      "diff": "Differentiable"
    },
    {
      "id": "matmul_1",
      "kind": "MatMul",
      "inputs": ["X", "W"],
      "outputs": ["XW"],
      "value_type": {
        "element": "f32",
        "shape": ["B", "O"]
      },
      "effects": [],
      "diff": "Differentiable"
    },
    {
      "id": "bias_b",
      "kind": "Parameter",
      "outputs": ["b"],
      "value_type": {
        "element": "f32",
        "shape": ["O"]
      },
      "effects": [],
      "diff": "Differentiable"
    },
    {
      "id": "add_1",
      "kind": "Add",
      "inputs": ["XW", "b"],
      "outputs": ["Y"],
      "value_type": {
        "element": "f32",
        "shape": ["B", "O"]
      },
      "broadcast": {
        "b": ["B", "O"]
      },
      "effects": [],
      "diff": "Differentiable"
    }
  ],
  "constraints": [
    "shape(X)[1] == shape(W)[0]",
    "shape(W)[1] == shape(b)[0]"
  ],
  "outputs": ["Y"]
}
```

---

# 附錄 B：GraphPatch 範例

```yaml
graph_patch:
  base_semantic_hash: "sha256:..."
  author: "ai-agent"
  status: "candidate"

changes:
  add_nodes:
    - id: "relu_1"
      kind: "ReLU"
      inputs: ["Y"]
      outputs: ["Y_relu"]
      value_type:
        element: "f32"
        shape: ["B", "O"]
      effects: []
      diff: "Subdifferentiable"

  change_outputs:
    from: ["Y"]
    to: ["Y_relu"]

proof_obligations:
  - "shape(Y_relu) == [B,O]"
  - "effect(relu_1) == pure"
  - "gradient_rule(relu_1) is registered"

validation:
  schema: "passed"
  type: "passed"
  shape: "passed"
  effect: "passed"
  diff: "passed"
  tests: "pending"

approval:
  required: true
  reason: "model behavior changes"
```

---

# 附錄 C：結構化錯誤範例

```yaml
error:
  kind: "ShapeError"
  source_nodes:
    - "matmul_1"

violated_constraints:
  - "shape(X)[1] == shape(W)[0]"

observed:
  X: ["B", 128]
  W: [256, "O"]

affected_projections:
  - "math_view"
  - "text_view"
  - "gpu_backend"

repair_candidates:
  - "change W input dimension to 128"
  - "insert projection operator 128 → 256"
  - "select a compatible W parameter"

status: "blocked"
```

---

# 附錄 D：系列十二篇位置

1. 從程式碼到意圖：程式概念的歷史轉換與後文本時代
2. 自然語言原生計算：從語句生成到語義狀態轉換
3. 形式化壓縮與算子演化：自然語言、形式語言與計算結構的生成
4. 語意附加程式設計：EML 與宿主中立語義中介層
5. **結構先於文字：Nova 與後文本程式語言本體論**
6. 符號作為算子：從靜態字元到可組合計算閉包
7. 意圖中介表示：從自然語言要求到可驗證能力計畫
8. 時間—空間程式控制：長時程 Agent 的迴圈、切片與反身執行
9. Agent Runtime：能力規劃、工具調用與可恢復執行
10. 可編譯世界：從程式執行到世界狀態演化
11. 人類可見狀態：意圖程式系統的稽核、解釋與可逆治理
12. 意圖程式文明：後文本語言、持續 Agent 與可編譯世界的統一理論

---

# 參考文獻

## Neo.K／EveMissLab 理論與規格文件

1. Neo.K with Aletheia，《從程式碼到意圖：程式概念的歷史轉換與後文本時代》，2026。
2. Neo.K with Aletheia，《語意附加程式設計：EML 與宿主中立語義中介層》，2026。
3. Neo.K，《Nova Core Baseline v3.0：統合前正式核心規格》，2026。
4. Neo.K，《Nova Unified Roadmap v1.0：新版計畫書與 AI 原生張量語言統合架構》，2026。
5. Neo.K，《Nova（Project ENL 2.0）：後文本時代的張量原生程式語言》，2026。
6. Neo.K，《EML Universal Semantic Overlay 2026 v2.0》，2026。
7. Neo.K，《符號算子系統（Symbol-as-Operator System, SOS）》，2026。
8. Neo.K，《計算的十六重範式》，2026。

## 一般理論背景

9. Chomsky, N., *Syntactic Structures*, 1957.
10. Knuth, D. E., “Semantics of Context-Free Languages,” 1968.
11. Reynolds, J. C., “The Discoveries of Continuations,” 1993.
12. Erwig, M. and Walkingshaw, E., “The Choice Calculus,” 2011.
13. JetBrains MPS Documentation, Projectional Editing.
14. Lattner, C. and Adve, V., “LLVM: A Compilation Framework for Lifelong Program Analysis & Transformation,” 2004.
15. Lattner, C. et al., “MLIR: Scaling Compiler Infrastructure for Domain Specific Computation,” 2021.
16. Baydin, A. G. et al., “Automatic Differentiation in Machine Learning: a Survey,” 2018.

---

# 版本紀錄

## v0.1 — 2026-07-25

- 完成系列第五篇。
- 將「結構先於文字」建立為程式本體論命題，而非視覺化介面主張。
- 形式化 Nova Core 七元模型。
- 區分文字先行與結構先行程式模式。
- 建立權威結構、正規化、語義雜湊與觀察等價。
- 完成文字、數學、節點、文件、除錯、審計與 AI 投影架構。
- 定義投影編輯與候選 GraphPatch。
- 建立結構化 diff、三方 merge 與全域重新驗證要求。
- 整理張量、形狀、效果、微分、記憶體、資源與後端語義。
- 建立七項後文本程式語言最低判準。
- 區分 Nova 與視覺化編程、數學語法糖、張量版 Python 及 AI 猜測語言。
- 加入主要風險與九項可證偽研究基準。
- 明確界定 EML、SOS、Intent IR 與 Runtime 的接口。

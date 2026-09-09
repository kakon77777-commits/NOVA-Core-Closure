---
title: "動態顯影作為語言調控示範"
subtitle: "EML-U、Operator IR、Nova Core 與 SNTME 的垂直統合規格"
english_title: "Dynamic Revealing as a Language-Regulation Demonstrator: A Vertical Integration Specification for EML-U, Operator IR, Nova Core, and SNTME"
author: "Neo.K with Aletheia"
organization: "EveMissLab／一言諾科技有限公司"
version: "v0.1"
date: "2026-07-27"
document_type: "技術定位文件／垂直示範規格／工程路線"
status: "初版完成"
language: "zh-TW"
keywords:
  - 動態顯影
  - EML-U
  - EML-P
  - Operator IR
  - Nova
  - SNTME
  - 語言調控
  - 原生張量記憶
  - 語意附加
  - 工作狀態重構
---

# 動態顯影作為語言調控示範

## EML-U、Operator IR、Nova Core 與 SNTME 的垂直統合規格

**作者：** Neo.K with Aletheia  
**機構：** EveMissLab／一言諾科技有限公司  
**版本：** v0.1  
**日期：** 2026 年 7 月 27 日  

---

## 摘要

動態顯影技術最初處理的是：系統如何依照當前查詢、任務、時間、權限與工作狀態，從大量潛在語義、歷史痕跡與關係結構中，選擇性地顯現出當下必要的局部狀態。當此理論進一步擴展至動態記憶顯影、原生張量記憶、記憶糾纏、差合化操作、工作態重構與污染治理後，它已不再只是記憶檢索技術，而形成一個可用來驗證新型程式語言架構的完整垂直案例。

本文提出：將動態顯影定位為 EML-U、EML Operator IR、Nova Core 與稀疏原生張量記憶引擎 SNTME 的第一個語言調控示範。所謂「語言調控」，不是以特殊語法取代既有程式碼，也不是讓語言任意控制模型輸出，而是由語言與中介表示明確規定：哪些語義可以進入活動域、哪些模式應被收縮、哪些關係可以分離、哪些記憶可以重新耦合、哪些權限不可穿透、哪些語義損失必須被標記或拒絕，以及結果如何驗證、投影與追加式寫回。

本文建立一條垂直統合鏈：EML-U 保存宿主中立的語義附加與多重觀測條件；EML-P 與 Operator IR 提供可確定解析、可降階與可執行的操作子集；Nova Core 將語義與操作轉化為型別化權威結構圖；SNTME 以稀疏局部張量核與關係超圖承載多模式記憶；動態顯影執行器完成治理選域、條件收縮、局部解纏、歷史回溯、工作態再糾纏與閉環驗證；最後再投影為人類介面、Agent 工作態、審計視圖或傳統後端執行計畫。

本文主張：動態顯影很適合作為 Nova 與 EML-U 的第一個共同示範，因為它同時需要語義身分、結構先於文字、多模式張量、非交換算子、權限治理、來源保持、語義降階、可撤銷操作與多投影一致性。它可以避免 Nova 在缺乏真實應用時過度抽象，也可以避免 EML-U 停留在純符號與語義附加願景。最小工程目標不是立即完成完整新語言，而是跑通一條可被測試、比較、否證與展示的 Dynamic Revealing Vertical Slice。

**關鍵詞：** 動態顯影、語言調控、EML-U、EML-P、Operator IR、Nova、SNTME、張量記憶、工作態重構、語義治理

---

# 一、問題：為什麼動態顯影適合成為語言示範

## 1.1 動態顯影不是單一演算法

一般資訊檢索系統的流程可以寫成：

$$
q
\rightarrow
\operatorname{Retrieve}(q,\mathcal D)
\rightarrow
\operatorname{Generate}
$$

動態顯影則需要同時處理：

- 查詢與任務；
- 語義與時間；
- 因果與版本；
- 來源與可信度；
- 主體與代理；
- 權限與治理；
- 分支與失敗路徑；
- 顯影、解纏、回溯、重構與驗證。

因此其實際運行鏈更接近：

$$
\boxed{
\text{治理選域}
\rightarrow
\text{條件顯影}
\rightarrow
\text{模式收縮}
\rightarrow
\text{局部解纏}
\rightarrow
\text{歷史回溯}
\rightarrow
\text{工作態再糾纏}
\rightarrow
\text{閉環驗證}
\rightarrow
\text{延續執行}
}
$$

這條鏈同時包含語義、資料、控制、權限、張量與驗證問題。它不是一個函式庫即可完整表達的局部功能，而是一個足以測試語言是否真的能承載高階結構的垂直案例。

## 1.2 現有語言可以實作，但會產生結構翻譯損耗

動態顯影當然可以先以 Python、JSON、向量資料庫、圖資料庫與工作流引擎完成。問題不在於「做不到」，而在於理論中的原生物件會被拆散成多個互不具有共同語義權威的工程物件：

```text
Python class
+ JSON metadata
+ vector embedding
+ graph edge
+ database row
+ permission rule
+ workflow state
+ prompt convention
```

此時系統必須依賴大量約定，才能知道這些物件共同代表某一個記憶態。常見風險包括：

- 相同概念在多個 schema 中重複定義；
- 語義與執行狀態不同步；
- 權限在檢索後才被補做；
- 來源只作為附加欄位而非操作約束；
- 解纏與再糾纏沒有型別契約；
- 降階至後端時發生靜默語義損失；
- 人類視圖與 Agent 視圖逐漸分裂。

動態顯影因此提供了一個實際問題，用來驗證：

> 新語言是否只是提供不同表面語法，還是真的能以共同結構本體調控語義、操作與投影。

---

# 二、「語言調控」的正式定義

## 2.1 語言調控不是輸出操縱

本文所稱的語言調控，不是：

- 以提示詞強迫模型輸出特定答案；
- 以關鍵字硬編碼所有流程；
- 讓語言層代替模型推理；
- 宣稱所有語義都能完全形式化；
- 用新語法重新包裝普通函式呼叫。

語言調控是指：

> 系統以可識別、可型別化、可驗證的語言物件，規定語義如何進入、轉換、顯影、執行、投影、降階、拒絕與寫回。

形式上，可將調控規格表示為：

$$
\mathbb C_{\xi}
=
\left(
G,
S,
P,
M,
O,
L,
V,
F
\right)
$$

其中：

- $G$：目標與任務；
- $S$：作用域與活動語義域；
- $P$：權限、來源與治理政策；
- $M$：需啟用的張量模式；
- $O$：允許的操作集合；
- $L$：語義損失預算與降階規則；
- $V$：驗證義務；
- $F$：失敗、回退與拒絕策略。

## 2.2 語言調控的八個問題

一個完整的動態顯影語言調控規格，至少必須回答：

1. **顯影什麼？**
2. **對誰顯影？**
3. **在什麼任務下顯影？**
4. **哪些模式可以被收縮？**
5. **哪些關係可以被解纏或重新合成？**
6. **哪些語義不可降階或不可跨越權限？**
7. **顯影結果如何被驗證？**
8. **結果是否、以及如何寫回總記憶場？**

因此：

$$
\boxed{
\text{Language Regulation}
=
\text{Semantic Admission}
+
\text{Structural Constraint}
+
\text{Operational Control}
+
\text{Projection Governance}
+
\text{Validation}
}
$$

---

# 三、四層垂直統合架構

## 3.1 總體鏈

本文建議的第一代垂直鏈為：

$$
\mathcal H
\xrightarrow{\mathcal A_U}
\mathbb E_U
\xrightarrow{\mathcal D_{P/OIR}}
\mathcal G_N
\xrightarrow{\mathcal L_M}
\mathfrak M_t
\xrightarrow{\mathcal R_{\xi}}
\widehat{\mathbb W}_{\xi,t}^{*}
\xrightarrow{\pi_H,\pi_A,\pi_X}
\mathcal V_{\xi}
$$

其中：

- $\mathcal H$：文件、對話、程式碼、日誌、版本與其他宿主；
- $\mathcal A_U$：EML-U 語義附加；
- $\mathbb E_U$：宿主中立語義物件；
- $\mathcal D_{P/OIR}$：EML-P／Operator IR 的確定性降階與操作化；
- $\mathcal G_N$：Nova 型別化權威結構圖；
- $\mathcal L_M$：載入或映射為稀疏張量記憶場；
- $\mathfrak M_t$：時間 $t$ 的總記憶場；
- $\mathcal R_{\xi}$：任務條件下的動態顯影與工作態重構；
- $\widehat{\mathbb W}_{\xi,t}^{*}$：經驗證工作態；
- $\pi_H,\pi_A,\pi_X$：人類、Agent 與執行後端投影。

## 3.2 EML-U：保存尚未降階的完整語義

EML-U 在本示範中的主要責任是：

- 將語義附著於原始宿主，而不破壞宿主；
- 維持語義身分與表面形式分離；
- 表達時間、因果、版本、來源、權限與不確定性；
- 允許二維、圖式與多重觀測者投影；
- 保存尚不能由 EML-P 或 Nova Core 完整執行的概念；
- 對每次降階產生明確 loss report。

一個最小 EML-U 顯影附加物件可以表示為：

```yaml
semantic_id: DR-SEM-0001
host_anchor: message://research/turn-184
kind: memory_trace
content_role: rejected_hypothesis
modes:
  semantic: "局部低秩近似足以保持全部版本關係"
  temporal: "2026-07-26"
  causal: "被版本反例否定"
  version: "SNTME-v0.1/branch-b"
  task: "工作態重構"
provenance:
  status: observed
  source_ids:
    - message-184
    - experiment-22
permission:
  reveal_to:
    - research-agent
  deny_to:
    - public-demo
projection_policy:
  eml_p: metadata_only
  nova: typed_relation
  python: explicit_record
```

此物件的重點不是 YAML 表面，而是每一欄位具有可追蹤的語義身分與降階政策。

## 3.3 EML-P 與 Operator IR：形成可執行調控子集

EML-P 不必承載 EML-U 的全部高階表面能力。它負責提供：

- 線性、可 Git diff 的交換形式；
- 穩定 parser；
- 可測試的核心操作；
- 對傳統宿主的確定性轉譯；
- 顯式 unsupported；
- 語義損失報告；
- 與 Operator IR 的一對一映射。

Operator IR 則應至少定義：

```text
reveal
contract
project
split
trace_back
merge
re_entangle
validate
commit
quarantine
revoke
```

以及張量與治理參數：

```text
modes
axes
shape
rank_budget
partition
provenance_policy
permission_policy
loss_budget
validation_obligations
fallback
```

例如：

```text
reveal memory.project_alpha
  under task("continue tensor-memory series")
  modes[semantic, temporal, causal, version, provenance]
  deny[private_personal]
  loss <= metadata_only
  then split by[version, source]
  trace_back depth 4
  merge as working_state
  validate[replay, provenance, contradiction]
```

這段文字可以只是 EML-P／OIR 的一種投影；真正權威的操作仍應進入 Nova 結構圖。

## 3.4 Nova Core：保存權威調控結構

Nova 在本示範中的責任不是取代 EML-U，而是將可操作部分轉化為：

- 型別化節點；
- 型別化資料與控制邊；
- 張量模式與形狀約束；
- 權限與效果約束；
- 解纏與再糾纏操作；
- 驗證義務；
- 失敗與回退分支；
- 可比較、可版本化與可撤銷的 GraphPatch。

最小權威物件可寫成：

$$
\mathcal N_{DR}
=
\left(
\mathcal G,
\mathcal T,
\mathcal S,
\mathcal E,
\mathcal P,
\mathcal V,
\mathcal R
\right)
$$

其中：

- $\mathcal G$：動態顯影操作圖；
- $\mathcal T$：值、張量與記憶物件型別；
- $\mathcal S$：形狀、模式、分割與秩約束；
- $\mathcal E$：讀取、推定、寫回與外部工具效果；
- $\mathcal P$：來源、權限與治理政策；
- $\mathcal V$：驗證義務；
- $\mathcal R$：Python、資料庫、GPU 或其他後端實現。

Nova 的核心價值在於：

$$
\boxed{
\text{同一顯影程序的文字、公式、節點、審計與 Agent 視圖，}
\text{都只是同一權威結構的投影。}
}
$$

## 3.5 SNTME：承載可被調控的記憶場

SNTME 不需要物理上建立單一巨大稠密張量。第一代工程形式應是：

$$
\boxed{
\text{局部型別張量核}
+
\text{稀疏關係超圖}
+
\text{低秩因子}
+
\text{來源錨點}
+
\text{追加式操作帳本}
}
$$

語言層對 SNTME 的作用不是直接指定每一個底層矩陣配置，而是宣告：

- 哪些模式參與本輪計算；
- 哪些關係必須保持；
- 哪些來源不可融合；
- 哪些張量核可以近似；
- 容許多少資訊損失；
- 哪些工作態可以寫回；
- 哪些結果只能暫時存在。

---

# 四、動態顯影作為語言調控的完整示範

## 4.1 示範任務

第一個正式案例可設定為：

> 從一個具有多篇論文、多次修訂、失敗路徑、分支討論與工程規劃的長期研究專案中，恢復足以繼續工作的局部狀態。

輸入包括：

- Markdown 論文；
- 對話紀錄；
- 版本差異；
- 實驗結果；
- 失敗紀錄；
- 任務清單；
- 權限與公開狀態。

期望輸出不是文件列表，而是：

$$
\widehat{\mathbb W}_{\xi}^{*}
=
\left(
\text{Goal},
\text{Current State},
\text{Accepted},
\text{Rejected},
\text{Evidence},
\text{Branches},
\text{Conflicts},
\text{Open Nodes},
\text{Next Actions}
\right)
$$

## 4.2 同一記憶場，不同語言調控結果

假設總記憶場為 $\mathfrak M$。

研究延續任務：

$$
\widehat{\mathbb W}_{\mathrm{research}}
=
\mathcal R_{\xi_{\mathrm{research}}}(\mathfrak M)
$$

工程實作任務：

$$
\widehat{\mathbb W}_{\mathrm{engineering}}
=
\mathcal R_{\xi_{\mathrm{engineering}}}(\mathfrak M)
$$

公開宣傳任務：

$$
\widehat{\mathbb W}_{\mathrm{public}}
=
\mathcal R_{\xi_{\mathrm{public}}}(\mathfrak M)
$$

三者來源相同，但模式、權限、顯影深度與輸出結構不同：

$$
\widehat{\mathbb W}_{\mathrm{research}}
\neq
\widehat{\mathbb W}_{\mathrm{engineering}}
\neq
\widehat{\mathbb W}_{\mathrm{public}}
$$

這正是語言調控最直觀的示範：不是改寫底層資料，而是以顯式條件改變局部工作態的形成方式。

## 4.3 調控步驟

### 步驟一：語義進入

EML-U 為原始內容建立：

- Semantic ID；
- Host Anchor；
- Source；
- Version；
- Time；
- Permission；
- Confidence；
- Relation Type。

### 步驟二：治理選域

$$
\mathfrak M_{\xi}^{\mathrm{allowed}}
=
\Gamma_{\xi}(\mathfrak M)
$$

任何未授權內容不得先被檢索、再於輸出階段遮蔽；權限必須先於顯影。

### 步驟三：條件收縮

$$
\mathbb A_{\xi}
=
\operatorname{Contract}
\left(
\mathfrak M_{\xi}^{\mathrm{allowed}},
\mathbb Q_{\xi}
\right)
$$

查詢不再只是語義向量，而是任務、時間、權限與工作狀態的對偶條件。

### 步驟四：局部解纏

$$
\Delta_{\mathcal P,C}(\mathbb A_{\xi})
=
\left(
\mathcal F_{\xi},
\mathbb E_{\xi}^{+},
\mathbb E_{\xi}^{?},
\mathbb E_{\xi}^{-}
\right)
$$

其中：

- $\mathcal F_{\xi}$：可辨識因子；
- $\mathbb E_{\xi}^{+}$：有效關係殘差；
- $\mathbb E_{\xi}^{?}$：未知殘差；
- $\mathbb E_{\xi}^{-}$：錯誤或污染殘差。

### 步驟五：回溯與工作態重構

$$
\mathcal H_{\xi}^{\mathrm{back}}
=
\mathcal B_{\xi}(\mathcal F_{\xi})
$$

$$
\widehat{\mathbb W}_{\xi}
=
\mathcal U_{\mathrm{work}}
\left(
\mathcal H_{\xi}^{\mathrm{back}},
\mathbb E_{\xi}^{+}
\right)
$$

### 步驟六：驗證

$$
\widehat{\mathbb W}_{\xi}^{*}
=
\mathcal V_{\xi}
\left(
\widehat{\mathbb W}_{\xi}
\right)
$$

至少檢查：

- 來源保持；
- 版本純度；
- 因果方向；
- 權限合法；
- 矛盾保持；
- 正向重播；
- 任務可執行性。

### 步驟七：多視圖投影

人類視圖：

$$
V_H=\pi_H(\widehat{\mathbb W}_{\xi}^{*})
$$

Agent 視圖：

$$
V_A=\pi_A(\widehat{\mathbb W}_{\xi}^{*})
$$

執行計畫：

$$
V_X=\pi_X(\widehat{\mathbb W}_{\xi}^{*})
$$

三種投影可以外觀不同，但必須共享同一語義雜湊或可證明的觀察等價關係。

---

# 五、語義調控物件與最小資料契約

## 5.1 Dynamic Revealing Control Object

建議建立一個跨 EML-U、Operator IR 與 Nova 的共享物件：

```yaml
control_id: DR-CONTROL-0001
goal: "恢復研究專案的可延續工作態"
scope:
  projects:
    - tensor-memory-series
  time_range:
    start: "2026-07-20"
    end: "2026-07-27"
  branches:
    include: [main, experimental]
    exclude: [archived-private]
reveal:
  modes:
    - semantic
    - temporal
    - causal
    - task
    - version
    - provenance
  depth: 4
  candidate_budget: 128
partition:
  by:
    - source
    - version
    - branch
  preserve_contradiction: true
entanglement:
  allow:
    - causal
    - evidence
    - task
  forbid:
    - identity_without_evidence
    - cross_permission
loss_policy:
  maximum: metadata_only
  silent_loss: forbidden
permission:
  principal: research-agent
  purpose: project-continuation
validation:
  required:
    - provenance
    - replay
    - version_purity
    - contradiction
fallback:
  on_ambiguous: return_alternatives
  on_permission_failure: reject
  on_validation_failure: quarantine
writeback:
  mode: append_only
  inferred_status: provisional
```

## 5.2 語義損失狀態

所有 EML-U 到 EML-P、Nova 或傳統後端的轉換，必須標記為：

```text
lossless
lossy
metadata_only
approximate
unsupported
human_decision_required
```

正式原則為：

$$
\boxed{
\text{Unsupported}
\neq
\text{Silent Approximation}
}
$$

## 5.3 操作結果型別

動態顯影操作不得只回傳成功或例外。建議使用：

```text
OperationResult<T> =
  Success<T>
  | Partial<T, LossReport>
  | Alternatives<T[]>
  | NeedsEvidence<Obligation[]>
  | Quarantined<Reason>
  | Rejected<PolicyViolation>
  | Unsupported<CapabilityGap>
```

這讓「拒絕執行」成為語言的合法結果，而不是系統失敗。

---

# 六、Nova 與 EML-U 的責任邊界

## 6.1 不應合併成一個超級語言

本示範的一體化不是將所有理論揉成單一語法。

合理關係是：

$$
\boxed{
\text{EML-U 保存完整語義，}
\quad
\text{Nova 保存權威可執行結構。}
}
$$

EML-U 可以包含：

- 尚未可執行的語義；
- 高維或二維投影；
- 多媒體錨點；
- 人類與 AI 的不同閱讀層；
- 降階政策與語義損失模型。

Nova Core 則必須保持：

- 型別可檢查；
- 形狀可約束；
- 操作可驗證；
- GraphPatch 可審計；
- 後端實現可追蹤；
- AI 建議不可越過驗證核心。

## 6.2 EML-P 的橋接角色

$$
\mathrm{EML\text{-}P}
\subseteq
\mathrm{EML\text{-}U}
$$

在動態顯影案例中，EML-P 是：

- 人類可寫的調控語法；
- 可測試的最小操作 Profile；
- EML-U 高階語義的部分降階；
- Nova GraphPatch 的文字投影之一；
- 傳統後端的穩定入口。

EML-P 不負責證明所有 EML-U 語義可執行；它負責誠實地表達自己能做什麼、不能做什麼，以及損失在哪裡。

---

# 七、Dynamic Revealing Vertical Slice 0.1

## 7.1 目標

完成一條真正可運行的垂直切片：

```text
Markdown／對話／版本紀錄
        ↓
EML-U Semantic Overlay
        ↓
EML-P／Operator IR
        ↓
Nova Typed Program Graph
        ↓
SNTME Sparse Memory Field
        ↓
Reveal／Disentangle／Trace／Re-entangle／Validate
        ↓
可驗證工作態＋來源圖＋下一步
```

## 7.2 第一階段不需要完成的項目

Vertical Slice 0.1 不要求：

- 完整 Nova 文字語法；
- 完整投影式 IDE；
- GPU 原生高效張量記憶；
- 自動學習所有糾纏規則；
- 通用多媒體 EML-U 編輯器；
- 所有記憶模式一次到位；
- 用 Nova 重寫全部後端。

第一階段可以使用 Python、SQLite／PostgreSQL、圖資料結構與現有張量函式庫作為實現後端。關鍵是權威語義與操作契約已經由 EML-U、OIR 與 Nova 結構表達。

## 7.3 最小模組

```text
packages/
├── eml-u-semantic/
│   ├── anchor
│   ├── overlay
│   ├── provenance
│   └── projection-policy
├── eml-operator-ir/
│   ├── reveal
│   ├── split
│   ├── merge
│   ├── validate
│   └── loss-report
├── nova-dr-core/
│   ├── graph-schema
│   ├── type-system
│   ├── constraint-checker
│   ├── graph-patch
│   └── python-lowering
├── sntme/
│   ├── trace-store
│   ├── sparse-hypergraph
│   ├── local-tensor-kernel
│   ├── reveal-engine
│   └── validation
└── apps/
    └── dynamic-revealing-demo/
```

## 7.4 第一個公開展示

展示介面可以讓使用者選擇：

- 任務：研究延續／工程實作／公開摘要；
- 顯影模式；
- 時間範圍；
- 版本與分支；
- 權限角色；
- 是否保持矛盾；
- 是否顯示推定內容；
- 驗證強度。

介面同步顯示：

1. EML-U 語義附加視圖；
2. Nova 操作圖；
3. SNTME 局部張量／超圖活動域；
4. 顯影後工作態；
5. 來源、損失與驗證報告。

這會使「語言調控」直接可見：使用者調整的是語義與操作政策，而不是重新撰寫一大段提示詞。

---

# 八、驗收標準

## 8.1 語義保持

同一權威物件經文字、圖形與 Agent 投影後，應保持語義雜湊或觀察等價：

$$
H_{\mathrm{sem}}(V_H)
\sim
H_{\mathrm{sem}}(V_A)
\sim
H_{\mathrm{sem}}(\mathcal G_N)
$$

## 8.2 無靜默語義損失

任何降階都必須產生：

- lossless；
- lossy；
- metadata-only；
- unsupported；
- human-decision-required。

不得回傳「看似成功」但實際遺失來源、權限或版本資訊的結果。

## 8.3 來源保持

$$
P_{\mathrm{prov}}
=
\frac{\text{正確來源關係數}}{\text{全部輸出來源關係數}}
$$

第一代示範應以高來源精確率優先於高召回。

## 8.4 版本與分支純度

舊版本不得因語義相似度較高而覆蓋新版本；衝突分支不得被自動平滑為單一敘事。

## 8.5 權限先於顯影

未授權節點不得進入活動張量，再於輸出端遮蔽。

$$
\Gamma_{\xi}
\prec
\Pi_{\xi}
$$

## 8.6 可撤銷性

任何由 AI 建議形成的 GraphPatch、推定關係與寫回操作，都必須可以：

- 查出來源；
- 比較差異；
- 撤銷；
- 隔離；
- 重新驗證。

## 8.7 工作態恢復而非文件命中

核心指標應是：

$$
R_{\mathrm{WSR}}
=
\frac{\text{成功恢復且可延續的任務狀態}}{\text{全部測試任務}}
$$

而不只是 Top-$k$ 檢索準確率。

## 8.8 對照實驗

至少比較：

1. Vector RAG；
2. Vector RAG＋metadata；
3. GraphRAG；
4. 事件／時間線記憶；
5. EML-U＋Nova＋SNTME 垂直切片。

比較項目包括：

- 工作態恢復率；
- 來源精確率；
- 版本純度；
- 因果方向；
- 權限違規率；
- 錯誤糾纏率；
- 語義降階損失；
- 執行成本。

---

# 九、工程順序與優先級

## 9.1 第一優先：共享語義契約

先固定：

- Semantic ID；
- Anchor；
- Provenance；
- Version；
- Permission；
- Loss Report；
- Operation Result；
- Validation Obligation。

沒有這些共享契約，EML-U、Nova 與 SNTME 會各自建立不同的相似欄位，最後失去一體化價值。

## 9.2 第二優先：Operator IR

先建立小而穩定的操作集合：

$$
\{
\operatorname{reveal},
\operatorname{contract},
\operatorname{split},
\operatorname{trace},
\operatorname{merge},
\operatorname{validate},
\operatorname{commit}
\}
$$

只有在真實案例出現反覆需求後，再新增算子。

## 9.3 第三優先：Nova Dynamic Revealing Profile

不先擴張完整 Nova，而建立：

```text
Nova-DR Profile
```

只支援動態顯影必要的：

- 型別節點；
- 張量模式；
- 超邊；
- 權限效果；
- 驗證義務；
- GraphPatch；
- Python lowering。

## 9.4 第四優先：真實專案測試

應直接選擇具有多版本、長對話、失敗路徑與開放節點的既有研究專案，而不是只用人造短文本。

## 9.5 第五優先：投影介面

等核心語義與操作閉環成立後，再建立：

- EML-U 二維視圖；
- Nova 節點圖；
- 顯影條件面板；
- 工作態與來源審計視圖。

介面應展示既有權威結構，不得反過來成為唯一真實來源。

---

# 十、商業與研究定位

## 10.1 對外產品名稱不必先強調語言

第一個商業入口可以是：

- Dynamic Revealing Memory Engine；
- AI Working-State Recovery Engine；
- Long-Horizon Agent Continuity Engine；
- Research Memory Reconstruction Platform。

對外價值主張是：

> 不只是找回相關文件，而是恢復 AI 可以繼續工作的專案狀態。

## 10.2 語言是底層護城河

對內技術棧則是：

$$
\boxed{
\text{EML-U 保留意義}
\rightarrow
\text{OIR 約束轉譯}
\rightarrow
\text{Nova 保存可執行結構}
\rightarrow
\text{SNTME 承載張量記憶}
\rightarrow
\text{動態顯影形成產品能力}
}
$$

這種策略可以避免要求市場先理解一套新語言，卻又讓產品持續反向驗證並推動語言工程。

## 10.3 動態顯影反向塑造 Nova

動態顯影會向 Nova 提出真實要求：

- 關係是否必須是一級物件；
- 來源能否進入型別與效果系統；
- 權限是否能在編譯與顯影前檢查；
- 解纏是否需要部分算子；
- 多候選結果如何型別化；
- 語義損失如何成為編譯產物；
- GraphPatch 如何撤銷；
- 張量模式如何動態加入；
- 人類與 Agent 投影如何保持同一語義身分。

因此，動態顯影不是 Nova 的附屬應用，而是第一個可以反向校準 Nova 語言本體的基準。

---

# 十一、主要風險

## 11.1 過早把所有概念放入 Nova Core

風險：核心膨脹、無法實作、接口循環依賴。

處理：建立 Nova-DR Profile；核心只保留可跨應用重用的型別與操作。

## 11.2 EML-U 變成任意 metadata

風險：任何概念都能附加，但無法驗證、映射或治理。

處理：每個語義節點必須具有 ID、作用域、型別、來源、狀態與降階政策。

## 11.3 以張量名義包裝普通圖資料

風險：理論稱為原生張量，工程實際只有圖節點與向量欄位。

處理：至少實作真正的多模式收縮、可分離近似、局部低秩因子或張量核，並與純圖方法比較。

## 11.4 AI 建議污染權威結構

風險：模型推定被直接寫入正式記憶。

處理：所有 AI 產物先進入 provisional／candidate 狀態，通過驗證後才能追加式提交。

## 11.5 投影失真

風險：人類視圖為求簡潔隱藏關鍵來源、權限或不確定性。

處理：簡化投影必須保留可展開的 loss／provenance／status 指示。

## 11.6 工程成本高於收益

風險：新語言層的維護成本高於直接用 Python 與資料庫實作。

處理：以對照與消融實驗判定哪些語言層真正提高來源保持、工作態恢復或治理可靠性；沒有收益的層應被縮減。

---

# 十二、可反證條件

本示範不應被設計成只能成功。若出現以下結果，應修正或縮小主張：

1. EML-U 語義附加無法穩定跨版本錨定；
2. Nova 結構圖相較一般 schema 沒有提供可測量的正確性或維護收益；
3. 張量模式無法在工作態恢復上超越圖＋向量混合基線；
4. 語義損失報告成本過高且無法被使用者理解；
5. 權限與來源型別化造成不可接受的實作負擔；
6. 多投影 round-trip 無法維持語義一致；
7. Vertical Slice 只有理論展示，無法恢復真實專案工作態。

若部分假設失敗，仍可保留：

- EML-U 作為語義附加與治理層；
- Nova 作為結構化張量程式語言；
- 動態顯影作為獨立記憶引擎；

而不必強迫三者維持不必要的緊密耦合。

---

# 十三、本文命題

## 命題一

$$
\boxed{
\text{動態顯影不是單一檢索演算法，而是一條可被語言調控的狀態形成鏈。}
}
$$

## 命題二

$$
\boxed{
\text{語言調控不是操縱輸出，而是約束語義進入、轉換、投影與寫回。}
}
$$

## 命題三

$$
\boxed{
\text{EML-U 保存完整語義，Nova 保存權威可執行結構。}
}
$$

## 命題四

$$
\boxed{
\mathrm{EML\text{-}P}
\subseteq
\mathrm{EML\text{-}U}
}
$$

且 EML-P 是動態顯影調控語義的穩定可執行 Profile。

## 命題五

$$
\boxed{
\text{權限必須先於顯影，來源必須進入操作約束。}
}
$$

## 命題六

$$
\boxed{
\text{Unsupported}
\neq
\text{Silent Semantic Loss}
}
$$

## 命題七

$$
\boxed{
\text{動態顯影可作為 Nova 結構先於文字的第一個真實驗證案例。}
}
$$

## 命題八

$$
\boxed{
\text{動態顯影可作為 EML-U 通用語義附加與多投影能力的第一個系統示範。}
}
$$

## 命題九

$$
\boxed{
\text{邏輯上張量原生，不要求物理上儲存單一巨大稠密張量。}
}
$$

## 命題十

$$
\boxed{
\text{產品出售工作態恢復能力，語言形成底層技術護城河。}
}
$$

---

# 十四、結論

動態顯影技術已從語義排序與記憶檢索，逐步發展成包含原生張量記憶、結構糾纏、差合化操作、工作態重構、長期連續性與污染治理的完整方法論。這使它非常適合作為 EML-U 與 Nova 的第一個共同垂直示範。

其價值不在於證明「只有 Nova 才能做動態顯影」，而在於用一個足夠複雜、又能被實驗驗證的真實問題，回答以下問題：

- EML-U 是否真的能保存跨宿主、跨版本與跨觀測者的語義；
- EML-P 與 Operator IR 是否能誠實地降階而不靜默失真；
- Nova 是否真的能讓結構先於文字，並使多投影共享同一權威本體；
- SNTME 是否真的能以多模式關係態提高工作記憶恢復能力；
- 語言、記憶與執行系統能否共同形成可審計、可撤銷與可延續的閉環。

完整定位可以濃縮為：

$$
\boxed{
\text{EML-U 負責語義附加與完整保存}
}
$$

$$
\boxed{
\text{EML-P／Operator IR 負責確定性調控與降階}
}
$$

$$
\boxed{
\text{Nova 負責權威結構、型別與操作約束}
}
$$

$$
\boxed{
\text{SNTME 負責稀疏原生張量記憶場}
}
$$

$$
\boxed{
\text{動態顯影負責把整套語言系統轉化為可展示、可驗證與可商用的能力}
}
$$

因此，近期工程不必直接全面提前完整 Nova 與 EML-U，而應優先建立：

$$
\boxed{
\text{Dynamic Revealing Vertical Slice 0.1}
}
$$

讓動態顯影成為語言上的第一個調控示範，也讓語言工程第一次由真實的記憶問題反向塑形。

---

# 附錄 A：最小端到端示意

```text
[原始文件／對話／版本／日誌]
               │
               ▼
[EML-U：Anchor＋Semantic Overlay＋Policy]
               │
               ▼
[EML-P／OIR：可解析操作＋Loss Report]
               │
               ▼
[Nova：Typed Graph＋Constraint＋GraphPatch]
               │
               ▼
[SNTME：Sparse Hypergraph＋Local Tensor Kernel]
               │
               ▼
[Reveal → Split → Trace → Re-entangle → Validate]
               │
               ▼
[經驗證工作態／來源圖／矛盾／下一步]
               │
       ┌───────┼────────┐
       ▼       ▼        ▼
  Human View Agent View Execution Plan
```

# 附錄 B：第一代里程碑

## M0：規格固定

- Shared Semantic Object；
- Loss Report；
- Operation Result；
- Dynamic Revealing Control Object；
- Nova-DR Graph schema。

## M1：確定性轉譯

- EML-P／OIR parser；
- OIR 到 Nova Graph；
- Nova Graph schema validator；
- Python lowering。

## M2：最小記憶場

- 原始痕跡庫；
- 稀疏關係超圖；
- 局部張量核；
- 來源與權限索引。

## M3：顯影閉環

- reveal；
- split；
- trace back；
- merge／re-entangle；
- validate；
- append-only commit。

## M4：公開示範

- 調控面板；
- EML-U 視圖；
- Nova 圖視圖；
- 工作態視圖；
- 來源與語義損失報告。

## M5：基準比較

- Vector RAG；
- GraphRAG；
- 時間線記憶；
- Nova-DR＋SNTME；
- 對照、消融與成本報告。

---

# 參考文件

1. Neo.K，《EML 雙版本架構：實用執行版與通用語意原始版》，2026。
2. Neo.K，《Nova Core Baseline v3.0：統合前正式核心規格》，2026。
3. Neo.K，《Nova Unified Roadmap v1.0：新版計畫書與 AI 原生張量語言統合架構》，2026。
4. Neo.K with Aletheia，《語意附加程式設計：EML 與宿主中立語義中介層》，2026。
5. Neo.K with Aletheia，《結構先於文字：Nova 與後文本程式語言本體論》，2026。
6. Neo.K with Aletheia，《動態顯影與原生張量記憶系列》第一至第八篇，2026。

---

# 版本紀錄

## v0.1 — 2026-07-27

- 將動態顯影定位為 EML-U／Nova 的語言調控示範。
- 定義語言調控八項核心問題與八元調控規格。
- 建立 EML-U、EML-P／Operator IR、Nova Core、SNTME 四層垂直架構。
- 提出 Dynamic Revealing Control Object 與操作結果型別。
- 定義 Dynamic Revealing Vertical Slice 0.1。
- 建立驗收標準、工程優先級、風險與可反證條件。
- 確立「產品出售工作態恢復，語言形成底層護城河」的雙層定位。

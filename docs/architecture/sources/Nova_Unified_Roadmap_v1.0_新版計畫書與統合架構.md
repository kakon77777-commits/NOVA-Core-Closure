# Nova Unified Roadmap v1.0  
## 新版計畫書路線與 AI 原生張量語言統合架構

**文件編號：** EML-NOVA-UNIFIED-ROADMAP-2026-v1.0  
**作者：** Neo.K  
**機構：** EveMissLab／一言諾科技有限公司  
**日期：** 2026 年 7 月  
**文件性質：** 研究計畫書、技術路線、系統統合規格  
**依賴基線：** 《Nova Core Baseline v3.0：統合前正式核心規格》  
**統合對象：** EML、Nova、ISQL、SOS、Cl-safe、計算的十六重範式、範式鍵結、程式碼替換本體論、單符號宇宙、最小充分意圖、虛擬轉現實理論

---

## 執行摘要

本計畫將 Nova 從一種「張量原生、投影編輯、可微分的後文本程式語言」，發展為一套以 AI 直接建構高維程式本體為核心、同時提供人類可讀投影、符號算子組合、安全驗證、計算範式選擇、多後端實現與最小控制句柄的完整計算棧。

本計畫不把多個既有理論粗暴合併成單一超大型語言。相反地，採用分層架構，使每一理論只負責它最擅長的問題：

$$
\boxed{
\begin{aligned}
\text{EML}
&=\text{人類高密度意圖入口}\\
\text{ISQL}
&=\text{高維語義狀態與交換協議}\\
\text{Nova}
&=\text{AI 原生張量程式本體}\\
\text{SOS}
&=\text{算子閉包與組合代數}\\
\text{Cl-safe}
&=\text{組合安全與失敗隔離}\\
\text{十六重範式}
&=\text{執行策略分類空間}\\
\text{範式鍵結}
&=\text{策略鏈合法性與演化規則}\\
\text{程式碼替換本體論}
&=\text{後端等價實現與物理最佳化}\\
\text{單符號宇宙}
&=\text{完整程式的最小控制句柄}\\
\text{虛擬轉現實理論}
&=\text{端到端轉化效率與影響度量}
\end{aligned}
}
$$

完整資料流為：

$$
z
\xrightarrow{Q_{\mathrm{ISQL}}}
T_{\mathrm{sem}}
\xrightarrow{\mathcal{B}_{\mathrm{Nova}}}
\mathcal{G}_{\mathrm{tensor}}
\xrightarrow{\mathcal{O}_{\mathrm{SOS}}}
\mathcal{G}_{\mathrm{operator}}
\xrightarrow{\mathcal{V}_{\mathrm{Cl}}}
\mathcal{G}_{\mathrm{safe}}
\xrightarrow{\mathcal{S}_{16F}}
\mathcal{P}_{\mathrm{exec}}
\xrightarrow{\mathcal{L}_{H}}
P_H
\xrightarrow{\operatorname{Run}}
\tau
$$

其中，$z$ 為意圖狀態，$T_{\mathrm{sem}}$ 為高維語義張量，$\mathcal{G}_{\mathrm{tensor}}$ 為 Nova 張量程式圖，$\mathcal{G}_{\mathrm{operator}}$ 為 SOS 算子閉包圖，$\mathcal{G}_{\mathrm{safe}}$ 為通過安全驗證的結構，$\mathcal{P}_{\mathrm{exec}}$ 為計算範式鏈，$P_H$ 為特定硬體實現，$\tau$ 為現實執行軌跡。

本計畫採用「階段門」而非只依賴年份。下一階段只有在上一階段達到可重現的驗收條件後才啟動，避免理論統合先於工程核心，或概念數量先於可執行系統。

---

# 第一部　計畫目標與原則

## 1. 總目標

建立一個系統，使人類與 AI 可以：

1. 以高層意圖描述目標；
2. 以高維語義張量保存意圖；
3. 由 AI 直接建立 Nova 程式本體，而非先生成文字再解析；
4. 以 SOS 算子閉包組合複雜能力；
5. 以 Cl-safe 阻止靜默結構損壞；
6. 由十六重範式規劃計算方式；
7. 在多個語義等價實現中尋找低摩擦物理路徑；
8. 將完整工作流封裝為可審計、可授權的最小控制句柄；
9. 以虛擬轉現實效率衡量整體系統，而不只衡量 Token 或執行速度。

## 2. 非目標

本計畫不承諾：

- 短期內淘汰 Python、C++、Rust 或 CUDA；
- 第一版直接實現無符號思想讀取；
- 所有意圖都能自動形式化；
- 所有算子組合都能靜態證明安全；
- $O(0)$ 可套用至所有問題；
- AI 可自動找到全局最佳程式；
- 單符號本身包含全部任務資訊；
- 高維向量等同於主觀意識；
- 理論統合後即可跳過工程驗證。

## 3. 統合原則

### 原則 U1：核心穩定，外層可替換

Nova Core 是最小穩定內核。ISQL、SOS 與策略系統透過版本化接口接入，不得任意改寫核心語義。

### 原則 U2：一個問題只設一個權威層

例如：

- 形狀相容由 Nova 型別系統負責；
- 符號閉包合成由 SOS 負責；
- 合成安全由 Cl-safe 負責；
- 執行策略由十六重範式負責。

避免多層重複判斷同一問題而產生不一致。

### 原則 U3：高維本體與人類投影分離

AI 原生程式不必以文字為本體；人類仍必須擁有可讀、可修改與可審計的投影。

### 原則 U4：壓縮不等於資訊消失

控制訊號縮短時，資訊轉移至：

- 共享記憶；
- 程式圖；
- 模型權重；
- 工具；
- 權限；
- 展開器；
- 環境。

### 原則 U5：寧可顯性失敗，不可靜默損壞

任何無法證明安全的組合，必須被拒絕、隔離、降級或要求人工確認。

### 原則 U6：每一層都可單獨運作

即使 ISQL 尚未完成，Nova 仍可由人類或一般 Agent 建構；即使 SOS 未完成，Nova Core 仍可運行；即使單符號控制未完成，完整系統仍可使用。

---

# 第二部　統一架構

## 4. 七層主架構

### L0：意圖與目標層

輸入：

$$
z=(g,c,p,m,r,\ldots)
$$

其中：

- $g$：目標；
- $c$：限制；
- $p$：偏好；
- $m$：記憶；
- $r$：風險。

來源可為：

- 人類自然語言；
- EML；
- AI 內部狀態；
- 結構化任務；
- 感測器與環境事件。

### L1：ISQL 語義張量層

將意圖量化為：

$$
T_{\mathrm{sem}}
=
(v,\phi,E,\Theta,F,\Gamma,\ldots)
$$

可包含：

- 語義向量；
- 相位；
- 光譜；
- 拓撲；
- 固定點；
- 關係圖；
- 置信度；
- 時序。

ISQL 的責任不是執行，而是保存高維語義與交換條件。

### L2：Nova 程式本體層

建立：

$$
\mathcal{N}
=
(\mathcal{G},\mathcal{T},\mathcal{C},\mathcal{E},\mathcal{M},\mathcal{D})
$$

Nova 是唯一權威可執行程式層。

### L3：SOS 算子閉包層

將部分 Nova 節點提升為：

$$
\hat O(S)
=
(G_S,\operatorname{Sem}_S,\operatorname{Comp}_S)
$$

在 AI 原生情境下，可擴展為：

$$
\hat O_A
=
(\operatorname{Sem},\operatorname{Comp},\operatorname{State},\operatorname{Effect},\operatorname{Projection})
$$

其中幾何可由投影層生成，不必是 AI 執行的必要前提。

### L4：Cl-safe 驗證層

對算子合成：

$$
\hat O(A)\bowtie\hat O(B)
$$

驗證：

1. Comp 不崩潰；
2. Sem 不在受控條件下發散；
3. 幾何或投影不失去一致性；
4. 效果與權限不衝突；
5. 結果仍位於型別系統定義域。

### L5：十六重範式與鍵結層

每個執行區段被分類為：

$$
(a,b,c)
\in
\{C,D\}
\times
\{C,J,P,R\}
\times
\{C,D\}
$$

其中第二軸：

- $C$：序列填補；
- $J$：跳躍；
- $P$：並行同時；
- $R$：識別／零填補。

策略鏈需符合鍵結條件與硬體限制。

### L6：物理後端與現實層

將合法策略鏈映射至：

- CPU；
- GPU；
- NPU；
- WebGPU；
- 分散式叢集；
- 類比／光子／神經形態後端；
- 機器人或外部 Agent 工具。

結果為現實軌跡：

$$
\tau=(e_0,e_1,\ldots,e_T)
$$

---

# 第三部　雙原生介面

## 5. Nova-H：人類原生投影

Nova-H 面向人類，提供：

- 數學公式；
- EML 高密度語法；
- 結構化文字；
- 節點圖；
- 文件視圖；
- 效果與權限視圖；
- 記憶體與裝置視圖；
- 執行策略視圖。

Nova-H 不是另一種程式本體，而是：

$$
\pi_H(\mathcal{N})
$$

## 6. Nova-A：AI 原生程式介面

Nova-A 面向 AI，允許直接提交：

```text
GraphPatch
TypeConstraint
ShapeConstraint
OperatorDefinition
MemoryPlan
DifferentiationRequest
ExecutionStrategyCandidate
VerificationEvidence
```

AI 不必先輸出程式文字，再讓 Nova 解析。

其核心操作是：

$$
\Delta_A:\mathcal{N}\rightarrow\mathcal{N}'
$$

每個修改都必須通過驗證器。

## 7. 同一程式的雙向一致性

要求：

$$
\operatorname{Sem}(\pi_H(\mathcal{N}))
=
\operatorname{Sem}(\pi_A(\mathcal{N}))
=
\operatorname{Sem}(\mathcal{N})
$$

人類與 AI 可以使用不同介面，但共享同一程式本體。

---

# 第四部　各系統接口

## 8. EML → Nova

EML 負責高密度人類輸入：

$$
T_{\mathrm{EML}}
\xrightarrow{\operatorname{Lower}_{EML}}
\mathcal{N}
$$

EML 應提供：

- 語義附加；
- 形狀簡寫；
- 效果簡寫；
- 後端提示；
- 巨集與工作流；
- 可逆展開。

EML 不直接決定底層記憶體與 kernel。

## 9. ISQL → Nova

接口：

```text
SemanticTensor {
  dimensions[]
  phase
  spectrum
  topology
  relations[]
  confidence
  provenance
}
```

轉換器：

$$
\mathcal{B}_{\mathrm{Nova}}
:
T_{\mathrm{sem}}
\rightarrow
(\mathcal{N},\mathcal{O})
$$

其中 $\mathcal{O}$ 是未解的證明義務與歧義集合。

不得把高維語義強制坍縮成唯一程式；可返回候選集：

$$
\{\mathcal{N}_1,\ldots,\mathcal{N}_k\}
$$

## 10. SOS ↔ Nova

Nova 節點可帶：

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

SOS 合成產生新的 Nova 子圖或算子定義。

## 11. Cl-safe ↔ SOS／Nova

輸入：

```text
CompositionCandidate
Context
Depth
ResourceLimits
```

輸出：

```text
Safe
Unsafe(reason)
ConditionallySafe(obligations)
Unknown(runtime_protocol)
```

不得只有布林值；必須保留失敗結構。

## 12. 十六重範式 ↔ Nova 編譯器

每個子圖產生候選分類：

```text
ParadigmCandidate {
  base_space
  fill_mode
  observation_scale
  preconditions
  cost_model
  fallback
}
```

編譯器可比較不同策略鏈。

## 13. 程式碼替換本體論 ↔ 後端最佳化

對語義等價類：

$$
[\mathcal{N}]_{\mathrm{sem}}
$$

搜尋物理成本較低的實現：

$$
P_H^*
=
\arg\min_{P_H\in[\mathcal{N}]_{\mathrm{sem}}}
F(P_H)
$$

但只接受已證明、差分測試或受控近似的等價轉換。

## 14. 單符號控制 ↔ ProgramHandle

完整程式封裝為：

```text
ProgramHandle {
  program_hash
  context_schema
  capability_requirements
  version
  entrypoint
  verification_policy
  rollback_policy
}
```

符號 $\Omega_k$ 只是一個受控引用：

$$
\Omega_k\mapsto\operatorname{ProgramHandle}_k
$$

它不是無上下文的無限資訊容器。

## 15. 虛擬轉現實度量

端到端效率：

$$
I=\eta w\Delta t
$$

本計畫將 $\eta$ 分解為：

$$
\eta
=
\eta_{\mathrm{semantic}}
\eta_{\mathrm{build}}
\eta_{\mathrm{validate}}
\eta_{\mathrm{plan}}
\eta_{\mathrm{lower}}
\eta_{\mathrm{execute}}
\eta_{\mathrm{verify}}
$$

系統優化目標不是只減少文字，而是提高：

$$
\eta_{\mathrm{total}}
$$

同時維持安全與可審計性。

---

# 第五部　新版開發路線

## 16. 路線管理方法

採用階段門：

$$
G_0\rightarrow G_1\rightarrow\cdots\rightarrow G_8
$$

每一門包含：

- 目標；
- 產物；
- 驗收；
- 禁止提前事項；
- 失敗回退。

---

## G0：理論與規格凍結

### 目標

建立統一詞彙與邊界，停止同一名稱代表多個層級。

### 產物

1. Nova Core Baseline v3.0；
2. Unified Roadmap v1.0；
3. 術語表；
4. 接口 schema 草案；
5. ADR 架構決策記錄目錄；
6. 版本政策。

### 驗收

- 每個系統有唯一責任；
- 無循環核心依賴；
- Nova Core 可不依賴統合層獨立執行；
- 所有數學符號有定義。

### 禁止

- 在核心未穩定前建立大型 IDE；
- 直接實作單符號控制；
- 把 AI 輸出當作驗證證明。

---

## G1：Nova Core 可執行閉環

### 目標

完成最小張量語言。

### 產物

- Core Graph schema；
- 型別與形狀求解器；
- 解釋器；
- CPU 後端；
- reverse-mode AD；
- CLI；
- 結構化文字投影；
- Python／DLPack FFI；
- 測試集。

### 驗收

需完成：

$$
Y=W\cdot X+b
$$

與小型訓練迴圈，並通過：

- 形狀錯誤拒絕；
- 梯度檢查；
- 序列化穩定；
- 與 Python 參考結果一致；
- 無記憶體洩漏。

### 退出條件

至少三個不同模型可執行：

- 線性回歸；
- MLP；
- 小型 attention。

---

## G2：Nova-H 投影與編輯

### 目標

建立人類可用介面。

### 產物

- 數學投影；
- 結構化文字投影；
- 節點圖；
- 結構化 diff；
- 錯誤視圖；
- Notebook 原型。

### 驗收

同一程式在三種投影間切換，語義雜湊不變：

$$
H(\mathcal{N})=\text{constant}
$$

### 失敗回退

若完整投影編輯成本過高，先採「結構化文字 + 局部公式元件」。

---

## G3：MSSP-AISMBI 與資源安全

### 目標

將記憶體推斷正式化為可驗證計畫。

### 產物

- 所有權狀態；
- 生命週期分析；
- buffer reuse；
- 裝置轉移計畫；
- AI 建議器；
- 決定性驗證器；
- 保守退回模式。

### 驗收

AI 建議關閉時仍能安全編譯；AI 開啟時應降低：

- 峰值記憶體；
- 不必要複製；
- 裝置傳輸。

安全性不得下降。

---

## G4：Nova-A AI 原生程式建構

### 目標

讓 AI 直接修改程式圖。

### 產物

- GraphPatch API；
- constraint API；
- build transaction；
- rollback；
- provenance；
- AI 沙盒；
- 差異審核視圖。

### 驗收

AI 能完成：

1. 新增層；
2. 改變形狀；
3. 修復型別錯誤；
4. 增加測試；
5. 建立微分請求；

且不需輸出完整文字程式。

### 安全條件

每次 patch 都必須：

$$
\operatorname{Validate}(\Delta_A(\mathcal{N}))=\operatorname{Pass}
$$

---

## G5：SOS 與 Cl-safe 統合

### 目標

建立算子閉包庫與安全合成。

### 產物

- OperatorDescriptor；
- Sem／Comp／Projection 槽；
- compose API；
- BrokenOperator 隔離；
- RVP；
- 深度限制；
- 可追蹤失敗；
- 基本算子閉包庫。

### 驗收

測試：

- 合法合成；
- Comp 崩潰；
- Sem 發散；
- 投影不一致；
- 效果衝突；
- 深層鏈損壞傳播阻止。

### 原則

SOS 不取代 Nova 型別系統，而是擴展算子級語義與組合契約。

---

## G6：十六重範式規劃器

### 目標

讓編譯器顯式選擇計算範式。

### 產物

- 三軸標記；
- 子圖分類器；
- 策略候選；
- 鍵結規則；
- 成本模型；
- fallback；
- profile-guided 更新。

### 驗收

至少在下列案例中產生不同策略：

- 密集張量：$P$；
- 稀疏查找：$J$；
- 順序依賴：$C$；
- 穩定特徵快取：受限 $R$。

### 校正

$O(0)$ 僅指在線填補量為零，不表示預計算、儲存與識別成本不存在。

---

## G7：ISQL 高維語義接口

### 目標

將意圖狀態與 Nova 程式圖連接。

### 產物

- SemanticTensor schema；
- 意圖到候選圖轉換器；
- 歧義集合；
- 置信度；
- provenance；
- 人類校正介面；
- 語義回投影。

### 驗收

相同意圖可產生多個候選，系統必須顯示差異與未決約束，而非假裝唯一正確。

### 成功指標

相較自然語言中介：

- 意圖保持率提升；
- 修正輪數降低；
- 結構錯誤降低；
- 可追蹤性提升。

---

## G8：最小充分控制與現實執行

### 目標

將完整已驗證流程封裝為最小句柄。

### 產物

- ProgramHandle；
- capability token；
- context schema；
- dry-run；
- approval policy；
- rollback；
- audit log；
- 單符號或短指令投影。

### 驗收

同一短控制句柄在：

- 正確上下文中可靠執行；
- 缺少權限時拒絕；
- 版本漂移時要求遷移；
- 高風險情境下強制預覽；
- 執行後可追溯全部展開鏈。

### 最終形式

$$
\Omega_k
\xrightarrow{M,C,A,E}
\tau_k
$$

但系統必須保留：

$$
\Omega_k
\Rightarrow
\mathcal{N}_k
\Rightarrow
\mathcal{P}_k
\Rightarrow
\tau_k
$$

的完整可審計展開。

---

# 第六部　專案結構

## 17. 建議儲存庫

```text
nova/
├─ specs/
│  ├─ core/
│  ├─ tensor/
│  ├─ effects/
│  ├─ differentiation/
│  ├─ memory/
│  ├─ operator/
│  ├─ paradigms/
│  └─ handles/
├─ schemas/
├─ compiler/
│  ├─ frontend/
│  ├─ solver/
│  ├─ ir/
│  ├─ ad/
│  ├─ memory/
│  ├─ optimizer/
│  └─ backends/
├─ runtime/
├─ studio/
├─ ai_interface/
├─ sos/
├─ clsafe/
├─ paradigm_planner/
├─ isql_bridge/
├─ eml_bridge/
├─ stdlib/
├─ interop/
├─ tests/
├─ examples/
├─ benchmarks/
└─ adr/
```

## 18. 版本政策

### 核心版本

Nova Core 使用語義版本：

```text
MAJOR.MINOR.PATCH
```

### 圖 schema 版本

每個檔案記錄：

```text
nova_core_version
schema_version
feature_flags
```

### 擴充版本

ISQL、SOS、Cl-safe 與範式規劃器分別版本化，避免整棧同步升級。

---

# 第七部　研究與工程工作包

## 19. WP-1：核心語義與形式規格

輸出：

- 型別規則；
- 形狀規則；
- 效果規則；
- 微分規則；
- 操作語義；
- 錯誤語義。

## 20. WP-2：圖與儲存

輸出：

- schema；
- canonical form；
- hash；
- diff；
- migration；
- incremental update。

## 21. WP-3：編譯與執行

輸出：

- interpreter；
- CPU；
- GPU；
- JIT；
- profiler；
- cost model。

## 22. WP-4：AI 原生建構

輸出：

- patch language；
- transaction；
- verifier；
- provenance；
- evaluation suite。

## 23. WP-5：算子與安全

輸出：

- operator closure；
- composition；
- typed failure；
- runtime validation；
- sandbox。

## 24. WP-6：計算範式規劃

輸出：

- classifier；
- bonding engine；
- fallback；
- profile adaptation；
- benchmark。

## 25. WP-7：語義張量

輸出：

- ISQL schema；
- encoder；
- decoder；
- ambiguity；
- human correction；
- semantic fidelity metrics。

## 26. WP-8：控制與現實閉環

輸出：

- handle；
- capability；
- approval；
- execution log；
- rollback；
- $\eta$ 度量。

---

# 第八部　評估指標

## 27. 核心正確性

- 型別檢查通過率；
- 非法程式拒絕率；
- backend 差分一致；
- 梯度正確率；
- schema 遷移成功率；
- 可重現率。

## 28. 人類開發效率

$$
E_H
=
\frac{\text{有效語義改變}}
{\text{人類操作數}+\text{修復成本}}
$$

測量：

- 完成任務時間；
- 顯式程式行為數；
- 錯誤修正輪次；
- 認知負擔問卷；
- 投影切換成本。

## 29. AI 建構效率

$$
E_A
=
\frac{\text{通過驗證的程式圖變更}}
{\text{AI 提案數}}
$$

測量：

- patch 接受率；
- 首次通過率；
- 回退率；
- 幻覺節點率；
- provenance 完整率。

## 30. 意圖保持率

$$
IR=1-D(z,\hat z)
$$

其中 $\hat z$ 是由結果與程式圖反推的意圖。

## 31. 控制壓縮率

$$
CR
=
\frac{K(\tau)}
{L(s)+I_{\mathrm{pre}}}
$$

不可只用 $K(\tau)/L(s)$，否則會忽略預置系統成本。

## 32. 虛擬轉現實效率

$$
\eta_R
=
\frac{U(\tau)}
{T\cdot C_H\cdot C_C\cdot R}
$$

其中：

- $U(\tau)$：結果效用；
- $T$：時間；
- $C_H$：人類操作成本；
- $C_C$：協調成本；
- $R$：風險與失敗修正成本。

---

# 第九部　風險登錄

## 33. 範圍爆炸

### 風險

同時開發語言、IDE、AI、符號系統、形式化、安全與新硬體，將使專案無法收斂。

### 控制

- Nova Core 先行；
- 階段門；
- 每層可獨立；
- 不做未驗收的跨層耦合。

## 34. 投影編輯器陷阱

### 風險

IDE 成為最大成本，核心語言反而未完成。

### 控制

先完成結構化文字與簡易圖視圖，再逐步投影化。

## 35. AI 不可靠

### 控制

AI 只提出候選；驗證器、測試器與沙盒決定是否接受。

## 36. 概念重疊

### 控制

建立權威術語表與 ADR。任何新理論接入前必須回答：

- 它解決哪一層問題？
- 是否已有其他層負責？
- 是否能以接口接入？
- 是否改變核心語義？

## 37. $R$ 範式濫用

### 風險

把快取或查表錯稱為無成本。

### 控制

分開計算：

$$
C_{\mathrm{total}}
=
C_{\mathrm{precompute}}
+
C_{\mathrm{storage}}
+
C_{\mathrm{recognition}}
+
C_{\mathrm{maintenance}}
$$

## 38. 單符號權限風險

### 控制

短指令必須綁定：

- 版本；
- 上下文；
- 權限；
- 風險等級；
- 預覽策略；
- 回滾。

## 39. 理論不可證明性

### 控制

明確區分：

- 定義；
- 公理；
- 工程規格；
- 猜想；
- 經驗結果；
- 尚未驗證主張。

---

# 第十部　治理與公開策略

## 40. 文件分級

1. 公開概念稿；
2. 公開技術規格；
3. 內部實作文件；
4. 安全敏感文件；
5. 實驗資料與模型。

## 41. 開源邊界

建議開源：

- Nova Core schema；
- 基本編譯器；
- interpreter；
- CPU 後端；
- 測試；
- EML bridge；
- 基本 SOS 描述；
- benchmark。

可延後公開：

- 高價值最佳化策略；
- 內部 AI 訓練資料；
- 敏感能力與權限系統；
- 未成熟的自主執行模組。

## 42. 標準治理

當核心達到穩定採用後，再考慮基金會或標準組織。在此之前由 EveMissLab 維護版本與 ADR。

---

# 第十一部　近期執行清單

## 43. 第一批必做文件

1. Nova Core Graph Schema v0.1；
2. Nova Type and Shape Rules v0.1；
3. Nova Text Projection Grammar v0.1；
4. Nova AD Semantics v0.1；
5. Nova Error Model v0.1；
6. Nova FFI Contract v0.1；
7. Nova Verification Matrix v0.1。

## 44. 第一批原型

1. Python 實作的圖解釋器；
2. Rust 或相近系統語言實作的 schema validator；
3. CPU 張量後端；
4. reverse-mode AD；
5. JSON／S-expression 儲存；
6. CLI；
7. 三個範例模型。

## 45. 第一批禁止事項

- 不先做完整自研 IDE；
- 不先做硬體 ISA；
- 不先做全語言字符 SOS；
- 不先宣稱取代 CUDA；
- 不先做無限制 Agent 自主部署；
- 不先把所有理論合入同一編譯器分支。

---

# 第十二部　里程碑完成定義

## 46. Nova Core 完成

Nova Core 不以「文件寫完」為完成，而以：

$$
\text{Spec}
+
\text{Reference Implementation}
+
\text{Tests}
+
\text{Examples}
+
\text{Versioned Schema}
$$

共同完成。

## 47. AI 原生完成

只有當 AI 能直接提交圖修改、通過驗證、保留 provenance，且不依賴文字中介時，才稱為 AI 原生程式建構。

## 48. SOS 統合完成

只有當算子閉包能：

- 定義；
- 合成；
- 驗證；
- 失敗隔離；
- 序列化；
- 回投影；

才算完成。

## 49. 範式規劃完成

只有當規劃器能在真實 benchmark 上選擇不同策略並提供 fallback，才算完成；分類論接入但不影響編譯，不算完成。

## 50. 單符號控制完成

只有當短句柄具有完整權限、安全、版本、審計與回滾，才算完成；單純建立巨集不算完成。

---

# 第十三部　最終系統圖

完整統一系統可表示為：

$$
\boxed{
\begin{aligned}
z
&\xrightarrow{\text{EML／ISQL}}
T_{\mathrm{sem}}\\
&\xrightarrow{\text{Nova-A Build}}
\mathcal{N}\\
&\xrightarrow{\text{SOS Enrichment}}
\mathcal{N}_{O}\\
&\xrightarrow{\text{Cl-safe}}
\mathcal{N}_{S}\\
&\xrightarrow{\text{16F Planner}}
\mathcal{P}\\
&\xrightarrow{\text{Physical Lowering}}
P_H\\
&\xrightarrow{\text{Runtime}}
\tau\\
&\xrightarrow{\text{Verification}}
U(\tau)
\end{aligned}
}
$$

人類操作面：

$$
\pi_H(\mathcal{N})
=
\{\text{EML},\text{數學公式},\text{圖},\text{文件},\text{審計}\}
$$

AI 操作面：

$$
\pi_A(\mathcal{N})
=
\{\text{GraphPatch},\text{Constraint},\text{Plan},\text{Evidence}\}
$$

最小控制面：

$$
\Omega_k
\mapsto
\operatorname{ProgramHandle}(\mathcal{N}_k)
$$

---

# 結論

Nova 的新版路線不應再被描述成「先做一套漂亮的數學程式語言，未來再加入 AI」。AI 原生性必須從程式本體、修改接口、驗證流程與執行規劃中被正式設計。

但 AI 原生也不等於把所有理論一次塞進核心。正確路線是：

$$
\boxed{
\text{先完成 Nova Core，}
\rightarrow
\text{再建立 AI 直接建構，}
\rightarrow
\text{再接入算子、安全與範式，}
\rightarrow
\text{最後壓縮為最小控制面。}
}
$$

在這個架構中：

- EML 保留人類進入未來計算的橋樑；
- ISQL 保存線性語言難以承載的高維意圖；
- Nova 成為唯一權威的可執行張量程式本體；
- SOS 讓符號與算子成為能動閉包；
- Cl-safe 阻止統合系統在靜默中損壞；
- 十六重範式使編譯器不再只選硬體，而能選擇計算本體；
- 程式碼替換本體論指導語義保持下的物理最佳化；
- 單符號宇宙將已存在的完整結構壓縮為最小可授權控制句柄；
- 虛擬轉現實理論衡量意圖究竟以多高效率成為現實。

最終目標不是讓一個符號神秘地包含一切，而是讓整個系統成熟到只需一個符號便能**正確定位、合法授權、可靠展開、完整驗證並形成現實結果**。

因此，Nova 的最終方向可以寫成：

$$
\boxed{
\text{高維意圖}
\rightarrow
\text{可驗證程式本體}
\rightarrow
\text{安全算子組合}
\rightarrow
\text{最適計算範式}
\rightarrow
\text{現實執行}
}
$$

以及：

$$
\boxed{
\text{理解得更多，表達得更少，完成得更多；}
\quad
\text{但每一次完成都必須可驗證、可追蹤、可回退。}
}
$$

---

## 附錄 A　統一術語表

| 術語 | 權威定義 |
|---|---|
| Nova Core | 結構化、張量原生、可微分的可執行語言核心 |
| Nova-H | Nova 對人類的投影與編輯介面 |
| Nova-A | AI 直接修改 Nova 程式本體的結構化介面 |
| EML | 人類高密度意圖與兼容過渡語言 |
| ISQL | 高維語義狀態與交換協議 |
| SOS | 算子閉包與組合代數 |
| Cl-safe | 算子組合的安全、失敗隔離與驗證規格 |
| 十六重範式 | 計算底空間、填補方式與觀察尺度的分類空間 |
| 範式鍵結 | 多個計算範式組成合法執行鏈的規則 |
| ProgramHandle | 指向完整已驗證程式的版本化、受權限控制句柄 |
| 單符號控制 | 以最小表面符號引用與啟動 ProgramHandle |
| 虛擬轉現實效率 | 意圖經編碼、建構、驗證、規劃、執行形成現實結果的端到端效率 |

## 附錄 B　架構決策記錄建議

| ADR | 問題 |
|---|---|
| ADR-001 | Nova 權威本體使用圖而非文字 |
| ADR-002 | Core IR 是否基於 MLIR |
| ADR-003 | Shape solver 的可判定核心 |
| ADR-004 | 效果系統的最小集合 |
| ADR-005 | MSSP 中 AI 與驗證器的責任分界 |
| ADR-006 | GraphPatch 交易與回滾 |
| ADR-007 | SOS 槽位如何映射至 Nova 節點 |
| ADR-008 | Cl-safe 靜態與執行期責任 |
| ADR-009 | 十六重範式成本模型 |
| ADR-010 | ProgramHandle 權限與版本策略 |

---

**文件結束**  
**EML-NOVA-UNIFIED-ROADMAP-2026-v1.0**

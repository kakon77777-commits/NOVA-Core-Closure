# Nova Core Baseline v3.0  
## 統合前正式核心規格：後文本、張量原生、可微分與 AI 輔助安全的程式語言

**文件編號：** EML-NOVA-CORE-2026-v3.0  
**作者：** Neo.K  
**機構：** EveMissLab／一言諾科技有限公司  
**文件性質：** 語言核心規格、研究原型規格、統合前基線  
**狀態：** 正式化草案  
**日期：** 2026 年 7 月  
**前置版本：** 《Nova（Project ENL 2.0）：後文本時代的張量原生程式語言》v2.0  
**適用範圍：** Nova 核心語言、Nova IR、投影編輯器、編譯器、執行時與最小標準庫  
**明確排除：** ISQL、SOS、Cl-safe、十六重範式、單符號宇宙與意圖直接耦合之完整統合；上述系統只保留擴充介面，不納入本文件的核心正確性依賴。

---

## 摘要

Nova 是一種以結構化程式物件而非純文字檔案為本體、以張量與算子圖為一級運算對象、以投影式編輯呈現給人類、並將自動微分、形狀約束、資源規劃與記憶體安全納入語言與編譯器共同責任的後文本程式語言。

Nova 的核心主張不是「用數學符號取代英文關鍵字」，而是重新定義程式的存在形式。傳統程式語言通常先建立文字序列，再由解析器重建抽象語法樹；Nova 則直接儲存型別化抽象語法圖，文字、數學公式、節點圖、除錯視圖與文件視圖皆為同一程式本體的不同投影。因此，Nova 的核心程式不是字串，而是：

$$
\mathcal{N}
=
(\mathcal{G},\mathcal{T},\mathcal{C},\mathcal{E},\mathcal{M},\mathcal{D})
$$

其中：

- $\mathcal{G}$：型別化程式圖；
- $\mathcal{T}$：值、張量、形狀與維度型別；
- $\mathcal{C}$：約束集合；
- $\mathcal{E}$：效果與外部作用；
- $\mathcal{M}$：記憶體、所有權與生命週期模型；
- $\mathcal{D}$：自動微分與可微分性資訊。

本文件將 Nova 從願景型白皮書提升為可實作的語言核心基線，正式規定其設計目標、非目標、程式物件模型、投影規則、型別與形狀系統、函數與控制流、自動微分、效果系統、MSSP-AISMBI 記憶體模型、編譯器管線、執行時、互操作、工具鏈、測試方法與最小可行版本。

**關鍵詞：** Nova、張量原生、後文本程式設計、投影式編輯、結構化程式、型別化程式圖、自動微分、MSSP-AISMBI、AI 輔助編譯器

---

# 第一部　定位、邊界與設計公理

## 1. Nova 的正式定位

Nova 是：

1. **結構原生語言**：程式本體是型別化結構，不是文字；
2. **張量原生語言**：張量、維度、形狀、軸與廣播是核心語義；
3. **數學投影語言**：數學形式是可執行結構的主要人類投影；
4. **一級可微分語言**：微分不是外部函式庫技巧，而是語言級轉換；
5. **多後端語言**：同一語義圖可映射到 CPU、GPU、NPU、分散式與其他計算後端；
6. **AI 輔助安全語言**：AI 可協助推斷記憶體與資源策略，但正確性不得僅依賴不可重現的模型判斷；
7. **可逆投影語言**：任何人類視圖皆不得成為唯一真實來源，程式本體必須保持可驗證的結構化儲存。

Nova 不是：

- 另一套僅以特殊符號縮短字元數的語法糖；
- 對 Python 或 C++ 的表面預處理器；
- 假設所有程式都可微分的封閉系統；
- 以 AI 猜測取代型別檢查與驗證的語言；
- 第一版就取代所有 Web、CRUD、作業系統與嵌入式語言的通用語言；
- 以「零 Bug」或「自動最佳化至全局最優」為承諾的系統。

## 2. 核心設計公理

### 公理 N1：結構先於投影

程式的權威本體為結構化程式圖：

$$
\mathcal{G}_{\mathrm{auth}}
$$

所有可見形式皆為投影：

$$
\pi_i(\mathcal{G}_{\mathrm{auth}})=V_i
$$

其中 $V_i$ 可為數學視圖、文字視圖、節點圖、文件視圖或除錯視圖。

### 公理 N2：語義先於表面語法

兩個投影若對應同一型別化程式圖，則視為同一程式：

$$
\pi_a(\mathcal{G})\equiv\pi_b(\mathcal{G})
$$

視覺差異不應自動造成語義差異。

### 公理 N3：張量是基本值，不是函式庫容器

標量為零階張量：

$$
x\in\operatorname{Tensor}[\tau;()]
$$

向量、矩陣與高階張量皆共享同一型別族。

### 公理 N4：形狀是型別的一部分

若：

$$
A:\operatorname{Tensor}[\tau;(m,n)]
$$

$$
B:\operatorname{Tensor}[\tau;(n,k)]
$$

則：

$$
A\cdot B:\operatorname{Tensor}[\tau;(m,k)]
$$

形狀不相容必須在編譯期、特化期或受控執行期被顯性處理。

### 公理 N5：數學表達與執行語義必須對齊

對於核心數學運算，顯示公式應直接映射至唯一或受約束的語義節點，不得依賴不可見的字串解析慣例。

### 公理 N6：AI 建議不得越過可驗證核心

AI 可以：

- 建議所有權；
- 建議配置策略；
- 建議後端；
- 產生證明義務；
- 搜尋最佳化候選。

AI 不可在缺乏驗證時直接宣告：

- 型別安全；
- 記憶體安全；
- 無競態；
- 數值等價；
- 微分正確；
- 結果可重現。

### 公理 N7：失敗必須型別化與可追蹤

任何無法完成的推斷、編譯或執行，不得退化為靜默猜測。系統必須輸出帶來源節點、約束集合與修復建議的結構化錯誤。

### 公理 N8：核心語義與後端實現分離

Nova 的語義正確性不依賴特定硬體：

$$
\operatorname{Sem}(\mathcal{G})
$$

後端只負責在物理約束下實現該語義：

$$
\operatorname{Lower}_H(\mathcal{G})=P_H
$$

---

# 第二部　程式本體與儲存格式

## 3. Nova 程式物件模型

一個 Nova 專案由下列物件構成：

$$
\mathcal{P}
=
(\mathcal{M\!od},\mathcal{Sym},\mathcal{Graph},\mathcal{Constraint},\mathcal{Artifact})
$$

其中：

- $\mathcal{M\!od}$：模組集合；
- $\mathcal{Sym}$：符號與名稱表；
- $\mathcal{Graph}$：程式圖集合；
- $\mathcal{Constraint}$：型別、形狀、效果與資源約束；
- $\mathcal{Artifact}$：編譯產物、測試、文件與追蹤資料。

### 3.1 節點

每個節點具有：

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

### 3.2 邊

邊不只是資料流，也可以是：

- 值依賴；
- 控制依賴；
- 效果依賴；
- 所有權轉移；
- 形狀依賴；
- 微分依賴；
- 資源依賴。

因此可定義：

$$
e=(u,v,k,\chi)
$$

其中 $k$ 是邊類型，$\chi$ 是附加約束。

### 3.3 圖而非純樹

Nova 的外觀可能像 AST，但其權威結構應允許：

- 共享子圖；
- 公共子表達式；
- 循環；
- 資料流；
- 反向微分邊；
- 跨模組引用。

因此使用型別化程式圖比單純 AST 更準確。

## 4. 權威儲存格式

### 4.1 必要特性

權威格式必須：

- 可版本化；
- 可確定性序列化；
- 可差異比較；
- 可局部更新；
- 可驗證；
- 可遷移；
- 不依賴 IDE 私有狀態；
- 支援未知欄位保留；
- 支援內容雜湊。

### 4.2 雙格式策略

第一階段可採：

1. **可讀交換格式**：JSON、TOML 或 S-expression；
2. **高效二進位格式**：MessagePack、CBOR、FlatBuffers 或自定義格式。

權威語義必須由 schema 決定，而不是由某個序列化格式決定。

### 4.3 確定性

相同程式本體必須產生相同正規化雜湊：

$$
\operatorname{Hash}(\operatorname{Canon}(\mathcal{G}_1))
=
\operatorname{Hash}(\operatorname{Canon}(\mathcal{G}_2))
$$

當且僅當兩者在規格定義的正規形式下等價。

---

# 第三部　投影式編輯

## 5. 投影不是程式本體

Nova IDE 顯示的內容是：

$$
V=\pi(\mathcal{G},U,S)
$$

其中：

- $\mathcal{G}$：程式圖；
- $U$：使用者與權限；
- $S$：顯示設定。

同一程式可有：

- 數學投影；
- 結構化文字投影；
- 節點圖投影；
- 訓練流程投影；
- 記憶體生命週期投影；
- 微分圖投影；
- 效能投影。

## 6. 編輯操作

使用者不是任意修改字串，而是提交結構化操作：

$$
\Delta:\mathcal{G}\rightarrow\mathcal{G}'
$$

基本操作包括：

- 建立節點；
- 連接輸入；
- 替換算子；
- 約束維度；
- 封裝函數；
- 展開函數；
- 建立微分請求；
- 添加效果；
- 選擇後端限制；
- 宣告測試性質。

每個操作必須經過局部驗證後才進入權威圖。

## 7. 文字模式

Nova 必須保留文字交換模式，但文字模式不是唯一來源。

文字模式的目標是：

- Git diff；
- 程式化生成；
- 批量修改；
- CLI；
- 無障礙；
- 與其他工具互操作。

文字模式需具有明確文法，並能無歧義地轉換為核心圖：

$$
\operatorname{Parse}(T)=\mathcal{G}
$$

而投影回文字時：

$$
\operatorname{Print}(\mathcal{G})=T_{\mathrm{canon}}
$$

不要求：

$$
\operatorname{Print}(\operatorname{Parse}(T))=T
$$

只要求其語義與正規結構一致。

---

# 第四部　核心型別系統

## 8. 值型別

Nova Core 至少包含：

- `Bool`
- 有號與無號整數族；
- 浮點族；
- 複數族；
- 字串與位元序列；
- 單位型別；
- 乘積型別；
- 和型別；
- 可選型別；
- 結果型別；
- 函數型別；
- 張量型別；
- 資源句柄；
- 外部物件句柄。

## 9. 張量型別

一般形式：

$$
\operatorname{Tensor}
[
\tau;
(d_1,d_2,\ldots,d_r);
\ell;
\delta
]
$$

其中：

- $\tau$：元素型別；
- $(d_1,\ldots,d_r)$：形狀；
- $\ell$：佈局；
- $\delta$：裝置或位置。

例如：

$$
X:
\operatorname{Tensor}
[
\operatorname{f32};
(B,T,D);
\operatorname{rowmajor};
\operatorname{gpu0}
]
$$

## 10. 維度表達式

維度可為：

- 常數；
- 符號；
- 仿射表達式；
- 受約束非線性表達式；
- 執行期維度。

例：

$$
d=2n+1
$$

$$
m\geq 1
$$

$$
k\mid n
$$

核心編譯器必須至少支援 Presburger 可判定子集；超出子集的條件需產生執行期檢查或證明義務。

## 11. 形狀相等與相容

### 11.1 嚴格相等

$$
S_1=S_2
$$

### 11.2 廣播相容

對軸 $i$：

$$
d_i=e_i
\lor
d_i=1
\lor
e_i=1
$$

### 11.3 收縮相容

矩陣與張量收縮要求指定軸相等：

$$
d_a=e_b
$$

### 11.4 不確定形狀

未知形狀不得自動視為相容。系統應返回：

```text
ShapeObligation {
  expression
  required_relation
  proof_status
  runtime_guard
}
```

## 12. 名義型別與結構型別

Nova Core 可採混合策略：

- 張量與純資料結構偏向結構型別；
- 資源、權限與外部句柄採名義型別；
- 使用者可宣告不透明型別，阻止意外等價。

## 13. 單位與量綱型別

對物理與工程程式，Nova 應支援量綱：

$$
v:\operatorname{Quantity}[\mathrm{m}\,\mathrm{s}^{-1}]
$$

非法運算如：

$$
3\,\mathrm{m}+2\,\mathrm{s}
$$

必須被拒絕。

---

# 第五部　運算、函數與控制流

## 14. 基本算子

Nova Core 應將下列操作作為標準語義節點：

- 元素級算術；
- 比較；
- 邏輯；
- 矩陣乘法；
- 張量收縮；
- 轉置與軸置換；
- reshape；
- slice；
- gather、scatter；
- reduce；
- scan；
- convolution；
- softmax；
- 隨機採樣；
- 稀疏算子；
- 線性代數分解。

符號顯示只是投影，例如：

$$
C=A\cdot B
$$

其底層節點為 `MatMul(A,B)`。

## 15. 函數

函數簽名需包含：

$$
f:
(X_1,\ldots,X_n)
\overset{\mathcal{E}}{\longrightarrow}
(Y_1,\ldots,Y_m)
$$

其中 $\mathcal{E}$ 為效果集合。

函數可以：

- 純函數；
- 可微分函數；
- 外部效果函數；
- 泛型函數；
- 形狀多態函數；
- 裝置多態函數。

## 16. 控制流

Nova 不得只適用於直線式張量圖。核心需包含：

- `if`／條件選擇；
- `match`／代數資料型別匹配；
- 有界迴圈；
- 一般迴圈；
- 遞迴；
- 結果傳播；
- 非同步等待；
- 並行映射。

投影可使用數學分段形式：

$$
f(x)=
\begin{cases}
g(x), & x>0\\
h(x), & x\leq 0
\end{cases}
$$

## 17. 靜態圖與動態圖

Nova Core 採分層策略：

1. 可靜態化區域優先建圖；
2. 動態控制流保留為控制節點；
3. 可在特化後重新靜態化；
4. 不強迫所有程式展開為有限無環圖。

---

# 第六部　一級可微分系統

## 18. 可微分性型別

每個函數或節點具有：

- `Differentiable`
- `PiecewiseDifferentiable`
- `NonDifferentiable`
- `UnknownDifferentiability`

可微分性不是布林標記，而可帶條件。

## 19. 微分算子

Nova 提供：

$$
\operatorname{grad}(f)
$$

$$
\operatorname{jacobian}(f)
$$

$$
\operatorname{jvp}(f,v)
$$

$$
\operatorname{vjp}(f,v)
$$

並允許投影為：

$$
\nabla f
$$

或：

$$
\frac{\partial f}{\partial x}
$$

## 20. 自動微分轉換

對程式圖 $\mathcal{G}$：

$$
\mathcal{D}_{r}(\mathcal{G})=\mathcal{G}_{\mathrm{reverse}}
$$

$$
\mathcal{D}_{f}(\mathcal{G})=\mathcal{G}_{\mathrm{forward}}
$$

編譯器應依輸入輸出維度與成本模型選擇模式。

## 21. 不可微分節點

不可微分操作必須要求下列之一：

- 停止梯度；
- 次梯度；
- 自定義梯度；
- 平滑近似；
- 顯式拒絕。

不得悄悄指定任意梯度。

## 22. 效果與微分

具有 I/O、隨機性或外部狀態的函數，必須指定微分語義。隨機節點需使用：

- 重參數化；
- 分數函數估計；
- 不可微分標記。

---

# 第七部　效果、併發與可重現性

## 23. 效果系統

效果集合可包括：

- `IO`
- `State`
- `Random`
- `Network`
- `File`
- `Device`
- `Unsafe`
- `NonDeterministic`
- `External`

純函數：

$$
f:X\rightarrow Y
$$

有效果函數：

$$
f:X\overset{\{IO,State\}}{\longrightarrow}Y
$$

## 24. 效果隔離

編譯器可自由重排純節點，但不得越過未證明可交換的效果邊。

## 25. 併發模型

Nova Core 應提供結構化併發：

- task scope；
- async；
- join；
- parallel map；
- device kernel；
- channel 或 typed stream。

第一版不要求通用共享可變記憶體為預設模式。

## 26. 可重現性

程式必須能宣告：

- 嚴格確定；
- 統計可重現；
- 非確定；
- 後端依賴。

隨機數種子、浮點重排與非確定 GPU kernel 必須進入構建與執行紀錄。

---

# 第八部　MSSP-AISMBI 記憶體模型

## 27. 基本原則

MSSP-AISMBI 的核心不是「讓 AI 隨意決定何時釋放記憶體」，而是：

1. 由靜態分析建立安全下界；
2. 由約束求解器建立所有權與生命週期候選；
3. 由 AI 排序候選與提出最佳化建議；
4. 由驗證器檢查；
5. 無法證明時採保守策略或要求顯式標註。

## 28. 記憶體狀態

資源可處於：

- owned；
- borrowed immutable；
- borrowed mutable；
- shared immutable；
- device resident；
- moved；
- released；
- external unmanaged。

## 29. 生命週期推斷

對值 $v$，編譯器計算使用區間：

$$
L(v)=[t_{\mathrm{first}},t_{\mathrm{last}}]
$$

並建立別名圖、裝置位置與逃逸分析。

## 30. AI 的角色

AI 可根據程式上下文建議：

- 移動；
- 借用；
- 複製；
- 原地更新；
- 張量重用；
- 記憶體池；
- checkpoint；
- CPU／GPU offload；
- 冷熱資料分離。

但輸出必須轉化為可檢查計畫：

```text
MemoryPlan {
  allocations[]
  aliases[]
  transfers[]
  deallocations[]
  obligations[]
  confidence
  verifier_result
}
```

## 31. 失敗策略

若無法證明計畫安全：

- 拒絕編譯；
- 切換保守 GC／ARC 區域；
- 插入執行期檢查；
- 要求使用者提供約束；
- 退回安全但較慢的配置。

## 32. 冷熱分離

Nova Core 保留 EML 1.5 的冷熱分離思想：

- 熱區：頻繁變化、需動態分析；
- 冷區：穩定、可結晶化、可快取；
- 冰區：內容雜湊固定、可預先編譯。

但「冷」不是永久不變；依賴改變必須使快取失效。

---

# 第九部　編譯器架構

## 33. 編譯器不是單次文字翻譯器

核心管線：

$$
\mathcal{G}_{source}
\rightarrow
\mathcal{G}_{typed}
\rightarrow
\mathcal{G}_{effect}
\rightarrow
\mathcal{G}_{diff}
\rightarrow
\mathcal{G}_{memory}
\rightarrow
\mathcal{G}_{opt}
\rightarrow
IR_H
\rightarrow
P_H
$$

## 34. 前端階段

1. 載入結構化專案；
2. schema 驗證；
3. 名稱解析；
4. 型別與形狀約束生成；
5. 約束求解；
6. 效果檢查；
7. 可微分性分析；
8. 錯誤圖建立。

## 35. Nova Core IR

Core IR 必須具有：

- SSA 或等價資料流語義；
- 顯式張量型別；
- 顯式形狀；
- 顯式效果；
- 顯式裝置；
- 顯式所有權或資源 token；
- 可表示控制流；
- 可表示自動微分轉換；
- 穩定版本。

## 36. 中階最佳化

至少包含：

- 常數折疊；
- 公共子表達式消除；
- dead node elimination；
- operator fusion；
- layout propagation；
- shape specialization；
- algebraic simplification；
- kernel selection；
- buffer reuse；
- transfer minimization。

每個最佳化需保留語義證據或測試義務。

## 37. 後端

第一階段建議：

- MLIR；
- LLVM CPU；
- CUDA 或 ROCm；
- WebGPU；
- 一個解釋器後端。

Nova 不應在第一版自行重寫所有底層編譯技術。

## 38. 成本模型

後端候選 $p$ 的成本：

$$
F(p)
=
\alpha T(p)
+
\beta S(p)
+
\gamma E(p)
+
\delta IO(p)
+
\epsilon R(p)
$$

其中分別表示時間、空間、能耗、I/O 與失敗風險。

第一版只需局部與啟發式最佳化，不宣稱全局最優。

## 39. 分層編譯

- AOT：可預測部署；
- JIT：動態形狀與特化；
- profile-guided；
- ahead-of-profile cache；
- kernel cache。

---

# 第十部　執行時

## 40. Nova Runtime 職責

- 張量配置；
- 裝置管理；
- kernel 調度；
- 非同步事件；
- 錯誤傳播；
- 執行期形狀守衛；
- 記憶體池；
- 模型與程式快取；
- tracing；
- profiling；
- 外部函式呼叫。

## 41. 執行模式

1. **解釋模式**：正確性與除錯；
2. **JIT 模式**：互動研究；
3. **AOT 模式**：部署；
4. **沙盒模式**：不可信程式；
5. **確定性模式**：可重現研究。

## 42. 錯誤物件

所有錯誤應至少包含：

```text
NovaError {
  category
  node_id
  projection_location
  violated_constraints[]
  inferred_context
  backend_context
  repair_candidates[]
  trace
}
```

---

# 第十一部　模組、套件與互操作

## 43. 模組

模組必須顯式匯出：

- 值；
- 型別；
- 函數；
- 效果；
- 裝置需求；
- 形狀契約；
- 微分契約。

## 44. 套件

套件清單至少包含：

```text
name
version
nova_core_version
dependencies
capabilities
backends
licenses
integrity_hashes
build_profiles
```

## 45. FFI

Nova Core 應優先支援：

- C ABI；
- Python；
- NumPy／DLPack；
- ONNX 或等價模型交換；
- MLIR；
- GPU kernel 外掛。

外部函式必須標記：

- 型別；
- 形狀；
- 所有權；
- 效果；
- 可微分性；
- 執行緒安全；
- 裝置。

未知資訊不得默認為安全。

---

# 第十二部　標準庫

## 46. 最小標準庫

### 46.1 Core

- 基本型別；
- 結果與錯誤；
- 容器；
- 字串；
- 數值；
- 測試；
- tracing。

### 46.2 Tensor

- 建立；
- 索引；
- reshape；
- broadcasting；
- reduction；
- contraction；
- linear algebra；
- random；
- sparse。

### 46.3 Diff

- grad；
- jvp；
- vjp；
- custom derivative；
- checkpoint。

### 46.4 Device

- CPU；
- GPU；
- memory transfer；
- stream；
- event。

### 46.5 Interop

- C；
- Python；
- DLPack；
- model exchange。

## 47. 非核心庫

Web、GUI、資料庫、遊戲引擎與分散式訓練應先以外部套件存在，不納入第一版核心。

---

# 第十三部　工具鏈

## 48. Nova Studio

第一版 IDE 不必一次完成所有視圖，但必須提供：

- 公式投影；
- 結構化文字投影；
- 圖視圖；
- 型別與形狀檢查；
- 即時執行；
- 錯誤定位；
- diff；
- 版本遷移。

## 49. CLI

建議命令：

```text
nova new
nova check
nova run
nova test
nova build
nova fmt
nova graph
nova diff
nova profile
nova export
nova migrate
```

## 50. Notebook

Nova Notebook 的單元格本體應為子圖，不是文字片段。輸出必須記錄：

- 輸入圖雜湊；
- 依賴；
- 執行環境；
- 隨機狀態；
- 後端；
- 結果雜湊。

## 51. 版本控制

需要結構化 diff：

- 節點新增；
- 邊改變；
- 型別改變；
- 約束改變；
- 投影變化；
- 純視覺改變。

純投影變化不得被誤認為語義改變。

---

# 第十四部　安全與信任邊界

## 52. 能力安全

具有外部效果的程式必須獲得能力：

$$
\operatorname{Capability}
=
(\text{resource},\text{action},\text{scope})
$$

沒有 `Network` 能力的程式不得發起網路請求。

## 53. 不可信 AI 建議

AI 生成的：

- 程式圖；
- 記憶體計畫；
- 最佳化；
- 自定義梯度；

均視為不可信輸入，必須經 schema、型別、約束、測試與沙盒驗證。

## 54. Unsafe 區域

若需跳過部分保護，必須進入顯式 `Unsafe` 區域，並輸出不可忽略的審計標記。

---

# 第十五部　最小可行版本

## 55. Nova Core MVP v0.1

### 必須完成

1. 結構化圖 schema；
2. 確定性序列化；
3. 基本張量型別；
4. 符號形狀約束；
5. 元素運算與矩陣乘法；
6. 純函數；
7. `if` 與有界迴圈；
8. reverse-mode 自動微分；
9. 解釋器；
10. CPU 後端；
11. 結構化文字投影；
12. 基本公式投影；
13. CLI；
14. 單元與性質測試；
15. Python／DLPack 互操作。

### 可延後

- 完整投影 IDE；
- AI 記憶體推斷模型；
- GPU 深度最佳化；
- 分散式執行；
- 完整效果系統；
- JIT；
- 自舉；
- 企業協作。

## 56. MVP 驗收範例

需能表示、檢查、微分並執行：

$$
Y=W\cdot X+b
$$

$$
L=\frac{1}{N}\sum_{i=1}^{N}(Y_i-\hat Y_i)^2
$$

並產生：

$$
\nabla_W L
$$

同時驗證：

- 錯誤形狀被拒絕；
- 梯度與參考實作一致；
- 序列化後雜湊穩定；
- Python 匯入匯出一致；
- CPU 結果可重現。

---

# 第十六部　測試與驗證

## 57. 測試層級

1. schema 測試；
2. parser／printer round-trip；
3. 型別測試；
4. 形狀求解測試；
5. IR 驗證；
6. 微分數值檢查；
7. 後端差分測試；
8. 記憶體 sanitizer；
9. fuzzing；
10. 性質測試；
11. 可重現性測試；
12. 版本遷移測試。

## 58. 差分測試

同一程式在：

- 解釋器；
- CPU；
- GPU；
- Python 參考實作；

之間比較。

允許浮點誤差：

$$
\lVert y_1-y_2\rVert\leq\varepsilon
$$

## 59. 微分檢查

有限差分：

$$
\frac{\partial f}{\partial x_i}
\approx
\frac{f(x+\epsilon e_i)-f(x-\epsilon e_i)}{2\epsilon}
$$

僅作測試，不作主要微分機制。

---

# 第十七部　已知限制與非承諾

## 60. 不可判定性

Nova 無法在一般情況下完全證明：

- 程式終止；
- 所有語義等價；
- 所有執行期錯誤不存在；
- 所有微分都數值穩定；
- 所有最佳化均為全局最佳。

## 61. AI 推斷限制

AI 可以降低標註成本，但不能消滅：

- 資料分布漂移；
- 模型幻覺；
- 置信度失真；
- 未見架構；
- 對抗性輸入。

## 62. 後文本限制

投影編輯解決字串解析問題，但會引入：

- IDE 綁定風險；
- 結構化 merge 複雜度；
- 大型圖導航問題；
- 可攜性與無障礙問題；
- 人類學習成本。

因此文字投影與開放格式是必要的。

---

# 第十八部　統合前擴充介面

本文件不統合後續理論，但預留以下接口：

## 63. 語義張量接口

```text
SemanticPayload
```

允許未來接入高維語義表示。

## 64. 算子閉包接口

```text
OperatorDescriptor
```

允許未來擴充幾何、語義與組合槽。

## 65. 安全驗證接口

```text
CompositionValidator
```

允許外部安全規則檢查算子合成。

## 66. 執行範式接口

```text
ExecutionStrategyDescriptor
```

允許外部系統標記序列、跳躍、並行或識別策略。

## 67. 控制句柄接口

```text
ProgramHandle
```

允許完整程式圖被封裝、引用與受權限啟動。

這些接口不改變 Nova Core 的基本語義；它們只是後續統合的穩定接點。

---

# 第十九部　正式核心定義

Nova Core 可濃縮為：

$$
\boxed{
\mathcal{N}_{\mathrm{Core}}
=
(\mathcal{G},
\mathcal{T},
\mathcal{S},
\mathcal{E},
\mathcal{M},
\mathcal{D},
\mathcal{R})
}
$$

其中：

- $\mathcal{G}$：結構化程式圖；
- $\mathcal{T}$：值與張量型別；
- $\mathcal{S}$：形狀與約束求解；
- $\mathcal{E}$：效果與可重現性；
- $\mathcal{M}$：可驗證記憶體規劃；
- $\mathcal{D}$：一級自動微分；
- $\mathcal{R}$：多後端實現。

其核心資料流為：

$$
\boxed{
\text{結構建立}
\rightarrow
\text{型別與形狀驗證}
\rightarrow
\text{效果與微分分析}
\rightarrow
\text{記憶體規劃}
\rightarrow
\text{最佳化}
\rightarrow
\text{後端實現}
\rightarrow
\text{可追蹤執行}
}
$$

Nova 最根本的改變不是使用更漂亮的數學符號，而是：

$$
\boxed{
\text{程式從「被解析的文本」轉變為「可投影、可驗證、可執行的結構本體」。}
}
$$

---

# 結論

Nova 的第一個正式工程任務，不是立刻承擔所有高維語義、符號本體論、計算範式與意圖控制理論，而是先成為一個可被實作、測試、版本化與否證的語言核心。

因此，本文件將 Nova 的統合前基線固定為：

1. 結構化程式圖是權威本體；
2. 張量與形狀是核心型別；
3. 數學是主要投影，而不是唯一儲存形式；
4. 自動微分是一級轉換；
5. AI 協助資源與記憶體推斷，但不能越過驗證器；
6. 編譯器實現語義，而非僅翻譯字串；
7. 多後端共享同一核心語義；
8. 所有錯誤、推斷與最佳化必須可追蹤；
9. 第一版先建立小而完整的可執行閉環；
10. 後續統合理論透過明確接口接入，而非改寫核心。

這個基線完成後，Nova 才有資格進入下一階段：從張量原生程式語言，擴展為 AI 原生的高維意圖—算子—執行統一系統。

---

## 附錄 A　建議儲存範例

```json
{
  "nova_version": "0.1",
  "module": "linear_model",
  "nodes": [
    {
      "id": "matmul_1",
      "kind": "MatMul",
      "inputs": ["W", "X"],
      "outputs": ["WX"],
      "type": {
        "element": "f32",
        "shape": ["B", "O"]
      },
      "effects": [],
      "diff": "Differentiable"
    },
    {
      "id": "add_1",
      "kind": "Add",
      "inputs": ["WX", "b"],
      "outputs": ["Y"],
      "type": {
        "element": "f32",
        "shape": ["B", "O"]
      },
      "effects": [],
      "diff": "Differentiable"
    }
  ],
  "constraints": [
    "shape(W) == [I, O]",
    "shape(X) == [B, I]",
    "shape(b) == [O]"
  ]
}
```

## 附錄 B　核心錯誤分類

| 類別 | 說明 |
|---|---|
| SchemaError | 結構化檔案不符合版本 schema |
| NameError | 名稱或模組解析失敗 |
| TypeError | 值型別不相容 |
| ShapeError | 張量形狀約束不可滿足 |
| EffectError | 效果越界或重排不合法 |
| DiffError | 微分要求無定義或缺少規則 |
| MemoryPlanError | 記憶體計畫無法驗證 |
| BackendError | 目標後端無法實現所需語義 |
| CapabilityError | 缺少外部能力 |
| ReproducibilityError | 宣告的可重現條件無法滿足 |
| MigrationError | 舊版本結構無法安全遷移 |

---

**文件結束**  
**EML-NOVA-CORE-2026-v3.0**

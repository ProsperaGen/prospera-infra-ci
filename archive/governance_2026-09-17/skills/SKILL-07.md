<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:無機制驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# SKILL-07｜Document Depth Validation
## Document Header
- Document Type: Codex
- Version: v1.0
- Status: Approved
- Owner: prospera-infra-ci/skills/
- Governing Authority: prospera-engineering-codex v1.0
- DNA Reference: 要素三（文件規範）+ 要素五（可工程實作）+ 要素七（寫作架構）
- Last Updated: 2026-05-19

---

## 1. Identity & Scope

確保所有提交到 repo 的文件符合 ProsperaGen 文件深度標準。
防止空洞文件、純敘述段落、無法工程實作的文件進入 repo。

---

## 2. Non-Goals

- 不管理程式碼品質（→ SKILL-04 Pre-flight）
- 不管理文件存放路徑（→ SKILL-02 Dir Structure）

---

## 3. 文件提交前三問（DNA 要素五）

提交任何文件前，必須回答以下三個問題：

```
Q1：工程師看完這份文件，能直接開始寫程式嗎？
Q2：這份文件能被自動化工具驗證（通過/失敗）嗎？
Q3：這份文件能被稽核員用來核查系統行為嗎？

三個都 YES → 文件合格 → 允許提交
任何一個 NO → 文件需要補強 → 不得提交
```

---

## 4. 文件類型對應寫作要求（DNA 要素七）

### Spec 文件（定義「什麼」）
```
必須包含：
□ 功能清單（做什麼）
□ Non-Goals（不做什麼）
□ 成功標準（可量化數字）
□ 失敗標準（可量化數字）

範例合格標準：
❌ 「API 應該要快」
✅ 「API 回應時間 P99 < 200ms，測試工具：k6，失敗標準：任何請求超過 500ms」
```

### Design 文件（定義「怎麼做」）
```
必須包含：
□ 架構圖（Component + 資料流）
□ API Interface（輸入/輸出格式，含型別）
□ State Machine（狀態轉換圖）
□ Error Handling（每種錯誤如何處理）
```

### Codex 文件（定義「必須遵守」）
```
必須包含：
□ MUST 規則（違反即失敗，有自動驗證機制）
□ SHOULD 規則（有理由可例外，需記錄）
□ MUST NOT 禁止事項
□ 執行機制（如何自動驗證這些規則）
```

---

## 5. 強制文件結構（DNA 要素三）

所有文件必須包含以下結構，缺一即無效：

```markdown
## Document Header
- Document Type: [Spec / Design / Codex / Blueprint / Audit]
- Version: [v1.0]
- Status: [Draft / Review / Approved / Frozen]
- Owner: [Repo 名稱]
- Governing Authority: prospera-engineering-codex v1.0
- Last Updated: [日期]

## 1. Identity & Scope
## 2. Non-Goals
## 3. System Context
## 4. Rules & Constraints
## 5. Matrix / Interface Definition   ← 至少一個決策矩陣
## 6. Failure Modes
## 7. Audit Requirements
```

---

## 6. 必須包含的四要素（缺一即無效）

| 要素 | 說明 | 不合格範例 | 合格範例 |
|------|------|----------|---------|
| Matrix | 至少一個決策矩陣或對照表 | 只有段落描述 | 含 \| 欄位 \| 值 \| 的表格 |
| Rule Set | 明確規則條文 | 「系統應遵守規範」 | 「MUST: commit message 格式為 [Phase][Layer]...」 |
| Constraint | 邊界與限制 | 省略不做的事 | 明確 Non-Goals 章節 |
| Interface | 輸入/輸出規格 | 只描述功能 | 含型別的 API 定義或函數簽名 |

---

## 7. 禁止事項（MUST NOT）

```
❌ 純敘述段落（沒有可執行規格）
❌ 「我們相信」「我們認為」「應該考慮」等主觀語氣
❌ 沒有來源的數據
❌ 模糊成功標準（「表現良好」「用戶體驗佳」）
❌ 沒有 Document Header
❌ 沒有 AI Header（AI 生成的文件）
```

---

## 8. Failure Modes

| 症狀 | 原因 | 修法 |
|------|------|------|
| 文件提交後 CI 抱怨 | 缺少 Document Header | 補完 Header 再 commit |
| 工程師看不懂如何實作 | 三問 Q1 = NO | 補 Interface Definition 和具體規格 |
| 稽核員無法核查 | 三問 Q3 = NO | 補 Audit Requirements 和可量化標準 |
| 文件是「方向性」的 | 是 Governance Direction Doc | 用 SKILL-05 §6 三問重判，改寫為 Spec |

---

## 9. Audit Requirements

文件審閱記錄到 prospera-audit-ledger：
```
[日期] DOC-REVIEWED: [文件名稱] [Document Type] [三問結果 Y/Y/Y] [審閱者]
```

---

*v1.0 · 2026-05-19 · prospera-infra-ci/skills/*

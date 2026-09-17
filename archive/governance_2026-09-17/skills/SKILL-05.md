<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:無機制驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# SKILL-05｜Phase & Stage Lock
## Document Header
- Document Type: Codex
- Version: v1.0
- Status: Approved
- Owner: prospera-infra-ci/skills/
- Governing Authority: prospera-engineering-codex v1.0
- DNA Reference: 要素一（Phase-Gated）+ 要素二（六 Stage）+ 要素五（可工程實作）
- Last Updated: 2026-05-19

---

## 1. Identity & Scope

防止 AI 輸出語義漂移（Governance Comfort Drift）。
強制 AI 在每次任務開始前宣告當前 Phase 和 Stage，並確認輸出物類型正確。

核心問題：AI 模型有「Semantic Gravity」——自然偏向生成高抽象治理文件，而非 runtime artifact。
這個 Skill 是抵抗 Semantic Gravity 的執行機制。

---

## 2. Non-Goals

- 不定義 Phase/Stage 的架構意義（→ DNA 要素一、二）
- 不管理 repo 間的依賴（→ prospera-global-inventory）

---

## 3. Phase Gate 查閱表（DNA 要素一）

| Phase | 名稱 | 允許的輸出物 | 禁止的輸出物 |
|-------|------|------------|------------|
| 0 | Engineering Governance Lock | Codex 版本宣告、GOVERNANCE_STATUS.md | 任何功能程式碼 |
| 1 | Problem Framing | Problem Statement、Non-Goals、System Context | 架構圖、程式碼 |
| 2 | Architecture & Boundary | 架構圖、Component 定義、依賴地圖 | 實作程式碼 |
| 3 | Authority & Invariant | Authority Matrix、Invariant 列表 | 執行邏輯程式碼 |
| 4 | Execution & Enforcement | 實作程式碼、State Machine、API Interface | 新的治理文件 |
| 5 | Failure Modes | Failure Mode Matrix、降級路徑 | 新功能程式碼 |
| 6 | Validation & Evolution | Test Plan、Audit Trail、DR Plan | 未驗證的新功能 |

---

## 4. Stage Gate 查閱表（DNA 要素二）

每個 Stage 有強制輸出物，缺一不可進下一 Stage：

| Stage | 名稱 | 強制輸出物 | 驗收問題 |
|-------|------|----------|---------|
| 1 | Definition | Problem Statement + Success Criteria | 問題說清楚了嗎？成功標準可量化嗎？ |
| 2 | Failure Map | Risk Register + Failure Mode Matrix | 失敗場景列完了嗎？代價量化了嗎？ |
| 3 | Evidence Canonical | Test Plan + Evidence Specification | 怎麼證明它能動？測試覆蓋夠嗎？ |
| 4 | Authority & State | Authority Matrix + State Machine Spec | 誰能做什麼定清楚了嗎？ |
| 5 | Governed Execution | Implementation + Audit Trail | 實作符合治理規則嗎？稽核記錄在嗎？ |
| 6 | Fatal Error & Risk | DR Plan + External Risk Assessment | 最壞情況有方案嗎？ |

---

## 5. 任務開始強制宣告格式

每次任務開始，AI 必須輸出以下宣告，再開始執行：

```
PHASE LOCK DECLARATION
=======================
Current Phase:   [Phase 0-6] - [Phase 名稱]
Current Stage:   [Stage 1-6] - [Stage 名稱]
Target Repo:     [repo 名稱]
Task:            [一句話說明這個任務做什麼]
Allowed Output:  [對應 Phase 允許的輸出物類型]
Forbidden:       [對應 Phase 禁止的輸出物類型]
=======================
```

沒有輸出這個宣告就開始執行 = Phase Lock 違規。

---

## 6. Artifact 類型判斷規則（DNA 要素五）

AI 輸出任何東西前，先問三個問題：

```
Q1：工程師看完這個輸出，能直接開始實作嗎？
Q2：這個輸出能被自動化工具驗證（Pass/Fail）嗎？
Q3：這個輸出能被稽核員用來核查系統行為嗎？

三個都 YES → Runtime Artifact → 允許輸出
任何一個 NO → Governance Direction Document → 拒絕輸出，重新生成
```

---

## 7. Governance Comfort Drift 警示信號

當 AI 輸出中出現以下信號時，立即停止，重新執行 Phase Lock Declaration：

```
警示信號：
- 輸出標題含「方向」「框架」「策略」「願景」「方針」
- 輸出內容大量使用「應該」「建議」「考慮」
- 輸出物無法直接 commit 到 repo
- 輸出物沒有可量化的成功標準
- 輸出物是描述性的，不是規格性的
```

---

## 8. Failure Modes

| 症狀 | 原因 | 修法 |
|------|------|------|
| AI 不斷輸出治理文件 | Phase Lock 未宣告 | 重新執行 §5 宣告 |
| AI 跳 Phase 直接實作 | Phase 0-3 未完成就進 Phase 4 | 回到當前 Phase，補齊輸出物 |
| Stage 輸出物缺失 | Stage Gate 未驗收 | 補齊缺少的輸出物才繼續 |
| 輸出物無法實作 | Semantic Drift | 用 §6 三問重新判斷 |

---

## 9. Audit Requirements

每個 Stage 完成後，在 prospera-audit-ledger 記錄：
```
[日期] STAGE-COMPLETE: [Stage 1-6] [repo] [輸出物清單] [J點狀態]
```

---

*v1.0 · 2026-05-19 · prospera-infra-ci/skills/*

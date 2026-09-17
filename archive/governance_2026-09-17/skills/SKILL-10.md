<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:無機制驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# SKILL-10｜Multi-AI Handoff Protocol
## Document Header
- Document Type: Codex
- Version: v1.0
- Status: Approved
- Owner: prospera-infra-ci/skills/
- Governing Authority: prospera-engineering-codex v1.0
- DNA Reference: 要素八（AI 協作協議）+ 三個 AI 分工
- Last Updated: 2026-05-19

---

## 1. Identity & Scope

規範 Claude / Claude Code / GPT / Gemini 四個 AI 之間的任務交接協議。
解決問題：AI 間重複試錯、GPT 推論 repo 狀態（幻覺）、Claude Code 重開後狀態遺失、同一問題被多個 AI 輪流試一遍消耗大量 token。

**觸發條件：**
- Claude 要交接任務給 Claude Code 前
- Claude Code 要交接複雜邏輯給 GPT 前
- 任何 AI 輸出需要另一個 AI 繼續處理前

---

## 2. Non-Goals

- 不管理各 AI 的內部執行邏輯
- 不管理 AI 工具的帳號設定

---

## 3. AI 分工邊界（硬性規則）

| AI | 職責 | 禁止做的事 |
|----|------|----------|
| Claude（本 Project）| 策略討論、優先順序、J 點確認、架構方向 | 直接讀寫 repo、生成大量程式碼 |
| Claude Code | 讀寫 C:\AI_WorkDir\GitHub\、執行 Pre-flight、標準結構程式碼 | 複雜業務邏輯、架構決策 |
| GPT | 複雜業務邏輯生成（需收到完整 spec）| 自行掃描 repo 現況（幻覺風險高）|
| Gemini AI Studio | 技術驗證、repo 健康分析、大量程式碼理解 | 直接 commit 到 repo |

---

## 4. Claude → Claude Code 交接協議

**觸發：** Claude 完成架構討論，要 Claude Code 執行時

**Claude 必須提供（缺一 Claude Code 不得開始執行）：**

```
HANDOFF: Claude → Claude Code
==============================
Task:        [一句話說明任務]
Target Repo: [C:\AI_WorkDir\GitHub\repo-name]
Target Path: [具體目錄和檔案路徑]
Phase:       [Phase 0-6]
Action:      [建立/修改/刪除/移動]
Spec:        [完整規格，工程師看完能直接執行]
Success:     [可量化的成功標準]
Forbidden:   [不能做的事]
J-Point:     [需要哪個 J 點確認]
==============================
```

---

## 5. Claude Code → GPT 交接協議

**觸發：** Claude Code 遇到複雜業務邏輯，需要 GPT 生成時

**Claude Code 必須提供（缺一 GPT 不得開始生成）：**

```
HANDOFF: Claude Code → GPT
===========================
Function Signature:
  def [function_name]([params]) -> [return_type]:

Input Example:
  [具體輸入範例，含型別]

Output Example:
  [具體輸出範例，含型別]

Business Rule:
  [這個函數的業務邏輯規則，可量化]

Failure Condition:
  [什麼情況下應該拋出 exception 或回傳 error]

Constraint:
  [不能做的事，例如：不能修改全局狀態]

Context:
  [這個函數在系統中的角色，一句話]
===========================
```

**GPT 不得：**
- 自行假設 repo 的目錄結構
- 自行推論未提供的 API 介面
- 生成超出 spec 範圍的額外功能

---

## 6. 任何 AI → Gemini AI Studio 交接協議

**觸發：** 需要深度分析 repo 現況、驗證技術方案時

```
HANDOFF: → Gemini AI Studio
============================
Analysis Type: [repo健康分析 / 技術驗證 / 深度程式碼理解]
Target:        [repo名稱 或 程式碼片段]
Question:      [具體問題，可量化答案]
Context:       [必要的背景資訊]
Output Format: [期待的輸出格式，例如：JSON / Markdown 表格]
============================
```

**Gemini 輸出回來後：**
- 必須與 GitHub 實際狀態交叉驗證（不直接信任）
- 不得直接 commit Gemini 生成的程式碼，需經 Pre-flight

---

## 7. Token 節省規則

```
規則一｜不讓 AI 重新理解已知資訊
  錯誤：讓 GPT 重新掃描 repo 現況
  正確：Claude Code 掃描後，把結果直接傳給 GPT

規則二｜交接時只傳必要資訊
  錯誤：把整個對話歷史貼給下一個 AI
  正確：只傳 Handoff 格式中要求的欄位

規則三｜同樣的錯誤只試一次
  遇到 CI 失敗 → 先查 known_failures.md
  找到 → 套標準修法，不讓 AI 重新試錯

規則四｜AI 不讀 repo 就不猜
  GPT 不得在沒有收到 Claude Code 掃描結果的情況下描述 repo 現況
  任何「我推測...」「可能是...」→ 停止，要求提供真實資料
```

---

## 8. 交接前確認清單

```
□ 交接格式完整（§4 或 §5 所有欄位填寫）
□ Target Repo 路徑確認存在
□ Success 標準可量化（不是「完成就好」）
□ Forbidden 列出（防止 AI 過度發揮）
□ J 點要求明確
```

---

## 9. Failure Modes

| 症狀 | 原因 | 修法 |
|------|------|------|
| GPT 生成的程式碼和 repo 實際結構不符 | GPT 自行推論 repo | 要求 Claude Code 先掃描，傳真實結構給 GPT |
| Claude Code 重開後重複執行已完成步驟 | 沒有 Handoff 記錄 | 查最後一個 CHECKPOINT → 執行 SKILL-06 §5 |
| 同一個 CI 錯誤三個 AI 輪流試 | 沒查 known_failures | 先查 known_failures.md，找到直接套 |
| token 爆炸 | 把整個對話歷史貼給下一個 AI | 只傳 Handoff 格式必要欄位 |

---

## 10. Audit Requirements

每次 AI 交接記錄到 prospera-audit-ledger：
```
[日期] AI-HANDOFF: [來源AI] → [目標AI] [任務名稱] [交接格式完整性 OK/FAIL]
```

---

*v1.0 · 2026-05-19 · prospera-infra-ci/skills/*

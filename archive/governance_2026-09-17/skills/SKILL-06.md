<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:無機制驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# SKILL-06｜Multi-Step Task Checkpoint
## Document Header
- Document Type: Codex
- Version: v1.1
- Status: Approved
- Owner: prospera-infra-ci/skills/
- Governing Authority: prospera-engineering-codex v1.0
- DNA Reference: 要素八（AI 協作協議 + J 點系統）
- Last Updated: 2026-05-24

---

## 1. Identity & Scope

防止多步驟任務中斷後失去狀態，避免 AI 在無法描述當前狀態時繼續執行造成錯誤疊加（如 commit b61683d 誤刪 02_kernel）。

核心原則：AI 無法描述當前狀態 → 必須停止 → 不得繼續執行。

---

## 2. Non-Goals

- 不取代 git log 和 GitHub Actions 記錄
- 不管理 repo 間的依賴順序（→ prospera-global-inventory）

---

## 3. Checkpoint 標準格式

每完成一個重要步驟，AI 必須輸出以下格式：

```
CHECKPOINT [步驟編號/任務名稱]
================================
DONE:     [這個步驟完成了什麼，具體可驗證]
VERIFIED: [已驗證的事，例如：CI Green / yamllint pass / 檔案存在]
SKIPPED:  [跳過了什麼，原因是什麼]（沒有填「無」）
NEXT:     [下一個步驟是什麼]
STATE:    [當前系統狀態一句話，例如：prospera-infra-registry CI Green，00_governance 已統一小寫]
================================
```

**無法填寫 STATE → 必須停止，向人類確認當前狀態後才繼續。**

---

## 4. J 點觸發規則（DNA 要素八）

### J1｜需求確認
```
觸發：AI 完成需求理解後，開始執行前
格式：「我理解的任務是：[具體描述]。確認嗎？」
等待：人類書面確認
繼續：確認後才執行
```

### J2｜品質審閱
```
觸發：AI 完成交付物後，準備發布前
格式：列出完整交付物清單 + 每個交付物的驗證狀態
等待：人類審閱確認
繼續：確認後才 push 或 deploy
```

### J3｜執行確認（不可逆操作）
```
觸發：任何不可逆操作前
不可逆操作清單：
  - git push（影響 remote）
  - git revert（改寫歷史）
  - rm -rf（刪除檔案）
  - deploy（上線）
  - GitHub Secret 設定（影響所有 workflow）

格式：
J3 CONFIRMATION REQUIRED
=========================
即將執行：[操作描述]
影響範圍：[哪些 repo / 哪些檔案]
不可逆性：[執行後能否回復，如何回復]
=========================
確認執行？（需要人類明確回覆「確認」）
```

---

## 5. Claude Code 記憶清空後的重啟流程

當 Claude Code 重開視窗（記憶清空），必須依序執行：

```
Step 1｜重新定位當前路徑
  pwd
  ls C:\AI_WorkDir\GitHub\

Step 2｜讀取上次 Checkpoint
  查看最近對話中最後一個 CHECKPOINT 格式輸出
  或查 git log --oneline -5 [repo名稱]

Step 3｜確認系統狀態
  確認每個進行中 repo 的 CI 狀態
  Start-Process "https://ccktaiwan.github.io/prospera-global-inventory/dashboard/"

Step 4｜輸出重啟宣告
RESTART DECLARATION
===================
Last Known State: [從 Checkpoint 或 git log 重建]
Pending Tasks:    [還沒做完的事]
Starting From:    [從哪個步驟繼續]
===================

Step 5｜等待人類確認後才繼續執行
```

---

## 6. 高風險操作額外保護

以下操作除 J3 外，還需要額外確認：

| 操作 | 額外要求 |
|------|---------|
| 刪除任何 02_kernel/ 內容 | 先截圖目錄結構，列出將刪除的檔案清單，等確認 |
| 修改 .github/workflows/ | 先執行 SKILL-01 驗證，yamllint 通過才執行 |
| git revert | 列出 revert 的 commit hash 和影響，等確認 |
| 批量 git mv | 每個 repo 獨立 commit，不批量跨 repo 一次執行 |

---

## 7. Failure Modes

| 症狀 | 原因 | 修法 |
|------|------|------|
| 誤刪 artifacts | 沒有 J3 確認就執行 rm | git revert [commit hash] |
| 任務中斷後不知做到哪 | 沒有 Checkpoint 記錄 | 查 git log + dashboard 重建狀態 |
| Claude Code 重開後重複執行已完成步驟 | 沒有 Restart Declaration | 執行 §5 重啟流程 |
| 多 repo 操作後狀態混亂 | 批量操作沒有逐 repo commit | 每個 repo 獨立 commit + push |

---

## 8. Audit Requirements

每個 J 點確認記錄到 prospera-audit-ledger：
```
[日期] J[1/2/3]-CONFIRMED: [任務名稱] [操作描述] [確認者]
```

---

## 9. PHASE SUMMARY 後輸出 Human Report（SKILL-11）

每次輸出 PHASE SUMMARY 後，必須緊接輸出 SKILL-11 Human-Readable Execution Report。

```
觸發：PHASE SUMMARY 輸出完畢後，立即觸發
動作：依 SKILL-11 §3 標準格式輸出 HUMAN REPORT
目的：讓人類 30 秒內掌握任務結果，不需逐行讀 PHASE SUMMARY
```

詳細格式與範例 → SKILL-11.md

---

*v1.1 · 2026-05-24 · prospera-infra-ci/skills/*

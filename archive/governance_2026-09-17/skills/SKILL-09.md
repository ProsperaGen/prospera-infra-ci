<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:無機制驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# SKILL-09｜Repo Health Audit
## Document Header
- Document Type: Codex
- Version: v1.0
- Status: Approved
- Owner: prospera-infra-ci/skills/
- Governing Authority: prospera-engineering-codex v1.0
- DNA Reference: 要素六（Repo 六種類型）+ Repo 成熟度標準（Level 0-7）
- Last Updated: 2026-05-19

---

## 1. Identity & Scope

41 個 repo 的健康診斷、整併評估、Level 升級、99_archive 救援流程。
解決問題：閒置 repo 判斷、有價值程式碼埋在 archive、Level 停滯不升、重複功能 repo 並存。

**觸發條件：**
- 每週治理例行掃描
- 任何 repo Level 升級前
- 99_archive 救援任務開始前
- repo 整併決策前

---

## 2. Non-Goals

- 不管理 repo 內部程式碼品質（→ SKILL-04）
- 不做架構決策（→ 線一｜Prospera OS）

---

## 3. Repo 分類矩陣

| 類別 | 判斷標準 | 處理方式 |
|------|---------|---------|
| 核心 Active | 有真實程式碼 + CI Green + 近 30 天有 commit | 維持，持續升級 |
| 待升級 | CI Green 但 Level < 3 | 排進升級計畫 |
| 治理空殼 | 只有文件，無可執行程式碼 | 補程式碼或降為 Template |
| 重複功能 | 與其他 repo 職責重疊 80%+ | 整併評估 |
| 閒置 | 90 天以上無 commit + Level 0-1 | 封存（archive）或整併 |
| 救援候選 | 有有價值程式碼但目錄結構混亂 | 99_archive 救援流程 |

---

## 4. Level 升級前置條件（DNA Repo 成熟度標準）

| 目標 Level | 前置條件 | 驗收方式 |
|-----------|---------|---------|
| Level 1 | 本地 `python app.py` 或 `node index.js` 跑起來無 error | 截圖執行結果 |
| Level 2 | 有測試且全部通過，覆蓋率 > 60% | pytest / jest 輸出 |
| Level 3 | CI/CD 全綠（GitHub Actions 100% pass） | dashboard CI Green |
| Level 4 | 有真實用戶輸入輸出 + Authority Matrix + State Machine | 兩份文件存在 |
| Level 5 | 有 monitoring agent，能自動偵測異常 | agent 觸發記錄 |
| Level 6 | 有 self-healing 機制，能自動修正已知錯誤 | healing log |
| Level 7 | 能自我優化（需架構決策）| → Prospera OS |

---

## 5. 99_archive 救援流程

```
Step 1｜全量掃描
  Get-ChildItem C:\AI_WorkDir\GitHub\[repo]\99_archive -Recurse -File |
    Select-Object FullName, Length, LastWriteTime |
    Sort-Object Length -Descending

Step 2｜價值判斷（四問）
  Q1：這個檔案有可執行邏輯嗎？（不是只有設定或文件）
  Q2：這個邏輯在其他 repo 有對應位置嗎？
  Q3：這個邏輯現在還需要嗎？
  Q4：如果遺失，重新開發需要多少時間？
  → 三問以上 YES → 列入救援清單

Step 3｜移植前確認
  確認目標 repo 和目標目錄（查 SKILL-02 §4）
  確認不覆蓋現有功能

Step 4｜移植執行
  複製到目標位置（不刪除原始 archive）
  補 AI Header
  執行 SKILL-04 Pre-flight
  獨立 commit，message 格式：
  [P4][LN] rescue: move [檔名] from 99_archive to [目標路徑] (recovered value)

Step 5｜驗證
  本地執行確認功能正常
  更新 99_archive_救援分類清單_v1.0.md
```

---

## 6. Repo 整併評估流程

```
Step 1｜識別重複
  兩個 repo 的 README 和主要功能 80% 以上重疊

Step 2｜確認主線
  較新的 / 有更多真實程式碼的 / CI Green 的 → 主線 repo

Step 3｜J1 確認
  「我判斷 [repo-A] 應整併進 [repo-B]，原因：[說明]。確認嗎？」
  等待人工確認

Step 4｜整併執行
  把 repo-A 的有價值程式碼和文件移植到 repo-B
  repo-A 設為 GitHub Archived
  更新 prospera-global-inventory

Step 5｜更新 dashboard
  確認 scanner 不再掃描 archived repo
```

---

## 7. 已知整併候選（參考）

| Repo-A（候選整併） | Repo-B（主線）| 狀態 |
|------------------|-------------|------|
| prospera-execution-layer | prospera-os | 待評估 |
| prospera-os-system-design | prospera-os | 待評估 |
| prospera-governance-self-disclosure | prospera-constitution-governance | 待評估 |

---

## 8. Failure Modes

| 症狀 | 原因 | 修法 |
|------|------|------|
| Level 升級後 scanner 仍顯示舊 Level | GOVERNANCE_STATUS.md 未更新 | 更新 maturityLevel 欄位 + push |
| 救援的程式碼跑不起來 | 依賴路徑硬編碼 | 修正 import 路徑後重跑 |
| 整併後主線 CI 紅燈 | 移植的程式碼有衝突 | git revert 整併 commit，重新評估 |
| archive 掃描找不到有價值檔案 | 嵌套在多層目錄 | 用 -Recurse + 按 Length 排序 |

---

## 9. Audit Requirements

每次 repo 操作記錄到 prospera-audit-ledger：
```
[日期] REPO-AUDIT: [操作類型] [repo名稱] [Level前] → [Level後] [說明]
```

---

*v1.0 · 2026-05-19 · prospera-infra-ci/skills/*

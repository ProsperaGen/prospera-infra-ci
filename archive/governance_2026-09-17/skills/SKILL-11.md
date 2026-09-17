<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:doc | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:審計注入 | IP:創造性歸 Kevin(發明人) -->
# SKILL-11｜Self-Executing Plan 模式

**版本**: v1.1
**建立**: 2026-05-29
**觸發條件**: 任何多步驟任務開始前 / 人說「執行下一項」時
**存放位置**: prospera-infra-ci/skills/SKILL-11.md

---

## 核心原則

**所有多步驟任務必須寫成 EXECUTION_PLAN.md，不依賴人工複製貼上。**

- 人的工作：判斷、決策、說「執行下一項」
- Claude Code 的工作：讀 PLAN、執行指令、更新狀態、commit

產出臨時指令讓人複製貼上 = 錯誤模式，禁止。

---

## 1. EXECUTION_PLAN.md 標準格式

```markdown
# EXECUTION_PLAN_v{版本}.md
**Authority**: ccktaiwan
**Created**: {日期}
**Status**: ACTIVE
**SSOT**: {repo}/00_governance/EXECUTION_PLAN_v{版本}.md

## 使用方式
每次開新對話，說「執行 EXECUTION_PLAN_v{版本}.md 下一項」

## 執行前必做
（git pull + 讀 CURRENT_STATE.md 的 Python 指令）

### ITEM-{序號} — {標題}
**狀態**: [ ] 或 ✅ 或 ❌
**目標**: {一句話說明}
**前置條件**: {依賴哪個 ITEM，若無填「無」}

**執行指令**:
（可直接 exec 的完整 Python 程式碼區塊）

**驗證方式**:
（確認成功的指令或條件）

**完成標準**: {具體可量測的二元標準}

## 完成記錄
| Item | 標題 | 完成日期 | Commit |
|------|------|---------|--------|
```

---

## 2. 觸發方式

| 人說 | Claude Code 行為 |
|------|-----------------|
| 「執行下一項」 | 找第一個 `[ ]`，執行，更新為 `✅` |
| 「執行 ITEM-{N}」 | 直接執行指定 ITEM |
| 「跳過 ITEM-{N}」 | 標記為 `⏭️`，記錄原因 |
| 「重試 ITEM-{N}」 | 重新執行已失敗的 ITEM |

**Claude Code 執行流程**：
```
1. git pull（對應 repo）
2. 讀 EXECUTION_PLAN.md
3. 找第一個狀態為 [ ] 的 ITEM
4. 執行「執行指令」Python 程式碼
5. 執行「驗證方式」確認成功
6. 更新 ITEM 狀態為 ✅ + 填入日期和 commit hash
7. git add EXECUTION_PLAN.md + git commit + git push
8. 輸出 PHASE SUMMARY
```

---

## 3. PLAN 存放位置

| 類型 | 存放路徑 |
|------|---------|
| 生態系級 PLAN | `prospera-os/00_governance/EXECUTION_PLAN_v{N}.md` |
| 產品級 PLAN | `{repo}/00_governance/EXECUTION_PLAN.md` |
| 客戶交付 PLAN | `prospera-product-{x}/00_governance/CLIENT_PLAN.md` |

PLAN 必須 git tracked + push，不得存於本地未 push 的狀態。

---

## 4. 狀態追蹤規則

| 狀態符號 | 意義 |
|---------|------|
| `[ ]` | 待執行 |
| `✅` | 完成（含 commit hash）|
| `❌` | 失敗（含失敗原因，等待人工決策）|
| `⏭️` | 跳過（含跳過原因）|

完成後自動 commit 格式：
```
[OpsGov][PLAN] chore: ITEM-{N} complete — {標題}
# 設計: 依 Kevin 架構 ｜執行: AI 工具(claude.ai+Claude Code) ｜驗證: 無機制驗證 ｜IP: 創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032)
```

---

## 5. 失敗處理規則

**失敗時不跳過，不自動繼續。**

```
1. 捕獲完整錯誤訊息（traceback）
2. 將 ITEM 狀態改為 ❌
3. 在 ITEM 下方加入「失敗記錄」：
   失敗時間 / 錯誤訊息 / 已嘗試的修復方式
4. commit EXECUTION_PLAN.md（記錄失敗狀態）
5. 輸出 PHASE SUMMARY 說明原因
6. 停止，等待人工決策
```

---

## 6. J-IRREVERSIBLE 例外

以下操作即使在 PLAN 中，執行前仍需人工確認：

```
❌ GitHub Repository Archive
❌ rm -rf 無備份永久刪除
❌ 生產環境部署（Production deploy）
❌ 花錢操作（Stripe / API paid calls）
❌ 資料庫破壞性操作（DROP / TRUNCATE）
```

遇到 J-IRREVERSIBLE：輸出警告 → 列出具體操作 → 等待確認。

---

## 7. PLAN 設計原則

- 每個 ITEM 必須獨立可執行（不依賴對話記憶）
- 執行指令必須是完整 Python 程式碼（Claude Code 直接 exec）
- 驗證方式必須可量測（有具體成功條件，不是「看起來正常」）
- 前置條件必須明確（依賴哪個 ITEM 或哪個服務）
- 完成標準必須二元（pass/fail，不可模糊）
- 一個 ITEM 一件事（不要把五個步驟塞進一個 ITEM）

---

## 8. 視覺化產出規則

所有互動式圖表、架構圖、Dashboard HTML 必須同步儲存到 GitHub：

| 規則 | 說明 |
|------|------|
| **存放位置** | `{repo}/01_docs/charts/` 或 `{repo}/05_products/dashboard/` |
| **格式** | `.html` / `.svg` / `.json`（不接受截圖）|
| **commit 格式** | `[OpsGov][v3.0] docs: add {圖表名稱} visualization` |
| **禁止狀態** | 不得只存在 Claude 對話或本地未 push 的狀態 |

```python
# 生成圖表後立即 commit
import subprocess
repo_path = r"C:\AI_WorkDir\GitHub\{repo}"
subprocess.run(["git", "-C", repo_path, "add", "01_docs/charts/"], capture_output=True)
subprocess.run(["git", "-C", repo_path, "commit", "-m",
    "[OpsGov][v3.0] docs: add {name} visualization\n\nIP: 創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032)"],
    capture_output=True, text=True)
subprocess.run(["git", "-C", repo_path, "push"], capture_output=True, text=True)
```

---

## 適用時機

| 情境 | 使用 SKILL-11？ |
|------|---------------|
| 超過 3 個步驟的任務 | ✅ 必須 |
| 跨多個 repo 的操作 | ✅ 必須 |
| 需要分多次對話完成 | ✅ 必須 |
| 單一簡單指令 | ❌ 不需要 |
| 一次對話可完成的小修改 | ❌ 不需要 |

---

*SKILL-11 v1.1 · 2026-05-29 · prospera-infra-ci/skills/ · ccktaiwan*

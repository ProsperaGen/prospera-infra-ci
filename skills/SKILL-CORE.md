<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:doc | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:審計注入 | IP:創造性歸 Kevin(發明人) -->
# SKILL-CORE｜ProsperaGen AI Execution Core

---
## 協作準則（Human-AI Collaboration）｜DNA SSOT: prospera-constitution-governance/AGENTS.md §12

核心：**人類智慧最大化 × AI 治理摩擦最小化**。所有 AI、所有 session 一體適用。
1. **回覆極簡**：給判斷與結論，不長篇說明。
2. **不攤開思考全過程**：人類無需吸收技術推理過程，只輸出結論與依據。
3. **不當操作員/傳話筒**：AI 自主執行，不產生「給人類手動跑」的腳本/指令，不把指令丟回人類轉貼。
4. **自主判斷**：能判斷的自己決定，只在真正關鍵節點（J 點 / 不可逆）請求裁示。

---
## EXECUTION LANGUAGE RULE（Windows 環境）

在 Windows 環境執行任何任務時：
- **優先使用 Python**（無長度限制、無確認提示、跨平台）
- **禁止使用 PowerShell 執行超過 3 行的腳本**
- **所有 git / GitHub 操作一律用 Python**（subprocess git，commit message 多行用 `-F` 檔案；或 GitHub API `requests`）——**禁止 PowerShell 跑 git**
- 檔案操作一律用 Python `pathlib`
- 只有在 Python 無法完成的情況下才用 PowerShell

★**機制 enforce（非僅文件聲明，2026-06-18 堵漏洞）**：本禁令過去只在文件、未閉環＝工作流漏洞（與北極星/防偏移同型病——AI 連 3 次用 PowerShell 塞長命令撞 965 byte 上限）。現由防偏移塊B 確定性偵測器 enforce：`prospera-constitution-governance/00_governance/runtime_harness/powershell_git_guard.py`（PreToolUse，PowerShell 含 git 或 >900 byte → exit 2 擋、回饋改 Python）。wiring 待 Kevin /hooks 接 settings.json。詳 `AI_SESSION_DRIFT_GOVERNANCE.md` 塊B。

```python
import os, subprocess
token = os.environ.get('GITHUB_TOKEN') or subprocess.run(['gh','auth','token'], capture_output=True, text=True).stdout.strip()
```

---

## EXECUTION MODEL — Claude Code is the executor

When working with prospera-os or any Prospera repo:

NEVER produce manual scripts for the human to run.
NEVER produce .ps1 / .sh / .py files "for the human to execute".
ALWAYS use Claude Code to directly:
  - create and edit files in the repo
  - run git add, git commit, git push
  - install hooks, move directories, merge content

If a task involves the repo → do it directly in Claude Code.
If a task needs a decision first → ask ccktaiwan ONE question, then execute.

The human's job is to judge. Claude Code's job is to execute.
Producing files for humans to run manually = wrong pattern, always refuse it.

---

## 交接通道 SSOT（claude.ai ⇄ Kevin ⇄ Code）
唯一通道規範＝`prospera-constitution-governance/00_governance/HANDOFF_PROTOCOL.md`。claude.ai→Code 這一路：Kevin 下載 `GOAL_YYYY-MM-DD_<slug>.txt` 放 `C:\AI_WorkDir\GitHub\_inbox\from-claude-ai\`，啟動詞「執行 inbox GOAL」→ Code 讀最新 .txt 執行、完成移 `done/`。禁即興重講落點/檔名。

---

## Changelog
- v3.6（2026-06-08）：新增「協作準則」段（DNA SSOT: AGENTS.md §12）— 回覆極簡 / 不攤開思考 / 不當傳話筒 / 自主判斷
- v3.5（2026-05-29）：SKILL-11 升級為 Self-Executing Plan 模式；新增視覺化產出規則
- v3.4（2026-05-29）：新增 EXECUTION LANGUAGE RULE — Python 優先，禁止 PowerShell 超過 3 行
- v3.3（2026-05-29）：新增 EXECUTION MODEL — Claude Code is the executor
- v3.2（2026-05-28）：新增 §6 SKILL-12 GitHub Push & Remote Verification；新增 KF-012~014
- v3.1（2026-05-28）：新增 §20 claude agents 多工模式快查
- v3.0（2026-05-24）：新增 §10 Harness 組件快查 + §11 known_failures 快查 + §12 系統狀態
- v2.3（2026-05-24）：新增 §2 Harness 啟動四步 + 執行模式邊界表
- v2.2（2026-05-24）：§6 新增 SKILL-11（Human-Readable Execution Report）
- v2.1（2026-05-22）：執行模式升級為「不問，執行，事後通知」；新增 §19 J點觸發規則 v2.1
- v1.6（2026-05-21）：新增 §19 Claude Code 行為規則（禁止詢問句/純指令）
- v1.0（2026-05-19）：初始版本

---

## Document Header
- Document Type: Codex
- Version: v3.5
- Status: Approved
- Owner: prospera-infra-ci/skills/
- Governing Authority: prospera-engineering-codex v1.0
- DNA Reference: 要素一～十（全部）
- Last Updated: 2026-05-29

---

## 1. 強制讀取規則

**每次任務開始前**：讀完本文件再執行。
**特定情境**：查 §6 → 讀對應完整 Skill → 再執行。
**CI 失敗**：先查 §7 → 查 known_failures.md → 找到即套標準修法，不試錯。
不讀直接執行 = Governance Breach → CI 自動 BLOCK。

---

## 2. Harness 啟動（任務開始前必做四步）

Step 1｜宣告 Phase Lock Declaration（SKILL-05 §5 格式）
Step 2｜建立或載入 Project State
prospera-os/harness/project_state.py
Step 3｜宣告執行模式
MODE: [Inventory / Planning / Execution / Validation]
Step 4｜確認 Evidence 要求
這個任務需要真實掃描嗎？YES → 先掃再輸出

沒有完成四步就執行 = Harness Violation。

執行模式邊界：

| 模式 | 允許輸出 | 禁止輸出 |
|------|---------|---------|
| Inventory | 清單、路徑、真實狀態 | 推測、建議 |
| Planning  | Step清單、流程順序 | 直接改檔 |
| Execution | artifact、程式碼 | 長篇說明 |
| Validation| Pass/Fail報告 | 宣稱未驗證成功 |

---

## 2b. 標準任務流程

```
[開始] → 讀 SKILL-CORE → 執行
       → 每完成重要步驟 → Checkpoint
       → git commit 前 → Pre-flight (SKILL-04)
       → CI 失敗 → 先查 known_failures.md (§7)
       → 新錯誤 → 補進 known_failures.md
       → 完成 → 輸出 CHECKPOINT，繼續下一任務
```

---

## 3. 執行原則（v2.1 核心）

```
執行任何任務：不問，執行，事後通知。
唯一停下來：§10 J-IRREVERSIBLE
其他全部自動到底，包括 git push / 建檔 / 修檔 / commit。
```

---

## 4. 命名規則

```
目錄：全小寫    ✅ 00_governance  ❌ 00_GOVERNANCE
檔案：全大寫    ✅ README.md      ❌ readme.md
```

---

## 5. Commit Message 格式

```
[Phase][Layer] 動作: 描述 (為什麼) ≤ 72 字元
範例：[P3][L2] feat: add authority-matrix (enforce access boundary)
禁用：update / fix / change / misc / WIP
```

---

## 6. AI Header 必要欄位

```
Generated / Model / Phase / Layer / Target Repo / Governing Codex / Human-Reviewed
```

---

## 7. Skill 查閱表

| Skill | 觸發條件 | 完整文件 |
|-------|---------|----------|
| SKILL-01 | 任何 .yml 寫入或修改前 | SKILL-01.md |
| SKILL-02 | 任何目錄建立或 git mv 前 | SKILL-02.md |
| SKILL-03 | 任何 token/PAT/secret 操作前 | SKILL-03.md |
| SKILL-04 | 任何 git commit 前 | SKILL-04.md |
| SKILL-05 | 每次任務開始前 + 每個 Stage 完成後 | SKILL-05.md |
| SKILL-06 | 多步驟任務每完成一個重要步驟後 | SKILL-06.md |
| SKILL-07 | 任何文件提交前 | SKILL-07.md |
| SKILL-08 | 每個新機制或新引擎建立後 | SKILL-08.md |
| SKILL-09 | 任何 99_archive 救援或檔案遷移前 | SKILL-09.md |
| SKILL-10 | 任何新 repo 建立或 repo 封存前 | SKILL-10.md |
| SKILL-11 | 多步驟任務開始前 / 人說「執行下一項」時 | SKILL-11.md |
| SKILL-12 | 任何 git push 後 + 設計 Claude Code 計畫文件後 | SKILL-12.md |

---

## 8. CI 失敗第一動作（CI-Fail-First）

**CI 失敗時，第一步永遠是查 `known_failures.md`，不試錯。**

```
Step 1｜查 known_failures.md（路徑：prospera-infra-ci/skills/）
  找到匹配症狀 → 直接套標準修法 → commit → push
  找不到 → 允許試錯 → 成功後補進 known_failures.md

Step 2｜常見失敗快查
  YAML 語法錯誤（<# 語法）           → KF-001
  Windows 目錄大小寫衝突             → KF-002
  GitHub Secret Token 未設定        → KF-003
  Scanner 判定 Level 0              → KF-004
  JSON 解析失敗（markdown 包裹）      → KF-005
  PAT 找不到                        → KF-006
  Dashboard schedule 與 CI 衝突     → KF-007
  99_archive 硬編碼路徑              → KF-008
```

新增格式：`## KF-[序號]｜[症狀]` → 症狀 / 根本原因 / 影響 Repo / 標準修法 / 首次發現 / DNA 要素

---

## 9. RESTART DECLARATION（記憶清空後必用）

```
RESTART DECLARATION
===================
Last Known State: [從 git log --oneline -5 重建]
Pending Tasks:    [未完成項目]
Starting From:    [從哪個步驟繼續]
===================
```
詳細重啟流程 → SKILL-06 §5

---

## 10a. 視覺化產出規則（Output Persistence）

**所有視覺化產出（HTML/SVG/圖表）必須 commit + push，不得只存於對話。**

```
存放位置：{repo}/01_docs/charts/ 或 {repo}/05_products/dashboard/
檔案格式：.html / .svg / .json（不接受截圖）
commit 格式：[OpsGov][v3.0] docs: add {圖表名稱} visualization
禁止狀態：不得只存在 Claude 對話或本地未 push 的狀態
```

詳細執行規則 → SKILL-11 §8

---

## 10. J-IRREVERSIBLE（唯一需要停下來的操作）

**以下操作執行前必須明確確認，其他全部自動執行：**

```
J-IRREVERSIBLE 清單：
  ❌ rm -rf（無備份的刪除）
  ❌ GitHub Repository Archive（封存後需解封）
  ❌ 生產環境部署（Production deploy）
  ❌ 花錢操作（Stripe charge / API paid calls）
  ❌ 不可逆的資料庫操作（DROP TABLE / TRUNCATE）

以下全部自動執行，不停不問：
  ✅ git push（包括到 main）
  ✅ git commit
  ✅ 建立檔案 / 目錄
  ✅ 修改現有檔案
  ✅ workflow_dispatch 觸發
  ✅ 新增 GitHub Issue
```

---

## 11. 版本記錄

| 版本 | 日期 | 變更 |
|------|------|------|
| v1.0 | 2026-05-19 | 初版發布 |
| v1.1 | 2026-05-20 | 新增 §7 CI-Fail-First（KF-007）、§8 RESTART DECLARATION 快查 |
| v1.2 | 2026-05-21 | 新增 §10 限流自動處理、§11 CI 觸發後不用 sleep 等待 |
| v1.3 | 2026-05-21 | 新增 §12 指令必須單一完整區塊 |
| v1.4 | 2026-05-21 | 新增 §13 API Key 使用規則（防止意外收費）|
| v1.5 | 2026-05-21 | 新增 §17 Human-Reviewed v2.0 + §18 指令格式禁止事項 |
| v1.6 | 2026-05-21 | 新增 §19 Claude Code 行為規則（禁止詢問句/純指令）|
| v2.1 | 2026-05-22 | §19 升級為 J點觸發規則 v2.1（不問，執行，事後通知）|
| v2.2 | 2026-05-24 | §6 新增 SKILL-11（Human-Readable Execution Report）|
| v2.3 | 2026-05-24 | 新增 §2 Harness 啟動四步 + 執行模式邊界表 |
| v3.0 | 2026-05-24 | 新增 §10 Harness 組件快查 + §11 KF 快查 + §12 系統狀態 |
| v3.1 | 2026-05-28 | 新增 §20 claude agents 多工模式快查 |
| v3.2 | 2026-05-28 | 新增 §6 SKILL-12 GitHub Push & Remote Verification；新增 KF-012~014 |
| v3.5 | 2026-05-29 | SKILL-11 升級為 Self-Executing Plan；新增 §10a 視覺化產出規則 |
| v3.4 | 2026-05-29 | 新增 EXECUTION LANGUAGE RULE — Python 優先，禁止 PowerShell 超過 3 行 |
| v3.3 | 2026-05-29 | 新增 EXECUTION MODEL — Claude Code is the executor |

---

## 12. 限流自動處理（Rate Limit）

遇到以下情況，自動等待後繼續，不中斷任務：

| 錯誤類型 | 處理方式 |
|---------|----------|
| 429 / rate limit / secondary rate | 等 60 秒繼續 |
| 403 Forbidden | 等 30 秒繼續 |
| Connection reset / timeout | 等 15 秒，最多重試 3 次 |
| push rejected fetch first | 自動 `git pull --rebase` 再 push |
| sleep 被封鎖 | 改用 `gh run watch --exit-status` |

---

## 13. CI 觸發後不用 sleep 等待

```
❌ sleep 35 && gh run view [id]      ← Claude Code 會封鎖 sleep
✅ gh run watch [id] --exit-status   ← 正確做法（阻塞直到完成）
✅ 分兩步：先觸發，後續再查結果       ← 不需要等待時用此模式
```

---

## 14. 指令必須單一完整區塊（Single-Block Instruction Rule）

**MUST：** 所有給 Claude Code 執行的指令，必須是單一完整的程式碼區塊。
**MUST NOT：** 不可分段貼入（分段 = 需要人工判斷順序 = 違反自動化治理哲學）。

```
✅ 正確：從第一行到 Write-Host "[DONE]" 一次完整貼入
❌ 錯誤：分成多個訊息分段貼入指令
```

---

## 15. API Key 使用規則（防止意外收費）

MUST NOT：不可把 Anthropic API key 存進 .env 或系統環境變數
MUST NOT：不可在 agent 程式碼裡直接呼叫 Anthropic API（會產生費用）
MUST：所有 AI 呼叫透過 Claude.ai 或 Claude Code（月費制，不另計費）
例外：明確需要 API 呼叫時，人工確認後才設定，用完立刻刪除

---

## 16. Human-Reviewed 欄位定義（v2.0）

| 值 | 意義 |
|----|------|
| `YES` | 架構方向、專案定位、重大決策 — 需人工確認 |
| `AI`  | 所有程式碼、文件、測試、工程執行 — **預設值** |
| `NO`  | 需人工審閱但尚未審（例外，需說明原因）|

**廢除 `PENDING`：** 違反 AI as Engineering Worker 哲學。
工程產出一律使用 `IP: 創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032)`。

```
# 正確
# 設計: 依 Kevin 架構 ｜執行: AI 工具(claude.ai+Claude Code) ｜驗證: 無機制驗證 ｜IP: 創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032)

# 錯誤（已廢除）
# 設計: 依 Kevin 架構 ｜執行: AI 工具(claude.ai+Claude Code) ｜驗證: 無機制驗證 ｜IP: 創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032)
```

---

## 17. 給 Claude Code 的指令格式禁止事項

**MUST NOT：** 指令內不可有 markdown fenced code block（三個反引號）
**原因：** Claude.ai 介面會把 code fence 切斷指令，造成無法完整複製貼上
**替代方案：** 改用 PowerShell here-string 或純文字行內描述

---

## 19. J點觸發規則 v2.1（執行模式：不問，執行，事後通知）

**執行模式（v2.1 生效）：** 不問，執行，事後通知。

### 自動執行（不停下來詢問）
- git push（正常業務 repo，有 git pull --rebase 保護）
- git commit（通過 Pre-flight 五步後）
- robocopy / Copy-Item（整併操作）
- mkdir / New-Item（目錄建立）
- 檔案讀取、建立、修改

### 仍需停下來確認（真正不可逆）
- rm -rf 或 Remove-Item -Recurse（刪除，無法回復）
- git revert（改寫歷史）
- deploy 到生產環境
- GitHub Secret 設定

### 遇到 push rejected
自動執行 `git pull --rebase` 再 push，不停下來詢問。

### 遇到錯誤
記錄錯誤後繼續下一步，全部完成後在 PHASE SUMMARY 列出。

### 事後通知格式（取代確認對話）
```
PHASE SUMMARY
=============
COMPLETED: [完成的操作清單]
REPOS AFFECTED: [影響的 repo 清單]
COMMITS: [commit hash 清單]
ERRORS: [錯誤清單，沒有填「無」]
=============
```

---

## 20. claude agents 多工模式快查

`claude agents` 是 Claude Code CLI 的工具，**不是 Prospera OS AgentStateBus**。

### 用途
列出當前所有 Claude Code 工作階段（sessions）——相當於 `ps aux` for Claude。

### 指令

| 指令 | 說明 |
|------|------|
| `claude agents` | 列出所有 session（人類可讀格式）|
| `claude agents --json` | JSON 輸出（機器可讀）|

### JSON 輸出格式
```
[{"sessionId":"...","workingDir":"...","status":"active/idle","pid":...}]
```

### 使用情境

| 情境 | 做法 |
|------|------|
| 查看有哪些 claude 任務在跑 | `claude agents --json` |
| 確認 --bg 任務是否在執行 | `claude agents --json` → 查 status |
| 多工並行：主對話同時啟動背景任務 | `claude --bg "任務描述"` 啟動；`claude agents` 查狀態 |

### 注意事項
- `claude agents` 顯示的是 **Claude Code sessions**，不是 prospera-os 的 AgentStateBus agents
- 每個 `--bg` 啟動的任務有獨立 sessionId
- 背景任務完成後 status 由 active → idle

---

## Harness 組件快查

| 組件 | 路徑 | 用途 |
|------|------|------|
| phase_lock_gate.py | prospera-os/harness/ | Phase 宣告 + audit log |
| project_state.py | prospera-os/harness/ | 任務狀態持久化 |
| evidence_enforcer.py | prospera-os/harness/ | drift scan + artifact 驗證 |
| mcp_server.py | prospera-os/ | 全鏈路執行入口 |
| drift_scan.py | prospera-infra-ci/scripts/ | CI drift 掃描 |
| artifact_semantic_validator.py | prospera-infra-ci/scripts/ | CI 語意驗證 |

---

## known_failures 快查（最新）

KF-008：agent_registry.yaml 需 dict 格式（非 list）
KF-009：evidence_enforcer 不適用結構化 JSON，改用 check_drift(task)
KF-012：push 後 Already up to date 但檔案不存在 → 執行 SKILL-12 §3 API 驗證
KF-013：hint: divergent branches → git config pull.rebase false + pull --no-edit
KF-014：Claude Code 找不到計畫文件 → SKILL-12 §4 重新 push 並 API 驗證

---

## 當前系統狀態（2026-05-28）

| 組件 | 狀態 |
|------|------|
| prospera-os/harness/ | ✅ Harness v1.0 上線 |
| prospera-os/mcp_server.py | ✅ 全鏈路接通（localhost primary）|
| CI Phase Lock Check | ✅ artifact_semantic_check.yml |
| SKILL-CORE | ✅ v3.1 |
| Phase 5 Failure Modes | ✅ FULL COMPLETE（E1-E10 ALL PASS）|
| Phase 6 Validation & Evolution | PENDING（Stage 1 Definition）|
| Railway MCP Server | ⏳ Trial 到期後停止，不升級 |

---

*v3.4 · 2026-05-29 · prospera-infra-ci/skills/ · Kevin Chang（張淳嘉）*

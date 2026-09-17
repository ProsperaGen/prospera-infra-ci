<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:doc | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:審計注入 | IP:創造性歸 Kevin(發明人) -->
# SKILL-04｜Commit Pre-flight
## Document Header
- Document Type: Codex
- Version: v1.0
- Status: Approved
- Owner: prospera-infra-ci/skills/
- Governing Authority: prospera-engineering-codex v1.0
- DNA Reference: 要素四（Commit 四標準）+ 要素九（AI Header）+ 快速參考卡第三組
- Last Updated: 2026-05-19

---

## 1. Identity & Scope

所有 `git commit` 前的強制驗證流程。
解決問題：CI 失敗、AI Header 缺失、Commit Message 格式錯誤、路徑不符規範。
這一層在本地攔截，不消耗 GitHub Actions 分鐘數和 CI token。

**觸發條件：** 任何 `git commit` 前，無例外，無豁免。

---

## 2. Non-Goals

- 不取代 CI/CD（CI 是第二道防線，Pre-flight 是第一道）
- 不管理 workflow 語法（→ SKILL-01）
- 不管理目錄結構（→ SKILL-02）

---

## 3. Pre-flight 清單（依序執行，任一失敗即停止）

```
□ Step 1｜語法驗證
□ Step 2｜AI Header 完整性
□ Step 3｜Commit Message 格式
□ Step 4｜Extended Description 存在
□ Step 5｜Path & Filename 正確
```

**所有 Step 通過 → 允許 commit**
**任何 Step 失敗 → 停止，修完，重跑全部 Pre-flight**

---

## 4. Step 詳細規則

### Step 1｜語法驗證

```bash
# Python 檔案
python -m py_compile [target.py]
→ 有 SyntaxError → 修完再繼續

# YAML 檔案（特別是 .github/workflows/）
yamllint [target.yml]
→ errors > 0 → 修完再繼續（詳見 SKILL-01）

# JSON 檔案
python -c "import json; json.load(open('[target.json]'))"
→ JSONDecodeError → 修完再繼續
```

### Step 2｜AI Header 完整性

所有 AI 生成的文件或程式碼必須包含以下標頭，缺任何欄位即不合格：

```
# ══════════════════════════════════════
# AI-GENERATED DOCUMENT
# ══════════════════════════════════════
# Generated:        [ISO 8601 timestamp]
# Model:            [model name + version]
# Phase:            [Phase 0-6]
# Layer:            [L1-L5 or ProsperaGen]
# Target Repo:      [repo name]
# Governing Codex:  prospera-engineering-codex v1.0
# 設計: 依 Kevin 架構 ｜執行: AI 工具(claude.ai+Claude Code) ｜驗證: 無機制驗證 ｜IP: 創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032)
# Review By:        [reviewer name or PENDING]
# Review Date:      [ISO 8601 or PENDING]
# ══════════════════════════════════════
```

**Human-Reviewed 規則：**
- `NO` → 可 commit，但 CI 會標記，不得 deploy 到 production
- `PENDING` → 必須在 48 小時內完成審閱
- 偽造 Header = Governance Breach，最高嚴重等級

### Step 3｜Commit Message 格式

```
格式：[Phase][Layer] 動作: 描述 (為什麼)
長度：≤ 72 字元

✅ 合格範例：
[P3][L2] feat: add authority-matrix (enforce access boundary)
[P1][CI] fix: replace invalid PS comment with YAML disabled stub
[P0][L1] chore: add GOVERNANCE_STATUS.md (scanner Level declaration)

❌ 禁用動詞（太模糊，必須更具體）：
update / fix（沒說修什麼）/ change / misc / WIP / temp / test

❌ 缺少 Phase 或 Layer 標記：
feat: add something
```

### Step 4｜Extended Description 存在

git commit -m 後必須有 body，包含以下四項：

```
這個 commit 在系統中的角色：[說明]
影響範圍：[哪些 repo / 哪些層]
關聯 Issue / Phase：[Issue # 或 Phase N]
Human-Reviewed：[YES / NO / PENDING]
```

PowerShell 多行 commit 寫法：
```powershell
git commit -m "[P3][L2] feat: add authority-matrix (enforce access boundary)" `
  -m "角色：定義 prospera-infra-registry 的存取權限邊界" `
  -m "影響範圍：prospera-infra-registry L2 / 依賴方：prospera-api-gateway" `
  -m "關聯 Issue：#42 / Phase：3" `
  -m "Human-Reviewed：PENDING"
```

### Step 5｜Path & Filename 正確

```
目錄：全小寫
  ✅ 00_governance/
  ❌ 00_GOVERNANCE/

檔案：全大寫（含底線）
  ✅ GOVERNANCE_STATUS.md
  ❌ governance_status.md

路徑格式：[layer]/[repo-type]/[filename].[ext]
  ✅ l1-kernel/governance/AUTHORITY-MATRIX-v1.md
  ❌ L1_Kernel/Governance/authority-matrix.md
```

---

## 5. Matrix

| 情境 | Step 重點 | 常見錯誤 |
|------|---------|---------|
| Python 程式碼 commit | Step 1（py_compile）+ Step 2（AI Header）| import 路徑錯、Header 缺欄位 |
| YAML workflow commit | Step 1（yamllint）| `<#` 語法、縮排錯 |
| 文件 commit | Step 2（Header）+ Step 4（Description）| Header 缺 Phase/Layer |
| 緊急修復 commit | 全部 5 步仍需執行 | 緊急不是跳過的理由 |

---

## 6. Pre-flight 快速執行腳本

> ⚠️ DEPRECATED（2026-06-06）：以下 preflight.ps1 已廢棄。
> 違反 SKILL-CORE EXECUTION MODEL：「禁止 PowerShell 超過 3 行」「NEVER produce .ps1 for the human」。
> 正確 preflight 鏈路：SKILL-CORE §1 強制讀取 → §2 Harness 四步（prospera-os/harness/*.py）→ entrypoint.md → system_index.yaml v3.0。

```powershell
# 存到 C:\AI_WorkDir\GitHub\preflight.ps1
param([string]$TargetFile)

$pass = $true

# Step 1: 語法
if ($TargetFile -match "\.py$") {
  python -m py_compile $TargetFile
  if ($LASTEXITCODE -ne 0) { Write-Host "❌ Step 1 FAIL: py_compile"; $pass = $false }
}
if ($TargetFile -match "\.yml$") {
  yamllint $TargetFile
  if ($LASTEXITCODE -ne 0) { Write-Host "❌ Step 1 FAIL: yamllint"; $pass = $false }
}

# Step 2: AI Header
$content = Get-Content $TargetFile -Raw
if ($content -notmatch "AI-GENERATED DOCUMENT") {
  Write-Host "❌ Step 2 FAIL: AI Header missing"
  $pass = $false
} elseif ($content -notmatch "Human-Reviewed:") {
  Write-Host "❌ Step 2 FAIL: Human-Reviewed field missing"
  $pass = $false
}

if ($pass) { Write-Host "✅ Pre-flight PASS - 允許 commit" }
else { Write-Host "🚫 Pre-flight FAIL - 修完再 commit" }
```

---

## 7. Failure Modes

| 症狀 | 原因 | 修法 |
|------|------|------|
| CI 失敗但本地沒跑 Pre-flight | 跳過 Pre-flight | 補執行，修正後再 push |
| Commit message 被 Guard BLOCK | 格式不符 | 重寫 message，格式見 Step 3 |
| IP: 創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032) 進入 production | 審閱流程缺失 | revert，補審閱後重新 commit |
| Extended Description 空白 | Step 4 跳過 | git commit --amend 補寫 |

---

## 8. Audit Requirements

Pre-flight 失敗記錄到 prospera-audit-ledger：
```
[日期] PREFLIGHT-FAIL: [repo] [檔名] [失敗的 Step] [原因]
```

---

*v1.0 · 2026-05-19 · prospera-infra-ci/skills/*

---

## 九、自動決策規則（2026-05-29 補充）

以下情況 AI 自動執行，不等待人工確認：

| 情況 | 自動決策 |
|------|---------|
| 同名檔案多版本衝突 | 選最大 bytes 版本（內容最完整） |
| CI 失敗 | 查 known_failures.md，有解自動套用 |
| 文件類 commit（Phase 0，.md 文件）| 直接 push，不需 J3 |
| Downloads 重複檔案（帶 (1)(2) 後綴）| commit 完成後自動刪除舊版 |
| SVG / 互動式圖表文件 | 完成後自動 commit + push 到對應 repo |

以下情況必須等待 J3 人工確認：

| 情況 | 原因 |
|------|------|
| 程式碼類 commit（Phase 2+）| 可能影響執行邏輯 |
| 不可逆操作（刪除、merge、deploy）| 損失無法恢復 |
| 架構決策（新引擎、新機制）| 需要 Kevin 確認方向 |
| 跨 repo 影響 | 影響範圍超過單一 repo |

原則：人只在「不可逆」和「架構決策」時介入，其他全部 AI 自動執行 + 事後回報。

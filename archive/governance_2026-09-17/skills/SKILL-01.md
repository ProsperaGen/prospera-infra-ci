<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:無機制驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# SKILL-01｜YAML Workflow Guard
## Document Header
- Document Type: Codex
- Version: v1.0
- Status: Approved
- Owner: prospera-infra-ci/skills/
- Governing Authority: prospera-engineering-codex v1.0
- DNA Reference: 要素四（Commit 四標準）+ 要素五（可工程實作）
- Last Updated: 2026-05-19

---

## 1. Identity & Scope

管理所有 `.github/workflows/*.yml` 的寫入、修改、停用流程。
解決問題：GPT 用 PowerShell `<# ... #>` 語法寫 YAML，導致 CI 100% 失敗，在多個 repo 重複出現。

**觸發條件：** 任何 `.github/workflows/*.yml` 寫入或修改前，無例外。

---

## 2. Non-Goals

- 不管理 workflow 的業務邏輯設計（→ 各 repo 負責人）
- 不管理 GitHub Actions 的 Secret 設定（→ SKILL-03）

---

## 3. Rules & Constraints

### 3.1 絕對禁止（MUST NOT）

```
❌ PowerShell 多行註解包裹 YAML 內容
<#
  任何內容
#>

❌ PowerShell 單行假停用
<# DISABLED #>
name: Something
on:
  push:

❌ 有效 trigger 但 jobs 區塊為空
on:
  push:
jobs:
  （空白）

❌ 未經 yamllint 驗證就 commit
```

### 3.2 停用 Workflow 唯一標準模板（MUST 使用此格式，不得自創）

```yaml
# DISABLED [日期] - [原因，例如：unified under prospera_guard.yml]
name: [原名稱] (Disabled)
on:
  workflow_dispatch:
jobs:
  disabled:
    runs-on: ubuntu-latest
    steps:
      - run: echo "This workflow is disabled"
```

### 3.3 Active Workflow 最小合法結構

```yaml
name: [名稱]
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  [job-name]:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: [步驟名稱]
        run: [指令]
```

---

## 4. 執行前驗證步驟（依序，失敗即停止）

```
Step 1｜掃描 <# 字串
  grep -rn "<#" .github/workflows/
  → 任何結果 → 立即換成停用模板，不得保留任何 <# 字串

Step 2｜yamllint 本地驗證
  pip install yamllint -q
  yamllint .github/workflows/[目標檔名].yml
  → errors > 0 → 依錯誤訊息修正，重跑直到 0 errors

Step 3｜邏輯一致性確認
  確認 on: 中的 trigger 與 jobs 中的邏輯一致
  → on: push 但無實質 job → 改成停用模板或補真實 job

Step 4｜Checkout token 確認（私有 repo）
  凡是 private repo 的 workflow 使用 actions/checkout
  → 必須加 with: token: ${{ secrets.PROSPERA_DASHBOARD_TOKEN }}
  → 缺少 → 補上（詳見 SKILL-03）
```

---

## 5. Matrix

| 情境 | 操作 | 使用模板 |
|------|------|---------|
| 停用舊 workflow | 換成停用模板 | §3.2 |
| 建新 active workflow | 從最小合法結構開始 | §3.3 |
| 修改現有 workflow | yamllint 驗證後再 commit | §4 Step 2 |
| CI 100% 失敗 | 先查 known_failures KF-001 | known_failures.md |

---

## 6. 批量修復指令（多個 repo 同時有壞 workflow）

```powershell
# 批量替換所有含 <# 的 workflow 為停用模板
$repos = @("prospera-constitution-governance", "prospera-engineering-codex",
           "prospera-engine-generation", "prospera-infra-ci")

$template = @'
# DISABLED 2026-05-19 - unified under prospera_guard.yml
name: PLACEHOLDER (Disabled)
on:
  workflow_dispatch:
jobs:
  disabled:
    runs-on: ubuntu-latest
    steps:
      - run: echo "This workflow is disabled"
'@

foreach ($repo in $repos) {
  $path = "C:\AI_WorkDir\GitHub\$repo\.github\workflows"
  Get-ChildItem $path -Filter "*.yml" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match "<#") {
      $name = $_.BaseName
      ($template -replace 'PLACEHOLDER', $name) |
        Out-File $_.FullName -Encoding utf8 -NoNewline
      Write-Host "Fixed: $repo/$($_.Name)"
    }
  }
  cd "C:\AI_WorkDir\GitHub\$repo"
  git add .github\workflows\
  git commit -m "[P1][CI] fix: replace invalid PS comment syntax with valid YAML disabled stubs"
  git push
}
```

---

## 7. Failure Modes

| 症狀 | 根本原因 | 標準修法 |
|------|---------|---------|
| `line N: could not find expected ':'` | `<#` PS 語法 | 換停用模板 |
| `mapping values are not allowed` | YAML 縮排錯誤 | yamllint 定位修正 |
| `could not find expected ':'` | 冒號後缺空格 | 全文搜尋 `:` 補空格 |
| `Input required and not supplied: token` | Secret 未設定 | → SKILL-03 |
| CI 100% fail 但本地 yamllint 通過 | trigger 邏輯問題 | 確認 on/jobs 一致性 |

---

## 8. Audit Requirements

每次修復壞 workflow 記錄到 prospera-audit-ledger：
```
[日期] YAML-FIX: [repo名稱] [修復的檔名] [根本原因] KF-001
```

---

*v1.0 · 2026-05-19 · prospera-infra-ci/skills/*

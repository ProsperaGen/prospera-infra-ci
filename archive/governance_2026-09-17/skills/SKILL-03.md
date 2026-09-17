<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:無機制驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# SKILL-03｜Secret & Credential Guard
## Document Header
- Document Type: Codex
- Version: v1.0
- Status: Approved
- Owner: prospera-infra-ci/skills/
- Governing Authority: prospera-engineering-codex v1.0
- DNA Reference: 要素八（AI 協作協議）
- Last Updated: 2026-05-19

---

## 1. Identity & Scope

管理所有 GitHub PAT、API Token、Secret 的建立、存放、設定、更新流程。
解決問題：PAT 找不到存在哪裡、token 90 天過期失效、同一 PAT 要設定多 repo 但流程不一致。

---

## 2. Non-Goals

- 不管理應用層 API Key（如 Anthropic API Key）→ 存放在各 repo .env
- 不管理 SSH Key

---

## 3. Rules & Constraints

### 3.1 PAT 本地存放規則（MUST）

```
固定路徑：C:\AI_WorkDir\prospera-credentials.md
格式：
# Prospera Credentials
## GitHub PAT
- Name: prospera-dashboard-classic
- Value: ghp_xxxx
- Expiry: 2027-08-05
- Scope: repo, workflow
- Used in: prospera-global-inventory, prospera-governance-dashboard
- Last Updated: 2026-05-19
```

**任何新 PAT 產生後，第一件事是寫進這個檔案，不得跳過。**

### 3.2 PAT 產生流程（MUST）

```
Step 1｜前往 https://github.com/settings/tokens
Step 2｜建立或 Regenerate token
Step 3｜Expiration 設定為 No expiration 或 1 年
Step 4｜Scope 勾選：repo（Full）+ workflow
Step 5｜複製 token（只顯示一次）
Step 6｜立即寫進 C:\AI_WorkDir\prospera-credentials.md
Step 7｜才去設定 GitHub Secret
```

### 3.3 GitHub Secret 設定流程（MUST）

```
Step 1｜查 prospera-credentials.md 確認 PAT 存在
Step 2｜前往 repo → Settings → Secrets and variables → Actions
Step 3｜New repository secret
Step 4｜Name：PROSPERA_DASHBOARD_TOKEN（統一命名）
Step 5｜Value：貼上 PAT
Step 6｜Save
Step 7｜立即用 workflow_dispatch 觸發驗證，確認成功才結束
Step 8｜更新 prospera-credentials.md 的 Used in 欄位
```

### 3.4 Workflow 使用 Token 標準寫法

```yaml
# ✅ 正確：明確傳入 token（私有 repo 必須）
- uses: actions/checkout@v4
  with:
    token: ${{ secrets.PROSPERA_DASHBOARD_TOKEN }}

# ❌ 錯誤：省略 token（私有 repo 會出現 terminal prompts disabled）
- uses: actions/checkout@v4
```

### 3.5 PAT 到期提醒

```
每次設定 PAT 後，在 prospera-audit-ledger 寫入：
PAT-EXPIRY-REMINDER: [到期日] prospera-dashboard-classic 需要 Regenerate
```

---

## 4. Matrix

| 情境 | 操作 | 注意事項 |
|------|------|---------|
| 新建 PAT | 產生 → 存 credentials.md → 設 Secret | Expiry 設 1 年以上 |
| PAT 找不到 | 查 credentials.md → 找不到就 Regenerate | 不要憑記憶猜 |
| PAT 過期 | Regenerate → 更新 credentials.md → 更新所有 repo Secret | 先查 Used in 欄位 |
| 新增 repo 使用同一 PAT | 查 credentials.md → 直接設 Secret → 更新 Used in | 不需重新 Regenerate |
| workflow 401/403 | 確認 Secret 名稱完全一致 + checkout 有傳 token | 大小寫敏感 |

---

## 5. Failure Modes

| 症狀 | 原因 | 修法 |
|------|------|------|
| `Input required and not supplied: token` | Secret 未設定 | 設定 PROSPERA_DASHBOARD_TOKEN |
| `terminal prompts disabled` | checkout 沒傳 token | 加 `with: token:` |
| `Bad credentials` | Token 過期或 Scope 不足 | Regenerate + 更新 Secret |
| `Resource not accessible by integration` | Scope 缺 workflow | 重建 PAT 加 workflow scope |

---

## 6. Audit Requirements

每次 PAT 操作記錄到 `prospera-audit-ledger`：
```
[日期] PAT-ACTION: [建立/Regenerate/設定Secret] [repo名稱] [操作者]
```

---

*v1.0 · 2026-05-19 · prospera-infra-ci/skills/*

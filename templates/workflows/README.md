<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:無機制驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# Workflow 範本

已合規（對齊 `governance/ACTIONS_USAGE_POLICY.md`）的 GitHub Actions 範本，供新 repo 複製。

## 內容
| 檔 | 用途 | 已內建 |
|---|---|---|
| `ci.yml` | 通用 CI（pytest）+ Actions 用量 lint caller | paths-ignore、concurrency、lint caller、timeout |
| `governance_check.yml` | 驗證型治理檢查（non-blocking） | paths-ignore、concurrency、timeout |

## 使用
1. 複製需要的檔到目標 repo 的 `.github/workflows/`。
2. 依 repo 實際情況調整 job 內容（如 test 指令、Python 版本）。
3. **勿移除 `ci.yml` 內的 `actions-usage-lint` job**——它呼叫 infra-ci 的 reusable lint，強制 MUST 1-5 / SHOULD 6。

## Lint 納管（既有 repo）
不複製範本時，於 repo 任一 workflow 加：
```yaml
jobs:
  actions-usage-lint:
    uses: ProsperaGen/prospera-infra-ci/.github/workflows/actions-usage-lint.yml@main
```

> SSOT 規範：`prospera-constitution-governance/governance/ACTIONS_USAGE_POLICY.md`

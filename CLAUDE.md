<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:doc | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:無機制驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
## 語言規則

語言：所有回報、commit message、PR 標題與內文、檔案內文一律繁體中文。程式碼識別字、路徑、指令、雜湊維持原文。使用者以其他語言提問時仍以繁體中文回報。

# CLAUDE.md — Prospera governance contract

**Authority**: ccktaiwan
**Schema**: prospera-os/DIRECTORY_SCHEMA.json
**Skills**: prospera-infra-ci/skills/SKILL-CORE.md
**Canonical source**: system_index.yaml v3.0

---

## EXECUTION MODEL

When working in any Prospera repo:
- NEVER produce manual scripts for the human to run
- ALWAYS use Claude Code to directly create files, run git, move directories
- If a task needs a decision -- ask ccktaiwan ONE question, then execute
- The human judges. Claude Code executes.

---

## This repo

**Ring**:    Ring 6
**Tier**:    L6 — Infrastructure
**Input**:   Every commit/PR from all repos
**Output**:  CI pass/fail + SKILL enforcement
**Owner**:   SKILL-CORE v3.4 + 4 workflows

## Git 操作硬規則（2026-06-22，防 auto mode 繞過）
- 絕不在未經 Kevin/claude.ai 明確當次指令下 push、commit、開 PR
- 「push hold」「不要動 X」等指令一旦下達，視為持續有效，即使 context 壓縮也不得恢復成自動 push
- force-push / reset --hard / rm -rf / checkout 覆蓋 = 絕對禁止，無論任何理由（含解 merge 衝突）
- 遇 merge 衝突 / push 被拒：停下回報選項，絕不自行升級為 force-push 或 reset
- 收工必須由 claude.ai 明確下「push」指令才 push，預設不 push（git 操作一律顯式授權）
- 機制保證：本規則同時硬編於 `.claude/settings.json`（deny/ask，跨 mode 不可繞過），自然語言失效時硬煞車仍在

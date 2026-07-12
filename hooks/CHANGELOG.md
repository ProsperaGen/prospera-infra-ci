<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:doc(版本紀錄) | 設計:Kevin 架構 | 執行:AI 工具(Claude Code) | 驗證:git tag | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# cost-gate CHANGELOG

## cost-gate v1.0.0 — 2026-07-13（發布 ⑤）
真 pre-execution GitHub Actions 成本閘（三次撞爆根治：6/19 $70 / 7/02 封鎖 / 7/12 $20/$20）。

- **prepush_cost_gate.py `__version__=1.0.0`**：push 前讀當月真實 org billing（net），累計超 $20 → `exit 1` 擋 push → workflow 不觸發 → 零 Actions 成本。逃生門 `PROSPERA_COST_OVERRIDE=1`（記帳）；fail-open 不 brick。
- **install_hooks.py / bootstrap-dev.sh**：`git config --global core.hooksPath` 一鍵覆蓋全 47 repo + 未來 clone（fleet 零缺口，冪等）。
- **test_prepush_cost_gate.py**：真陰（spend>budget→exit1）/ 真陽 8/8 全過。
- 現場活證：對真帳單 net $29.71 → exit1 真擋；真 `git push` 觸發 hook 並記帳。
- 取代 `budget_gate.yml`（workflow_dispatch 手動、歷來 0 執行、架構性擋不了）。
- 元根因監測：`check_gate_effectiveness.py`（governance repo，接 L1 daily-sprint）。

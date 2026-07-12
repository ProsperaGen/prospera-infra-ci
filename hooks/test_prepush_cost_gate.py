#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Prospera SYSTEM HEADER (ADR-0032/SBOM) | 設計:Kevin 架構 | 執行:Claude Code | 驗證:自身即測試 | IP:創造性歸 Kevin(發明人)
"""test_prepush_cost_gate.py — pre-execution 成本閘真陰/真陽測試。

DoD 要求：真陰＝模擬超預算 push → BLOCK(exit 1)＝「不跑」。真陽＝預算內 → 放行。
不依賴 pytest；直接跑：python test_prepush_cost_gate.py（exit 0 全過 / 1 有敗）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prepush_cost_gate as g

PROS = "https://github.com/ProsperaGen/prospera-constitution-governance.git"
OTHER = "https://github.com/someone/other-repo.git"
# 一行 push ref（非零 sha，new-branch 走 origin/main 分支；此處給既有 sha 對，讓 diff 走 range）
REFS = "refs/heads/main abc123 refs/heads/main def456\n"

FAILS = []


def check(name, got, want):
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got={got} want={want}")
    if not ok:
        FAILS.append(name)


def run():
    print("=== pre-execution 成本閘 真陰/真陽測試 ===")

    # 真陰①：當月已 $25 > $20 預算 → BLOCK
    os.environ["PROSPERA_COST_TEST_SPEND"] = "25"
    os.environ.pop("PROSPERA_COST_OVERRIDE", None)
    os.environ["PROSPERA_ACTIONS_BUDGET"] = "20"
    check("真陰: spend$25>budget$20 → BLOCK(1)", g.decide(PROS, REFS), 1)

    # 真陰②：當月 $16（未超）但本次邊際 $5 使投影跨 $20 → BLOCK（測 projected 邏輯）
    _saved = g.estimate_marginal
    g.estimate_marginal = lambda files, repo: {"minutes": 5.0, "cost": 5.0, "reasons": ["test$5"], "n_files": 1}
    os.environ["PROSPERA_COST_TEST_SPEND"] = "16"
    check("真陰: spend$16+邊際$5→投影$21跨$20 → BLOCK(1)", g.decide(PROS, REFS), 1)
    g.estimate_marginal = _saved

    # 真陽①：當月 $1 遠低於預算 → 放行
    os.environ["PROSPERA_COST_TEST_SPEND"] = "1"
    check("真陽: spend$1 → ALLOW(0)", g.decide(PROS, REFS), 0)

    # 真陽②：WARN 帶（$16≥75%×20=15 但 <20）→ 放行(0)
    os.environ["PROSPERA_COST_TEST_SPEND"] = "16"
    check("真陽: spend$16 WARN → ALLOW(0)", g.decide(PROS, REFS), 0)

    # 隔離①：非 ProsperaGen remote → 一律放行(0)，不干擾
    os.environ["PROSPERA_COST_TEST_SPEND"] = "25"
    check("隔離: 非 ProsperaGen remote → ALLOW(0)", g.decide(OTHER, REFS), 0)

    # 逃生門：override=1 即使超預算也放行(0)
    os.environ["PROSPERA_COST_OVERRIDE"] = "1"
    check("逃生門: OVERRIDE=1 超預算仍 ALLOW(0)", g.decide(PROS, REFS), 0)
    os.environ.pop("PROSPERA_COST_OVERRIDE", None)

    # 邊界：估算器對非 .md 變更給 pipeline 重工分鐘
    est = g.estimate_marginal([".github/workflows/x.yml", "a.py"], "gov")
    check("估算: 非.md+關鍵路徑 minutes≥7", est["minutes"] >= 7.0, True)
    est2 = g.estimate_marginal(["CURRENT_STATE.md"], "gov")
    check("估算: 純 state 檔 minutes≤1", est2["minutes"] <= 1.0, True)

    print(f"\n結果：{'✅ 全過' if not FAILS else '❌ 敗: ' + ', '.join(FAILS)}")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(run())

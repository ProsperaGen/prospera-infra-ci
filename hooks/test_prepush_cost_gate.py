#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Prospera SYSTEM HEADER (ADR-0032/SBOM) | 設計:Kevin 架構 | 執行:Claude Code | 驗證:自身即測試 | IP:創造性歸 Kevin(發明人)
"""test_prepush_cost_gate.py — pre-execution 成本閘真陰/真陽 + v1.1 動態閾值/override反常態化。

v1.1 修正：閘值 $20 固定值在 net>$20 後致 override 常態化 → 改動態 org budget×0.9。
不依賴 pytest；python test_prepush_cost_gate.py（exit 0 全過 / 1 有敗）。
"""
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prepush_cost_gate as g

PROS = "https://github.com/ProsperaGen/prospera-constitution-governance.git"
OTHER = "https://github.com/someone/other-repo.git"
REFS = "refs/heads/main abc123 refs/heads/main def456\n"
FAILS = []


def check(name, got, want):
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got={got} want={want}")
    if not ok:
        FAILS.append(name)


def run():
    print("=== pre-execution 成本閘 真陰/真陽 + v1.1 動態閾值 ===")
    os.environ["PROSPERA_CI_BUDGET"] = "50"          # 動態 budget=50 → block_at=45, warn_at=37.5
    os.environ.pop("PROSPERA_COST_OVERRIDE", None)

    # 真陰①：net $46 > block_at $45 → BLOCK
    os.environ["PROSPERA_COST_TEST_SPEND"] = "46"
    check("真陰: net$46 > budget50×0.9=45 → BLOCK(1)", g.decide(PROS, REFS), 1)

    # 真陰②：net $44 + 邊際 $5 → 投影 $49 ≥ 45 → BLOCK
    _saved = g.estimate_marginal
    g.estimate_marginal = lambda files, repo: {"minutes": 5.0, "cost": 5.0, "reasons": ["test$5"], "n_files": 1}
    os.environ["PROSPERA_COST_TEST_SPEND"] = "44"
    check("真陰: net$44+邊際$5→投影$49≥45 → BLOCK(1)", g.decide(PROS, REFS), 1)
    g.estimate_marginal = _saved

    # ★真陽（修復證明）：net $29.71（當前實況）在 budget$50 下 < 45 → ALLOW（不再 override 常態化）
    os.environ["PROSPERA_COST_TEST_SPEND"] = "29.71"
    check("★修復: net$29.71(當前) budget50 → ALLOW(0) 不再逼override", g.decide(PROS, REFS), 0)

    # 真陽②：WARN 帶（$40 ≥ 37.5 但 < 45）→ ALLOW
    os.environ["PROSPERA_COST_TEST_SPEND"] = "40"
    check("真陽: net$40 WARN帶 → ALLOW(0)", g.decide(PROS, REFS), 0)

    # 隔離：非 ProsperaGen → ALLOW
    os.environ["PROSPERA_COST_TEST_SPEND"] = "46"
    check("隔離: 非 ProsperaGen → ALLOW(0)", g.decide(OTHER, REFS), 0)

    # 逃生門：override 超閾值仍 ALLOW
    os.environ["PROSPERA_COST_OVERRIDE"] = "1"
    check("逃生門: OVERRIDE=1 超閾值仍 ALLOW(0)", g.decide(PROS, REFS), 0)
    os.environ.pop("PROSPERA_COST_OVERRIDE", None)

    # 估算邊界
    est = g.estimate_marginal([".github/workflows/x.yml", "a.py"], "gov")
    check("估算: 非.md+關鍵路徑 minutes≥7", est["minutes"] >= 7.0, True)

    # ★v1.1 新增①：動態閾值真讀取（env 覆寫路徑）
    os.environ["PROSPERA_CI_BUDGET"] = "30"
    amt, srcb = g.budget_amount()
    check("動態閾值: env PROSPERA_CI_BUDGET=30 讀到 30", amt, 30.0)
    os.environ["PROSPERA_CI_BUDGET"] = "50"

    # ★v1.1 新增②：override 連續 3 次 → excursion 記錄（防常態化）
    tmp = tempfile.mkdtemp()
    g.LEDGER = os.path.join(tmp, "ledger.jsonl")
    g.EXCURSION = os.path.join(tmp, "excursion.jsonl")
    os.environ["PROSPERA_COST_OVERRIDE"] = "1"
    g.decide(PROS, REFS); g.decide(PROS, REFS); g.decide(PROS, REFS)  # 連 3 次
    exc = os.path.isfile(g.EXCURSION) and len(open(g.EXCURSION, encoding="utf-8").read().strip()) > 0
    check("override連續3次 → excursion ledger 記錄", exc, True)
    os.environ.pop("PROSPERA_COST_OVERRIDE", None)

    print(f"\n結果：{'✅ 全過' if not FAILS else '❌ 敗: ' + ', '.join(FAILS)}")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(run())


# ── org 改名遺留：舊名 remote 亦須覆蓋（2026-07-20，真陽真陰）──────────────
def test_org_alias_ccktaiwan_covered():
    """★真陽：org 舊名 ccktaiwan 之 remote 須被覆蓋。
    實測坐實：本機 79 clone 中 76 個 remote 仍為舊名 → 原判定只認 prosperagen
    致成本閘實際只覆蓋 3/79，此為它從未攔截過之真因。"""
    assert g.is_prospera_remote("https://github.com/ccktaiwan/prospera-infra-ci.git")
    assert g.is_prospera_remote("git@github.com:ccktaiwan/prospera-os.git")


def test_org_alias_prosperagen_still_covered():
    """不破既有：新名仍覆蓋。"""
    assert g.is_prospera_remote("https://github.com/ProsperaGen/prospera-os.git")


def test_non_prospera_remote_still_passthrough():
    """★真陰：非本組織 remote 一律放行，不干擾他人 repo。"""
    assert not g.is_prospera_remote("https://github.com/someoneelse/other.git")
    assert not g.is_prospera_remote("https://gitlab.com/ccktaiwan/x.git")
    assert not g.is_prospera_remote("")

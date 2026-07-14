#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Prospera SYSTEM HEADER (ADR-0032/SBOM) | 設計:Kevin 架構(PENDING-270) | 執行:Claude Code | 驗證:自身即測試(pytest) | IP:創造性歸 Kevin(發明人), AI 為執行工具
"""test_override_reconciliation.py — override 對帳真陰/真陽（pytest, tmp_path 造真記帳）。

真陰真陽（非 mock existence，注入真 jsonl 記帳）：
  ① 無記帳檔 → 0 override 不報錯（fail-safe）
  ② 注入 N 筆 override → total/current streak 統計正確
  ③ 尾端 streak ≥ 閾值 → alarm True（常態化告警）
  ④ 尾端 streak < 閾值（override 後接非-override 打斷）→ alarm False
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import override_reconciliation as r

PROS = "https://github.com/ProsperaGen/prospera-infra-ci.git"


def _write_ledger(path, events):
    """把事件列表寫成真 jsonl 記帳（造真陽輸入，非 mock）。"""
    with open(path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def _ovr(streak=None):
    e = {"event": "override", "remote": PROS}
    if streak is not None:
        e["streak"] = streak
    return e


def _allow():
    return {"event": "allow", "repo": "prospera-infra-ci", "net": 10.0}


# ① 真陰：無記帳檔 → 0 override，不報錯
def test_no_ledger_returns_zero(tmp_path):
    missing = str(tmp_path / "does_not_exist.jsonl")
    rep = r.reconcile(ledger=missing, excursion=str(tmp_path / "no_exc.jsonl"), threshold=3)
    assert rep["ledger_exists"] is False
    assert rep["total_overrides"] == 0
    assert rep["current_streak"] == 0
    assert rep["alarm"] is False


def test_read_events_missing_file_is_empty(tmp_path):
    assert r.read_events(str(tmp_path / "nope.jsonl")) == []


# ② 真陽：注入 N 筆 override → 統計正確
def test_counts_injected_overrides(tmp_path):
    ledger = str(tmp_path / "ledger.jsonl")
    # 混入非-override 事件，確保只數 override
    _write_ledger(ledger, [_allow(), _ovr(1), _allow(), _ovr(1), _ovr(2)])
    rep = r.reconcile(ledger=ledger, excursion=str(tmp_path / "exc.jsonl"), threshold=3)
    assert rep["ledger_exists"] is True
    assert rep["total_events"] == 5
    assert rep["total_overrides"] == 3          # 3 筆 override 中 1 筆被 allow 打斷
    assert rep["current_streak"] == 2           # 尾端連續 2 筆 override
    assert rep["max_streak"] == 2
    assert abs(rep["override_rate"] - 0.6) < 1e-9


# ③ 真陽：尾端 streak ≥ 閾值 → alarm True
def test_streak_at_threshold_alarms(tmp_path):
    ledger = str(tmp_path / "ledger.jsonl")
    _write_ledger(ledger, [_allow(), _ovr(1), _ovr(2), _ovr(3)])
    rep = r.reconcile(ledger=ledger, excursion=str(tmp_path / "exc.jsonl"), threshold=3)
    assert rep["current_streak"] == 3
    assert rep["alarm"] is True


def test_streak_above_threshold_alarms(tmp_path):
    ledger = str(tmp_path / "ledger.jsonl")
    _write_ledger(ledger, [_ovr(1), _ovr(2), _ovr(3), _ovr(4), _ovr(5)])
    rep = r.reconcile(ledger=ledger, excursion=str(tmp_path / "exc.jsonl"), threshold=3)
    assert rep["current_streak"] == 5
    assert rep["alarm"] is True


# ④ 真陰：尾端 streak < 閾值（override 被非-override 打斷）→ alarm False
def test_streak_below_threshold_no_alarm(tmp_path):
    ledger = str(tmp_path / "ledger.jsonl")
    # 歷史曾連 3 次，但尾端被 allow 打斷 → 當前 streak = 1
    _write_ledger(ledger, [_ovr(1), _ovr(2), _ovr(3), _allow(), _ovr(1)])
    rep = r.reconcile(ledger=ledger, excursion=str(tmp_path / "exc.jsonl"), threshold=3)
    assert rep["current_streak"] == 1           # 尾端只剩 1
    assert rep["max_streak"] == 3               # 歷史最長仍記 3
    assert rep["alarm"] is False


def test_threshold_env_override(tmp_path, monkeypatch):
    ledger = str(tmp_path / "ledger.jsonl")
    _write_ledger(ledger, [_ovr(1), _ovr(2)])
    # 閾值降到 2 → 尾端 streak 2 觸發 alarm（驗 env 可覆寫）
    monkeypatch.setenv("PROSPERA_OVERRIDE_STREAK_ALARM", "2")
    rep = r.reconcile(ledger=ledger, excursion=str(tmp_path / "exc.jsonl"))
    assert rep["threshold"] == 2
    assert rep["current_streak"] == 2
    assert rep["alarm"] is True


# excursion 記帳計數（gate 連 3 次另寫 excursion ledger）
def test_excursion_count(tmp_path):
    ledger = str(tmp_path / "ledger.jsonl")
    exc = str(tmp_path / "exc.jsonl")
    _write_ledger(ledger, [_ovr(1), _ovr(2), _ovr(3)])
    _write_ledger(exc, [{"event": "override", "streak": 3, "excursion": True}])
    rep = r.reconcile(ledger=ledger, excursion=exc, threshold=3)
    assert rep["excursions"] == 1


# 壞行 fail-safe：不完整 json 行被跳過，不整檔崩
def test_corrupt_line_skipped(tmp_path):
    ledger = str(tmp_path / "ledger.jsonl")
    with open(ledger, "w", encoding="utf-8") as f:
        f.write(json.dumps(_ovr(1), ensure_ascii=False) + "\n")
        f.write("{ this is not valid json\n")
        f.write(json.dumps(_ovr(2), ensure_ascii=False) + "\n")
    rep = r.reconcile(ledger=ledger, excursion=str(tmp_path / "exc.jsonl"), threshold=3)
    assert rep["total_overrides"] == 2
    assert rep["current_streak"] == 2

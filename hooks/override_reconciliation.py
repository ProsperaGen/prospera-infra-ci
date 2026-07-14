#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Prospera SYSTEM HEADER (ADR-0032/SBOM) | 設計:Kevin 架構(PENDING-270 override 對帳) | 執行:Claude Code | 驗證:test_override_reconciliation | IP:創造性歸 Kevin(發明人), AI 為執行工具
"""override_reconciliation.py — pre-push 成本閘「override 逃生門」對帳（PENDING-270）。

背景：prepush_cost_gate.py（v1.1.0）的逃生門 PROSPERA_COST_OVERRIDE=1 使用時「記帳」，
      寫入 prepush_cost_ledger.jsonl（{"event":"override",...}），連續 3 次另記
      prepush_excursion_ledger.jsonl。若 override 常態化＝閘閾值失準訊號（BGE 反模式）。

本對帳（讀帳 → 統計 → 告警，非攔截）：
  1. 讀 override 記帳（沿用 gate 既定 LEDGER 路徑；env PROSPERA_COST_LEDGER 可覆寫）。
  2. 統計：總 push 事件、總 override 次數、override 率、當前尾端 streak、歷史最長 streak、excursion 數。
  3. 尾端 streak ≥ 閾值（env PROSPERA_OVERRIDE_STREAK_ALARM，預設 3）→ 告警旗標（常態化訊號）。
  4. fail-safe：記帳檔不存在 → 回報 0 override（非報錯，供全新 fleet / 未觸發時安全跑）。

CLI：python hooks/override_reconciliation.py         # 印報告，預設 exit 0
     python hooks/override_reconciliation.py --strict # 告警時 exit 2（可接 CI 響鈴）
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import prepush_cost_gate as _gate          # 單一真相：沿用 gate 的 ledger 路徑與閾值常數
    _DEFAULT_LEDGER = _gate.LEDGER
    _DEFAULT_EXCURSION = _gate.EXCURSION
    _DEFAULT_ALARM = _gate.OVERRIDE_STREAK_ALARM
except Exception:                              # gate 缺席也不 brick（fail-safe）
    _here = os.path.dirname(os.path.abspath(__file__))
    _DEFAULT_LEDGER = os.path.join(_here, "prepush_cost_ledger.jsonl")
    _DEFAULT_EXCURSION = os.path.join(_here, "prepush_excursion_ledger.jsonl")
    _DEFAULT_ALARM = 3


def ledger_path() -> str:
    return os.environ.get("PROSPERA_COST_LEDGER") or _DEFAULT_LEDGER


def excursion_path() -> str:
    return os.environ.get("PROSPERA_EXCURSION_LEDGER") or _DEFAULT_EXCURSION


def alarm_threshold() -> int:
    v = os.environ.get("PROSPERA_OVERRIDE_STREAK_ALARM")
    if v:
        try:
            return int(v)
        except ValueError:
            pass
    return int(_DEFAULT_ALARM)


def read_events(path: str):
    """讀記帳 jsonl → list[dict]。fail-safe：檔不存在或壞行 → 略過，不報錯。"""
    if not path or not os.path.isfile(path):
        return []
    events = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except (ValueError, json.JSONDecodeError):
                    continue                   # 壞行跳過（fail-safe）
    except OSError:
        return []
    return events


def trailing_streak(events) -> int:
    """尾端連續 override 次數（與 gate._override_streak 同義：常態化訊號）。"""
    streak = 0
    for e in reversed(events):
        if e.get("event") == "override":
            streak += 1
        else:
            break
    return streak


def max_streak(events) -> int:
    """歷史最長連續 override streak。"""
    best = cur = 0
    for e in events:
        if e.get("event") == "override":
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def reconcile(ledger=None, excursion=None, threshold=None) -> dict:
    """對帳核心：讀 override 記帳 → 統計報告 dict。純函式，供測試注入路徑。"""
    ledger = ledger if ledger is not None else ledger_path()
    excursion = excursion if excursion is not None else excursion_path()
    threshold = threshold if threshold is not None else alarm_threshold()

    events = read_events(ledger)
    overrides = [e for e in events if e.get("event") == "override"]
    total_events = len(events)
    total_overrides = len(overrides)
    cur = trailing_streak(events)
    exc_events = read_events(excursion)

    return {
        "ledger": ledger,
        "ledger_exists": os.path.isfile(ledger) if ledger else False,
        "total_events": total_events,
        "total_overrides": total_overrides,
        "override_rate": round(total_overrides / total_events, 3) if total_events else 0.0,
        "current_streak": cur,
        "max_streak": max_streak(events),
        "threshold": threshold,
        "alarm": cur >= threshold,
        "excursions": len(exc_events),
    }


def format_report(rep: dict) -> str:
    lines = []
    lines.append("=" * 66)
    lines.append("[override-對帳] PENDING-270 pre-push override 逃生門對帳")
    lines.append("=" * 66)
    if not rep["ledger_exists"]:
        lines.append(f"記帳檔不存在（{rep['ledger']}）→ 0 override（fail-safe，尚未觸發）。")
    else:
        lines.append(f"記帳檔：{rep['ledger']}")
        lines.append(f"總 push 事件：{rep['total_events']}｜總 override：{rep['total_overrides']}"
                     f"（override 率 {rep['override_rate']}）")
        lines.append(f"當前尾端 streak：{rep['current_streak']}｜歷史最長 streak：{rep['max_streak']}"
                     f"｜excursion 記錄：{rep['excursions']}")
    lines.append(f"告警閾值：streak ≥ {rep['threshold']}")
    if rep["alarm"]:
        lines.append(f"🚨 告警：當前 streak {rep['current_streak']} ≥ {rep['threshold']} —— override 正在常態化！")
        lines.append("  → 請改本機驗收降 push 頻率，或調高 org budget（若確為合理成長）。")
    else:
        lines.append("✅ 正常：override 未常態化（streak < 閾值）。")
    lines.append("=" * 66)
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    strict = "--strict" in argv
    rep = reconcile()
    print(format_report(rep))
    if strict and rep["alarm"]:
        return 2                               # 可選：告警時非 0（接 CI 響鈴）
    return 0                                    # 預設報告用 exit 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                       # 對帳絕不 brick（fail-safe）
        print(f"[override-對帳] ⚠ 例外（fail-safe，回報 0）：{e}")
        sys.exit(0)

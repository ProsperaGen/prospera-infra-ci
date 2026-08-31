#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Prospera SYSTEM HEADER (ADR-0032/SBOM) | 設計:Kevin 架構(發明人) | 執行:Claude Code | 驗證:test_precommit_fleet_gate 真陽真陰 | IP:創造性歸 Kevin(發明人), AI 為執行工具
"""precommit_fleet_gate.py — fleet 級 pre-commit 閘（經 global core.hooksPath 覆蓋全機 repo）。

★為何需要（2026-07-20，Kevin 裁簡體戰場＝Code 輸出／commit／**客戶交付物**）：
  簡體閘與交付物閘都住在**治理 repo**，但**交付物住在客戶 repo**——
  客戶 repo 實測**完全沒有本地 pre-commit**（5 個有 deliverables/ 的 client repo 皆然），
  且 `check_deliverable_gate.py` **未接任何 workflow**（`DELIVERABLE_PIPELINE.md:26` 宣稱
  「CI 機器閘…強制」與實際不符）→ 客戶交付物側**實際零閘**。
  global core.hooksPath 是唯一能覆蓋客戶 repo 的執行點，故 fleet 級檢查掛此。

檢查：
  1. 簡體零容忍：staged 之文字檔（判準沿用治理 repo canonical `detect_simplified`，禁另建字集）
     ★S1-A（PENDING-646，2026-08-31）：判準模組不可及**不再靜默 fail-open**。
       原 `return []` 與「零違規」不可分辨 ⇒ 缺閘偽裝成通過，全機 staged 檔靜默放行。
       改為印 BLOCKING 並回一筆哨兵違規（擋 commit）。爆炸半徑＝治理 repo 未 checkout
       或 PROSPERA_GOV_ROOT 設錯之機器，commit 會被擋；此為**刻意**（缺閘要可見），
       修法印在訊息裡（checkout 治理 repo 或設 PROSPERA_GOV_ROOT）。
     ※ 單檔讀取／解碼失敗仍 continue，但印 WARN 指名該檔未受檢（不再靜默漏檢）。
  2. 交付物閘：staged 路徑含 `deliverables/` 時，跑 `check_deliverable_gate`（含其簡體檢查）

scope：只對 ProsperaGen/ccktaiwan remote 生效（同 prepush_cost_gate 之自 scope 原則），
其餘 remote 一律放行不干擾。

退出碼：0=通過/不適用｜1=違規擋 commit
"""
import os
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 治理 repo（判準來源）。允許以環境變數覆寫，便於測試與異機路徑。
_GOV_DEFAULT = "C:/AI_WorkDir/GitHub/prospera-constitution-governance"
GOV = os.environ.get("PROSPERA_GOV_ROOT", _GOV_DEFAULT)

_ORG_ALIASES = ("prosperagen", "ccktaiwan")
_TEXT_EXT = {".md", ".py", ".yml", ".yaml", ".json", ".txt", ".csv", ".toml", ".ini", ".cfg"}


def _run(args):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=15)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def in_scope() -> bool:
    """只對本組織 remote 生效；無 remote（新 repo）亦視為在範圍內（保守守）。"""
    url = _run(["git", "config", "--get", "remote.origin.url"]).strip().lower()
    if not url:
        return True
    return "github.com" in url and any(o in url for o in _ORG_ALIASES)


def staged_files() -> list:
    out = _run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"])
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def _load(path, name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sentinel(reason: str, detail: str) -> list:
    """判準不可及之哨兵違規：讓「無法檢查」與「檢查後零違規」可分辨（PENDING-646）。"""
    print(f"[fleet-gate] ❌ BLOCKING：簡體判準模組{reason} ⇒ 無法檢查，不得靜默放行。")
    print(f"[fleet-gate]   detail: {detail}")
    print(f"[fleet-gate]   修法：checkout 治理 repo，或設 PROSPERA_GOV_ROOT 指向其根目錄"
          f"（現值 GOV={GOV}）。")
    return [("<簡體判準不可及>", f"{reason}: {detail}")]


def check_simplified(files: list) -> list:
    """回 [(file, hits)]。★判準模組不可及 → 回哨兵違規（非靜默 []），見模組 docstring。"""
    ds = os.path.join(GOV, "00_governance", "fitness", "detect_simplified.py")
    if not os.path.isfile(ds):
        return _sentinel("不存在", ds)
    try:
        mod = _load(ds, "_fleet_detect_simplified")
        exclude = getattr(mod, "SELF_EXCLUDE", set())
    except Exception as e:
        return _sentinel("載入失敗", f"{type(e).__name__}: {e} @ {ds}")
    viol = []
    for f in files:
        if os.path.splitext(f)[1].lower() not in _TEXT_EXT:
            continue
        if os.path.basename(f) in exclude:
            continue
        try:
            raw = open(f, "rb").read()
            if raw.startswith(b"\xef\xbb\xbf"):
                raw = raw[3:]
            hits = mod.find_simplified(raw.decode("utf-8", errors="ignore"))
        except Exception as e:
            # ★不再靜默：指名「該檔未受檢」，缺漏可見（PENDING-646）
            print(f"[fleet-gate] ⚠ WARN：{f} 讀取/檢查失敗，"
                  f"該檔未受簡體檢查（{type(e).__name__}: {e}）")
            continue
        if hits:
            viol.append((f, "".join(hits)))
    return viol


def check_deliverables(files: list) -> list:
    """staged 觸及 deliverables/ 時跑交付物閘。回 violations（含缺 render.log/md 與簡體）。"""
    if not any("deliverables/" in f.replace("\\", "/") for f in files):
        return []
    gate = os.path.join(GOV, "00_governance", "fitness", "check_deliverable_gate.py")
    if not os.path.isfile(gate):
        return []
    try:
        from pathlib import Path
        mod = _load(gate, "_fleet_deliverable_gate")
        dirs = sorted({os.path.dirname(f) for f in files
                       if "deliverables/" in f.replace("\\", "/")})
        res = mod.scan([Path(d) for d in dirs if os.path.isdir(d)])
        return res.get("violations", [])
    except Exception:
        return []


def main() -> int:
    if not in_scope():
        return 0
    files = staged_files()
    if not files:
        return 0
    bad = False

    sim = check_simplified(files)
    if sim:
        bad = True
        print("[fleet-gate] ❌ BLOCKING：簡體字命中（繁體鎖定零容忍，四出口共用判準）")
        for f, hits in sim:
            print(f"  - {f}: {hits}")

    dlv = check_deliverables(files)
    if dlv:
        bad = True
        print("[fleet-gate] ❌ BLOCKING：交付物閘未過（③驗證閘，缺一不交付）")
        for v in dlv:
            print(f"  - {v.get('docx')}: 缺 {v.get('missing')}")

    if bad:
        print("[fleet-gate] 修正後再 commit；判準源＝治理 repo canonical（禁另建）。")
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:      # fail-open：閘自身故障不得 brick commit
        print(f"[fleet-gate] 略過（例外 fail-open）：{e}")
        sys.exit(0)

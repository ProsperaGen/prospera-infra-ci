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
     ★S1-B（PENDING-646 結案面，2026-09-12）：**編碼例外一律判紅，工具故障明示 SKIPPED**。
       原 `_run()` 以 `text=True` 不帶 `encoding`，Windows 下退回 locale（cp950），
       git 輸出中任一非 Big5 位元組即 `UnicodeDecodeError`，舊碼在 `except` 內回 `""`
       ⇒ `staged_files()` 拿到**空母體**而 `main()` 判「無 staged 檔」放行
       ⇒ **exit 0 假綠**（實測五次 commit 全印「略過（例外 fail-open）」）。
       口徑沿本庫既有鐵律「受檢母體 0／不可測 ⇒ 判**未執行**，不得計為通過」
       （`00_governance/audits/AUDITOR_SELFTEST_2026-08-08.md:32`）。
       ①受檢內容之解碼例外 → **判紅**（`GateDecodeError` 或列為違規），不得靜默略過；
       ②工具面故障（git 不可及／逾時／交付物閘載入失敗）→ 印 `SKIPPED（未執行，非通過）`
         並回 0，**不 brick commit**，但缺閘可見；
       ③單檔**不存在**（如 rename 之舊名）＝非編碼問題 → 印 WARN 指名該檔未受檢後續掃。
     ★`staged_files()` 加 `-c core.quotepath=false`：預設 quotepath 把非 ASCII 檔名輸出成
       `"a\350..."`，引號與跳脫使副檔名比對失準 ⇒ **中日文檔名被靜默略過**（另一路假綠）。
  2. 交付物閘：staged 路徑含 `deliverables/` 時，跑 `check_deliverable_gate`（含其簡體檢查）

scope：只對 ProsperaGen/ccktaiwan remote 生效（同 prepush_cost_gate 之自 scope 原則），
其餘 remote 一律放行不干擾。

★**本檔未承載者（具名）**：判準來源釘選 `origin/main`（`PENDING-673`）**不在本次範圍**——
  該筆之三個根治方向尚待 L0 擇一，執行層不得以實作代替裁決。本閘判準仍讀 `GOV` 工作樹。

退出碼：0=通過/不適用/明示 SKIPPED｜1=違規擋 commit（含編碼例外）
"""
import os
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        # ★六處 except 逐處判（PENDING-646）之第①處：**唯一保留靜默者**。
        #   理由：本段跑在任何輸出管道就緒之前，此處若改印訊息，訊息自身可能再炸；
        #   且其失敗**不可能造成假綠**——所有受檢內容自本次起一律以 bytes 讀入、
        #   顯式 `decode("utf-8")`，判定不再經由 stdout 編碼。失敗只影響訊息可讀性。
        pass

# 治理 repo（判準來源）。允許以環境變數覆寫，便於測試與異機路徑。
_GOV_DEFAULT = "C:/AI_WorkDir/GitHub/prospera-constitution-governance"
GOV = os.environ.get("PROSPERA_GOV_ROOT", _GOV_DEFAULT)

_ORG_ALIASES = ("prosperagen", "ccktaiwan")
_TEXT_EXT = {".md", ".py", ".yml", ".yaml", ".json", ".txt", ".csv", ".toml", ".ini", ".cfg"}


class GateDecodeError(Exception):
    """讀取／解碼受檢內容時之編碼例外。★必須判紅，不得 fail-open（PENDING-646）。"""


def _skip(msg: str) -> None:
    """★明示 SKIPPED：工具面故障**不得計為通過**（同本庫「母體 0 ⇒ 判未執行」口徑）。"""
    print("[fleet-gate] SKIPPED（**未執行，非通過**）：{}".format(msg))


def _run(args):
    """跑 git。回 stdout 字串；rc 非 0 回 `""`；**工具面故障回 `None`**。

    ★六處 except 逐處判之第②處（PENDING-646 根因所在）：
      原寫法 `text=True` 不帶 `encoding`，Windows 下由 locale（cp950）解碼，
      實測訊息 `'cp950' codec can't decode byte 0x99 ... illegal multibyte sequence`。
      舊碼把該例外與「找不到 git」一併回 `""`，兩者不可分辨 ⇒ 空母體假綠。
      現改為：**顯式 UTF-8 解碼**，解碼例外拋 `GateDecodeError`（判紅），
      工具面故障回 `None`（由呼叫端明示 SKIPPED）。
    """
    try:
        r = subprocess.run(args, capture_output=True, timeout=15)
    except Exception:
        return None                       # 工具面故障（找不到 git／逾時）→ 呼叫端明示 SKIPPED
    if r.returncode != 0:
        return ""
    try:
        return r.stdout.decode("utf-8")
    except UnicodeDecodeError as e:
        raise GateDecodeError("git 輸出非 UTF-8：{}".format(e)) from e


def in_scope() -> bool:
    """只對本組織 remote 生效；無 remote（新 repo）亦視為在範圍內（保守守）。"""
    out = _run(["git", "config", "--get", "remote.origin.url"])
    if out is None:
        return True                       # 工具面故障：保守視為在範圍內，交由呼叫端明示
    url = out.strip().lower()
    if not url:
        return True
    return "github.com" in url and any(o in url for o in _ORG_ALIASES)


def staged_files():
    """回 staged 檔名 list；**工具面故障回 `None`**（呼叫端明示 SKIPPED，不得當成空母體）。

    ★`-c core.quotepath=false`：預設 quotepath 會把非 ASCII 檔名輸出成 `"a\\350..."`，
      該引號與跳脫使副檔名比對失準 ⇒ 中日文檔名**被靜默略過**（假綠之另一路）。
    """
    out = _run(["git", "-c", "core.quotepath=false", "diff", "--cached",
                "--name-only", "--diff-filter=ACM"])
    if out is None:
        return None
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
        # ★第③處：判準模組載入失敗 ⇒ 哨兵違規（判紅），S1-A 已定，本次不改。
        return _sentinel("載入失敗", f"{type(e).__name__}: {e} @ {ds}")
    viol = []
    for f in files:
        if os.path.splitext(f)[1].lower() not in _TEXT_EXT:
            continue
        if os.path.basename(f) in exclude:
            continue
        try:
            with open(f, "rb") as fh:
                raw = fh.read()
        except OSError as e:
            # ★第④處：檔已不在工作樹（如 rename 之舊名）＝**非編碼問題**，
            #   不 brick 整次 commit，但指名該檔未受檢（S1-A 已定之可見性）。
            print(f"[fleet-gate] ⚠ WARN：{f} 讀取失敗，"
                  f"該檔未受簡體檢查（{type(e).__name__}: {e}）")
            continue
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
        try:
            # ★第⑤處（PENDING-646 核心）：**顯式 UTF-8 且不吞**。
            #   原 `errors="ignore"` 會把非 UTF-8 檔之壞位元組丟掉後當乾淨檔放行
            #   ⇒ 受檢但等同未檢。現改為列為違規（判紅）。
            txt = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            viol.append((f, "<讀檔編碼例外，判紅：{}>".format(e)))
            continue
        hits = mod.find_simplified(txt)
        if hits:
            viol.append((f, "".join(hits)))
    return viol


def check_deliverables(files: list):
    """staged 觸及 deliverables/ 時跑交付物閘。回 `(violations, skipped_reason)`。

    ★第⑥處（PENDING-646）：原 `except Exception: return []` 與「零違規」不可分辨，
      閘載不起來時**靜默計為通過**。現改回 `skipped_reason` 由呼叫端印 SKIPPED。
      不改判紅：本閘之判準檔不可及屬工具面，與簡體判準（繁體鎖定零容忍）不同級。
    ★審查母體仍為 staged 檔**之所在目錄**——改為 staged docx 本身屬 `ADR-0323`／
      `PENDING-625` 之範圍，不在本次（PENDING-646）內，執行層不擴充批次。
    """
    if not any("deliverables/" in f.replace("\\", "/") for f in files):
        return [], None
    gate = os.path.join(GOV, "00_governance", "fitness", "check_deliverable_gate.py")
    if not os.path.isfile(gate):
        return [], "交付物閘判準不可及：{}".format(gate)
    try:
        from pathlib import Path
        mod = _load(gate, "_fleet_deliverable_gate")
        dirs = sorted({os.path.dirname(f) for f in files
                       if "deliverables/" in f.replace("\\", "/")})
        res = mod.scan([Path(d) for d in dirs if os.path.isdir(d)])
        return res.get("violations", []), None
    except Exception as e:
        return [], "交付物閘載入或執行失敗：{}: {}".format(type(e).__name__, e)


def main() -> int:
    if not in_scope():
        return 0
    files = staged_files()
    if files is None:
        # ★空母體與「取不到母體」必須可分辨（PENDING-646）：後者印 SKIPPED，不計為通過。
        _skip("無法取得 staged 清單（git 不可及）")
        return 0
    if not files:
        return 0
    bad = False

    sim = check_simplified(files)
    if sim:
        bad = True
        print("[fleet-gate] ❌ BLOCKING：簡體字命中或讀檔編碼例外"
              "（繁體鎖定零容忍，四出口共用判準）")
        for f, hits in sim:
            print(f"  - {f}: {hits}")

    dlv, dlv_skip = check_deliverables(files)
    if dlv_skip:
        _skip(dlv_skip)
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
    except GateDecodeError as e:
        # ★編碼例外**一律判紅**（PENDING-646）：原本此類例外落入下方通用 fail-open，
        #   實測五次 commit 全印「略過（例外 fail-open）」且 exit 0
        #   ＝閘根本沒跑，卻被下游（ENABLEMENT_ATTESTATION 一系）讀成「已檢查且無問題」。
        print(f"[fleet-gate] ❌ BLOCKING：編碼例外（判紅，非 fail-open）：{e}")
        print("[fleet-gate] 修正：受檢檔以 UTF-8 儲存；或以 UTF-8 模式執行（PYTHONUTF8=1）。")
        sys.exit(1)
    except Exception as e:      # 工具自身故障：明示 SKIPPED，不得計為通過
        print(f"[fleet-gate] SKIPPED（**未執行，非通過**）：閘自身故障 {type(e).__name__}: {e}")
        sys.exit(0)

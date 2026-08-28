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

檢查（皆 fail-open，任何例外/找不到判準模組 → exit 0，缺閘不 brick commit）：
  1. 簡體零容忍：staged 之文字檔（判準沿用治理 repo canonical `detect_simplified`，禁另建字集）
  2. 交付物閘：staged 路徑含 `deliverables/` 時，跑 `check_deliverable_gate`（含其簡體檢查）

scope：只對 ProsperaGen/ccktaiwan remote 生效（同 prepush_cost_gate 之自 scope 原則），
其餘 remote 一律放行不干擾。

退出碼：0=通過/不適用｜1=違規擋 commit
"""
import os
import subprocess
import sys
import tempfile

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


class GateDecodeError(Exception):
    """讀取／解碼判準或受檢內容時之編碼例外。★必須判紅，不得 fail-open。"""


def _run(args, cwd=None):
    """跑 git。★**明示 UTF-8**（PENDING-646 根因）：

    原寫法 `text=True` 不帶 `encoding`，Windows 下退回 locale（cp950），
    git 輸出中任一非 Big5 位元組即 `UnicodeDecodeError` → 舊碼在 except 內回 ""
    → `staged_files()` 拿到空母體 → **exit 0 假綠**（受檢母體 0 卻計為通過）。
    實測訊息：`'cp950' codec can't decode byte 0x99 ... illegal multibyte sequence`。

    回傳 stdout（rc 非 0 回 ""）。**解碼例外改拋 `GateDecodeError`**（判紅），
    其餘工具面故障（找不到 git／逾時）回 `None` 由呼叫端明示 SKIPPED。
    """
    try:
        r = subprocess.run(args, capture_output=True, timeout=15, cwd=cwd)
    except Exception:
        return None                      # 工具面故障 → 呼叫端明示 SKIPPED
    if r.returncode != 0:
        return ""
    try:
        return r.stdout.decode("utf-8")
    except UnicodeDecodeError as e:
        raise GateDecodeError(f"git output not UTF-8: {e}") from e


def in_scope() -> bool:
    """只對本組織 remote 生效；無 remote（新 repo）亦視為在範圍內（保守守）。"""
    out = _run(["git", "config", "--get", "remote.origin.url"])
    if out is None:
        return True                      # 工具面故障：保守視為在範圍內，交由呼叫端明示
    url = out.strip().lower()
    if not url:
        return True
    return "github.com" in url and any(o in url for o in _ORG_ALIASES)


def staged_files():
    """回 staged 檔名 list；工具面故障回 None（呼叫端明示 SKIPPED，不得當成空母體）。

    ★`-c core.quotepath=false`：預設 quotepath 會把非 ASCII 檔名輸出成 `"a\350..."`，
      該引號與跳脫使副檔名比對失準 → 非 ASCII 檔名**被靜默略過**（另一路假綠，實測）。
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


# -- PENDING-647:判準來源釘選 origin/main，不讀本機工作樹 --------------
#   ★病灶：原以 `GOV/00_governance/fitness/detect_simplified.py` 直接載入判準，
#     `GOV` 為治理庫**工作樹** ⇒ 判準＝該工作樹當下 checkout 到哪個分支。
#     實測（2026-08-28）工作樹停在舊分支時，其判準檔較 `origin/main` 少 44 行，
#     全機 pre-commit 當時正跑在過期判準上，且**無任何訊號**。
#   ★本次採 L0 指定之根治方向①「閘改讀 `origin/main` 版」。
#     `origin/main` 為**本機 remote-tracking ref**，讀它不連網、不受離線影響
#     （該 ref 落後與否是另一件事，故一併輸出提交碼供事後稽核）。
#   ★不是「一行路徑改動」：判準模組以 `Path(__file__).parents[2]` 推導字集檔，
#     白名單檔亦以 `Path(__file__).parent` 推導，故須把三檔按**庫內相對路徑**
#     一起還原到快取目錄；只還原一支會導致字集載入失敗（RuntimeError）
#     或白名單失效（ADR-0322 測試樣本例外被誤擋）。
_CRITERION_BLOBS = (
    "00_governance/fitness/detect_simplified.py",
    "00_governance/fitness/SIMPLIFIED_GATE_WHITELIST.txt",
    "00_governance/data/simplified_charset.json",
)
_PIN_ROOT = os.path.join(tempfile.gettempdir(), "prospera-gate-pin")


def criterion_root():
    """回 (root, 提交碼)。取不到 origin/main 回 (None, 原因) 由呼叫端明示 SKIPPED。

    ★**不再退回工作樹**：靜默退回正是 PENDING-647 之病灶本身
      （「你正在用的判準不是主線那份」而無訊號）。取不到即明示未執行。
    """
    out = _run(["git", "-C", GOV, "rev-parse", "origin/main"])
    if not out:
        return None, "取不到 origin/main（治理庫不可及或無該 ref）"
    sha = out.strip()
    root = os.path.join(_PIN_ROOT, sha[:12])
    stamp = os.path.join(root, ".ok")
    if os.path.isfile(stamp):
        return root, sha[:12]
    for rel in _CRITERION_BLOBS:
        blob = _run(["git", "-C", GOV, "show", sha + ":" + rel])
        if not blob:
            return None, "origin/main 缺判準檔 " + rel
        dst = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8", newline="") as fh:
            fh.write(blob)
    with open(stamp, "w", encoding="utf-8") as fh:
        fh.write(sha)
    return root, sha[:12]


def check_simplified(files: list):
    """回 (violations, skipped_reason)。

    ★三類分流（PENDING-646，L0 2026-08-28 裁）：
      ①判準模組不可及／載入失敗 → skipped_reason（明示 SKIPPED＝**未執行，非通過**）
      ②受檢檔之讀取／解碼例外 → **判紅**（列為 violation），不得靜默略過
      ③命中簡體 → 判紅
    """
    root, tag = criterion_root()
    if root is None:
        return [], "判準不可及：" + tag
    ds = os.path.join(root, "00_governance", "fitness", "detect_simplified.py")
    try:
        mod = _load(ds, "_fleet_detect_simplified")
        exclude = getattr(mod, "SELF_EXCLUDE", set())
    except Exception as e:
        return [], "判準模組載入失敗：{}".format(e)
    viol = []
    for f in files:
        if os.path.splitext(f)[1].lower() not in _TEXT_EXT:
            continue
        if os.path.basename(f) in exclude:
            continue
        try:
            with open(f, "rb") as fh:
                raw = fh.read()
        except OSError:
            continue                      # 檔已不在工作樹（如 rename 之舊名）＝非編碼問題
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
        try:
            txt = raw.decode("utf-8")     # ★明示 UTF-8 且**不吞**：原 errors="ignore"
        except UnicodeDecodeError as e:   #   會把非 UTF-8 檔靜默當乾淨
            viol.append((f, "<讀檔編碼例外，判紅：{}>".format(e)))
            continue
        hits = mod.find_simplified(txt)
        if hits:
            viol.append((f, "".join(hits)))
    return viol, None


def check_deliverables(files: list) -> list:
    """staged 之 deliverables/*.docx 跑交付物閘。回 violations（含缺 render.log/md 與簡體）。

    ★審查範圍＝**本次 staged 之 docx 本身**，非其所在目錄（`ADR-0323`，採納 2026-08-28）。
    理由：原以 `dirname(staged)` 為掃描根，會使既有歷史檔因他檔提交被回頭審查——
    修一行 README 即引燃全目錄存量缺口，且該缺口不可由執行層消除
    （補 render.log ＝捏造證據；重跑渲染＝覆蓋已對外交付物）⇒ 形成無出口之擋。
    閘擋新債，存量債以列冊償還（`PENDING-625` 結案、`PENDING-647` 列冊）。

    連帶後果（ADR-0323 明載）：只 stage `.md`／`.render.log` 而未 stage 同名 docx 時不觸發檢查；
    `staged_files()` 之 `--diff-filter=ACM` 本即不含刪除。
    """
    docx = [f for f in files
            if "deliverables/" in f.replace("\\", "/") and f.lower().endswith(".docx")]
    if not docx:
        return [], None
    gate = os.path.join(GOV, "00_governance", "fitness", "check_deliverable_gate.py")
    if not os.path.isfile(gate):
        return [], "交付物閘判準不可及：{}".format(gate)
    try:
        from pathlib import Path
        mod = _load(gate, "_fleet_deliverable_gate")
        res = mod.scan([Path(f) for f in sorted(docx) if os.path.isfile(f)])
        return res.get("violations", []), None
    except Exception as e:
        return [], "交付物閘載入或執行失敗：{}".format(e)


def _skip(msg: str) -> None:
    """★明示 SKIPPED：工具面故障不得計為通過（同本庫「受檢母體 0 ⇒ 判未執行」口徑）。"""
    print("[fleet-gate] SKIPPED（**未執行，非通過**）：{}".format(msg))


def main() -> int:
    if not in_scope():
        return 0
    files = staged_files()
    if files is None:
        _skip("無法取得 staged 清單（git 不可及）")
        return 0
    if not files:
        return 0
    bad = False

    sim, sim_skip = check_simplified(files)
    if sim_skip:
        _skip(sim_skip)
    if sim:
        bad = True
        print("[fleet-gate] ❌ BLOCKING：簡體字命中或讀檔編碼例外（繁體鎖定零容忍，四出口共用判準）")
        for f, hits in sim:
            print("  - {}: {}".format(f, hits))

    dlv, dlv_skip = check_deliverables(files)
    if dlv_skip:
        _skip(dlv_skip)
    if dlv:
        bad = True
        print("[fleet-gate] ❌ BLOCKING：交付物閘未過（③驗證閘，缺一不交付）")
        for v in dlv:
            print("  - {}: 缺 {}".format(v.get('docx'), v.get('missing')))

    if bad:
        _root, _tag = criterion_root()
        print("[fleet-gate] 判準來源 origin/main@{}（釘選，非本機工作樹）".format(_tag))
        print("[fleet-gate] 修正後再 commit；判準源＝治理 repo canonical origin/main（禁另建）。")
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except GateDecodeError as e:
        # ★讀檔／解碼編碼例外**一律判紅**（PENDING-646）：
        #   原本此類例外落入下方通用 fail-open，五次 commit 全印「略過」而 exit 0
        #   ＝閘根本沒跑卻被下游讀成「已檢查且無問題」。
        print("[fleet-gate] ❌ BLOCKING：編碼例外（判紅，非 fail-open）：{}".format(e))
        print("[fleet-gate] 修正：以 UTF-8 儲存受檢檔；或於 UTF-8 模式執行（PYTHONUTF8=1）。")
        sys.exit(1)
    except Exception as e:      # 工具自身故障：明示 SKIPPED，不得計為通過
        print("[fleet-gate] SKIPPED（**未執行，非通過**）：閘自身故障 {}".format(e))
        sys.exit(0)

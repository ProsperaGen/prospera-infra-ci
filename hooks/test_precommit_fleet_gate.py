#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Prospera SYSTEM HEADER (ADR-0032/SBOM) | 設計:Kevin 架構(發明人) | 執行:Claude Code | 驗證:自身即測試(真陽真陰) | IP:創造性歸 Kevin(發明人), AI 為執行工具
"""test_precommit_fleet_gate.py — fleet 級 pre-commit 閘真陽/真陰。

真陽（gate 該擋就擋）：staged 檔含簡體 → 違規；deliverables/*.docx 缺 render.log/md → 違規。
真陰（gate 不該擋就放行）：純繁體 → clean；非本組織 remote → skip；判準源不可及 → fail-open。

★簡體測資一律以 `chr(0x....)` 碼位構造，**禁寫字面簡體字**——
  否則本檔自身會被 repo 的簡體零容忍閘擋下（自我否定測試檔）。

pytest 收集（python -m pytest hooks/ -q），亦可獨立跑：python hooks/test_precommit_fleet_gate.py
"""
import contextlib
import importlib
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import precommit_fleet_gate as g  # noqa: E402

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))

PROS_REMOTE = "https://github.com/ProsperaGen/prospera-client-phoenix.git"
CCK_REMOTE = "https://github.com/ccktaiwan/prospera-os.git"
OTHER_REMOTE = "https://github.com/someoneelse/x.git"

# 簡體測資：一律碼位構造 U+8FD9／U+53D1／U+4E1A／U+56FD（不得寫字面簡體字）
SIMP = "測試內容" + chr(0x8FD9) + chr(0x53D1) + chr(0x4E1A) + chr(0x56FD) + "結尾"
TRAD = "這是純繁體內容，用於真陰測試。交付物驗證閘。"


@contextlib.contextmanager
def temp_repo(remote=PROS_REMOTE, files=None, add=True):
    """建臨時 git repo、寫檔、git add，並 chdir 進去（閘皆以 cwd 為準）。"""
    d = tempfile.mkdtemp(prefix="fleetgate_")
    prev = os.getcwd()
    try:
        subprocess.run(["git", "init", "-q"], cwd=d, check=True,
                       capture_output=True)
        if remote:
            subprocess.run(["git", "remote", "add", "origin", remote], cwd=d,
                           check=True, capture_output=True)
        for rel, content in (files or {}).items():
            p = os.path.join(d, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if isinstance(content, bytes):
                with open(p, "wb") as fh:
                    fh.write(content)
            else:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(content)
        if add:
            subprocess.run(["git", "add", "-A"], cwd=d, check=True,
                           capture_output=True)
        os.chdir(d)
        yield d
    finally:
        os.chdir(prev)
        shutil.rmtree(d, ignore_errors=True)


def _gov_available():
    """判準源（治理 repo canonical）是否可及；不可及時真陽測試無意義（閘 fail-open）。"""
    return os.path.isfile(os.path.join(
        g.GOV, "00_governance", "fitness", "detect_simplified.py"))


# ── 真陽：該擋 ────────────────────────────────────────────────────

def test_simplified_staged_is_violation():
    """真陽①：staged .md 含簡體 → check_simplified 命中且 main() 擋（exit 1）。"""
    if not _gov_available():
        print("[SKIP] 判準源不可及，真陽①無意義")
        return
    with temp_repo(files={"docs/note.md": SIMP}):
        viol = g.check_simplified(g.staged_files())
        assert viol, "簡體 staged 檔應命中，實際 clean（閘漏擋）"
        assert any("note.md" in f for f, _ in viol), f"違規未指名檔案：{viol}"
        assert g.main() == 1, "main() 應回 1 擋 commit"


def test_deliverable_missing_log_and_md_is_violation():
    """真陽②：deliverables/*.docx 缺 render.log 與 md → 交付物閘違規。"""
    if not os.path.isfile(os.path.join(
            g.GOV, "00_governance", "fitness", "check_deliverable_gate.py")):
        print("[SKIP] check_deliverable_gate 不可及")
        return
    with temp_repo(files={"deliverables/report.docx": b"PK\x03\x04fake-docx"}):
        viol = g.check_deliverables(g.staged_files())
        assert viol, "缺 render.log+md 之 docx 應違規，實際放行"
        missing = viol[0].get("missing")
        assert "render.log" in missing and "md" in missing, f"missing 不完整：{missing}"
        assert g.main() == 1, "main() 應回 1 擋 commit"


def test_deliverable_md_simplified_is_violation():
    """真陽③：交付物真相源 .md 含簡體 → 交付物閘違規（③驗證閘之簡體補強）。"""
    if not _gov_available():
        print("[SKIP] 判準源不可及")
        return
    with temp_repo(files={
        "deliverables/r.docx": b"PK\x03\x04fake",
        "deliverables/r.render.log": "rendered ok\n",
        "deliverables/r.md": SIMP,
    }):
        viol = g.check_deliverables(g.staged_files())
        assert viol, "交付物 md 含簡體應違規"
        assert any("簡體" in m for m in viol[0].get("missing", [])), viol


# ── 真陰：不該擋 ──────────────────────────────────────────────────

def test_pure_traditional_is_clean():
    """真陰①：純繁體 staged → 無違規，main() 放行。"""
    with temp_repo(files={"docs/note.md": TRAD, "src/a.py": "# " + TRAD + "\n"}):
        assert g.check_simplified(g.staged_files()) == [], "純繁體被誤擋（假陽）"
        assert g.main() == 0, "純繁體 main() 應回 0"


def test_readme_only_does_not_rescan_existing_deliverables():
    """真陰⑥（ADR-0323 成對驗證②）：目錄內存在缺 sidecar 之**既有** docx，
    本次僅 stage `deliverables/README.md` → 不得回頭審既有檔，必過。

    與真陽②成對：同一目錄、同一缺口，差別只在**該 docx 這次有沒有被 staged**。
    """
    if not os.path.isfile(os.path.join(
            g.GOV, "00_governance", "fitness", "check_deliverable_gate.py")):
        print("[SKIP] check_deliverable_gate 不可及")
        return
    with temp_repo(files={"deliverables/old.docx": b"PKfake-docx",
                          "deliverables/README.md": TRAD}, add=False):
        subprocess.run(["git", "add", "deliverables/README.md"], check=True,
                       capture_output=True)
        staged = g.staged_files()
        assert staged == ["deliverables/README.md"], f"測試前提：只應 stage README，實際 {staged}"
        msg = "既有 docx 不得因他檔提交被回頭審（ADR-0323 存量豁免）"
        assert g.check_deliverables(staged) == [], msg
        assert g.main() == 0, "僅改 README 應放行"


def test_out_of_scope_remote_is_skipped():
    """真陰②：非 ProsperaGen/ccktaiwan remote → 不在範圍，含簡體亦放行。"""
    with temp_repo(remote=OTHER_REMOTE, files={"docs/note.md": SIMP}):
        assert g.in_scope() is False, "someoneelse/x 應判定 out of scope"
        assert g.main() == 0, "out-of-scope repo 不得干擾（應 exit 0）"


def test_in_scope_org_aliases():
    """真陰③補：ProsperaGen 與 ccktaiwan 皆在範圍；無 remote 之新 repo 保守視為在範圍。"""
    with temp_repo(remote=PROS_REMOTE, files={"a.md": TRAD}):
        assert g.in_scope() is True, "ProsperaGen remote 應在範圍"
    with temp_repo(remote=CCK_REMOTE, files={"a.md": TRAD}):
        assert g.in_scope() is True, "ccktaiwan remote 應在範圍"
    with temp_repo(remote=None, files={"a.md": TRAD}):
        assert g.in_scope() is True, "無 remote（新 repo）應保守視為在範圍"


def test_no_staged_files_is_clean():
    """真陰④：無 staged 檔 → 直接放行。"""
    with temp_repo(files={"a.md": SIMP}, add=False):
        assert g.staged_files() == []
        assert g.main() == 0


def test_binary_and_unknown_ext_ignored():
    """真陰⑤：非文字副檔名不掃（避免二進位誤判）。"""
    if not _gov_available():
        print("[SKIP] 判準源不可及")
        return
    with temp_repo(files={"blob.bin": SIMP.encode("utf-8"),
                          "x.docx": SIMP.encode("utf-8")}):
        assert g.check_simplified(g.staged_files()) == [], "非文字副檔名不應被掃"


# ── fail-open：判準源不可及不得 brick commit ──────────────────────

def test_fail_open_when_gov_root_unreachable():
    """fail-open：PROSPERA_GOV_ROOT 指向不存在路徑 → 含簡體亦放行（缺閘不 brick commit）。"""
    prev = os.environ.get("PROSPERA_GOV_ROOT")
    os.environ["PROSPERA_GOV_ROOT"] = os.path.join(
        tempfile.gettempdir(), "prospera_gov_root_does_not_exist_zzz")
    try:
        mod = importlib.reload(g)
        assert not os.path.isdir(mod.GOV), "測試前提：GOV 路徑須不存在"
        with temp_repo(files={"docs/note.md": SIMP,
                              "deliverables/r.docx": b"PK\x03\x04fake"}):
            assert mod.check_simplified(mod.staged_files()) == [], "判準不可及應 fail-open"
            assert mod.check_deliverables(mod.staged_files()) == [], "交付物閘不可及應 fail-open"
            assert mod.main() == 0, "fail-open 下 main() 必須回 0"
    finally:
        if prev is None:
            os.environ.pop("PROSPERA_GOV_ROOT", None)
        else:
            os.environ["PROSPERA_GOV_ROOT"] = prev
        importlib.reload(g)


# ── shim 佈線：pre-commit 必須先跑 fleet 閘再委派本地 hook ─────────

def test_shim_wires_fleet_gate_before_local_delegation():
    """佈線驗證：hooks/pre-commit 內 fleet 閘呼叫必須在本地 hook 委派之前。"""
    shim = os.path.join(HOOK_DIR, "pre-commit")
    txt = open(shim, encoding="utf-8").read()
    assert "precommit_fleet_gate.py" in txt, "shim 未接 fleet 閘"
    i_gate = txt.index("precommit_fleet_gate.py")
    i_local = txt.index('LOCAL="$GITDIR/hooks/pre-commit"')
    assert i_gate < i_local, "fleet 閘必須先於本地 hook 委派"
    # `--git-path` 只可出現於註解（保留原因說明），不得出現於可執行行。
    code = [ln for ln in txt.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    assert not any("--git-path" in ln for ln in code), \
        "可執行行禁用 --git-path（會被 core.hooksPath 改寫致遞迴）"
    assert any("--git-dir" in ln for ln in code), "須以 rev-parse --git-dir 取路徑"
    assert "--git-path" in txt, "應保留 --git-path 之為何不可用註解"
    # ★回歸：Windows 上 `python3` 常是 WindowsApps stub（rc=49、無輸出），
    #   只用 command -v 探測會命中它 → 閘永遠不跑卻靜默放行（實測踩過）。
    assert '"$c" -c "import sys"' in txt, \
        "直譯器探測須實際執行，否則會命中 WindowsApps python3 stub"
    assert '[ "$rc" -eq 1 ] && exit 1' in txt, "須只對違規碼 1 攔截（其餘 fail-open）"


# ── 獨立執行入口 ─────────────────────────────────────────────────

def _run_standalone() -> int:
    fails = []
    tests = [(n, o) for n, o in sorted(globals().items())
             if n.startswith("test_") and callable(o)]
    print("=== fleet 級 pre-commit 閘 真陽/真陰 ===")
    for name, fn in tests:
        try:
            fn()
            print(f"  [PASS] {name}")
        except AssertionError as e:
            print(f"  [FAIL] {name}: {e}")
            fails.append(name)
        except Exception as e:                       # noqa: BLE001
            print(f"  [ERROR] {name}: {type(e).__name__}: {e}")
            fails.append(name)
    print(f"\n結果：{'全過' if not fails else '敗: ' + ', '.join(fails)}"
          f"（{len(tests) - len(fails)}/{len(tests)}）")
    return 0 if not fails else 1


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    sys.exit(_run_standalone())

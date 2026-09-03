#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Prospera SYSTEM HEADER (ADR-0032/SBOM) | 設計:Kevin 架構(發明人) | 執行:Claude Code | 驗證:自身即測試(真陽真陰) | IP:創造性歸 Kevin(發明人), AI 為執行工具
"""test_precommit_fleet_gate.py — fleet 級 pre-commit 閘真陽/真陰。

真陽（gate 該擋就擋）：staged 檔含簡體 → 違規；deliverables/*.docx 缺 render.log/md → 違規。
真陰（gate 不該擋就放行）：純繁體 → clean；非本組織 remote → skip；判準源不可及 → fail-open。
xlsx 真閘六案（判準 2026-09-04 收窄）：只以 `t="inlineStr"` >0 退件；
  **缺 `xl/sharedStrings.xml` 不再是退件理由**（純數值檔合法無 sharedStrings）。

★簡體測資一律以 `chr(0x....)` 碼位構造，**禁寫字面簡體字**——
  否則本檔自身會被 repo 的簡體零容忍閘擋下（自我否定測試檔）。

pytest 收集（python -m pytest hooks/ -q），亦可獨立跑：python hooks/test_precommit_fleet_gate.py
"""
import contextlib
import importlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

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


# ── xlsx inlineStr 真閘 六案（判準 2026-09-04 收窄：只留 inlineStr>0 即退件）──
#   ★「缺 sharedStrings 即退件」已自判準刪除；案②③⑥即該變更之行為級證據。
#   測試用 xlsx 一律**即時產生**（openpyxl／zipfile 手工組），不進二進位檔入 repo。
#   ★不吃 pytest fixture（_run_standalone 以 fn() 直呼），一律經 `g.` 取用函式。

def _xlsx_bytes(shared: bool, inline: int) -> bytes:
    """手工組最小 xlsx。shared=是否含 xl/sharedStrings.xml；inline=t="inlineStr" 格數。"""
    if inline:
        cells = "".join(f'<c r="A{i + 1}" t="inlineStr"><is><t>x{i}</t></is></c>'
                        for i in range(inline))
    else:
        cells = '<c r="A1"><v>123</v></c>'
    sheet = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             f'<sheetData><row r="1">{cells}</row></sheetData></worksheet>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("xl/workbook.xml", "<workbook/>")
        z.writestr("xl/worksheets/sheet1.xml", sheet)
        if shared:
            z.writestr("xl/sharedStrings.xml",
                       '<sst count="1" uniqueCount="1"><si><t>x</t></si></sst>')
    return buf.getvalue()


def _numeric_xlsx_bytes() -> bytes:
    """第六案素材：純數值、完全無字串之 xlsx（openpyxl 直出；無 openpyxl 則手工組）。"""
    try:
        from openpyxl import Workbook
    except Exception:                                # noqa: BLE001
        print("      [note] openpyxl 不可用 → 改以 zipfile 手工組純數值 xlsx")
        return _xlsx_bytes(shared=False, inline=0)
    wb = Workbook()
    ws = wb.active
    for r, row in enumerate([[1, 2.5, 3], [4, 5, 6.75]], start=1):
        for c, v in enumerate(row, start=1):
            ws.cell(row=r, column=c, value=v)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _probe(data: bytes):
    """回 (是否含 sharedStrings, worksheets 內 inlineStr 計數)——供 fixture 自我驗證與逐案報表。"""
    z = zipfile.ZipFile(io.BytesIO(data))
    names = z.namelist()
    n = sum(z.read(x).decode("utf-8", errors="ignore").count('t="inlineStr"')
            for x in names
            if x.startswith("xl/worksheets/") and x.endswith(".xml"))
    return ("xl/sharedStrings.xml" in names), n


def _xlsx_case(title, rel, data, expect_block, expect_shared, expect_inline):
    """跑單案並印「案名 → 預期 → 實際 → 通過與否」。expect_block=True 表應退件。"""
    shared, inline = _probe(data)
    # fixture 自我驗證：素材若不是宣稱的形狀，該案等於沒測到判準（假通過）
    assert shared is expect_shared, \
        f"{title}：素材 sharedStrings 應為 {expect_shared}，實際 {shared}（fixture 失真）"
    assert inline == expect_inline, \
        f"{title}：素材 inlineStr 應為 {expect_inline}，實際 {inline}（fixture 失真）"
    with temp_repo(files={rel: data}):
        viol = g.check_xlsx_shared_strings(g.staged_files())
        actual_block = bool(viol)
        exp_s = "退件" if expect_block else "放行"
        act_s = "退件" if actual_block else "放行"
        detail = viol[0]["msg"] if viol else "無違規"
        print(f"    {title}｜素材: sharedStrings={shared}/inlineStr={inline}"
              f"｜預期: {exp_s}｜實際: {act_s}（{detail}）"
              f"｜{'PASS' if actual_block == expect_block else 'FAIL'}")
        assert actual_block == expect_block, \
            f"{title}：預期{exp_s}，實際{act_s}｜viol={viol}"
        # 行為級：main() 退出碼。簡體判準源不可及時 main() 恆回哨兵違規，該斷言無意義故略過。
        if _gov_available():
            rc = g.main()
            assert rc == (1 if expect_block else 0), \
                f"{title}：main() 應回 {1 if expect_block else 0}，實際 {rc}"


def test_xlsx_case1_shared_present_no_inline_passes():
    """案①（真陰）：有 sharedStrings、inlineStr=0（soffice round-trip 後之形狀）→ 放行。"""
    _xlsx_case("案①有 sharedStrings + inlineStr=0", "deliv/a.xlsx",
               _xlsx_bytes(shared=True, inline=0),
               expect_block=False, expect_shared=True, expect_inline=0)


def test_xlsx_case2_no_shared_no_inline_passes():
    """案②（判準變更核心，真陰）：缺 sharedStrings 但 inlineStr=0 → 必須放行，不得退件。"""
    _xlsx_case("案②缺 sharedStrings + inlineStr=0", "deliv/b.xlsx",
               _xlsx_bytes(shared=False, inline=0),
               expect_block=False, expect_shared=False, expect_inline=0)


def test_xlsx_case3_no_shared_with_inline_blocks():
    """案③（真陽，變更後新可達分支）：缺 sharedStrings 且 inlineStr=3（openpyxl 直出含字串之形狀）→ 退件。

    改前此路徑在「缺 sharedStrings」即 continue，根本沒數過 inlineStr；本案守住該回歸。
    """
    _xlsx_case("案③缺 sharedStrings + inlineStr=3", "deliv/c.xlsx",
               _xlsx_bytes(shared=False, inline=3),
               expect_block=True, expect_shared=False, expect_inline=3)


def test_xlsx_case4_shared_present_with_inline_blocks():
    """案④（真陽）：有 sharedStrings 但仍殘留 inlineStr=2 → 退件（唯一保留判準）。"""
    _xlsx_case("案④有 sharedStrings + inlineStr=2", "deliv/d.xlsx",
               _xlsx_bytes(shared=True, inline=2),
               expect_block=True, expect_shared=True, expect_inline=2)


def test_xlsx_case5_working_dir_is_skipped():
    """案⑤（真陰）：`_working/` 為迭代區，即使 inlineStr=3 亦略過放行（交付/迭代二階）。"""
    _xlsx_case("案⑤_working/ 下 inlineStr=3", "_working/e.xlsx",
               _xlsx_bytes(shared=False, inline=3),
               expect_block=False, expect_shared=False, expect_inline=3)


def test_xlsx_case6_pure_numeric_no_strings_passes():
    """案⑥（新增，真陰）：純數值、完全無字串之 xlsx（無 sharedStrings 亦無 inlineStr）→ 放行。

    openpyxl 直出純數值檔實測 namelist 無 `xl/sharedStrings.xml`；舊判準會誤擋（假陽）。
    """
    _xlsx_case("案⑥純數值無字串（openpyxl 直出）", "deliv/f.xlsx",
               _numeric_xlsx_bytes(),
               expect_block=False, expect_shared=False, expect_inline=0)


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

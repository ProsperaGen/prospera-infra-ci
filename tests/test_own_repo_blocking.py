# -*- coding: utf-8 -*-
# Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:test | 設計:Kevin 架構(發明人) | 執行:AI 工具(Claude Code) | 驗證:本檔即驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具
"""序52（L0 Kevin 2026-09-16，卡5 選 A）「我方庫擋下／客戶庫記錄級」成對測試。

受測兩處（判準須一致）：
  (1) scripts/governance_check.py —— warnings 於我方庫併入 violations（結束碼 1）
  (2) .github/workflows/reusable-governance.yml「PENDING 格式閘」heredoc —— 我方庫有 issues 即結束碼 1

測法：
  - (1) 以 importlib 載入測判準函式，並以子行程在 tmp 目錄實跑（缺 CONTRACT.md＝警告）。
  - (2) 從 yml 以純字串抽出 heredoc 原文（CI 只裝 pytest，不 import yaml），在 tmp 目錄實跑。
  - 同一張測資表驅動兩處，並比對兩處常數行逐字一致（防名單漂移）。
  - fail-closed：GITHUB_REPOSITORY 為空字串或未設定 → 擋。
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GOV_CHECK = REPO_ROOT / "scripts" / "governance_check.py"
REUSABLE_GOV = REPO_ROOT / ".github" / "workflows" / "reusable-governance.yml"

_UNSET = object()

# (庫名, 預期是否擋下, 說明)
CASES = [
    ("ProsperaGen/prospera-blueprint-ip", True, "我方庫"),
    ("ProsperaGen/prospera-os", True, "我方庫"),
    ("ProsperaGen/prospera-infra-ci", True, "我方庫"),
    ("ProsperaGen/prospera-standard-ip", True, "我方庫"),
    ("ProsperaGen/prospera-client-phoenix", False, "客戶庫"),
    ("ProsperaGen/prospera-client-buddhayana", False, "客戶庫（curl 版 governance_check 呼叫者）"),
    ("prosperagen/prospera-client-yuandao-guanyin", False, "客戶庫（owner 小寫）"),
    ("ProsperaGen/prospera-product-client-template", False, "客戶範本"),
    ("", True, "空字串 fail-closed"),
    ("   ", True, "空白 fail-closed"),
    (_UNSET, True, "未設定 fail-closed"),
    # ── 以下為「命名依賴風險」之現況釘選（非期望行為背書，名單改變時此處須同步改）──
    ("ProsperaGen/prospera-client-prosperagen", False, "風險1：我方租戶符合前綴被放行"),
    ("ProsperaGen/some-future-customer", True, "風險2：不依前綴命名之客戶庫被擋"),
    ("OtherOrg/prospera-client-x", True, "非本 org 不算客戶"),
    ("ProsperaGen/prospera-product-client-template-v2", True, "範本為精確比對"),
]


def _ids(cases):
    return ["<未設定>" if c[0] is _UNSET else (c[0] or "<空字串>") for c in cases]


def _load_gov_check():
    spec = importlib.util.spec_from_file_location("governance_check_under_test", GOV_CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _extract_pending_heredoc():
    """抽出「PENDING 格式閘」步驟 heredoc 之 python 原文（純字串切割）。"""
    lines = REUSABLE_GOV.read_text(encoding="utf-8").splitlines()
    step = next(i for i, l in enumerate(lines) if "name: PENDING 格式閘" in l)
    start = next(i for i in range(step, len(lines)) if "<<'PY'" in lines[i])
    end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "PY")
    body = lines[start + 1:end]
    indent = len(body[0]) - len(body[0].lstrip())
    return "\n".join(l[indent:] if l.strip() else "" for l in body) + "\n"


def _env(repo):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env.pop("GITHUB_REPOSITORY", None)
    if repo is not _UNSET:
        env["GITHUB_REPOSITORY"] = repo
    return env


def _run_heredoc(cwd, repo):
    code = _extract_pending_heredoc()
    return subprocess.run([sys.executable, "-c", code], cwd=str(cwd), env=_env(repo),
                          capture_output=True, text=True, encoding="utf-8")


def _run_gov_check(cwd, repo):
    return subprocess.run([sys.executable, str(GOV_CHECK)], cwd=str(cwd), env=_env(repo),
                          capture_output=True, text=True, encoding="utf-8")


# ── 判準函式 ──
@pytest.mark.parametrize("repo,block,why", CASES, ids=_ids(CASES))
def test_gov_check_classifier(repo, block, why):
    mod = _load_gov_check()
    arg = None if repo is _UNSET else repo
    assert mod.is_client_repo(arg) is (not block), why


def test_client_list_constants_identical_in_both_places():
    """名單常數兩處逐字一致（防漂移）。"""
    src = GOV_CHECK.read_text(encoding="utf-8").splitlines()
    wf = [l.strip() for l in _extract_pending_heredoc().splitlines()]
    for name in ("CLIENT_REPO_PREFIXES", "CLIENT_REPO_EXACT"):
        a = [l.strip() for l in src if l.startswith(name + " =")]
        b = [l for l in wf if l.startswith(name + " =")]
        assert len(a) == 1 and len(b) == 1, name
        assert a == b, f"{name} 兩處不一致：{a} vs {b}"


# ── 52-2：reusable-governance PENDING 格式閘實跑 ──
@pytest.mark.parametrize("repo,block,why", CASES, ids=_ids(CASES))
def test_pending_gate_with_issue(tmp_path, repo, block, why):
    (tmp_path / "bad.md").write_text("待辦 PENDING-ART-031 格式錯\n", encoding="utf-8")
    r = _run_heredoc(tmp_path, repo)
    assert r.returncode == (1 if block else 0), f"{why}\n{r.stdout}\n{r.stderr}"


@pytest.mark.parametrize("repo,block,why", CASES, ids=_ids(CASES))
def test_pending_gate_clean_never_blocks(tmp_path, repo, block, why):
    (tmp_path / "ok.md").write_text("待辦 PENDING-031 格式正確\n", encoding="utf-8")
    r = _run_heredoc(tmp_path, repo)
    assert r.returncode == 0, f"{why}\n{r.stdout}\n{r.stderr}"


# ── 52-4：governance_check.py 實跑（缺 CONTRACT.md＝警告）──
@pytest.mark.parametrize("repo,block,why", CASES, ids=_ids(CASES))
def test_gov_check_warning(tmp_path, repo, block, why):
    r = _run_gov_check(tmp_path, repo)
    assert "CONTRACT.md missing" in r.stdout
    assert r.returncode == (1 if block else 0), f"{why}\n{r.stdout}\n{r.stderr}"


@pytest.mark.parametrize("repo,block,why", CASES, ids=_ids(CASES))
def test_gov_check_clean_never_blocks(tmp_path, repo, block, why):
    (tmp_path / "CONTRACT.md").write_text("# contract\n", encoding="utf-8")
    r = _run_gov_check(tmp_path, repo)
    assert r.returncode == 0, f"{why}\n{r.stdout}\n{r.stderr}"


# ── 附帶：繁體中文強制閘字集由字面改 \x{碼位}（fleet 簡體閘會擋字面），驗證等價不弱化 ──
# 原字面 10 字之碼位（本檔不留字面簡體）
_ORIGINAL_CODEPOINTS = [0x8FD9, 0x8BF4, 0x9879, 0x5B9E, 0x8BE5, 0x4E0E, 0x5BF9, 0x4ECE, 0x5C06, 0x5E94]


def _simplified_gate_pattern():
    import re
    text = REUSABLE_GOV.read_text(encoding="utf-8")
    m = re.search(r"LC_ALL=C\.UTF-8 grep -rP '([^']+)'", text)
    assert m, "繁體中文強制閘須以 LC_ALL=C.UTF-8 固定語系（C 語系下 \\x{} 報錯＝靜默放行）"
    return m.group(1)


def test_simplified_gate_pattern_equivalent():
    import re
    pat = _simplified_gate_pattern()
    cps = [int(h, 16) for h in re.findall(r"\\x\{([0-9a-fA-F]+)\}", pat)]
    assert cps == _ORIGINAL_CODEPOINTS
    assert pat == "|".join(r"\x{%04x}" % c for c in _ORIGINAL_CODEPOINTS)


# Windows 下由非 msys 行程叫 Git for Windows 之 grep，語系環境變數不生效（實測 -P 對 \x{} 恆回 1），
# 故僅在 POSIX（CI ubuntu-latest＝閘實際執行環境）跑行為測試；字集等價由上一支測試在各平台驗。
@pytest.mark.skipif(os.name == "nt" or __import__("shutil").which("grep") is None,
                    reason="非 POSIX 或無 grep（行為以 CI ubuntu 為準）")
def test_simplified_gate_grep_behaviour(tmp_path):
    pat = _simplified_gate_pattern()
    hit, clean = tmp_path / "hit", tmp_path / "clean"
    hit.mkdir(); clean.mkdir()
    for i, c in enumerate(_ORIGINAL_CODEPOINTS):
        (hit / f"h{i}.md").write_text("前文" + chr(c) + "後文\n", encoding="utf-8")
    (clean / "c.md").write_text("這說項實該與對從將應\n", encoding="utf-8")
    env = dict(os.environ, LC_ALL="C.UTF-8")
    r = subprocess.run(["grep", "-rlP", pat, "--include=*.md", str(hit)], env=env, capture_output=True)
    assert r.returncode == 0 and len(r.stdout.splitlines()) == len(_ORIGINAL_CODEPOINTS), r.stderr
    r = subprocess.run(["grep", "-rlP", pat, "--include=*.md", str(clean)], env=env, capture_output=True)
    assert r.returncode == 1, r.stderr

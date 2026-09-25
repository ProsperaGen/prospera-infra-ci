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


def test_heredoc_extraction_matches_yaml_parse():
    """字串切割抽出之 heredoc 須與 YAML 解析後 run 內容逐字相同（防縮排問題致 Actions 實跑另一份）。

    CI 只裝 pytest，無 PyYAML 時略過；本機有 yaml 時必跑。
    """
    yaml = pytest.importorskip("yaml")
    doc = yaml.safe_load(REUSABLE_GOV.read_text(encoding="utf-8"))
    steps = doc["jobs"]["governance-check"]["steps"]
    run = next(s["run"] for s in steps if s.get("name", "").startswith("PENDING 格式閘"))
    lines = run.splitlines()
    start = next(i for i, l in enumerate(lines) if "<<'PY'" in l)
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == "PY")
    assert "\n".join(lines[start + 1:end]) + "\n" == _extract_pending_heredoc()


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
    (tmp_path / "bad.md").write_text("待辦 PENDING-31 格式錯\n", encoding="utf-8")
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


# ── 2026-09-25：PENDING 格式接受代號（PENDING-<2～5 大寫字母>-<三位數字>）──
@pytest.mark.parametrize("text,ok,why", [
    ("PENDING-ART-031", True, "真陽：客戶命名空間編號"),
    ("PENDING-031", True, "三位數字"),
    ("PENDING-AR-031", True, "誤判情境一：代號拼錯但格式合法，本檢查只查格式"),
    ("PENDING-GOV-031", True, "誤判情境三：代號與治理庫前綴相同不視為撞號"),
    ("PENDING-31", False, "真陰：兩位數字"),
    ("PENDING-ART-31", False, "真陰：代號後兩位數字"),
    ("PENDING-art-031", False, "誤判情境二：小寫代號正確拒絕"),
    ("PENDING-Y01", True, "治理庫既有：單字母＋兩位數"),
    ("PENDING-GENPACE-IP-01", True, "治理庫既有：代號－兩字母－兩位數"),
    ("PENDING-CLAUDE-UPDATE", True, "治理庫既有：代號－英文字"),
])
def test_pending_format_namespaced(tmp_path, text, ok, why):
    (tmp_path / "x.md").write_text(f"待辦 {text}\n", encoding="utf-8")
    r = _run_heredoc(tmp_path, "ProsperaGen/prospera-blueprint-ip")
    assert r.returncode == (0 if ok else 1), f"{why}\n{r.stdout}\n{r.stderr}"
    if text == "PENDING-art-031":
        assert "大寫" in r.stdout

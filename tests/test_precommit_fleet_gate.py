# -*- coding: utf-8 -*-
# Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:test | 設計:Kevin 架構(發明人) | 執行:AI 工具(Claude Code) | 驗證:本檔即驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具
"""precommit_fleet_gate 之行為級驗證（真陽／真陰／缺閘可見）。

★為何存在（2026-08-31，PENDING-646）：
  hook 檔頭宣稱「驗證:test_precommit_fleet_gate 真陽真陰」，但該測試檔**實際不存在**
  ——宣稱與實作不符本身就是 KF-028 族（保護面窄於發生面）。本檔補上。

判準模組以 tmp 內之 stub 注入（PROSPERA_GOV_ROOT），使測試在 CI 上不依賴治理 repo 之
checkout；測的是 hook 的**接線與失敗可見性**，非 detect_simplified 之字集本身
（後者由治理 repo 自己的 test_detect_simplified 負責，禁另建字集）。

本檔內一律以 \\uXXXX 轉義表示簡體字，不留字面簡體，避免自撞 fleet 簡體閘。
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = str(Path(__file__).resolve().parents[1] / "hooks" / "precommit_fleet_gate.py")

# 簡體樣本：\u9019\u500b\u6E2C\u8A66 之簡體對應（以轉義寫入，本檔不留字面簡體）
SIMPLIFIED_SAMPLE = "\u8fd9\u4e2a\u6d4b\u8bd5"

STUB_DETECTOR = (
    "# -*- coding: utf-8 -*-\n"
    "SELF_EXCLUDE = {'detect_simplified.py'}\n"
    "_CHARS = set('\\u8fd9\\u4e2a\\u6d4b\\u8bd5')\n"
    "def find_simplified(text):\n"
    "    return sorted({c for c in text if c in _CHARS})\n"
)


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


def _make_repo(tmp_path, remote="https://github.com/ProsperaGen/fake-repo.git"):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", ".")
    if remote:
        _git(repo, "remote", "add", "origin", remote)
    return repo


def _make_gov(tmp_path, detector_src=STUB_DETECTOR):
    gov = tmp_path / "gov"
    d = gov / "00_governance" / "fitness"
    d.mkdir(parents=True)
    (d / "detect_simplified.py").write_text(detector_src, encoding="utf-8")
    return gov


def _run(repo, gov_root):
    env = dict(os.environ)
    env["PROSPERA_GOV_ROOT"] = str(gov_root)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, HOOK], cwd=str(repo), env=env,
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def _stage(repo, name, text):
    (repo / name).write_text(text, encoding="utf-8")
    _git(repo, "add", name)


def test_真陰_乾淨檔通過(tmp_path):
    repo = _make_repo(tmp_path)
    gov = _make_gov(tmp_path)
    _stage(repo, "clean.md", "\u7e41\u9ad4\u6e2c\u8a66\u5167\u5bb9\n")
    r = _run(repo, gov)
    assert r.returncode == 0, r.stdout + r.stderr


def test_真陽_簡體檔擋下(tmp_path):
    repo = _make_repo(tmp_path)
    gov = _make_gov(tmp_path)
    _stage(repo, "bad.md", SIMPLIFIED_SAMPLE + "\n")
    r = _run(repo, gov)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "bad.md" in r.stdout


def test_判準檔不存在_不得靜默放行(tmp_path):
    """PENDING-646 核心：改前 return [] ⇒ 與「零違規」不可分辨，靜默放行全部。"""
    repo = _make_repo(tmp_path)
    _stage(repo, "bad.md", SIMPLIFIED_SAMPLE + "\n")
    r = _run(repo, tmp_path / "no_such_gov")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "BLOCKING" in r.stdout
    assert "PROSPERA_GOV_ROOT" in r.stdout


def test_判準模組載入失敗_不得靜默放行(tmp_path):
    repo = _make_repo(tmp_path)
    gov = _make_gov(tmp_path, detector_src="raise RuntimeError('boom')\n")
    _stage(repo, "bad.md", SIMPLIFIED_SAMPLE + "\n")
    r = _run(repo, gov)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "BLOCKING" in r.stdout
    assert "boom" in r.stdout


def test_單檔讀取失敗_印WARN指名該檔且不擋整次commit(tmp_path):
    """單檔壞掉不 brick 整次 commit（保留），但不得靜默——需指名該檔未受檢。"""
    repo = _make_repo(tmp_path)
    gov = _make_gov(tmp_path)
    _stage(repo, "ghost.md", "\u7e41\u9ad4\n")
    (repo / "ghost.md").unlink()          # staged 仍列出，實體已不在 ⇒ 讀取必然失敗
    r = _run(repo, gov)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "WARN" in r.stdout
    assert "ghost.md" in r.stdout


def test_範圍外remote_一律放行(tmp_path):
    repo = _make_repo(tmp_path, remote="https://github.com/someone-else/other.git")
    _stage(repo, "bad.md", SIMPLIFIED_SAMPLE + "\n")
    r = _run(repo, tmp_path / "no_such_gov")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "BLOCKING" not in r.stdout

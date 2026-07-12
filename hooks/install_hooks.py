#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Prospera SYSTEM HEADER (ADR-0032/SBOM) | 設計:Kevin 架構 | 執行:Claude Code | 驗證:install 後 git config 實查 | IP:創造性歸 Kevin(發明人)
"""install_hooks.py — 把 pre-execution 成本閘裝成 global core.hooksPath（fleet 零缺口）。

一鍵覆蓋本機所有 git repo（含未來 clone）；hook 本體自 scope，只對 ProsperaGen remote 生效。
反安裝：git config --global --unset core.hooksPath
"""
import os
import stat
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    posix = HOOKS_DIR.replace("\\", "/")
    # 1. 設 global core.hooksPath
    r = subprocess.run(["git", "config", "--global", "core.hooksPath", posix],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("[install] ✗ 設 core.hooksPath 失敗：", r.stderr)
        return 1
    # 2. pre-push 可執行位（Git Bash 尊重）
    pp = os.path.join(HOOKS_DIR, "pre-push")
    try:
        os.chmod(pp, os.stat(pp).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    except Exception as e:
        print("[install] ⚠ chmod pre-push 略過：", e)
    # 3. 驗證讀回
    got = subprocess.run(["git", "config", "--global", "--get", "core.hooksPath"],
                         capture_output=True, text=True).stdout.strip()
    ok = got == posix
    print(f"[install] core.hooksPath = {got}  {'✅' if ok else '✗ 不符 '+posix}")
    print(f"[install] pre-push hook = {pp} {'(存在)' if os.path.isfile(pp) else '(缺!)'}")
    print("[install] 覆蓋範圍：本機所有 git repo（含未來 clone）；hook 只對 ProsperaGen remote 生效。")
    print("[install] 反安裝：git config --global --unset core.hooksPath")
    return 0 if ok and os.path.isfile(pp) else 1


if __name__ == "__main__":
    sys.exit(main())

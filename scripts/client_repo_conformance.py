# -*- coding: utf-8 -*-
# SSOT＝prospera-constitution-governance/00_governance/repo_governance/client_repo_conformance.py，本檔為鏡像
# Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:engineering(L1 顧客repo conformance checker,observe預設/--strict阻斷) | 設計:Kevin 架構(發明人) | 執行:AI 工具(Claude Code) | 驗證:test_client_repo_conformance 真陰真陽 | IP:創造性歸 Kevin(發明人), AI 為執行工具
"""client_repo_conformance.py — L1 顧客 repo 構件協定機器強制。

協定 SSOT：00_governance/CLIENT_REPO_CONFORMANCE_PROTOCOL.md（現況必備基線，非 Gen-C 終態）。
零影響紅線：只驗不改；預設 observe（缺項 WARN 但 exit 0），--strict 才 exit 1。

用法：
  python client_repo_conformance.py <repo_path>            # observe：報告 + exit 0
  python client_repo_conformance.py <repo_path> --strict   # blocking：缺必備 exit 1
  python client_repo_conformance.py <repo_path> --json      # 機器可讀
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# ── 必備構件（現況基線，以 phoenix 實證反推；SSOT=CLIENT_REPO_CONFORMANCE_PROTOCOL.md）──
REQUIRED_FILES = ["CLAUDE.md", "CONTAINER_IDENTITY.md", "CONTRACT.md", "manifest.json"]
REQUIRED_DIRS = ["00_identity", "00_legal/compliance", "01_ground_truth"]  # L2 結構亦驗此節
REQUIRED_COMPLIANCE = ["00_legal/compliance/DATA_BOUNDARY.md",
                       "00_legal/compliance/DATA_SECURITY_SELF_ASSESSMENT.md"]
REQUIRED_CI_GLOB = ".github/workflows"  # 至少一個 *.yml


def check_repo(repo: Path) -> dict:
    """回傳 conformance 結果 dict：{pass, missing:{files,dirs,compliance,ci}}。"""
    missing = {"files": [], "dirs": [], "compliance": [], "ci": []}
    for f in REQUIRED_FILES:
        if not (repo / f).is_file():
            missing["files"].append(f)
    for d in REQUIRED_DIRS:
        if not (repo / d).is_dir():
            missing["dirs"].append(d)
    for c in REQUIRED_COMPLIANCE:
        if not (repo / c).is_file():
            missing["compliance"].append(c)
    ci_dir = repo / REQUIRED_CI_GLOB
    if not (ci_dir.is_dir() and any(ci_dir.glob("*.yml"))):
        missing["ci"].append(f"{REQUIRED_CI_GLOB}/*.yml")
    total_missing = sum(len(v) for v in missing.values())
    return {"repo": str(repo), "pass": total_missing == 0, "missing": missing,
            "missing_count": total_missing}


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    strict = "--strict" in argv
    as_json = "--json" in argv
    if not args:
        print("用法：python client_repo_conformance.py <repo_path> [--strict] [--json]")
        return 2
    repo = Path(args[0])
    if not repo.is_dir():
        print(f"[FAIL] repo 路徑不存在：{repo}")
        return 2
    res = check_repo(repo)
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        if res["pass"]:
            print(f"[PASS] {repo.name} L1 conformance 全備（files/dirs/compliance/ci）")
        else:
            tag = "FAIL" if strict else "WARN"
            print(f"[{tag}] {repo.name} L1 conformance 缺 {res['missing_count']} 項：")
            for k, v in res["missing"].items():
                for item in v:
                    print(f"    - {k}: {item}")
            if not strict:
                print("  （observe 模式，exit 0；--strict 啟用阻斷）")
    if not res["pass"] and strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

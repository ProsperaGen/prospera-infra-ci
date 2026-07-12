#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ── Prospera SYSTEM HEADER (ADR-0032/SBOM) ──
# 性質:engineering ｜設計:Kevin 架構 ｜執行:AI 工具(claude.ai+Claude Code)
# 驗證:無機制驗證 ｜IP:創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032)
"""
集中式治理 producer 邏輯（單一真源，SSOT）。

由各 repo 的 .github/workflows/governance_check.yml（job id=governance-check，
= branch protection required context）以 curl 取本檔後執行。改邏輯只改此一處，
全生態系下次 run 自動生效 —— 解 PENDING-024 的「required check 無 producer / 護欄劇場」。

退出碼語意：
  0 = 通過（含 validation 警告，non-blocking）
  1 = 硬違規（DIRECTORY_SCHEMA 目錄違規 / Fitness A 本體 hardcode）→ 擋 PR

來源：2026-06-09 L3 治理稽核 root-cause-1 修復。runner：ubuntu-latest / python3 stdlib only。
"""
import json
import subprocess
import sys
from pathlib import Path

# Windows cp950 console 下 print emoji 會 UnicodeEncodeError，強制 stdout 為 utf-8。
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass  # Python < 3.7 無 reconfigure；CI runner 為 ubuntu/python3 不受影響

ROOT = Path(".")
warnings: list[str] = []
violations: list[str] = []


def check_contract():
    if (ROOT / "CONTRACT.md").exists():
        print("✅ CONTRACT.md found")
    else:
        warnings.append("CONTRACT.md missing — 建議補齊以符合 ECOSYSTEM_DESIGN_v3.0")
        print("⚠️ CONTRACT.md missing")


def check_binaries():
    found = []
    for ext in ("*.exe", "*.dll", "*.zip"):
        for p in ROOT.rglob(ext):
            s = str(p)
            if ".git" in s or "99_archive" in s:
                continue
            found.append(s)
            if len(found) >= 5:
                break
    if found:
        warnings.append("forbidden binaries: " + ", ".join(found))
        print("⚠️ Forbidden binaries:", found)
    else:
        print("✅ No forbidden binaries")


def check_directory_schema():
    schema_file = ROOT / "DIRECTORY_SCHEMA.json"
    if not schema_file.exists():
        print("ℹ️ no DIRECTORY_SCHEMA.json — skip dir-schema (non-os repo)")
        return
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    canonical = set(schema["canonical_dirs"].keys())
    forbidden = set(schema["forbidden_root_dirs"])
    for d in ROOT.iterdir():
        if d.name.startswith(".") or not d.is_dir():
            continue
        if d.name in forbidden:
            violations.append(f"FORBIDDEN root dir: {d.name}")
        elif d.name[0].isdigit() and d.name not in canonical:
            violations.append(f"UNKNOWN numbered dir: {d.name}")
    # 註：非數字未知目錄之白名單收緊屬 DIR-03(low)，另案，本處不擋。
    if not violations:
        n = sum(1 for x in ROOT.iterdir() if x.is_dir())
        print(f"✅ directory schema OK — {n} dirs checked")


def check_fitness():
    f = ROOT / "governance" / "fitness" / "check_ontology_hardcode.py"
    if not f.exists():
        return
    print("▶ Fitness A — ontology hardcode guard")
    r = subprocess.run([sys.executable, str(f), "."], capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stdout.write(r.stderr)
        violations.append("Fitness A — ontology hardcode 違規（本體進 runtime，D2 防再生）")


def check_pii_chokepoint():
    """PII 儲存咽喉靜態閘（四面一體鏈 STEP 1）：repo-local opt-in——僅 repo 含此 checker 才跑。

    掃「PII 路徑（journey duckdb / .pseudonym_salt）的直接 open()/DuckKVStore()」繞過 02_kernel/
    pii_storage.py 咽喉 → 硬違規擋 PR。非 os repo（無此 checker）自動 skip，不影響其餘生態系。
    """
    f = ROOT / "bi_ingestion" / "pii_chokepoint_check.py"
    if not f.exists():
        return  # repo-local：非 os repo 無此 checker → skip（不影響 38 repo）
    print("▶ PII 咽喉靜態閘 — 掃 PII 路徑直接 open() 繞過咽喉")
    r = subprocess.run([sys.executable, str(f)], capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stdout.write(r.stderr)
        violations.append("PII 咽喉 — 有 PII 路徑直接 open()/DuckKVStore 繞過 02_kernel/pii_storage.py（個資隔離破口）")


def main():
    print("=== Prospera Governance Check (central producer) ===")
    check_contract()
    check_binaries()
    check_directory_schema()
    check_fitness()
    check_pii_chokepoint()

    if warnings:
        print("\n-- WARNINGS (non-blocking) --")
        for w in warnings:
            print("  ⚠️", w)
    if violations:
        print("\n❌ GOVERNANCE CHECK FAILED:")
        for v in violations:
            print("  ✗", v)
        sys.exit(1)
    print("\n✅ governance-check PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()

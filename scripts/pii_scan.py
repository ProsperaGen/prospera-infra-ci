#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:tool(個人層 PII 樣式掃描器,阻斷級 CI 閘本體) | 設計:Kevin 架構(發明人, 2026-07-22 Tier 0 核准)
# 執行:AI 工具(Claude Code) | 驗證:--selftest 真陽真陰 + 合成假 PII 注入實測真阻擋 | IP:創造性歸 Kevin(發明人), AI 為執行工具
"""pii_scan — 個人層 PII 落 git 之阻斷級掃描器（DATA_BOUNDARY `AUTONOMY_RULES §18` 之機器閘）。

★**為何需要本檔**（PENDING-394）：client repo 之 PII 紅線原本**只有 `.gitignore`**（2026-07-11 硬化）
＝被動防呆——`git add -f` 或不符樣式之新檔皆可繞；client repo CI（`reusable-governance.yml`）
只有繁中閘與 PENDING 格式閘，**無任何 PII 掃描** ⇒ 紅線無機器強制、全靠人為紀律。

**掃什麼（個人層 PII，§18 中欄）**：身分證字號／手機／LINE userId／個人 email。
**不掃什麼（業務事實，§18 左欄，Kevin 2026-07-22 定稿 (a)）**：統一編號、法人全名、
**登記代表人姓名**（GCIS／宗教資訊網公開登記）——此三者屬業務事實，**本掃描器不視為 PII**。

**豁免**：檔案含標記 `PII-SCAN-ALLOW` 者跳過（供合成 PII 測試 fixture 使用）。
★豁免是**檔案級明示**，不接受路徑萬用字元——避免「整個 tests/ 免掃」這種悄悄擴大的破口。

用法：
  python pii_scan.py --path .                # 掃當前 repo，有命中 exit 1
  python pii_scan.py --path . --format github  # CI 用（輸出 ::error:: 註記）
  python pii_scan.py --selftest              # 真陽真陰自驗
退出碼：0＝零命中｜1＝**有 PII 命中（阻斷）**｜2＝錯誤。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ALLOW_MARKER = "PII-SCAN-ALLOW"

# ★手機／身分證之前後界用 (?<!\d)/(?!\d)，避免 epoch 時戳（如 1784177847839）被誤判——
#   此誤判實際發生過（2026-07-22 稽核初掃 6 檔告警全為時戳）。
PATTERNS = [
    ("tw_id", re.compile(r"(?<![A-Za-z0-9])[A-Z][12]\d{8}(?![A-Za-z0-9])"), "身分證字號"),
    ("mobile", re.compile(r"(?<!\d)09\d{2}-?\d{3}-?\d{3}(?!\d)"), "手機號碼"),
    ("line_uid", re.compile(r"(?<![0-9a-fA-F])U[0-9a-f]{32}(?![0-9a-f])"), "LINE userId"),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "email"),
]

# email 之機構／範例網域白名單（非個人 PII）
EMAIL_SAFE = re.compile(
    r"@((.*\.)?github\.com|example\.(com|org|net)|test\.|localhost|"
    r"prospera.*|anthropic\.com|sentry\.io)", re.I)

# `_infra-ci`＝CI 內 checkout 之掃描器自身副本（見 prospera-os/.github/workflows/pii_guard.yml），
# 非受掃 repo 內容；不排除則掃描器會掃到自己的測資。
SKIP_DIRS = {"_infra-ci", ".git", "__pycache__", "node_modules", ".venv", "venv", ".pytest_cache", "dist", "build"}
SKIP_SUFFIX = {".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".docx", ".xlsx",
               ".zip", ".gz", ".ico", ".woff", ".woff2", ".duckdb"}


def scan_text(text: str, name: str = "") -> list[tuple]:
    """回 [(kind, label, lineno, redacted)]；檔案含豁免標記則回空。"""
    if ALLOW_MARKER in text:
        return []
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        for kind, rx, label in PATTERNS:
            for m in rx.finditer(line):
                s = m.group(0)
                if kind == "email" and EMAIL_SAFE.search(s):
                    continue
                out.append((kind, label, i, _redact(s)))
    return out


def _redact(s: str) -> str:
    """只留頭尾各 2 字元——**命中內容本身不得完整寫進 CI log**（否則掃描器自己洩漏 PII）。"""
    return s if len(s) <= 4 else f"{s[:2]}…{s[-2:]}（共 {len(s)} 字元）"


def walk(root: Path) -> list[tuple]:
    hits = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() in SKIP_SUFFIX:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue
        for kind, label, ln, red in scan_text(text, p.name):
            hits.append((str(p.relative_to(root)).replace("\\", "/"), kind, label, ln, red))
    return hits


def _selftest() -> int:
    # 真陽：四類各一
    assert scan_text("身分證 A123456789")
    assert scan_text("電話 0912345678")
    assert scan_text("uid Uabcdef0123456789abcdef0123456789")
    assert scan_text("聯絡 someone@gmail.com")
    # ★真陰 1：業務事實不得被判 PII（統編 8 位／法人全名／登記代表人姓名）
    assert not scan_text("統一編號 80189440 香華天股份有限公司 代表人 黃錦春")
    # ★真陰 2：epoch 時戳不得被誤判為手機（實際誤判過）
    assert not scan_text('{"ts": 1784177847839, "topic": "抗老"}')
    # ★真陰 3：範例／機構 email 放行
    assert not scan_text("寄到 noreply@users.noreply.github.com 或 a@example.com")
    # ★真陰 4：SSH remote（git@github.com:org/repo）非 email——infra-ci 實際誤判過
    assert not scan_text("git@github.com:ProsperaGen/prospera-os.git")
    # ★真陰 5：豁免標記整檔跳過
    assert not scan_text("PII-SCAN-ALLOW\n電話 0912345678")
    # ★遮罩：命中內容不得完整出現於輸出
    red = scan_text("電話 0912345678")[0][3]
    assert "0912345678" not in red, "★掃描器自身洩漏 PII"
    print("[pii_scan] selftest PASS — 真陽 4（身分證/手機/LINE uid/email）"
          "／真陰 5（統編·法人名·代表人姓名＝業務事實、epoch 時戳、範例 email、SSH remote、豁免標記）；遮罩生效")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="個人層 PII 樣式掃描（阻斷級）")
    ap.add_argument("--path", default=".")
    ap.add_argument("--format", choices=["plain", "github"], default="plain")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    root = Path(a.path).resolve()
    hits = walk(root)
    if not hits:
        print(f"[pii_scan] ✅ 零命中（{root.name}）——個人層 PII 未落 git")
        return 0
    print(f"[pii_scan] ❌ 命中 {len(hits)} 筆個人層 PII（DATA_BOUNDARY §18 阻斷）")
    for f, kind, label, ln, red in hits:
        if a.format == "github":
            print(f"::error file={f},line={ln}::PII（{label}）：{red}")
        else:
            print(f"  · {f}:{ln} {label} {red}")
    print("★修法：移出 git（留客戶系統或加密儲存），repo 只收淨化彙總；"
          "合成測試資料請在該檔加標記 PII-SCAN-ALLOW。")
    return 1


if __name__ == "__main__":
    sys.exit(main())

# ── PII-SCAN-ALLOW ─────────────────────────────────────────────────────
# ★本檔自身含合成假 PII（regex 範例與 selftest fixture：A123456789／0912345678／
# Uabcdef…／a@example.com）＝掃描器之真陽測資，非真實個人資料。
# 不豁免則掃描器會擋下自己（自噬），故此標記為必要且僅限本檔。

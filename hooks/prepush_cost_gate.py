#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Prospera SYSTEM HEADER (ADR-0032/SBOM) | 設計:Kevin 架構(pre-execution 成本閘 v2) | 執行:Claude Code | 驗證:test_prepush_cost_gate | IP:創造性歸 Kevin(發明人), AI 為執行工具
"""prepush_cost_gate.py — 真 pre-execution GitHub Actions 成本閘（客戶端 pre-push hook 本體）。

★三次撞爆的機制真相（2026-07-12 API 坐實）：
  6/19 建的 budget_gate.yml 是 workflow_dispatch 手動觸發、歷來 0 執行；且它自己跑起來就計費、
  exit-1 只紅它自己、擋不了別的 workflow → 在 GitHub-hosted Actions 上架構性不可能是 pre-execution 閘。
  BGE 證實：workflow 一觸發、runner 一指派就已計費；真 pre-execution 只有「讓 workflow 根本不被建立」。
  唯一可程式化的「執行前擋」＝本機 pre-push hook：push 前判斷，超預算就擋 push → 零 workflow 觸發 → 零成本。

本閘（真擋，非記錄）：
  1. 只作用於 push 到 github.com/ProsperaGen（其餘 remote 一律放行，不干擾）。
  2. 讀「當月實際 org Actions 花費」（enhanced billing usage API，禁憑印象＝讀真帳單）。
  3. 估算本次 push 的邊際成本（變更檔 → 觸發的 workflow）。
  4. 當月實付 + 邊際 ≥ 預算 → BLOCK（exit 1）→ push 被擋 → workflow 不觸發 → 零 Actions 成本。
  5. 逃生門：PROSPERA_COST_OVERRIDE=1（明確、記帳，非靜默）。任何錯誤 → fail-open（exit 0）不 brick。

退出碼：0=放行（含 WARN）｜1=BLOCK（超預算，push 被擋）。
"""
import os
import sys
import json
import subprocess

# hook 在 Windows 終端（cp950）印訊息 → 強制 UTF-8 輸出，避免 emoji/中文 UnicodeEncodeError
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ORG = "ProsperaGen"
RATE_PER_MIN = 0.008                       # 保守（2026 實際 $0.006，寧高估）
BUDGET = float(os.environ.get("PROSPERA_ACTIONS_BUDGET", "20") or 20)
WARN_RATIO = 0.75                          # 75% 預算 → 響鈴但放行
LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prepush_cost_ledger.jsonl")


def _run(cmd, inp=None):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", input=inp)


def is_prospera_remote(url: str) -> bool:
    u = (url or "").lower()
    return "prosperagen" in u and "github.com" in u


def current_month_spend():
    """讀當月實際 org Actions 花費（net + gross）。回 (net, gross, source)。
    測試/演練可用 PROSPERA_COST_TEST_SPEND 注入 net 值（真陰測試用）。"""
    inj = os.environ.get("PROSPERA_COST_TEST_SPEND")
    if inj is not None:
        v = float(inj)
        return v, v, "injected(test)"
    # 日期由 git log 取（不取系統時鐘以可測）；billing API 需 year/month
    ym = _run(["git", "log", "-1", "--format=%cd", "--date=format:%Y %m"])
    parts = (ym.stdout or "").split()
    if len(parts) < 2:
        return None, None, "no-date"
    y, m = parts[0], str(int(parts[1]))
    r = _run(["gh", "api", f"organizations/{ORG}/settings/billing/usage?year={y}&month={m}"])
    if r.returncode != 0 or not r.stdout.strip():
        return None, None, f"api-fail:{(r.stderr or '')[:60]}"
    try:
        items = json.loads(r.stdout).get("usageItems", [])
    except Exception as e:
        return None, None, f"parse-fail:{e}"
    net = sum(it.get("netAmount", 0) for it in items if it.get("product") == "actions")
    gross = sum(it.get("grossAmount", 0) for it in items if it.get("product") == "actions")
    return round(net, 2), round(gross, 2), f"billing-api {y}-{m}"


def changed_files(refs_stdin: str):
    """從 pre-push stdin 的 ref 行算變更檔。回 list[str]。"""
    files = set()
    for line in (refs_stdin or "").splitlines():
        p = line.split()
        if len(p) < 4:
            continue
        local_sha, remote_sha = p[1], p[3]
        Z = "0000000000000000000000000000000000000000"
        if local_sha == Z:                 # 刪分支，無檔變更
            continue
        if remote_sha == Z:                # 新分支 → 對 origin/main 或單 commit 估
            rng = f"origin/main..{local_sha}"
            if _run(["git", "rev-parse", "--verify", "origin/main"]).returncode != 0:
                rng = local_sha
        else:
            rng = f"{remote_sha}..{local_sha}"
        d = _run(["git", "diff", "--name-only", rng])
        if d.returncode == 0:
            files.update(f for f in d.stdout.splitlines() if f.strip())
    return sorted(files)


def estimate_marginal(files, repo: str) -> dict:
    """估本次 push 的邊際計費分鐘（保守）。非 .md 變更＝觸發重管線；碰 .github/adr 加 guard。"""
    STATE = ("MASTER_LOG.md", "CURRENT_STATE.md", "ACTIVE_STATE.md")
    non_md = [f for f in files if not f.endswith(".md")]
    only_state = files and all(os.path.basename(f) in STATE or "/session-log/" in f for f in files)
    minutes = 0.0
    reasons = []
    if only_state or not files:
        reasons.append("純 state/.md（push paths-ignore 多半跳過）")
        minutes += 0.5
    elif non_md:
        minutes += 6.0                      # governance-pipeline 2 job 重工（pip+gitleaks+~28 檢查）
        reasons.append("非 .md 變更→L0 pipeline(~6 計費分)")
    else:
        minutes += 1.5                      # 純 .md（PR 端仍觸發 pipeline，保守）
        reasons.append("純 .md 變更(~1.5 計費分)")
    hit_key = any(f.startswith(".github/") or "/adr/" in f.lower()
                  or "constitution" in f.lower() for f in files)
    if hit_key:
        minutes += 1.0
        reasons.append("碰關鍵路徑→key-path-guard(+1)")
    return {"minutes": round(minutes, 1), "cost": round(minutes * RATE_PER_MIN, 3),
            "reasons": reasons, "n_files": len(files)}


def _log(row: dict):
    try:
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def decide(remote_url: str, refs_stdin: str) -> int:
    if not is_prospera_remote(remote_url):
        return 0                            # 非 ProsperaGen → 不干擾
    if os.environ.get("PROSPERA_COST_OVERRIDE") == "1":
        print("[cost-gate] ⚠ PROSPERA_COST_OVERRIDE=1 → 明確略過成本閘（已記帳）。")
        _log({"event": "override", "remote": remote_url})
        return 0

    repo = remote_url.rstrip("/").split("/")[-1].replace(".git", "")
    net, gross, src = current_month_spend()
    files = changed_files(refs_stdin)
    est = estimate_marginal(files, repo)

    if net is None:                         # 讀不到帳單 → fail-open（不 brick），但響鈴
        print(f"[cost-gate] ⏭ 無法讀當月帳單（{src}）→ 放行（fail-open）。本次估 ~${est['cost']}。")
        _log({"event": "skip-open", "src": src, "est": est})
        return 0

    projected = round(net + est["cost"], 2)
    warn_at = round(BUDGET * WARN_RATIO, 2)
    line = (f"當月實付 net=${net}（gross=${gross}, {src}）＋本次估 ${est['cost']}"
            f"（{est['minutes']}分, {est['n_files']}檔）= 投影 ${projected} / 預算 ${BUDGET}")

    if net >= BUDGET or projected >= BUDGET:
        print("=" * 66)
        print(f"[cost-gate] ⛔ BLOCK：{line}")
        print(f"  已達/將超 ${BUDGET} 月預算 → 擋 push（workflow 不觸發＝零 Actions 成本）。")
        print(f"  變更觸發：{'；'.join(est['reasons'])}")
        print("  出路：① 本機驗收後再一次 push（py_compile/pytest 本機跑，省整筆 CI）")
        print("        ② 確需上 CI：PROSPERA_COST_OVERRIDE=1 git push（明確、記帳）")
        print("        ③ commit 訊息帶 [hold] 讓 CI 端 PROSPERA_HOLD_GUARD 跳過")
        print("=" * 66)
        _log({"event": "block", "repo": repo, "net": net, "projected": projected,
              "budget": BUDGET, "est": est})
        return 1

    if net >= warn_at:
        print(f"[cost-gate] ⚠ WARN：{line}（≥{int(WARN_RATIO*100)}%）→ 放行，但建議改本機驗收降 push 頻率。")
        _log({"event": "warn", "repo": repo, "net": net, "projected": projected, "est": est})
        return 0

    print(f"[cost-gate] ✅ {line} → 放行。")
    _log({"event": "allow", "repo": repo, "net": net, "projected": projected, "est": est})
    return 0


def main() -> int:
    remote_url = sys.argv[2] if len(sys.argv) > 2 else (sys.argv[1] if len(sys.argv) > 1 else "")
    refs_stdin = "" if sys.stdin.isatty() else sys.stdin.read()
    return decide(remote_url, refs_stdin)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[cost-gate] ⚠ 例外（fail-open 不 brick push）：{e}")
        sys.exit(0)

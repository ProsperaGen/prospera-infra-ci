<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:doc | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:審計注入 | IP:創造性歸 Kevin(發明人) -->
# ProsperaGen Known Failures
## Document Header
- Document Type: Audit
- Version: v1.0
- Status: Active（Append-only，不可修改已有記錄）
- Owner: prospera-infra-ci/skills/
- Governing Authority: prospera-engineering-codex v1.0
- Last Updated: 2026-05-19

---

## 使用規則

CI 失敗時：
1. 先查這個檔案
2. 找到匹配症狀 → 直接套標準修法，不試錯
3. 找不到 → 允許試錯 → 成功後補進本檔案
4. 新增記錄格式見 §新增規則

---

## 新增規則

```
## [KF-序號]｜[症狀簡述]
- 症狀：[觸發條件或錯誤訊息]
- 根本原因：[為什麼發生]
- 影響 Repo：[哪些 repo 出現過]
- 標準修法：[可直接執行的指令或步驟]
- 首次發現：[日期]
- DNA 要素：[對應哪個 DNA 要素]
```

---

## KF-001｜YAML 中的 PowerShell 多行註解

- 症狀：CI Fail，`yaml: line 4: could not find expected ':'` 或 `mapping values are not allowed`
- 根本原因：GPT 用 PowerShell `<# ... #>` 包裹 disabled workflow，YAML parser 不認識
- 影響 Repo：prospera-constitution-governance、prospera-engineering-codex、prospera-engine-generation、prospera-infra-ci
- 標準修法：
  ```powershell
  $template = @'
  # DISABLED [日期] - unified under prospera_guard.yml
  name: [原名稱] (Disabled)
  on:
    workflow_dispatch:
  jobs:
    disabled:
      runs-on: ubuntu-latest
      steps:
        - run: echo "This workflow is disabled"
  '@
  $template | Out-File ".github\workflows\[檔名].yml" -Encoding utf8 -NoNewline
  git add .github\workflows\[檔名].yml
  git commit -m "[P1][CI] fix: replace invalid PS comment with valid YAML disabled stub"
  git push
  ```
- 首次發現：2026-05-07
- DNA 要素：要素四（Commit 四標準）、要素五（可工程實作）

---

## KF-002｜Windows Case-Only 目錄重命名失敗

- 症狀：`git mv 00_GOVERNANCE 00_governance` 在 Windows 無效，git index 仍顯示大寫
- 根本原因：Windows NTFS 不區分大小寫，case-only rename 在 git index 不生效
- 影響 Repo：prospera-infra-registry、prospera-infra-ci、prospera-codex-documentation-standard、prospera-ontology-engine
- 標準修法：三步走
  ```bash
  # 有衝突檔案先撤出
  git mv 00_governance/FILE.md _FILE.tmp
  # 大寫改中性暫名
  git mv 00_GOVERNANCE _gov_tmp
  # 暫名改目標小寫
  git mv _gov_tmp 00_governance
  # 放回檔案
  git mv _FILE.tmp 00_governance/FILE.md
  git commit -m "fix: normalize governance dir to lowercase"
  git push
  ```
- 首次發現：2026-05-17
- DNA 要素：要素六（Repo 六種類型）

---

## KF-003｜GitHub Secret Token 未設定

- 症狀：`Input required and not supplied: token` 或 `terminal prompts disabled`
- 根本原因：workflow 使用 `${{ secrets.PROSPERA_DASHBOARD_TOKEN }}` 但 repo 沒設定這個 Secret
- 影響 Repo：prospera-governance-dashboard、任何使用 checkout 的私有 repo
- 標準修法：
  1. 查 `C:\AI_WorkDir\prospera-credentials.md` 找到 PAT 值
  2. 前往 `https://github.com/ccktaiwan/[repo]/settings/secrets/actions`
  3. New repository secret → Name: `PROSPERA_DASHBOARD_TOKEN` → 貼上 PAT
  4. 確認 workflow 的 checkout 步驟有 `with: token: ${{ secrets.PROSPERA_DASHBOARD_TOKEN }}`
  5. workflow_dispatch 觸發驗證
- 首次發現：2026-05-08
- DNA 要素：要素八（AI 協作協議）

---

## KF-004｜Scanner 判定 Level 0（GOVERNANCE_STATUS.md 缺失）

- 症狀：repo 在 dashboard 顯示 Level 0，但目錄結構存在
- 根本原因：Scanner 找不到 `GOVERNANCE_STATUS.md`，或檔案內容缺少 `maturityLevel` 欄位
- 影響 Repo：prospera-engine（2026-05-18）
- 標準修法：
  ```powershell
  $content = @"
  # GOVERNANCE_STATUS.md
  maturityLevel: 3
  owner: [repo-name]
  governingAuthority: prospera-engineering-codex v1.0
  ciStatus: green
  lastAudit: $(Get-Date -Format 'yyyy-MM-dd')
  "@
  $content | Out-File "GOVERNANCE_STATUS.md" -Encoding utf8
  git add GOVERNANCE_STATUS.md
  git commit -m "[P0][INFRA] chore: add GOVERNANCE_STATUS.md for scanner (Level 3 declaration)"
  git push
  ```
- 首次發現：2026-05-18
- DNA 要素：要素六（Repo 成熟度標準）

---

## KF-005｜JSON 解析失敗（API 回傳 markdown 包裹）

- 症狀：`Expecting value: line 1 column 1 (char 0)` 或 `JSON parse failed`
- 根本原因：Claude API 回傳的 JSON 被 markdown ` ```json ` 包裹，直接 `json.loads()` 失敗
- 影響 Repo：prospera-os（generation_engine.py）
- 標準修法：
  ```python
  import re, json

  def parse_json_robust(raw: str) -> dict:
      cleaned = raw.strip()
      # 清除 markdown code block
      if "```" in cleaned:
          match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
          if match:
              cleaned = match.group(1).strip()
      # 找第一個完整 JSON 物件
      start = cleaned.find("{")
      if start == -1:
          return {"raw_output": raw}
      brace = 0
      for i, c in enumerate(cleaned[start:], start):
          if c == "{": brace += 1
          elif c == "}":
              brace -= 1
              if brace == 0:
                  try:
                      return json.loads(cleaned[start:i+1])
                  except:
                      break
      return {"raw_output": raw}
  ```
- 首次發現：2026-05-17
- DNA 要素：要素五（可工程實作）

---

## KF-006｜PAT 找不到（token 未存檔）

- 症狀：需要設定 Secret 但不知道 PAT 在哪裡
- 根本原因：PAT 產生後沒有存到固定路徑，只存在 GitHub Secrets 中
- 影響 Repo：所有需要設定 PROSPERA_DASHBOARD_TOKEN 的 repo
- 標準修法：
  1. 前往 `https://github.com/settings/tokens`
  2. 找到 `prospera-dashboard-classic` → Regenerate（或建新的）
  3. Expiry 改為 No expiration
  4. 複製 token
  5. 立即存到 `C:\AI_WorkDir\prospera-credentials.md`（見 SKILL-03 格式）
  6. 才去設定 GitHub Secret
- 首次發現：2026-05-08
- DNA 要素：要素八（AI 協作協議）

---

## KF-007｜Dashboard daily schedule 與治理 CI 衝突

- 症狀：prospera-governance-dashboard CI 100% Fail（daily-report workflow 定時觸發失敗）
- 根本原因：`daily-report.yml` 含 `schedule: cron` trigger，定時與治理 CI 同時執行衝突，且 `dashboard_server.py --health-check` 在 Ubuntu CI 環境無法執行（有 Windows 硬編碼路徑 + FastAPI 依賴）
- 影響 Repo：prospera-governance-dashboard
- 標準修法：
  ```yaml
  # 把 on: 區塊從 schedule+workflow_dispatch 改為只有 workflow_dispatch
  on:
    workflow_dispatch:
  # 移除：
  # schedule:
  #   - cron: '30 1 * * *'
  ```
  ```powershell
  git add .github/workflows/daily-report.yml
  git commit -m "[P1][CI] fix: remove schedule trigger prevent governance conflict (manual only)"
  git push
  ```
- 首次發現：2026-05-20
- DNA 要素：要素四（Commit 四標準）

---

## KF-008｜99_archive 硬編碼路徑

- 症狀：救回的程式碼有 `C:\Prospera_Audit` 或其他絕對路徑硬編碼，換機器即 FileNotFoundError
- 根本原因：archive 時路徑未參數化，直接寫死 Windows 本機路徑
- 影響 Repo：prospera-os（consulting_pipeline_v1.py）、prospera-governance-dashboard（dashboard logs）
- 標準修法：
  ```python
  import os
  from pathlib import Path

  BASE = Path(os.environ.get("PROSPERA_AUDIT_PATH", Path(__file__).parent.parent))
  LOG_PATH = Path(__file__).parent.parent / "reports" / "governance_logs.jsonl"
  ```
- 首次發現：2026-05-20
- DNA 要素：要素五（可工程實作）

---

## KF-009｜SYSTEM_INDEX.md 缺失（Codex Validation STRUCTURAL_WARNING）

- 症狀：governance_validation_v2.yml 輸出 `[STRUCTURAL_WARNING] SYSTEM_INDEX.md missing`，CI exit 1
- 根本原因：SYSTEM_INDEX.md 是 Codex Validation 的強制存在檔案，缺失即觸發 STRUCTURAL_WARNING
- 影響 Repo：prospera-infra-ci、prospera-identity-authority、任何需通過 Three-Class Validation 的 repo
- 標準修法：在 repo root 建立 SYSTEM_INDEX.md，內容索引所有 governance docs + kernel modules
  ```bash
  # 最小合法 SYSTEM_INDEX.md
  echo "# SYSTEM_INDEX
## Governance Entry Point
See AGENTS.md and GOVERNANCE_STATUS.md." > SYSTEM_INDEX.md
  git add SYSTEM_INDEX.md
  git commit -m "fix(governance): add SYSTEM_INDEX.md — resolve STRUCTURAL_WARNING"
  git push
  ```
- 首次發現：2026-05-21
- DNA 要素：要素六（Repo 結構）

---

## KF-010｜Gmail App Password 被拒（SMTP auth failed）

- 症狀：dawidd6/action-send-mail@v3 失敗，`Invalid login`，GitHub Actions log 顯示 `535-5.7.8`
- 根本原因：1) App Password 產生後未立即設定 Secret（舊密碼過期）2) SMTP port 選錯（465 SSL vs 587 STARTTLS）
- 影響 Repo：prospera-infra-ci（governance_daily_sprint.yml）
- 標準修法：
  1. Gmail → Google Account → Security → App Passwords → 建立新密碼（Prospera OS）
  2. `gh secret set NOTIFY_EMAIL_PASSWORD --repo ccktaiwan/prospera-infra-ci --body "16碼密碼"`
  3. 確認 workflow 使用 `server_port: 587` + `secure: false`（STARTTLS，不是 465 SSL）
- 首次發現：2026-05-21
- DNA 要素：要素八（AI 協作協議）

---

## KF-011｜Private repo checkout 失敗（PROSPERA_DASHBOARD_TOKEN 未設定）

- 症狀：`Input required and not supplied: token` 或 checkout 步驟 ✗，CI exit 1
- 根本原因：引用其他 private repo（如 prospera-agent-monitor）的 workflow 需要 PAT，但 Secret 未設定
- 影響 Repo：prospera-infra-ci（governance_daily_sprint.yml 的 second checkout）
- 標準修法：
  ```bash
  # 從 gh CLI 取得當前 token 直接設定（不需找存檔）
  gh auth token | gh secret set PROSPERA_DASHBOARD_TOKEN --repo ccktaiwan/prospera-infra-ci
  ```
  注意：self-checkout（checkout 自己的 repo）不需要 token，用預設 GITHUB_TOKEN 即可。
- 首次發現：2026-05-21
- DNA 要素：要素八（AI 協作協議）

---

## KF-012｜write_skills.py 執行後覆蓋手動修改的 SKILL-CORE.md

- 症狀：更新 SKILL-CORE.md 後執行 write_skills.py，發現檔案被覆蓋回舊版本
- 根本原因：write_skills.py 是 canonical source，所有 skill 內容硬編碼在 Python 字串中。執行 script = 從 Python 覆蓋到 GitHub + OneDrive。應先改 script 再跑
- 影響 Repo：prospera-infra-ci（skills/SKILL-CORE.md）
- 標準修法：
  1. 先修改 `scripts/write_skills.py` 中對應的 content 字串
  2. 再執行 `python scripts/write_skills.py`（sync 到兩個位置）
  3. 才 git add + commit + push
  順序：改 Python → 跑 script → commit — 不可反過來
- 首次發現：2026-05-21
- DNA 要素：要素五（可工程實作）

---

## KF-013｜Windows CRLF 行尾 → yamllint 失敗

- 症狀：yamllint 輸出 `wrong indentation` 或 `unexpected end of file`，本地 git show 正常，但 CI 失敗
- 根本原因：Windows 環境下 Out-File 預設 CRLF 行尾，yamllint 在 Linux CI 上對 CRLF 敏感
- 影響 Repo：所有在 Windows 上建立 .yml 的 repo
- 標準修法：
  ```bash
  sed -i 's/
//' .github/workflows/[file].yml
  # 或確認 .gitattributes 有：
  # *.yml text eol=lf
  ```
  使用 Bash Write tool 建立 YAML（不用 PowerShell Out-File）可避免此問題。
- 首次發現：2026-05-21
- DNA 要素：要素四（Commit 四標準）

---

## KF-014｜sleep 指令被 Claude Code 封鎖

- 症狀：執行 `sleep 35 && gh run view [id]` 時 Claude Code 環境封鎖 sleep，任務中斷
- 根本原因：Claude Code Bash 工具對長時間 sleep 有限制，不允許超過閾值的 blocking sleep
- 影響 Repo：所有需要等待 CI 結果的操作
- 標準修法：
  ```bash
  # ❌ 錯誤
  sleep 35 && gh run view 12345 --repo owner/repo
  # ✅ 正確：阻塞直到 CI 完成
  gh run watch 12345 --repo owner/repo --exit-status
  # ✅ 或分兩步：先觸發，後續 Sprint 再查
  gh workflow run workflow.yml --repo owner/repo
  # 下次對話再執行：
  gh run list --repo owner/repo --limit 1
  ```
- 首次發現：2026-05-21
- DNA 要素：要素五（可工程實作）

---

## KF-015｜push rejected — fetch first（遠端有新 commit）

- 症狀：`git push` 失敗，`error: failed to push some refs`，`hint: Updates were rejected because the remote contains work`
- 根本原因：在 push 前沒有 pull 遠端最新 commit，push 時衝突
- 影響 Repo：多人協作或多個 Agent 同時操作的 repo
- 標準修法：
  ```bash
  git pull --rebase origin main
  git push origin main
  # 如果有 stash：
  git stash
  git pull --rebase origin main
  git stash pop
  git push origin main
  ```
- 首次發現：2026-05-21
- DNA 要素：要素四（Commit 四標準）

---

## KF-016｜Anthropic API key 放進 .env 造成意外計費

- 症狀：platform.claude.com 出現非預期費用（$40-$100/天）
- 根本原因：agent 測試時把 API key 存進 .env 和 Windows 系統環境變數，Python 腳本大量呼叫 Anthropic API
- 影響 Repo：prospera-os（consulting_agent 測試期間，3 天花費 $94.48）
- 標準修法：
  1. platform.claude.com → API keys → 刪除問題 key
  2. `[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $null, "User")`
  3. 清除 .env 中的 ANTHROPIC_API_KEY
  4. Spend limit 調降到 $20 止血
- 預防：見 SKILL-CORE §13（API Key 使用規則）
- 首次發現：2026-05-21
- DNA 要素：要素八（Secret 管理）

---

## KF-017｜Human-Reviewed PENDING 誤用

- 症狀：工程產出標注 PENDING，暗示人類需要逐一確認
- 根本原因：沒有區分人類治理和 AI 工程執行兩個角色
- 影響 Repo：所有 prospera-* repo 的 AI Header
- 標準修法：工程產出一律改為 `IP: 創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032)`，僅架構決策用 `YES`
- 首次發現：2026-05-21
- DNA 要素：要素九（AI Header 標準）

---

## KF-018｜指令內有 markdown fenced code block 造成介面切斷

- 症狀：Claude.ai 把指令切成多段，無法完整複製貼上
- 根本原因：指令內使用三個反引號的 code fence，Claude.ai 介面將其解析為格式符號
- 影響 Repo：所有透過 Claude.ai 發送給 Claude Code 的 PowerShell 指令
- 標準修法：改用 PowerShell here-string（@'...'@）或純文字行內描述，避免三反引號
- 首次發現：2026-05-21
- DNA 要素：要素四（Commit 四標準）

---

## KF-019｜指令混入詢問句或說明文字

- 症狀：Claude Code 停下來詢問，或使用者無法分辨哪段是指令
- 根本原因：指令和說明文字混合，或加入 y/n 確認句
- 影響 Repo：all
- 標準修法：純指令區塊，不含任何說明或詢問（SKILL-CORE §19）
- 首次發現：2026-05-21
- DNA 要素：要素八

---

*v1.0 · 2026-05-19 · prospera-infra-ci/skills/ · Append-only*

## KF-020 Self-Healing 未覆蓋的新錯誤模式
- 症狀：auto_heal 回傳 unknown_failure_create_issue
- 根本原因：新錯誤不在 known_failures.md 中
- 標準修法：pattern_learner 觀察 3 次以上失敗 → 自動生成 KF 候選 → 人工確認後補入
- 首次發現：2026-05-21
- DNA 要素：要素五

---

## KF-021｜Spend Limit 止血後未重設正常值導致 Claude Code 中斷

- 症狀：收到 Anthropic 信件「your account balance has crossed the $X threshold」，Claude Code 停止運作，API 呼叫全部暫停至月底
- 根本原因：
  1. 之前 LK5 API key 洩漏事件（2026-05）緊急止血，將 spend limit 從 $500 調低至 $20
  2. 止血後沒有重新設定符合正常運作的合理上限
  3. 正常用量（Claude Code + gateway 開發測試）每月約 $20-30，早已超過止血值
- 影響範圍：所有依賴 API 的工作流程（Claude Code 全停、gateway.py 測試中斷）
- 標準修法：
  1. 前往 https://platform.claude.com/settings/billing
  2. Spend limits → 點「Adjust limit」
  3. 設為 $50（符合正常用量，不需隨意擴張）
  4. 確認 SKILL-CORE §16 API key 安全規則仍然生效（不直接呼叫 API）
- 預防機制：
  - 每次緊急調低 spend limit 後，必須在 known_failures 登記「待重設」
  - 正常運作上限：$50（Claude Code + gateway 開發測試用量）
  - 若出現異常飆升（單日 > $10）→ 立即查 API keys 是否洩漏（參照 KF-016 流程）
- 首次發現：2026-05-21
- DNA 要素：要素八（AI 協作協議）

---

## KF-022｜雙向生成演算法未整合進主諮詢流程

- 症狀：consulting_pipeline 執行但各引擎獨立運作，未使用雙向對齊結果
- 根本原因：各引擎分別建立，沒有統一入口串接 Alignment → External → Knowledge
- 標準修法：使用 prosperagen_full_pipeline.py 作為統一入口（已修復）
  - 引擎鏈：Diagnostic → Alignment → External → Knowledge → Layout → Pipeline
  - 缺失引擎（ontology/learning/community）自動降級，不影響核心流程
- 首次發現：2026-05-21 已修復（commit a422369）
- DNA 要素：要素三（雙向生成演算法）

---

## KF-023｜Docker Hub Rate Limit 導致 Smoke-test 失敗

- 症狀：CI Fail，`docker build` 第二次執行時 `#2 [auth] library/python:pull token` 卡住或失敗，exit code 非 0
- 根本原因：workflow 內 smoke-test 步驟重複執行 `docker build .`，第二次從 Docker Hub pull base image 觸發 rate limit（匿名用戶 100次/6小時）
- 影響 Repo：prospera-os
- 標準修法：
  1. build step 加 `load: true`，讓 image 載入 local daemon（不重複 pull）
  2. smoke-test 步驟改用已 build 的 image tag，不再觸發 pull

  ```yaml
  # build step（加 load: true + 固定 tag）
  - name: Build Docker image
    uses: docker/build-push-action@v5
    with:
      context: .
      push: false
      load: true
      tags: prospera-os:smoke

  # smoke-test step（直接 run 已有 image，不 pull）
  - name: Smoke test
    run: docker run prospera-os:smoke python -c "print('smoke ok')"
  ```
- 首次發現：2026-05-24
- DNA 要素：要素五（可工程實作）

---

## KF-024｜Claude Project 分段輸出 HANDOFF 問題

- 症狀：HANDOFF 指令在 Claude.ai 介面傳送給 Claude Code 時被截斷，Claude Code 只收到前半段，後半段（通常是格式規範或程式碼區塊）遺失，導致任務不完整
- 根本原因：HANDOFF 內含 markdown fenced code block（三反引號），Claude.ai Project 介面將其解析為格式符號並截斷輸出流，Claude Code 收到的訊息不完整
- 影響 Repo：all（透過 Claude.ai Project HANDOFF 傳送的所有跨任務指令）
- 標準修法：
  1. HANDOFF 中的程式碼區塊改用 PowerShell here-string 格式（@'...'@）
  2. 或將程式碼區塊改寫為純文字描述，不使用三反引號
  3. 傳送後確認 Claude Code 端收到完整內容（查看 context 長度是否合理）
  4. 若懷疑截斷：Claude Code 端補充詢問「HANDOFF 是否完整？請回傳最後一行」
- 預防：見 SKILL-CORE §18（給 Claude Code 的指令格式禁止事項）
- 首次發現：2026-05-24（SKILL-11 HANDOFF 在 § 3. Human Report 標準格式後截斷）

---

## KF-008｜agent_registry.yaml list→dict 格式錯誤

- 症狀：GovernanceKernel.validate_agent() KeyError 或 TypeError
- 根本原因：AGENT_REGISTRY.yaml agents 欄位為 list，但 validate_agent() 需要 dict 索引
- 影響 Repo：prospera-os（b0d4dfa）
- 標準修法：agents 欄位改為 dict，key = agent_id
- 首次發現：2026-05-24
- DNA 要素：要素五（可工程實作）

---

## KF-009｜evidence_enforcer 不適用結構化 JSON result

- 症狀：enforce(json.dumps(result)) 誤判 PASS/DRIFT，邏輯錯誤
- 根本原因：enforce() 設計用途是掃描 AI 文字輸出的 drift signal，
  不適用於結構化 JSON（無 drift signal 但也無 artifact marker）
- 影響 Repo：prospera-os mcp_server.py（b0d4dfa）
- 標準修法：MCP 結果改用 check_drift(req.task) 掃描 task 輸入字串
- 首次發現：2026-05-24
- DNA 要素：要素五（可工程實作）

---

## KF-025｜Claude 給 Claude Code 的指令混入說明文字

- 症狀：指令夾雜說明段落、分隔線、STEP標題，浪費 token
- 根本原因：Claude 用「人類讀者」思維寫「機器執行」指令
- 標準格式：一個 code block，純指令，無說明，無分隔線
  結構：PHASE LOCK → MODE → 指令序列 → CHECKPOINT 格式
- MUST NOT：code block 外出現任何說明文字
- MUST NOT：用 ─── 或 STEP N 製造視覺層次
- 首次發現：2026-05-24
- DNA 要素：要素八（AI 協作協議）

---

## KF-026｜當日 SESSION_AUDIT 未產出前，governance repo 任何 PR 之 governance-pipeline 必紅

- 症狀：`gh pr checks <n>` → `governance-pipeline fail`，log 末行
  `[FAIL] 當日 SESSION_AUDIT 不存在：SESSION_AUDIT_YYYY-MM-DD.md（收工未完成，鐵律五）`（exit 1）。
- 根本原因：`.github/workflows/governance-pipeline.yml:160` **無條件**跑
  `00_governance/fitness/check_session_audit.py`，而該 checker docstring 自載之接線建議為
  「**只在 PR 觸及 state 三檔（CURRENT_STATE/ACTIVE_STATE/MASTER_LOG）時強制**，一般 PR 不需 SESSION_AUDIT」
  ⇒ **實際覆蓋面寬於文件宣稱**：收工前（當日 audit 尚未產出）開的任何 PR 都被判「未收工」而紅。
  ★非本機環境問題、非 PR 內容問題——同日任何 PR 皆同症。
- 影響 Repo：prospera-constitution-governance（首見 PR #1091，2026-07-25）
- 標準修法（依情境二擇一，**禁為求綠而先寫假收工 audit**）：
  1. **一般日間 PR**：留 PR OPEN，待當日收工儀式產出 `00_governance/session-log/SESSION_AUDIT_YYYY-MM-DD.md` 後檢查自動轉綠再 merge。
  2. **確為收工 PR**：同 PR 內一併帶當日 SESSION_AUDIT（必填四欄：`session_date`／
     `three_strike_triggered`／`problems_recurred`／`next_session_warnings`），並附 HANDOFF_PROOF 塊。
  · 治根（待 Kevin 裁，非本 KF 自行執行）：把該步收窄為「僅當 diff 觸及 state 三檔才跑」，
    使閘覆蓋面回到 checker 自述之判準。
- 首次發現：2026-07-25（開工同步表 PR #1091；本機 `python 00_governance/fitness/check_session_audit.py` 同樣 exit 1，已重現）
- DNA 要素：要素五（可工程實作）／要素十（宣稱≠生效：閘覆蓋面寬於文件宣稱亦屬名實不符）

---

## KF-027｜`semantic-check` 兩段連環擋：先缺 `[PhaseN]`，補了又撞 phase↔artifact 型別不合

- 症狀（**兩段，會連續紅兩次，容易誤判為修法無效**）：
  1. 第一段 `Phase Lock check` → `FAIL PHASE LOCK VIOLATION: missing [PhaseN]`（exit 1）。
  2. 補上 `[Phase4]` 後轉為第二段 `Artifact semantic validation` →
     `SEMANTIC VIOLATION: <檔>.md is governance_doc, Phases [4] allow ['runtime_code', 'state_spec']`（exit 1）。
- 根本原因：`.github/workflows/artifact_semantic_check.yml:28-29` 由 **HEAD commit 訊息**
  抽 `[PhaseN]` 得 `PHASES`，再交 `scripts/artifact_semantic_validator.py` 依
  `PHASE_RULES`（`:17-23`）比對檔案型別。`classify()`（`:32`）把**所有 `.md` 一律判 `governance_doc`**，
  而 `PHASE_RULES[4]` 只收 `runtime_code`／`state_spec`
  ⇒ **改 `.md` 卻標 `[Phase4]` 必紅**，兩者互斥。
- 型別↔Phase 對照（照 `PHASE_RULES` 原文）：

  | Phase | 允許型別 |
  |---|---|
  | 0 | `governance_doc` |
  | 1／2／3 | `governance_doc`＋`state_spec` |
  | 4 | `runtime_code`＋`state_spec` |

- 標準修法：
  1. **只改 `.md`** → commit 訊息標 `[Phase0]`（或 1／2／3）。
  2. **混類 PR（`.md`＋`.py` 同批）** → **同一則訊息內同時標** `[Phase0][Phase4]`；
     `validator.validate()` 之 docstring（`:36-37`，ADR-0061）明訂多 phase tag 取 **union**，
     此為設計內行為，非繞道。
  3. ★**判準取自 HEAD commit 訊息**：既有歷史提交訊息不合者，
     **不必改寫歷史**（force push 屬不可逆操作）——**補一筆帶正確標記之實質提交推進 HEAD 即可**。
- 影響 Repo：`prospera-infra-ci`（首見 PR #23，2026-08-28；同批連撞 run `33134266742` 與 `33134510316`）
- 首次發現：2026-08-28（`skills/SKILL.md` §2b／§2c 增補 PR）
- DNA 要素：要素四（Commit 四標準）／要素五（可工程實作）

## KF-028｜★族名：保護面窄於發生面（Protection Surface Narrower Than Incidence Surface）

> ★**本則為族名條目**（Kevin L0 2026-08-31 立），供後續同型直接歸族，不必每次重新推導根因。

- 族定義：**機制存在、判準正確、且確實執行過**，但其**作用範圍**（保護面）**小於病症實際發生的範圍**（發生面）
  ⇒ 該機制在自己涵蓋的那一塊是有效的，在涵蓋外的那一塊**完全無防護，且不會報錯**。
  ★**與「宣稱≠生效」之別**：那一族是**機制沒真跑到**；本族是**機制真跑了，只是沒跑到需要它的地方**。
  ★**為何特別難抓**：機制回綠、log 漂亮、測試通過——**證據全部長得像健康**，缺口只在沒被看的那一側。
- 判定三問（任一為「否」即歸本族）：
  1. 這支機制**宣稱**保護的面，與**接線上實際**覆蓋的面，是同一個面嗎？
  2. 它用來比對的**詞集／路徑集／檔案集**，涵蓋得了實際會出現的全部值嗎？
  3. 它**綠燈**時，是「真的沒問題」還是「沒看那一塊」？（母體為零之綠燈＝未執行，見 S-11）
- 首次立族：2026-08-31（同日三例並發，見下）
- DNA 要素：要素十（宣稱≠生效之鄰族）／要素五（可工程實作：三例修法皆為「把面補齊」，非重造機制）

### 立族當日三例（同型，不同面）

| # | 案例 | 宣稱／實際之落差 | 取證 |
|---|---|---|---|
| ① | **訊息面 vs 接線面**：`check_branch_base` | 輸出自稱「**⛔ 阻擋級｜動作已中止**」，而 `.githooks/pre-commit:195` 以 `\|\| true` 接線丟棄退出碼 ⇒ **該路徑從不阻擋**。操作者讀到「動作已中止」會誤信被擋下而不再自查＝**假安全感** | 2026-08-31 實測：該訊息出現後提交仍成功；修訊息面後真陽性實跑 exit 仍為 1（接線未動）。`PENDING-650`／governance PR #1348 |
| ② | **詞集面**：`check_pending_format._CLOSED_LIKE` | 終態詞集僅 `{CLOSED, RESOLVED, MERGED}` **3 詞**，登記簿實際使用 **9 詞**（`WITHDRAWN 21／MOVED 5／WONTFIX 2／REJECTED 1／DELIVERED 1`）⇒ **已撤銷之條目仍被要求填 due**，形同「撤銷了還要承諾交期」 | 2026-08-31 實測分佈；`WITHDRAWN` 於暴露前**已使用 21 次**，僅因開立日早於 `DUE_REQUIRED_SINCE` 而未觸發（**缺陷早於暴露**）。governance PR #1351 |
| ③ | **收集面**：`prospera-product-gengrant` 線上檢查 | **失敗不擋，且只收集 `tests/`** ⇒ 該目錄外之測試不進母體，**CI 全綠不等於無害** | 登記於 `PENDING-645`（2026-08-28 開立，P1）。★**本 KF 未自行複驗此例**，係引該筆登記之記載 |

### 歸族後的標準第一動作

1. **先量兩個面，不要先修**：把「宣稱涵蓋面」與「接線／詞集／路徑實際涵蓋面」各自列出來，差集即缺口。
2. **差集若不為零，先問缺陷是否早於暴露**——多數本族案例在被照出之前已存在很久，
   **登記時須寫明「非本批造成」**，否則會被誤讀為新增退步。
3. **修法一律是「把面補齊」，不是重造機制**（三例皆然：改訊息文字／補詞集／擴收集範圍）。
4. ★**補面之後必須以真陽性實跑取證**——補了面卻沒被觸發過，就是把本族換成「宣稱≠生效」族。

### ★族注記｜指令標的以實測重現為準，不重現即拒補（Kevin L0 2026-08-31 立）

- **判準**：修補本族缺口時，**指令所指之標的須先以實測重現**；跑一次判準本身、看它是否真的咬到那個檔／那個值。
  **不重現者一律拒補**，並回報實測輸出與退出碼。
- **為何**：本族的修法是「把保護面補齊」，而**補一個不存在的缺口＝加一條死排除／死規則**，
  它不會保護任何東西，卻**實質收窄了保護面**——那正是本族病症的反向，等於用修法製造同型缺陷。
- **立此注記之實例（2026-08-31）**：L0 指令為「`detect_simplified.py` 之 `SELF_EXCLUDE` 補 `GOVERNANCE_LIFECYCLE_DEFINITIVE` 一行」。實測：

  ```
  python detect_simplified.py 00_governance/GOVERNANCE_LIFECYCLE_DEFINITIVE.md
  [detect-simplified] 無簡體（掃 1 檔）    exit=0
  ```

  ⇒ **偵測器未咬該檔，缺口不存在**。★**該指令源自對早前 P1 死結之三手轉述，已失真**（L0 自陳）。
  正確標的為 `reusable-code-ci.yml` **自身內嵌之偵測字集**：改前 exit 1、改後 exit 0，
  且合成簡體樣本**仍 exit 1**（閘未被削弱）——**雙向取證齊備**方為完成。
- **操作順序**：① 先跑判準對指令標的取證 → ② 重現才動手 → ③ 不重現則據實回報並拒補 →
  ④ 若同時發現**別的**標的真的重現，改補該標的並具名說明標的已更換。

## KF-029｜靜默形狀不合＝對用戶說謊（收進「假通」族）

> 立條依據：Kevin L0 2026-09-01 裁 1。實例為 2026-09-01 於 `main` 上實測捕獲之活體斷鏈。

- 症狀：呼叫方以 **A 形狀**餵入，被呼叫方預期 **B 形狀**，而被呼叫方以 `.get(key, {})` 之類的
  **靜默預設**吸收缺失 ⇒ **不報錯、不警告，回一份語法正確而語意為空的結果**。
- ★**為何比崩潰更嚴重**：崩潰會被看見；本型**回傳的是一句對用戶的斷言**。
  實例中該斷言是「**無符合管道**」——申請人被告知沒有可申請的補助，
  **而系統實際上一條都沒評估過**。這不是漏判，是**說謊**。
- 判定三問（任一為「是」即歸本型）：
  1. 缺欄位時，程式是用 `.get(k, 預設)` 吸收，而不是 raise？
  2. 吸收之後，回傳值**在形狀上仍然合法**（呼叫方看不出異常）？
  3. 該回傳值**會被當成對用戶的事實陳述**（而非中間值）？
- 立條當日實例（2026-09-01，`grant_qualify` 重複註冊）：
  同一 task key 被 `prospera-os/02_kernel/agents/grant_qualify_agent.py` 與
  `prospera-product-gengrant/agents/grant_qualifier_agent.py` 各註冊一次；後者最後載入而勝出。
  以前者之形狀（`task["client"]`／`task["channels"]`／`context["company_data"]`）餵入實測：

  ```
  summary = '無符合管道。'   warnings = []   ready/pending/failed/blocked = 0/0/0/0
  ```

  ★**兩份實作皆委派同一判準 SSOT**（`gengrant/agents/grant_qualifier.py`），
  故此非判準錯誤，**純粹是輸入契約不一致 ＋ 靜默預設**造成。
- 標準修法（三件，缺一不可）：
  1. **輸入形狀驗證**：未知形狀 **raise 明確錯誤**（訊息須說出「收到什麼、預期什麼」），
     **禁 `.get()` 靜默預設**。
  2. **重複註冊由警告升為載入期硬錯誤**——重複＝**部署錯誤**，不是可容忍狀態。
     ★升級前先確認現無其他重複 key，否則會 brick 掉載入。
  3. **回歸鎖**：以另一形狀餵入須**非空評估或顯式錯誤**；「乾淨的空結果」不得再現。
- ★**與「保護面窄於發生面」（KF-028）之別**：那族是**機制沒跑到該跑的地方**；
  本型是**機制跑到了、也跑完了，但吃進去的是錯的東西而它不說**。
- DNA 要素：要素十（宣稱≠生效之極端形態——**宣稱的內容本身是假的**）／要素五（可工程實作）

---

## KF-030｜刪閘檔必同步撤保護設定（否則該庫永久無法合併）

> 立條依據：Kevin L0 2026-09-01 裁 2。實例造成 **57 天無人察覺之全庫合併癱瘓**。

- 症狀：branch protection 之 `required_status_checks.contexts` 仍列某 check，
  而**產出該 check 的 workflow 檔已被刪除** ⇒ 該 check **永不執行**（不是紅，是**根本不出現**）
  ⇒ 所有 PR 恆為 `BLOCKED`。
- ★**為何 57 天無人察覺**：症狀是「PR 一直卡著」，**不是報錯**。
  合併按鈕變灰的理由寫在小字裡，而每個人只看到「還在等 CI」。
- 立條當日實例（`prospera-gateway`）：

  | 事實 | 取證 |
  |---|---|
  | required contexts | `["governance-check"]`（`gh api .../branches/main/protection`） |
  | 該 workflow 於 main | **不存在**（`git ls-tree origin/main` 僅有 `ci.yml`） |
  | 刪除提交 | `145d5fd` **2026-07-05** `[OpsGov] 刪 governance_check.yml` |
  | 最後成功合併之 PR | **#10，2026-07-04——刪除的前一天** |

- ★**這是 KF-028 的鏡像**：不是保護面**窄**於發生面，是**保護面指向空氣**，
  結果 fail-closed 到癱瘓。**兩者同源——保護設定與實際裝置之間沒有對帳。**
- 標準修法：**把閘裝回去**（不是放寬保護設定）。
  ★**復原時不得照抄本機殘留副本**——實例中工作區留有被刪原檔（逐位元組差異 0），
  但它 `curl` 的是**舊 org `ccktaiwan`**（org 已於 2026-06-26 遷 `ProsperaGen`）⇒ 照復原會 404 而紅。
  **應自 SSOT 模板取件**（`prospera-infra-ci/templates/workflows/`）。
- ★**自證技巧（打破死結）**：同庫 PR 之 `pull_request` 事件使用 **head 分支**的 workflow 檔，
  故「加入該 workflow 的那個 PR」會**在自己身上跑起該 check** ⇒ 不需 `--admin` 越過即可解套。
  實例：`prospera-gateway#13` 之 `governance-check` **pass**，狀態由 `BLOCKED` 轉 `UNSTABLE` 後合併。
- **系統性補強（列 S5）**：建檢查器對帳 **protection contexts ↔ 實際 workflows**，
  差集非空即報。★**未做前，本型仍可能在其他庫復發**——
  已知 fleet 有多庫套用同一 producer 範本。
- DNA 要素：要素十（宣稱≠生效）／要素五（可工程實作：對帳器為單一腳本）

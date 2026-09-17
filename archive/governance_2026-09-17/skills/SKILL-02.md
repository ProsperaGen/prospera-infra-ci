<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:無機制驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# SKILL-02｜Directory Structure Guard
## Document Header
- Document Type: Codex
- Version: v1.0
- Status: Approved
- Owner: prospera-infra-ci/skills/
- Governing Authority: prospera-engineering-codex v1.0
- DNA Reference: 要素六（Repo 六種類型 + 目錄結構）
- Last Updated: 2026-05-19

---

## 1. Identity & Scope

管理所有 repo 的目錄建立、重命名、結構驗證流程。
解決問題：大小寫衝突（00_GOVERNANCE vs 00_governance）、拼字錯誤（00_goverance）、新舊目錄並存、Windows NTFS case-insensitive 造成 git index 與實體不同步。

**觸發條件：** 任何目錄建立、重命名、`git mv`、或新 repo 初始化前。

---

## 2. Non-Goals

- 不管理檔案內容格式（→ SKILL-07）
- 不管理 commit message 格式（→ SKILL-04）

---

## 3. 命名規則（MUST，無例外）

```
目錄名稱：全部小寫 + 底線數字前綴
  ✅ 00_governance
  ✅ 01_docs
  ✅ 02_kernel
  ✅ 99_archive
  ❌ 00_GOVERNANCE
  ❌ 01_Docs
  ❌ 00_goverance        ← 拼字錯誤，已知錯誤
  ❌ 02_KERNEL

檔案名稱：全部大寫 + 底線
  ✅ GOVERNANCE_STATUS.md
  ✅ README.md
  ✅ MATURITY_DECLARATION.md
  ❌ governance_status.md
  ❌ readme.md
```

---

## 4. Repo 類型對應目錄結構（DNA 要素六，硬編碼）

### Platform Repo（-platform 後綴）
```
00_governance/
  constitution.md
  authority-matrix.md
  audit-requirements.md
01_docs/
02_kernel/          ← 核心邏輯 + 可執行程式碼
03_engines/
04_workflows/
05_products/
06_memory/
07_data/
08_tools/
09_ip/
10_archive/
11_tests/
99_archive/
README.md
GOVERNANCE_STATUS.md
MATURITY_DECLARATION.md
.github/workflows/
```

### Governance Repo（-governance / -codex 後綴）
```
00_governance/
  constitution.md
  authority-matrix.md
  audit-requirements.md
changelog/          ← Append-only
README.md
GOVERNANCE_STATUS.md
MATURITY_DECLARATION.md
.github/workflows/
```

### Engine Repo（-engine 後綴）
```
spec/               ← Phase 3 產出
design/             ← Phase 4 產出
src/
tests/
docs/
README.md
GOVERNANCE_STATUS.md
.github/workflows/
```

### Shared Repo（-shared / -ci 後綴）
```
scripts/
skills/             ← ProsperaGen Skills 體系
tests/
README.md
GOVERNANCE_STATUS.md
.github/workflows/
```

### Registry Repo（-registry 後綴）
```
00_governance/
registry/           ← 狀態索引資料
README.md
GOVERNANCE_STATUS.md
.github/workflows/
```

---

## 5. Windows Case-Only Rename 三步走（MUST）

```bash
# 情境：00_GOVERNANCE → 00_governance（Windows NTFS 不分大小寫）
# 直接 git mv 在 Windows 無效，必須三步：

# Step 1｜衝突檔案先撤出（如 00_governance/ 和 00_GOVERNANCE/ 同時存在）
git mv 00_governance/CONFLICT_FILE.md _CONFLICT_FILE.tmp

# Step 2｜大寫目錄改中性暫名（避開 case-only 問題）
git mv 00_GOVERNANCE _gov_tmp_normalize

# Step 3｜暫名改目標小寫
git mv _gov_tmp_normalize 00_governance

# Step 4｜撤出的檔案放回
git mv _CONFLICT_FILE.tmp 00_governance/CONFLICT_FILE.md

git commit -m "fix: normalize governance dir to lowercase"
git push
```

---

## 6. 新 Repo 初始化清單

```
□ 確認 repo 類型（Platform / Governance / Engine / Shared / Registry / Template）
□ 查 §4 對應目錄結構，完整建立
□ 確認所有目錄名稱小寫
□ 確認根目錄有 README.md 和 GOVERNANCE_STATUS.md
□ GOVERNANCE_STATUS.md 包含 maturityLevel 欄位
□ .github/workflows/ 有至少一個 active workflow
```

---

## 7. 掃描衝突指令

```bash
# 找 41 個 repo 中 git index 的大小寫衝突
cd /c/AI_WorkDir/GitHub && for d in */; do
  d="${d%/}"
  cd "/c/AI_WorkDir/GitHub/$d" 2>/dev/null || continue
  [ -d .git ] || continue
  variants=$(git ls-files | grep -iE '^0[0-9]_' \
    | awk -F'/' '{print $1}' | sort -u)
  lower=$(echo "$variants" | grep -E '^[0-9]+_[a-z]')
  upper=$(echo "$variants" | grep -E '^[0-9]+_[A-Z]')
  [ -n "$upper" ] && echo "CONFLICT: $d → upper=$upper"
  cd ..
done
```

---

## 8. Matrix

| 情境 | 操作 | 注意事項 |
|------|------|---------|
| 建新目錄 | 查 §4 對應結構，全小寫建立 | 不得自行推斷目錄名稱 |
| 大寫轉小寫 | §5 三步走 | Windows 必須三步，不可跳步 |
| 拼字錯誤修正 | git mv 舊名 正確名 + push | 不需三步走，直接 mv |
| 新舊目錄並存 | 先確認哪個是主線，合併後刪舊 | 合併前截圖兩個目錄內容 |

---

## 9. Failure Modes

| 症狀 | 原因 | 修法 |
|------|------|------|
| git mv 後大寫目錄仍存在 | Windows case-only rename 問題 | §5 三步走 |
| Scanner 找不到 governance 目錄 | 拼字錯誤或大寫 | 用 §7 掃描，找到後修正 |
| 兩個目錄內容衝突 | 重構做一半 | 先截圖兩個目錄，確認主線後合併 |
| 新 repo 建立後 Level 0 | 缺 GOVERNANCE_STATUS.md | 補建，見 KF-004 |

---

## 10. Audit Requirements

每次目錄結構修正記錄到 prospera-audit-ledger：
```
[日期] DIR-FIX: [repo名稱] [修正內容] [修正前狀態 → 修正後狀態]
```

---

*v1.0 · 2026-05-19 · prospera-infra-ci/skills/*

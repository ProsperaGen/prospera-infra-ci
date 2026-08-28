<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:doc | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:審計注入 | IP:創造性歸 Kevin(發明人) -->
# ProsperaGen Skills 總索引
## Document Header
- Document Type: Codex
- Version: v1.3
- Status: Approved
- Owner: prospera-infra-ci/skills/
- Governing Authority: prospera-engineering-codex v1.0
- DNA Reference: 要素一～十（全部）
- Last Updated: 2026-08-28

---

## 1. Identity & Scope

Skills 是 ProsperaGen Engineering DNA 的執行觸發器。
不是新規則，是 DNA 十個要素的操作化介面。

**MUST：** 任何 AI 執行任何任務前，先查 §3 查閱表，讀完對應 Skill 才開始執行。
**MUST NOT：** 不讀 Skill 直接執行 = Governance Breach → CI 自動 BLOCK。

---

## 2. Non-Goals

- 不取代 DNA（DNA 是規則定義，Skills 是執行介面）
- 不包含架構決策（→ Prospera OS）
- 不包含產品邏輯（→ 各自 repo）

---

## 2b. 開工協議（Boot Protocol）

> 本節為**行為層固化**，三條皆**掛既有裝置**（既有 SSOT 見各條「承」欄），
> **不新建閘、不新建工具**。裁決效力仍在原 SSOT，本節僅為 skills 側之強制入口。

### 2b.1 並行判準（開工前必答）

**承**：`prospera-constitution-governance/00_governance/AUTONOMY_RULES.md:642` §6.16（獨立子任務並行，
2026-07-07 Kevin 裁）＋ `:670` §6.16b（依賴圖＋泳道判定）。
**既有閘**：`00_governance/tools/parallel_gate.py`（`tests/hooks/test_parallel_gate.py` 真陽真陰），
成對驗證掛於 `.github/workflows/newly_mounted_gates.yml:46`。

派工前必答：**哪些任務互不依賴**。
- 互不依賴者 → **必須 multi-agent 並行**（不得以「順手就做了」串行掉）
- 有依賴者 → **標依賴鏈**（後階吃前階輸出＝同泳道＝禁並行，§6.16b①）

**本節新增之強制點（掛既有回報形狀，非新裝置）**：
回報**首段第一行**必含

```
並行判定：X 並行／Y 串行／依賴鏈：<A→B→C，或「無」>
```

**缺此行＝回報格式不符**，與缺 Tier 標記同級處置（退回補齊，不追認）。

### 2b.2 讀前驗態（任何 repo 操作前）

**承**：`prospera-constitution-governance/00_governance/instructions/INSTRUCTIONS_DOD.md` §Q0 開工協議
之「★開工分支已驗」條（2026-07-28 新增，三振第 5/6 例修法）。
★**本條為該條之補遺，不重述已有條文**——既有 Q0 已規定回報 `git branch --show-current`
與 `git rev-list --count HEAD..origin/main`（非 `main` 或落後 >0 即紅）。

**補之 delta 兩項**：既有 Q0 只驗 **branch** 與 **behind**，另兩態靜默通過。故加驗：

| 態 | 指令 | 判準 |
|---|---|---|
| ahead（未推） | `git rev-list --count origin/main..HEAD` | >0 即須報，先處置再開工 |
| dirty（工作樹） | `git status --porcelain` | 非空即須報；命中 key-path 即 **Tier 0 停手** |

**實例（2026-08-28，本條之立法事實）**：`prospera-infra-ci` 本機 `main`
＝ behind 22 ／ ahead 1（`62d98a1` hooks shim 未推）／ dirty 20+ 檔且含 `.github/workflows/` 八支
（key-path-guard 保護路徑）。**現行 Q0 只會抓到 behind**，ahead 與 dirty 全數靜默通過——
若逕行在該工作樹提交，Tier 0 路徑將被夾帶入 commit。

### 2b.3 SSOT 引用紀律（升為通則）

**承**：`ADR-0164`（ontology repo 為唯一本體 SSOT，`org_topology.json` 降本地鏡像／指針）、
`ADR-0292`（GitHub 唯一 SSOT，OneDrive 降純鏡像／交付暫存，非真相源）、
`00_governance/INDUSTRY_PRACTICES_REGISTRY.md:16` 引用紀律（原僅限該表）。

**升通則**：
- **裁決性引用**（用以支撐判斷、結案、Tier 判定者）→ **必回原 SSOT 檔取原文行號**，
  格式 `<repo>/<path>:<line>`；引用時應為當次實查所得，非記憶或轉述。
- **鏡像與摘要僅供導航**：state 檔、dashboard、handoff、session log、OneDrive 副本、
  本節之「承」欄本身——**皆不得作為裁決依據**，只能作為找到原檔的指路。
- 找不到原文行號 → 記為**未證實**，不得以鏡像文字補位。

---

## 2c. 模式協議（Mode Protocol）

> **落點說明**：指令指定「緊接同步協議之後」。實查 `skills/*.md` **無「同步協議」節**
> （`grep -rn "同步協議|## 同步|同步觸發" skills/*.md` 零命中）；同步之判準本體在
> `prospera-constitution-governance/00_governance/instructions/INSTRUCTIONS_DOD.md` §同步觸發詞。
> 故本節置於 §2b 開工協議之後（開工 → 同步 → 模式，順序不變），**同步判準不在此複寫，引原檔為準**。

### 2c.1 模式進入（自動，不需重申）

Kevin 說「**同步**」→ 輸出五項同步內容後，**立即自動進入「治理計畫 × PGDA」運作模式**。
不需 Kevin 再說一次。

**模式定義**：所有工作**掛在當前在辦治理計畫（GOAL）之下**，
每回合回報**首行**標注：

```
主軸:<治理計畫名>｜橫軸第N步｜縱軸第M段
```

軸名與段名一律以原 SSOT 為準——橫軸十步見
`00_governance/GOVERNANCE_LIFECYCLE_DEFINITIVE.md:12-21`；
縱軸八段見 `00_governance/PGC_CHAIN_DEFINITIVE.md:29-36`。
★**不得使用外部私有記號**（承 §2b.3 引用紀律）。

### 2c.2 主軸鎖

Kevin 宣告當日主軸後，**寫入 `ACTIVE_STATE.md` 當日節**。
此後任何回合，內容若**不服務主軸**，須於**首行自標**：

```
支線:<事由>，主軸不變
```

**無此標注而離題＝違規**。Kevin 可一句「**偏移**」召回，被召回即計為
鐵律四同類問題（`AUTONOMY_RULES.md` §6.15 執行期自主段之「忘記主軸而反應式救火」）。

### 2c.3 斷線續航

任何中斷（claude.ai 新開對話／Claude Code 重啟／`--resume`）後，
**讀 SKILL 本節 ＋ `ACTIVE_STATE.md` 即恢復模式與主軸**。
★**不得以「新 session」為由重置模式或主軸**——重置需經 §2c.4。

因此 `ACTIVE_STATE.md` **必含三欄**（缺一即斷線續航失效）：

| 欄 | 內容 |
|---|---|
| 當前治理計畫名 | 在辦 GOAL 之檔名或 ID |
| 雙軸位置 | 橫軸第 N 步／縱軸第 M 段 |
| 當日主軸 | Kevin 當日宣告之主軸，含宣告日期 |

### 2c.4 退出與變更

**僅 Kevin 明示「收工」或「切換主軸」可變更模式狀態。**
模式狀態變更**本身**須寫入 `ACTIVE_STATE.md` 留痕（何時進入／何時退出／切到哪條主軸）。
執行層不得自行判定模式已結束。

### 2c.5 強制點（掛既有回報形狀，不新建裝置）

本節之強制＝**回報首行格式檢查**，與 §2b.1 之並行判定行同掛既有回報形狀閘。
一回合之回報首行須為下列二者之一，否則格式不符：

1. `主軸:<治理計畫名>｜橫軸第N步｜縱軸第M段`
2. `支線:<事由>，主軸不變`

★本節為**運作模式之固化（PGDA 橫軸⑥）與強制（⑦）**；
依 `GOVERNANCE_LIFECYCLE_DEFINITIVE.md:17-18`，⑥＝policy 映射納管、⑦＝機器擋非只提醒。
**現況誠實標記**：本節之強制目前為**回報形狀之格式約定**，
`SessionStart` 提示掛鉤（治理庫 `.claude/hooks/`）只做注入提示，**不阻斷**；
故本節之⑦尚未達「機器擋」全標準，不得宣稱已強制。

---

## 2d. 回報規範｜待辦連結（Actionable-Link Discipline）

> 承 §2c.5 回報形狀（`▶過程／■回報／⏸待Kevin` 三段）。本節只治 **`⏸ 待 Kevin` 段**。

### 2d.1 條文

**`⏸ 待 Kevin` 段中，凡需 Kevin 在外部系統動作者（merge／審核／簽署／付款），
必附可直達之完整 URL，或明確位置（檔案路徑＋行號）。
無法取得 URL 時，明標【連結取證失敗:<原因>】。**

★**立法事實（2026-08-28）**：本場回報三次列出「請你按 merge」而**未附任何 URL**，
Kevin 須自行翻找 repo 與 PR 號。待辦落在外部系統而回報只給編號，等同把定位成本轉嫁給人類，
違 `SKILL-CORE.md` 協作準則③「不當操作員／傳話筒」。

### 2d.2 取證紀律（URL 不得手拼）

- **URL 須來自 `gh`／API 之取證輸出**，例如 `gh pr view <n> --json url -q .url`。
  **禁止依 `owner/repo/pull/<n>` 規則手拼**——手拼看起來會對，但 repo 改名／轉移／PR 號誤植時
  無任何機制會咬住，屬 existence-check 同型（沒查過而看起來像查過）。
- **private 資源須併註可見性與所需權限**。取證指令：`gh repo view --json url,visibility -q .`。
  若 `visibility` 為 `PRIVATE`，回報中須註明「**需以具 org 權限之 GitHub 帳號登入後開啟**」。

### 2d.3 強制（機器擋）

治理庫 gate0 判斷層閘之 **`R-待辦連結`**：`⏸` 段偵測到外部動作動詞
（`merge`／`併`／`審`／`簽`／`核准`）而**同段無 URL／檔案路徑，且無 `【連結取證失敗:…】` 標記**
⇒ **擋下重寫**。
**FP-safe**：純問答、裁決徵詢（非外部系統動作）放行。
規則實作附測試，真陽／真陰各 ≥2。

---

## 3. Skill 查閱表

| Skill | 觸發條件 | 主要解決問題 | DNA 要素 | 位置 |
|-------|---------|------------|---------|------|
| **開工協議** | **每次開工前（含每次中斷後恢復）** | 單線漏並行、髒工作樹夾帶 Tier 0 路徑、引鏡像當裁決依據 | 要素一、四、八 | **本文件 §2b** |
| **模式協議** | **Kevin 說「同步」後，直到明示收工／切換主軸** | 新 session 重置主軸、離題無標注、雙軸位置失聯 | 要素一、二、五 | **本文件 §2c** |
| **回報規範·待辦連結** | **每次輸出 `⏸ 待 Kevin` 段時** | 待辦只給編號不給 URL、手拼連結、private 資源未註權限 | 要素五、十 | **本文件 §2d** |
| SKILL-01 | 任何 .yml 寫入或修改前 | YAML syntax error、PS 語法污染 | 要素四、五 | 本文件 §5 |
| SKILL-02 | 任何目錄建立或 git mv 前 | 大小寫衝突、目錄命名混亂 | 要素六 | 本文件 §6 |
| SKILL-03 | 任何 token/PAT/secret 操作前 | PAT 失蹤、secret 設定不一致 | 要素八 | SKILL-03.md |
| SKILL-04 | 任何 git commit 前 | CI 失敗、Header 缺失、格式錯 | 要素四、九 | 本文件 §7 |
| SKILL-05 | 每次任務開始前 + 每個 Stage 完成後 | Governance Drift、語義漂移 | 要素一、二、五 | SKILL-05.md |
| SKILL-06 | 多步驟任務每完成一個重要步驟後 | 任務中斷失憶、誤刪 artifacts | 要素八 J 點 | SKILL-06.md |
| SKILL-07 | 任何文件提交前 | 文件深度不足、無法工程實作 | 要素三、五、七 | SKILL-07.md |
| SKILL-08 | 每個新機制或新引擎建立後 | IP 未登記、核心邏輯外洩 | 要素十 | SKILL-08.md |
| SKILL-09 | 任何 99_archive 救援或檔案遷移前 | 救援流程不一致、artifacts 遺失 | 要素八 | SKILL-09.md |
| SKILL-10 | 任何新 repo 建立或 repo 封存前 | Repo 命名混亂、封存不完整 | 要素六、九 | SKILL-10.md |

---

## 4. 標準任務流程

```
[開始任務]
    ↓
開工協議（並行判準／讀前驗態／引用紀律）  ← §2b
    ↓
模式協議（同步後自動進入治理計畫×PGDA 模式）  ← §2c
    ↓
讀 SKILL.md §3 → 找對應 Skill → 讀完
    ↓
確認 Phase (0-6) + Stage (1-6)        ← SKILL-05
    ↓
執行任務
    ↓
每完成重要步驟 → Checkpoint            ← SKILL-06
    ↓
git commit 前 → Pre-flight            ← SKILL-04
    ↓
新錯誤 → 補進 known_failures.md
```

---

## 5. SKILL-01｜YAML Workflow Guard

**DNA：要素四（Commit 四標準）+ 要素五（可工程實作）**
**觸發：** 任何 `.github/workflows/*.yml` 寫入或修改前

### 5.1 禁止事項（MUST NOT）

```
❌ PowerShell 多行註解
<#  任何內容  #>

❌ on: push 但 jobs 為空（造成 parse error）

❌ 未使用 yamllint 驗證就直接 commit
```

### 5.2 停用 Workflow 標準模板

```yaml
# DISABLED [日期] - [原因，例如：unified under prospera_guard.yml]
name: [原名稱] (Disabled)
on:
  workflow_dispatch:
jobs:
  disabled:
    runs-on: ubuntu-latest
    steps:
      - run: echo "This workflow is disabled"
```

### 5.3 執行前驗證步驟（依序，失敗即停）

```
Step 1｜檢查 <# 字串
  grep -n "<#" .github/workflows/*.yml
  → 有 → 換成停用模板，不得保留

Step 2｜yamllint 驗證
  yamllint .github/workflows/[檔名].yml
  → errors > 0 → 修完再 commit

Step 3｜確認 trigger 與 jobs 邏輯一致
  → on: push 但 jobs 空 → 補 disabled stub 或真實 job
```

### 5.4 已知錯誤快查

| 症狀 | 根本原因 | 標準修法 |
|------|---------|---------|
| CI Fail line 4/6 syntax error | `<#` PowerShell 語法 | 換成停用模板 |
| `mapping values are not allowed` | YAML 縮排錯誤 | yamllint 定位修正 |
| `could not find expected ':'` | 冒號後缺空格 | 全文搜尋補空格 |
| `Input required and not supplied: token` | Secret 未設定 | 見 SKILL-03 |

---

## 6. SKILL-02｜Directory Structure Guard

**DNA：要素六（Repo 六種類型 + 目錄結構）**
**觸發：** 任何目錄建立、重命名、或 `git mv` 前

### 6.1 命名規則（MUST）

```
目錄名稱：全部小寫
  ✅ 00_governance / 01_docs / 02_kernel
  ❌ 00_GOVERNANCE / 01_Docs / 02_KERNEL

檔案名稱：全部大寫（含底線）
  ✅ GOVERNANCE_STATUS.md / README.md
  ❌ governance_status.md / readme.md
```

### 6.2 Platform Repo 標準目錄（硬編碼，不得自行推斷）

```
00_governance/     ← constitution.md、authority-matrix.md
01_docs/
02_kernel/         ← 核心邏輯 + 可執行程式碼
03_engines/
04_workflows/
05_products/
06_memory/
07_data/
08_tools/
09_ip/
10_archive/
11_tests/
99_archive/        ← 待清理封存
```

### 6.3 Windows Case-Only Rename 三步走（MUST）

```bash
# 情境：00_GOVERNANCE → 00_governance
# 直接 git mv 在 Windows NTFS 會失敗，必須三步：

# Step 1：衝突檔案先撤出
git mv 00_governance/FILE.md _FILE.tmp

# Step 2：大寫改中性暫名
git mv 00_GOVERNANCE _gov_tmp

# Step 3：暫名改目標小寫
git mv _gov_tmp 00_governance

# Step 4：撤出的檔案放回
git mv _FILE.tmp 00_governance/FILE.md

git commit -m "fix: normalize dir to lowercase"
```

### 6.4 衝突掃描指令

```bash
cd /c/AI_WorkDir/GitHub && for d in */; do
  d="${d%/}"
  cd "/c/AI_WorkDir/GitHub/$d" 2>/dev/null || continue
  [ -d .git ] || continue
  variants=$(git ls-files | grep -iE '^00_governance/' \
    | awk -F'/' '{print $1}' | sort -u | tr '\n' '|')
  [ -n "$variants" ] && echo "CONFLICT: $d → $variants"
  cd ..
done
```

---

## 7. SKILL-04｜Commit Pre-flight

**DNA：要素四（Commit 四標準）+ 要素九（AI Header）**
**觸發：** 任何 `git commit` 前，無例外

### 7.1 Pre-flight 清單（依序，任一失敗即停止）

```
□ Step 1｜語法驗證
  Python：python -m py_compile [file]
  YAML：  yamllint [file]
  → 失敗 → 修完再繼續

□ Step 2｜AI Header 完整
  必要欄位：Generated / Model / Phase / Layer /
            Target Repo / Governing Codex / Human-Reviewed
  → 缺欄位 → 補完再繼續

□ Step 3｜Commit Message 格式
  格式：[Phase][Layer] 動作: 描述 (為什麼)
  範例：[P3][L2] feat: add authority-matrix (enforce access boundary)
  長度：≤ 72 字元
  禁用動詞：update / fix / change / misc / WIP
  → 格式錯 → 重寫

□ Step 4｜Extended Description 存在
  必須包含：系統角色 / 影響範圍 / 關聯 Issue / Human-Reviewed 狀態
  → 空白 → 補完

□ Step 5｜Path & Filename 正確
  目錄小寫、檔案大寫
  → 不符 → 改正
```

### 7.2 AI Header 標準模板

```
# ══════════════════════════════════════
# AI-GENERATED DOCUMENT
# ══════════════════════════════════════
# Generated:        [ISO 8601 timestamp]
# Model:            [model name + version]
# Phase:            [Phase 0-6]
# Layer:            [L1-L5 or ProsperaGen]
# Target Repo:      [repo name]
# Governing Codex:  prospera-engineering-codex v1.0
# 設計: 依 Kevin 架構 ｜執行: AI 工具(claude.ai+Claude Code) ｜驗證: 無機制驗證 ｜IP: 創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032)
# Review By:        [reviewer name or PENDING]
# Review Date:      [ISO 8601 or PENDING]
# ══════════════════════════════════════
```

### 7.3 成功標準

全部 5 個 Step 通過 → 允許 commit
任何 Step 失敗 → 停止，修完，重跑 Pre-flight

---

## 8. known_failures.md 使用規則

CI 失敗時：
1. 先查 `known_failures.md`
2. 找到 → 直接套標準修法，不試錯
3. 找不到 → 允許試錯 → 成功後必須補進 known_failures.md

---

## 8b. 待批節｜合併授權與交辦載體（L0 2026-08-28 授權，即刻生效）

> 授權原話（Kevin 2026-08-28）：「**手工操作不應丟給 Kevin**」。
> 本節為**常設授權**，非單次；撤銷須由 L0 明示。

### 8b.1 PR 合併授權（分兩級）

| 類別 | 判準 | 授權 |
|---|---|---|
| **非規則檔 PR**（產品／文件／測試／相依套件） | CI 綠 ＋ `MERGEABLE` | **Claude Code 逕以 `gh pr merge --merge` 代併**，不必先問 |
| **規則檔 PR**（SKILL／gate／閘門本體） | Kevin 於對話**明示「准」** | 由 Code 代併；**commit 訊息須引述授權原話＋日期** |

**合併方式硬規則**：
- 一律 `--merge`（一般合併）。**禁 `--squash` 於已被引用之 commit**（squash 會改寫提交碼，使既有引用失效）。
- **永禁 `--admin`／force／任何 bypass**。分支保護擋下時，正解是 `--auto`（滿足條件後自動併），不是繞過。
- 檢查未跑完 ⇒ `--auto --merge`；**不得以「等一下應該會綠」為由直接併**。

### 8b.2 權限分類器

若權限分類器擋下 `gh pr merge`，將**該指令樣式**加入 `permissions.allow` 並進版控——
**僅限 merge，不得含 force／delete**。★2026-08-28 實測：五張 PR 之合併與關閉**均未被擋**，故本次未新增任何允許規則（不預先加不需要的權限）。

### 8b.3 跨 session 交辦之載體要求（L0 2026-08-28 增訂）

**跨 session 交辦之任何清單或代號，發令時必附「git 載體路徑」或「重建方法」。**
**無載體之代號＝無效指令，承接者應拒收**，並回報「查無載體」而非猜測母體。

> 立此條之實例（同日）：交辦「12 筆證據歸屬」與「側分支 35 筆」兩代號，治理庫內查無出處——
> `grep 清倉` 零命中、當日無 MASTER_LOG／CURRENT_STATE 條目；分支母體六種計數（390／316／291／232／42／16）無一為 35，
> 證據類母體四種計數（30／99／30／1）無一為 12。承接者拒收為正確行為，L0 當場認可並補給重建方法。
> ★**與 `ADR-0320` 同型**（跨 project 交接須落 git artifact，下游才得採信），差別只在這次發生在 **L0 → 執行層**這一段。

---
## 9. Skill 更新規則

- 人工更新：需 J2 Review + commit message 標註 `[SKILL-UPDATE]`
- AI 不可自行修改 Skill 文件
- 每次更新需同步更新 Version 和 Last Updated

---

*v1.0 · 2026-05-19 · prospera-infra-ci/skills/ · Kevin Chang（張淳嘉）*

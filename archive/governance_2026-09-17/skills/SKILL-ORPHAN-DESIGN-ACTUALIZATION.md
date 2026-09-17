<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:今日 commit 實證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# SKILL-ORPHAN-DESIGN-ACTUALIZATION｜孤兒設計做實法（四問法 v2，第三問=9 archetype 反面驗證）

## Document Header
- Document Type: Skill
- Version: v2.0（2026-06-14；第三問以真實反例彈藥重寫）
- Status: Active
- Owner: prospera-infra-ci/skills/
- 鉤接: 四問法（提案→證據→**反面驗證**→更優解）／`SKILL-INTELLIGENCE-RESEARCH-TRANSPLANT`／`SKILL_COUNTER_VALIDATION_CORPUS.md`（governance）／ADR-0045（reward hacking）

---

## 何時用
撞到「**設計有、實作零/散落/自述不實**」的孤兒（雙向生成定義、AIW 身分、harness 協調、資安 spec…皆是）。目標＝把孤兒**拉出來做到能用**，不是再寫一輪文件。

## 核心命題（一句）
**自述・印象・記憶・單一 source ＝ 不可信；實測・git 取證・到該 repo・查業界 ＝ 真相。** 孤兒做實＝用後者打前者。

---

## 四問法骨架（做實版）

### 第一問 — 提案：孤兒是什麼性質？（先分類，處置不同）
「沒有」必須先分三類（archetype H）：① **沒設計** → 要先設計 ② **有設計沒實作** → 拉出做實（本 skill 主場）③ **有但散落未成 SSOT** → 成文收口。**grep .py/.md 零命中 ≠ 沒做**，先判性質。

### 第二問 — 證據：到「那個 repo」取真實況（不憑別處描述）
- 跨 repo 結論**必到該 repo grep**（archetype D：別 repo 的 spec 會對該 repo 失明）。
- 「已實作/完整」**grep 行數/函式/return stub**（archetype C：35 行 stub vs 180 行真實作）。
- 既有鷹架先盤（多數孤兒可**擴充**已測過的東西，非從零）。

### 第三問 — 反面驗證：9 archetype 彈藥（做實前逐條自問）★本問是牙齒
> 每條附今日真實 commit 反例（`SKILL_COUNTER_VALIDATION_CORPUS.md` 全文）。做實聲稱「好了」前，逐條過：

| # | Archetype | 第三問防呆問句 | 反例 commit |
|---|---|---|---|
| A | real source ≠ 內容對 | source=real，**抓到的具體內容**貼出來看了嗎？ | `2c554f2` 眼1 nav 血塊 |
| B | 症狀 ≠ 根因 | 歸因**讀了證據**還是猜的？反假設能排除嗎？ | `4c1a727` method_whitelist |
| C | 自述 ≠ 實際 | 「完整」**grep 行數/stub** 了嗎？ | `8a3e57c` audit stub |
| D | 跨 repo 失明 | 結論**到那個 repo 取證**還是憑別處描述？ | `0c48b54` rate limit 誤判 |
| E | 難度誇大無據 | **查過業界現成**嗎？難度用實測還是形容詞？ | `37e679e` agent 身分 3 行 |
| F | 測量工具陷阱 | 工具**可見範圍/權限**？看不到的會否致錯？ | `397b355` curl 只 public |
| G | 記憶 ≠ git 真相 | 是記憶還是**剛 git/雲端取證**？ | `397b355` client 5→7 |
| H | 缺 SSOT ≠ 缺機制 | 「沒有」是沒設計/沒實作/散落？ | `cf3a548` AIW 散落 |
| I | 假完成 | 修的是**前置**還是**功能**？端到端**實跑**、輸出真資料？ | `24ce9fc` 眼睛未睜開 |

### 第四問 — 更優解：做到能用 + 實測為憑
- 真目標＝**功能能用**非刷指標（ADR-0045 規則1）；端到端實跑、輸出真資料才算。
- 難度以**實測 commit 時長/行數/測試數**為憑（ADR-0045 規則2），非形容詞。
- 不假裝接上（archetype I）；**剩未完成的誠實登 PENDING**。

---

## 做實六陷阱速查表（第5步收尾前過）
1. **real source 陷阱**：source 真 ≠ 內容對 → 看內容
2. **症狀陷阱**：表面歸因 → 讀堆疊驗根因
3. **自述陷阱**：信註解/PENDING → grep code
4. **跨 repo 陷阱**：憑 A 判 B → 到 B 取證
5. **難度陷阱**：形容詞放大 → 查業界+實測
6. **假完成陷阱**：修前置當完成 → 端到端實跑

## 吸收判準（外部設計/業界元素要不要拉進來，Kevin 校正 2026-06-14）
> **判準＝對 Prospera OS「整體或未來成長」有幫助 → 學習吸收（按自身節奏長成自己的）；非只看「當前痛有沒有用」。**
- 雙向生成讀「**世界往哪走**」（領先訊號/未來），非只讀「當前缺什麼」——對未來有用者也學習，**非當前無意義就擋門外**。
- 吸收分層：**現用**（立刻長進器官）／**未來啟用**（理解+納 roadmap，規模/需求到了按節奏啟用）／**留指針**（僅真路線衝突或無遷移價值者）。
- 反例（本判準校正前的錯）：把「五模式/A2A/框架選型」當「對當前痛無意義→指針」一刀切——漏了它們對**未來 agent 生態擴張**的價值。校正後改「整體吸收層」（現用 vs 未來啟用）。
- 接 `SKILL-INTELLIGENCE-RESEARCH-TRANSPLANT` C-0 移植閘：吸收判準補此原則（不被巨頭甩開的領先訊號精神）。

## 產出紀律
每孤兒獨立 commit、繁體零簡體、append-only、實測為憑、剩餘誠實登 PENDING。

<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:無機制驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# SKILL-13｜_reference 抽取法 + 五點驗收 + 閘門（Brand 試點沉澱）
## Document Header
- Document Type: Codex
- Version: v1.0
- Status: Approved
- Owner: prospera-infra-ci/skills/
- Governing Authority: prospera-engineering-codex v1.0
- DNA Reference: 要素六（SSOT 唯一真相）+ 要素八（AI 協作協議）
- Last Updated: 2026-06-10

---

## 1. Identity & Scope

本 Skill 定義從 MIT 授權 `_reference` 套件抽取框架結構、改寫為 Prospera 客戶交付物的標準方法論。

**適用場景**：任何產品群（Brand/Growth/Operation/Consulting/Resource）需要從 `_reference` repo 吸收業界框架並填入客戶真實資料的任務。

**首次驗證**：Brand 試點（2026-06-10），四個核心檔 P1-P4，全部 DoD PASS，merge 至 main。

---

## 2. Non-Goals

- 不適用：憑空創作框架（必須有 _reference 來源）
- 不適用：直接複製 _reference 內容（必須改寫）
- 不適用：填入未經 SSOT 驗證的客戶數據（禁止生成）

---

## 3. 四步抽取法（每個 _reference 檔必走）

```
Step 1｜整檔讀入結構
  - 讀取 _reference 原始檔，識別 Purpose/Input/Process/Output 骨架
  - 不讀摘要，整檔讀入
  - 記錄：來源路徑 / 授權（MIT？）/ 作者 / 結構類型

Step 2｜改寫：通用框架 → Prospera 場景
  - 通用行銷 → 繁體中文 + Prospera SME×健康醫療×中西整合×政府補助場景
  - 保留骨架結構，替換內容語境
  - 確認：全繁體中文，無簡體

Step 3｜填 SSOT 客戶真實數據
  - 從 BrandKB JSON / brand_intelligence / internal_reference 讀取
  - 不憑空生成任何人物/數字/主張
  - 若 SSOT 無對應資料 → 標「⚠️ 待補」，不編造

Step 4｜標來源 + 更新 SOURCES.md
  - 衍生檔頭部：「結構抽取自 <_reference 路徑>（MIT 授權，作者）」
  - 更新 SOURCES.md 抽取記錄表
```

---

## 4. DoD 逐項打勾（GATE 2，每檔必通過）

```
□ 來源可追溯：標了 _reference 具體檔路徑（非泛稱）
□ 全繁體中文，無簡體
□ 接真材料：用到的客戶數據來自 SSOT，非生成
□ 無 ghost path：所有指針指向實際存在的檔
□ 結構完整：Purpose/Input/Process/Output 四段齊（或等效框架四欄）

任一不過 → 停，回報哪檔哪項卡住，不要硬 commit。
```

---

## 5. 閘門設計（GATE 1 → GATE 4）

```
GATE 1｜清點分類（只讀，不寫）
  - 掃 _reference 候選檔
  - 判斷對應哪個群/層級/現有交付物
  - 輸出：比較表 + 建議抽取清單（3-5 檔）
  - 停：等 Kevin 確認分類才進 GATE 2

GATE 2｜DoD 驗收（每檔自動，§4 五項）
  - 每檔逐項打勾
  - 任一不過 → 停回報，不硬 commit

GATE 3｜phoenix 實質驗證（自動）
  - 用抽取後的檔實際產出客戶交付物
  - 對比舊版骨架：是否真有血肉？假數據/貧瘠是否消失？
  - 回報：新舊對照表

GATE 4｜merge 裁示（Kevin 人工）
  - 呈五點驗收報告（§6）
  - 不 merge，等 Kevin 裁示
  - merge 後才更新 MASTER_LOG + ACTIVE_STATE
```

---

## 6. GATE 4 五點驗收骨架

```
① 原始設計品質：_reference 源檔結構品質評鑑
② 抽取方式：DoD 逐檔打勾表（證明整檔抽取非二手）
③ 五群對應：各檔落在哪個群/層，有無錯位
④ 系統驗證：
   - 實質：新舊血肉對照（哪裡從骨架變實）
   - 格式：docx/pdf 交付件路徑（Stage 3b）
⑤ 待確認：哪些要修 / 能不能 merge
+ branch 名
```

---

## 7. 真實性守則（防 GATE 4 錯誤）

```
✅ 人物/院長聲音：必須來自 SSOT 或 Kevin 提供的真實資料
✅ 數字：必須有 BrandKB 或 git 可見文案佐證
✅ SSOT 無的個人資料 → 標「⚠️ 待補」，絕不推導/編造

🔴 錯誤範例（Brand 試點 GATE 4 發現）：
   - 「李醫師」= 虛構人物，BrandKB 無此人 → CRITICAL 錯誤
   - 修正：查 SSOT 確認真實院長名稱，個資待補標記，品牌層聲音保留
```

---

## 8. 格式交付（Stage 3b）

```
Step 1｜查 _reference 是否有 client_report_generator 類腳本（MIT 授權）
Step 2｜評估適用性（若為 GA4/HubSpot 類數據報告 → 不適用）
Step 3｜不適用 → 用 python-docx 直接產品牌交付件 docx
Step 4｜驗收：封面 / 執行摘要在前 / 繁中 / 表格排版 / 頁尾來源聲明
Step 5｜記錄腳本來源（若借用 _reference 骨架）於 SOURCES.md
```

---

## 9. 與既有系統的介面

| 系統 | 介面點 |
|---|---|
| SSOT | BrandKB JSON → 客戶數字填入；不憑空 |
| SOURCES.md | 每次抽取後同步更新 |
| PENDING_REGISTER.md | 完成後更新 OPEN → CLOSED |
| MASTER_LOG.md | merge 後 prepend 新條目 |
| ACTIVE_STATE.md | merge 後更新進行中狀態 |
| feature branch | 全程在 branch，不碰 main；merge 後才記 |

---

## 10. known_failures 對應

| 症狀 | 修法 |
|---|---|
| 找到「李醫師」類虛構人物 | 查 BrandKB SSOT；有→接；無→標待補；絕不保留編造 |
| 幽默感設為絕對禁用 | 改為「有守則的低度使用」；補使用守則段 |
| ghost path（指向不存在的檔） | 掃描所有 _reference 路徑，確認實際存在後才引用 |
| _reference 腳本不適用 | 說明不適用原因，改用 python-docx 等直接方法 |

---

*v1.0 · 2026-06-10 · prospera-infra-ci/skills/ · 設計：Claude Sonnet 4.6*  
*來源驗證：Brand 試點 feat/brand-extraction-pilot（commit `8c27b02` → merge `290c4b1`）*

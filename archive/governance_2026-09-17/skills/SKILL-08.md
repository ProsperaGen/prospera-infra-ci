<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:無機制驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# SKILL-08｜IP Extraction Check
## Document Header
- Document Type: Codex
- Version: v1.0
- Status: Approved
- Owner: prospera-infra-ci/skills/
- Governing Authority: prospera-engineering-codex v1.0
- DNA Reference: 要素十（IP 萃取框架）
- Last Updated: 2026-05-19

---

## 1. Identity & Scope

每個新機制或新引擎建立後，強制執行 IP 評估並登記。
防止核心 IP 未被識別就公開上雲或進入 AI 訓練資料。

---

## 2. Non-Goals

- 不提供法律意見（→ 線二｜法務與知識產權）
- 不管理授權條款細節

---

## 3. IP 四問評估（DNA 要素十，MUST）

每個新機制建立後，必須回答以下四問：

```
Q1：這個機制是否獨特？（市場上有沒有類似的？）
Q2：這個機制是否可以申請專利？（有新穎的技術特徵嗎？）
Q3：這個機制是否是競爭優勢的來源？
Q4：如果這個機制被競爭對手複製，損失有多大？
```

---

## 4. IP 分級矩陣（DNA 要素十）

| Level | 名稱 | 範例 | 保護方式 | 上雲限制 |
|-------|------|------|---------|---------|
| A | 核心算法 | GOVERNANCE_KERNEL、Drift Isolation | 不上雲、不進 AI 訓練 | 禁止 |
| B | 獨特架構 | 五層架構、雙向生成引擎、ProsperaGen DNA | 申請專利 / 商業秘密 | 限制 |
| C | 方法論 | 顧問交付方法論、三層 Prompt 架構 | 版權 / 品牌保護 | 謹慎 |
| D | 公開知識 | 通用工程實踐、開源工具整合 | 開放分享 | 無限制 |

---

## 5. 評估流程

```
Step 1｜執行 IP 四問（§3）
Step 2｜根據四問結果，對照 §4 分級矩陣，判定 Level
Step 3｜登記到 prospera-intellectual-property IP Registry
Step 4｜根據 Level 執行對應保護措施

Level A：
  - 不 commit 到公開 repo
  - 存放到 prospera-intellectual-property（私有 repo）
  - 程式碼中加入 IP 保護標記
  - 不得貼入任何 AI 對話

Level B：
  - 通知線二｜法務與知識產權，評估專利申請
  - 確認 repo 為私有

Level C/D：
  - 正常 commit 流程
  - Document Header 標注 IP Level
```

---

## 6. IP Registry 登記格式

登記到 `prospera-intellectual-property/IP_REGISTRY.md`：

```markdown
## IP-[序號]
- Name: [機制名稱]
- Level: [A/B/C/D]
- Repo: [所在 repo]
- Path: [檔案路徑]
- Description: [一句話描述這個機制做什麼]
- Uniqueness: [為什麼獨特]
- Registered: [日期]
- Status: [Active / Deprecated]
```

---

## 7. 已登記 IP 候選（參考）

| IP-ID | 名稱 | Level | 狀態 |
|-------|------|-------|------|
| IP-01 | GOVERNANCE_KERNEL | A | Active |
| IP-02 | MetaLearningEngine | B | Active |
| IP-03 | GlobalSelfHealingEngine | B | Active |
| IP-04 | ProsperaGen Engineering DNA | B | Active |

---

## 8. Failure Modes

| 症狀 | 原因 | 修法 |
|------|------|------|
| Level A 機制出現在公開 repo | 未執行 IP Check | 立即移除，改存私有 repo |
| 新機制未登記 IP Registry | IP Check 被跳過 | 補執行四問 + 登記 |
| AI 對話中貼入核心算法 | 不知道是 Level A | 查 IP Registry 確認 Level 再決定是否分享 |

---

## 9. Audit Requirements

每次 IP 評估記錄到 prospera-audit-ledger：
```
[日期] IP-CHECK: [機制名稱] [Level A/B/C/D] [登記狀態] [評估者]
```

---

*v1.0 · 2026-05-19 · prospera-infra-ci/skills/*

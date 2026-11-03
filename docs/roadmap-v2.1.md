# Agent Wiki V2.1 → V2.3 路線圖

**狀態：** 草案，2026-11-03
**基礎：** [`spec.md`](../spec.md) V2 0.1、`personal-memory` Skill 0.2.2、[驗證結果](../README.md#驗證結果)

## 一句話

不換記憶引擎，強化記憶行為。Notion 繼續當唯一可編輯來源、官方 Notion connector／MCP 繼續當存取層，下一步把 `personal-memory` 做成**可量測、可驗證、跨 Agent 一致的 Memory Behavior Layer**。

## 為什麼不換儲存層

目前的證據指向行為，不指向儲存：

| 證據 | 說明 |
|---|---|
| [Experiment 1 第 1 輪](experiments/experiment-1-retrieval.md) | 沒有 Skill 時 3/3 只用內建記憶，Notion 檢索 0/3 |
| [Experiment 1 第 3 輪](experiments/experiment-1-round-3.md) | 載入 Skill 後，改寫過的題目 10/10 主動查 Notion 且答對；口語轉術語由 Agent 自己完成 |
| [Skill 0.2.0 回饋](experiments/skill-0.2.0-review.md) | claude.ai 只裝外掛程式時 Skill 從未被觸發；靠內建記憶提醒「先載入 Skill」後才穩定 |
| [Experiment 3](experiments/experiment-3-cross-agent.md) | 跨 AI 讀取 8/8，反向寫入讀回成功 |

瓶頸是「Agent 不知道要去查」，不是「查不到」。換成 Mem0、Graphiti 或自架服務都不會解決觸發問題，反而會失去已驗證的跨 AI、手機與匯出能力（規格第 11 節）。

## 借鑑的設計模式

只借解法，不整合系統。

| 參考專案 | 借鑑的能力 | 在 Agent Wiki 的做法 | 階段 | 優先級 |
|---|---|---|---|---|
| OpenClaw | 核心記憶與詳細記憶分層、按需召回 | 極短的常駐 Bootstrap Rule ＋既有漸進式載入 Skill | V2.1 | P0 |
| Graphiti | Bi-temporal、歷史事實、失效關係 | 重要決策區分「生效／被取代日期」與「記錄日期」，保留被推翻的觀點 | V2.2 | P1 |
| Mem0 | 擷取、去重、檢索評估 | Capture 決策表（重複／修正／矛盾／推測／來源不明）＋回歸測試 | V2.1–V2.2 | P1 |
| Basic Memory | 專案知識組織、關聯搜尋 | 總覽頁與主題頁之間的「相關頁面」連結 | V2.2 | P1 |
| Cognee | Session 知識整合、跨文件關聯 | 把討論中的重要經驗整理回專案總覽 | V2.3 | P2 |
| Letta | 可持續更新的記憶、審核與整理 | 按需執行的 Memory Maintenance：先提摘要、確認後才改 | V2.3 | P2 |

OpenClaw 的分層是 Runtime 層級的 Hook，能在每回合前執行程式。在 ChatGPT、claude.ai 這類既有客戶端，我們只能控制常駐指令與工具，不能保證每回合執行自製的前置程式。Bootstrap Rule 是在這個限制下最接近的做法。

## V2.1：讓 Agent 可靠地主動查（P0）

目標：解決觸發可靠性，並建立之後每次修改都能用的量測基準。

| 項目 | 內容 | 狀態 |
|---|---|---|
| Bootstrap Rule | 一段 5 行以內、各平台常駐入口都放得下的規則，只負責「先載入 Skill、不以內建記憶取代」 | 本 PR：[`docs/bootstrap-rule.md`](bootstrap-rule.md) |
| Retrieval Gate | Skill 內明確列出要查／不用查／不確定時的判斷，同時降低漏查與誤查 | 本 PR：`SKILL.md` 0.3.0 |
| 回歸測試集 | 30 題固定題目（20 題需要記憶、10 題不需要），各平台重複執行 | 本 PR：[`experiments/benchmark-v2.1.md`](experiments/benchmark-v2.1.md) |
| 各平台實測 Bootstrap 載入 | claude.ai 個人偏好／內建記憶、Claude Code、Codex 全域 `AGENTS.md`、ChatGPT 自訂指令 | 待實測 |
| 跨裝置實測 | Experiment 4 目前是「推論通過、未實測」，用手機跑回歸測試的子集補上 | 待實測 |

### V2.1 驗收門檻

建議的第一階段門檻，不是目前測得的成績：

| 指標 | 門檻 |
|---|---|
| 需要記憶時的主動觸發率 | ≥ 90% |
| 不需要記憶時的誤觸發率 | ≤ 10% |
| 已觸發後的正確檢索率 | ≥ 85% |
| 引用歷史資訊時的來源追溯率 | 100% |
| 舊觀點誤判為目前結論 | 0 |
| 未授權覆蓋或錯誤宣稱已保存 | 0 |

## V2.2：提升記憶品質，而不是數量（P1）

每一項都等 V2.1 的基準跑出來，用失敗題目決定先做哪個。

### 1. 時間與來源語意（借鑑 Graphiti）

不加 Schema，只對「重要決策」要求一致的輕量寫法：

```text
決策 A · 歷史觀點
當時採用：Local-first
生效日期：2026-09-06
理由：希望自行控制資料、搜尋與生命週期
後續狀態：2026-10-31 被決策 B 取代

決策 B · 目前方向
採用：Notion-first
決策日期：2026-10-31
理由：跨帳號與裝置存取便利性優先
來源：使用者確認
```

- 區分「事情發生／成立的日期」與「整理到 Notion 的日期」（現有的「整理到：」）。
- 被取代的段落加「後續狀態」，不刪除、不改寫原文。
- `retrieve.md` 補一條：回答「目前」怎麼做時，先找有沒有「後續狀態」或更晚的修正段落。

### 2. Capture 去重與衝突判斷（借鑑 Mem0）

`capture.md` 改成決策表：

| 情況 | 處理 |
|---|---|
| 新資訊 | 追加到最相關的主題頁 |
| 已有相同內容 | 不重複保存，回覆既有頁面連結 |
| 修正舊觀點 | 保留舊段落，追加新結論、日期與理由，舊段落加「後續狀態」 |
| 內容互相矛盾 | 兩種都記，標日期、來源與可信程度，不自行選邊 |
| 只有推測 | 明確標「未證實」 |
| 來源或權限不清楚 | 不自動寫入，先確認 |

不複製 Mem0 的自動擷取引擎；Notion Page 上保留歷史與避免重複，比自動產生大量 atomic memory 重要。

### 3. 頁面關聯（借鑑 Basic Memory）

- `page-format.md` 加「相關頁面」一行，連到同專案或跨專案的相關主題頁（例如工作專案的交易原子化 ↔ SQL Server 可靠性）。
- 查詢時可從總覽頁沿相關頁面延伸，不另建 Wiki 引擎或 Graph DB。

## V2.3：按需整理知識（P2）

從「人提出 → Agent 查 → Agent 存」擴充到「Agent 讀到多份相關記憶 → 發現重複、矛盾或過時 → 建議整理 → 確認後更新」。

- 只在使用者要求整理時執行，不做每日排程（Dreaming Pipeline）。
- 先提出修改摘要，確認後才寫入；保留原始來源與歷史觀點；重要修改讀回確認。
- 規則放新的 `references/maintenance.md`，由路由表載入。
- 等真的出現大量重複或過期內容，才評估自動排程。

## 分層決策：什麼繼續、什麼暫緩

| 層次 | 決策 |
|---|---|
| Storage：Notion | 繼續作為唯一可編輯來源 |
| Access：官方 Notion connector／MCP | 繼續使用 |
| Behavior：`personal-memory` Skill | 持續強化（本路線圖主體） |
| Index：自建 FTS／Vector／Graph | 暫不做 |
| Background Processing | 暫不做 |
| Storage Adapter 抽象層 | 保留設計邊界（Skill 不寫工具名稱），不實作 |

README「已知限制」寫的是早期印象：「Notion 搜尋偏關鍵字」。官方 Remote Notion MCP 目前已有搜尋、Markdown 讀寫、OAuth 與較省 context 的工具介面，應該用回歸測試對目前的 connector 重新量測，不沿用舊結論。

### 什麼情況才換掉 Notion MCP

依實際失敗情境，從最便宜的處置開始：

| 出現的問題 | 優先處置 |
|---|---|
| Agent 沒有主動查 | 改 Bootstrap Rule／Skill 觸發 |
| 找到不相關頁面 | 改主題入口、搜尋關鍵字與讀取策略 |
| 查到過時資訊 | 加強時間語意與來源判讀（V2.2-1） |
| 重複保存大量內容 | 改 Capture／Consolidation（V2.2-2、V2.3） |
| 相同問法反覆找不到資料 | 用回歸測試比較 Notion 與混合搜尋的命中率 |
| 高頻檢索導致成本或延遲過高 | 評估衍生索引或替代 backend |
| 需要真正的存取隔離 | 使用獨立身分或具權限控制的儲存方案 |
| 多 Agent 同時寫入互相覆蓋 | 評估具版本或併發控制的寫入方式 |

若未來試用 Basic Memory、Mem0 或 Graphiti，先以 Notion 匯出快照做唯讀比較，不讓兩套系統同時擁有寫入權。

## 安全提醒

- 官方 Notion MCP 以登入身分的完整權限存取 workspace。Skill 的「只查 Personal Brain Lab」是行為規則，不是存取隔離。
- 公司 AI 帳號不應直接連到有完整私人 Brain 存取權的個人 Notion 身分（規格 5.2）。
- 公司非公開資料能否交給外部 AI 處理，要遵守公司與客戶的授權規範；只移除個資與憑證不一定足夠。這點比規格第 6 節的「禁止保存項目」範圍更廣，V2.2 修改 Capture 時一併補進 `capture.md`。

## 版本對應

| 版本 | Skill | 內容 |
|---|---|---|
| V2.1 | 0.3.x | Bootstrap Rule、Retrieval Gate、回歸測試基準 |
| V2.2 | 0.4.x | 時間與來源語意、Capture 決策表、相關頁面 |
| V2.3 | 0.5.x | 按需 Memory Maintenance |
| V3 | 未定 | 是否需要獨立 Memory Engine，由回歸測試結果決定，不預先指定 |

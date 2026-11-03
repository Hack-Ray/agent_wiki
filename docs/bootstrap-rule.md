# Bootstrap Rule

V2.1 P0。一段放在各平台**常駐指令入口**的短規則，只負責一件事：在 Skill 被載入之前，讓 Agent 想到要載入它。怎麼查、怎麼存、怎麼更新，全部留在 `personal-memory` Skill。

## 為什麼需要

- claude.ai 只裝外掛程式時，Skill 從未被觸發；改用內建記憶提醒「先載入 Skill」後才穩定（[Skill 0.2.0 回饋](experiments/skill-0.2.0-review.md)）。
- 沒有指示時，Agent 優先用平台內建記憶，不會去查 Notion（[Experiment 1 第 1 輪](experiments/experiment-1-retrieval.md)）。

觸發決策發生在 Skill 載入**之前**，所以只改 Skill 內文修不到這一步，需要一段一定會被載入的常駐規則。

這不是 Runtime Hook。在既有客戶端上，我們只能控制常駐指令與工具，不能保證每回合先執行自製程式；規則是否生效要各平台實測。

## 規則本文

各平台使用同一段文字，改版時只改這裡：

```text
當問題可能涉及我的專案現況、過往經驗、技術決策、問題排查、個人偏好或觀點演變時，
即使沒有明說「以前」或「記憶」，回答前先載入最新版 personal-memory Skill，
並依它的規則查詢 Notion 的 Personal Brain Lab。
我要求「記下來」「更新記憶」時，也先載入這個 Skill，寫進 Personal Brain，不是平台內建記憶。
平台內建記憶不能取代 Personal Brain 查詢。一般知識，或只靠本輪資訊就能回答的問題，不需要查。
```

設計考量：

- **短。** 常駐入口通常有字數限制，而且每回合都佔 context。細節交給 Skill 的漸進式載入。
- **涵蓋隱性情境。** 「即使沒有明說」是為了抓「我該用 A 還是 B」這類沒提過去、但答案會受既有決策影響的問題。
- **包含保存。** [Skill 0.2.0 回饋](experiments/skill-0.2.0-review.md)中「更新回記憶」被當成內建記憶，所以保存觸發也要在 Skill 載入前就成立。
- **明說不用查的情況。** 降低誤觸發，對應回歸測試的「誤觸發率 ≤ 10%」。
- **不寫工具名稱。** 各平台的 Notion 工具名稱不同（AGENTS.md）。

## 放在哪裡

| 平台 | 常駐入口 | 狀態 |
|---|---|---|
| claude.ai／Claude 手機 App | 設定中的「個人偏好」（personal preferences），每個對話都會帶入 | 已設定，待回歸測試量測 |
| claude.ai（替代做法） | 內建記憶：照 README 步驟 2-3 在未用過 connector 的新對話請 Claude 記住 | 0.2.2 已驗證可觸發，非每次 |
| Claude Code | 使用者層級 `~/.claude/CLAUDE.md`；雲端 session 會帶入 claude.ai 個人偏好 | 待實測 |
| Codex | 全域 `~/.codex/AGENTS.md` | 待實測 |
| ChatGPT | 「自訂指令」；外掛程式在一般對話中會自行觸發，這段規則是備援 | 待實測 |

個人偏好與內建記憶擇一即可。兩者都設時內容要一致，避免出現兩套觸發條件。

## 怎麼驗證

用 [V2.1 回歸測試集](experiments/benchmark-v2.1.md) 在每個平台各跑一次，記錄：

- 需要記憶的題目中，有沒有載入 Skill、有沒有實際查 Personal Brain。
- 不需要記憶的題目中，有沒有誤查。
- 回覆過程是否顯示載入的是最新版 Skill（版本號或規則內容）。

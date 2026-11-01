# agent_wiki — Personal AI Memory

讓 Claude、ChatGPT 與 Claude Code 在不同裝置、不同對話中，讀寫同一份個人記憶。

## 這是什麼

每個 AI 平台都有自己的內建記憶，但彼此不相通：在 Claude 討論過的決策，ChatGPT 不知道；換一台裝置或開新對話，前因後果又要重講一次。內建記憶也看不出出處，內容過時了也不會告訴你。

agent_wiki 的做法是把記憶放在你自己的 Notion，再給每個 AI 一份相同的行為規則：

- **記憶存在 Notion**。Notion 的「Personal Brain Lab」頁面是唯一的記憶來源，你隨時可以直接閱讀、修改或匯出。
- **AI 用官方 Notion connector 存取**。不需要架伺服器，也沒有要安裝的程式。
- **行為規則是一份 Skill**。[`personal-memory`](skills/personal-memory/SKILL.md) 規定 AI 什麼時候該查記憶、怎麼引用、什麼時候該存、怎麼更新，以外掛程式發布到 Claude 與 ChatGPT。

它保存的不只是結論，也包括當時為什麼這樣想、後來發現什麼、為什麼改變決定。AI 回答時會區分目前結論、過去的觀點與未證實的推測，並附上 Notion 頁面連結。

```text
Claude / ChatGPT / Claude Code
        │  官方 Notion connector
        ▼
Notion「Personal Brain Lab」  ← 唯一的記憶來源
        ▲
        │  何時查、怎麼答、何時存、怎麼更新
personal-memory Skill（本 repo，以外掛程式發布）
```

## 使用教學

### 步驟 1：準備 Notion

1. 在 Notion 建立一個名為 `Personal Brain Lab` 的頁面。記憶都放在它底下。
2. 在底下建一頁「00 — About This Brain」，用幾句話說明這裡存什麼。
3. 之後每個專案或主題會有一個總覽頁，AI 會依 Skill 的規則自己建立與維護，不需要事先建好分類。

### 步驟 2：設定 Claude（claude.ai、手機 App、Claude Code）

1. **接上 Notion。** 在 claude.ai 的「設定 → 連接器」接上由 Notion 發布的官方 **Notion** connector。不要另外安裝社群版的 Notion 外掛。Claude Code 會自動同步 claude.ai 的 connector。

2. **安裝外掛程式。** 外掛程式只包含 Skill，不包含任何 connector 或 MCP server。
   - claude.ai：「設定 → 外掛程式 → 新增 → 新增市集 → 從儲存庫新增」，輸入 `Hack-Ray/agent_wiki`，再從市集安裝 `personal-memory`。
   - Claude Code：

     ```text
     /plugin install personal-memory --marketplace Hack-Ray/agent_wiki
     ```

3. **讓 Claude 記得先載入 Skill。** claude.ai 不會自己觸發外掛程式的 Skill，要靠內建記憶提醒它。開一個**還沒用過 Notion 的**新對話（用過 connector 的對話無法寫入內建記憶），輸入 `/personal-memory` 載入 Skill，再送出：

   ```text
   請把這條規則記住，以後所有對話都適用：
   只要對話涉及我自己的事，包括我問你我的專案、經驗、決策，也包括我告訴你專案進度、做了什麼調整、遇到什麼問題，或要你記下來、更新記憶，第一步都要先載入最新版的 personal-memory skill，再照它的規則查詢與寫入 Notion 的 Personal Brain Lab。不要先寫進你的內建記憶就當作處理完了。我的 skill 還在迭代，每次都要重新載入，不要沿用舊版本。
   ```

4. **確認。** 開新對話問一個和自己有關的問題，回覆過程應出現「已載入技能 personal-memory」，回答附上 Notion 頁面連結。

### 步驟 3：設定 ChatGPT

1. **接上 Notion。** 在 ChatGPT 設定接上 Notion connector。
2. **建立外掛程式。** 對 ChatGPT 的 Plugin Creator 說：「協助我建立一個外掛程式，掛上 https://github.com/Hack-Ray/agent_wiki」。
3. **確認內容。** 請它列出外掛程式裡的所有檔案並貼出原文，確認 `SKILL.md` 與 `references/` 下的檔案都在，而且和 repo 版本一致、沒有被改寫。

ChatGPT 的外掛程式在一般對話中會自己觸發，不需要額外設定記憶。

### 日常使用

直接用平常的說法就好，不需要指定工具或頁面。

| 想做的事 | 可以這樣說 | AI 會做什麼 |
|---|---|---|
| 查過去的事 | 「我的部落格最近進展如何？」「當初為什麼不用 SSR？」 | 從專案總覽頁開始查，回答附頁面連結，區分目前結論與過去觀點 |
| 保存新經驗 | 「記下來」「更新記憶」「把這次的踩坑存起來」 | 先找相關頁面，有就更新、沒有才新建，寫完讀回確認並附連結 |
| 修正舊觀點 | 「那個規劃其實已經完成了，記下來」 | 保留舊內容與日期，追加修正段落，不直接改寫 |
| 告訴它近況 | 「我昨天調整了一版 CMS」 | 先查是否已經記過；只把真正新增的部分寫進去 |

在 Claude 上，如果回覆過程沒有出現「已載入技能 personal-memory」，或它只說「已記進記憶」卻沒有附 Notion 連結，代表它沒讀 Skill。輸入 `/personal-memory` 再說一次即可。

### 更新 Skill

本 repo 發布新版時（`.claude-plugin/plugin.json` 的 `version` 改變）：

- **claude.ai**：「設定 → 外掛程式 → 新增 → 管理市集」，在 `agent_wiki` 按 `…` 同步，再更新外掛程式。
- **Claude Code**：`/plugin update personal-memory`，重新啟動後生效。
- **ChatGPT**：對 Plugin Creator 說「重新同步 Agent Wiki 外掛程式」，確認版本號與 `references/` 檔案都已更新。

Claude 記憶裡那條「先載入最新版 Skill」的規則不需要跟著改。

## 資料邊界

禁止保存的只有兩類，其餘有未來參考價值的內容都可以存進 Personal Brain（規格第 6 節）：

- 客戶個資與帳務識別：客戶 ID、身分證字號、統編、帳號、姓名、地址、電話、真實案件資料與金額。
- 憑證：password、API key、token、private key、connection string。

允許存進 Personal Brain 不代表可以公開或提交到這個 repo。repo 只放共用的規則、文件與去識別化範例。

## 已知限制

- claude.ai 不會自己觸發外掛程式的 Skill。靠內建記憶提醒時大多有效，但不保證每次都觸發，漏掉時需要手動輸入 `/personal-memory`。
- Claude 在用過 connector 的對話中無法更新內建記憶，內建記憶會逐漸落後於 Notion。以 Notion 為準。
- Notion 的官方 connector 預設會把沒指定位置的頁面建成私人草稿。Skill 已禁止這個行為，但沒讀到 Skill 時仍可能發生。
- Notion connector 以你的完整權限存取整個 workspace，無法只開放單一頁面。
- Notion 搜尋偏關鍵字比對，剛寫入的內容可能因索引延遲暫時搜不到。
- ChatGPT 的外掛程式是 repo 的快照，每次發布新版都要手動重新同步。
- Notion 匯出的 zip 中文檔名未標記 UTF-8，終端機的 `unzip` 會失敗，請用 Finder 解壓。

## 驗證結果

| 項目 | 結果 | 紀錄 |
|---|---|---|
| 檢索：沒有 Skill | Claude 3 題都只用內建記憶，沒有查 Notion | [Experiment 1](docs/experiments/experiment-1-retrieval.md) |
| 檢索：有 Skill、題目經第三方改寫 | Claude 10/10 主動查 Notion 且答對 | [Experiment 1 第 3 輪](docs/experiments/experiment-1-round-3.md) |
| 跨 AI 讀寫 | ChatGPT 讀到 Claude 寫入的內容 8/8；ChatGPT 寫入、Claude 讀回 | [Experiment 3](docs/experiments/experiment-3-cross-agent.md) |
| 跨裝置 | 推論通過，未實測 | [Experiment 4](docs/experiments/experiment-4-cross-device.md) |
| 可攜性 | Notion Markdown 匯出完整、可離線閱讀 | [Experiment 5](docs/experiments/experiment-5-portability.md) |
| 獨立子代理檢索 | 3 題中 2 題符合判讀，1 題因測試資料已刪除無法判定 | [Experiment 6](docs/experiments/experiment-6-clean-subagents.md) |
| Skill 0.2.x 實際使用回饋 | 頁面組織規則、claude.ai 載入方式、保存位置修正 | [Skill 0.2.0 回饋](docs/experiments/skill-0.2.0-review.md) |

主要發現：瓶頸不是搜尋品質，而是 AI 不知道要去查。Notion 搜尋偏關鍵字，但 AI 會自己把口語轉回技術術語再搜，不需要自建索引或向量資料庫。整套系統沒有常駐服務，也沒有程式碼，只有一份 Skill。

## 專案結構

| 路徑 | 說明 |
|---|---|
| [`spec.md`](spec.md) | 權威規格 |
| [`skills/personal-memory/`](skills/personal-memory/) | 記憶 Skill：`SKILL.md` 放核心規則與路由，`references/` 放查詢、保存、更新、頁面格式的細節 |
| [`.claude-plugin/`](.claude-plugin/) | 外掛程式與 marketplace 設定 |
| [`docs/experiments/`](docs/experiments/) | 實驗計畫與結果 |
| [`docs/v1/`](docs/v1/) | V1 設計文件（封存） |
| [`AGENTS.md`](AGENTS.md) | 給 AI 的開發規則 |

V1 是本機 Python MCP server 加 SQLite FTS5 的實作，已從 `main` 移除，完整程式保存在 git tag [`v1-baseline`](https://github.com/Hack-Ray/agent_wiki/tree/v1-baseline)。

## License

[MIT](LICENSE)

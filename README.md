# agent_wiki — Personal AI Memory

讓不同的 AI（Claude、ChatGPT、Claude Code）在不同裝置與 Session 中，讀寫同一份個人記憶：過去的經驗、決策、踩過的坑、觀點如何改變。

記憶存在你自己的 Notion。本 repo 不放任何記憶內容，只提供一份共用的行為規則 [`personal-memory` Skill](skills/personal-memory/SKILL.md)，告訴 AI 什麼時候該查、怎麼引用、什麼時候該存。沒有伺服器，也沒有要安裝的程式。

規格見 [`spec.md`](spec.md)。

## 運作方式

```text
Claude / ChatGPT / Claude Code
        │  官方 Notion connector
        ▼
Notion「Personal Brain Lab」  ← 唯一的記憶來源
        ▲
        │  何時查、怎麼答、何時存
personal-memory Skill（本 repo）
```

## 設定

### 1. Notion

建立一個名為 `Personal Brain Lab` 的頁面，記憶都放在它的子頁。建議先建一頁「00 — About This Brain」，簡短說明這裡存什麼。

### 2. Claude（claude.ai、手機 App、Claude Code）

1. 在 claude.ai 的「設定 → 連接器」接上由 Notion 發布的官方 **Notion** connector。不要另外安裝社群版 Notion 外掛。Claude Code 會自動同步 claude.ai 的 connector。
2. 安裝本 repo 的 `personal-memory` 外掛程式。本外掛只包含 Skill，不包含任何 connector 或 MCP server。
   - claude.ai：「設定 → 外掛程式 → 新增 → 新增市集 → 從儲存庫新增」，輸入 `Hack-Ray/agent_wiki`，再從 `hack-ray` 市集安裝 `personal-memory`。
   - Claude Code：

     ```text
     /plugin install personal-memory --marketplace Hack-Ray/agent_wiki
     ```

   之後 repo 發布新版時，在外掛程式頁面或用 `/plugin update personal-memory` 更新。

3. 在一般對話中請 Claude 把路由規則記進內建記憶。實驗中只安裝 Skill 時，Project 以外的對話不會觸發它；記進內建記憶後才會主動查 Notion。

   ```text
   請把這條規則記住，以後所有對話都適用：
   關於我自己的問題（專案進度與現況、過去的經驗、決策、偏好、踩過的坑），先用 Notion 搜尋「Personal Brain Lab」再回答，並附上頁面連結。你的內建記憶只當線索，可能已經過時，兩邊衝突時以 Personal Brain Lab 為準。我說「記下來」、「記住」時，要寫進 Personal Brain Lab，只更新內建記憶不算完成。詳細規則在已安裝的 personal-memory Skill。
   ```


### 3. ChatGPT

1. 在 ChatGPT 設定接上 Notion connector。
2. 用 ChatGPT 的 Plugin Creator 建立私人外掛程式：「協助我建立一個外掛程式，掛上 https://github.com/Hack-Ray/agent_wiki」。建好後請它列出外掛程式裡的所有檔案並貼出原文，確認 `SKILL.md` 與 `references/` 下的檔案都在，且和 repo 版本一致、沒有被改寫。
3. 外掛程式是 repo 的快照。repo 發布新版時，對 Plugin Creator 說「重新同步 Agent Wiki 外掛程式」，並確認版本號和 `.claude-plugin/plugin.json` 一致。

## 驗證結果（V0.1，2026-10-31）

| 項目 | 結果 | 紀錄 |
|---|---|---|
| 檢索：沒有 Skill | Claude 0/3 查 Notion，只用內建記憶 | [Experiment 1](docs/experiments/experiment-1-retrieval.md) |
| 檢索：有 Skill、題目經第三方改寫 | Claude 10/10 主動查 Notion 且答對 | [Experiment 1 第 3 輪](docs/experiments/experiment-1-round-3.md) |
| 跨 AI 讀寫 | ChatGPT 讀到 Claude 寫的內容 8/8；ChatGPT 寫入、Claude 讀回 | [Experiment 3](docs/experiments/experiment-3-cross-agent.md) |
| 觀點演進 | 舊觀點、修正與「沒有紀錄的原因」都能正確區分 | Experiment 1、3 |
| 跨裝置 | 推論通過，未實測 | [Experiment 4](docs/experiments/experiment-4-cross-device.md) |
| 可攜性 | Notion Markdown 匯出完整、可離線閱讀 | [Experiment 5](docs/experiments/experiment-5-portability.md) |
| 自建基礎設施／新增程式碼 | 0 個常駐服務，0 行程式碼 | |

主要發現：瓶頸不是搜尋品質，而是 AI 不知道要去查。Notion 搜尋偏關鍵字，但 AI 會自己把口語轉回技術術語再搜，不需要自建索引。

## 已知限制

- 在 Claude 上，上傳的 Skill 在 Project 以外不會被觸發，需要靠內建記憶裡的路由規則。
- Claude 在用過 connector 的對話中無法更新內建記憶，內建記憶會逐漸落後於 Notion。
- Notion connector 以使用者的完整權限運作，無法只開放單一頁面。不要在同一個 Notion workspace 放公司資料。
- Notion 匯出的 zip 中文檔名未標記 UTF-8，終端機 `unzip` 會失敗，請用 Finder 解壓。

## V1

V1 是本機 Python MCP server 加 SQLite FTS5 的實作，已從 `main` 移除。完整程式在 git tag [`v1-baseline`](https://github.com/Hack-Ray/agent_wiki/tree/v1-baseline)，設計文件在 [`docs/v1/`](docs/v1/)。

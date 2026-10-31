# AGENTS.md

## Project

`agent_wiki` V2 是跨 AI、跨裝置、跨 Session 的個人記憶系統。記憶存在使用者的 Notion，各 AI 用自己的官方 Notion connector 存取，本 repo 只放共用的行為規則（Skill）、文件與實驗紀錄。

權威規格是 [`spec.md`](spec.md)。本檔與規格衝突時以規格為準，除非使用者明確變更需求。

V1（本機 Python MCP + SQLite）已從 `main` 移除。完整程式保存在 git tag `v1-baseline`，V1 文件保留在 [`docs/v1/`](docs/v1/) 作為設計演進紀錄。

## Repository 內容

| 路徑 | 狀態 | 說明 |
|---|---|---|
| `spec.md` | V2 | 權威規格 |
| `skills/personal-memory/` | V2 | 共用的記憶 Skill，也是要發布的產物 |
| `.claude-plugin/` | V2 | 外掛程式與 marketplace 設定檔 |
| `docs/experiments/` | V2 | 實驗計畫與結果 |
| `docs/v1/` | V1 封存 | V1 規格、README、AGENTS，不再修改 |

不要從 `v1-baseline` 把 V1 程式搬回 `main`，除非使用者明確要求。

## 開發原則

- 先用 Agent 與平台既有的能力。出現問題時，依序檢查 Skill 措辭、Notion 資料組織、平台權限、使用方式，最後才考慮寫程式（規格第 11 節）。
- 新增程式前，在 PR 或文件中回答規格第 11 節的五個問題，並附上可重現的證據。
- 不預先實作規格第 2.2 節排除的元件。
- 不在 repo 存放任何私人記憶內容。範例必須去識別化。

## 修改 Skill

`skills/personal-memory/SKILL.md` 同時用於三個地方：Skill 上傳、claude.ai Project 指令、ChatGPT Project 指令。

- 不寫特定工具名稱或固定呼叫順序。本文要能直接貼進任何平台的指令欄位。
- `description` 決定 Skill 是否被觸發，涵蓋的問法要和本文的「何時查」一致。
- 每條規則應對應一個實際觀察到的問題。修改後在 `docs/experiments/` 記錄是哪次結果促成這次修改。
- 本 repo 同時是 Claude 外掛程式（`.claude-plugin/plugin.json`）與它的 marketplace（`.claude-plugin/marketplace.json`）。修改 Skill 後，兩個檔案的 `version` 要一起升版，並執行 `claude plugin validate .`。不升版，已安裝的人不會收到更新。
- 修改後，提醒使用者更新 ChatGPT 與 claude.ai Project 的指令。這兩處無法透過外掛程式更新。

## 實驗紀錄

- 每個實驗一份檔案，放在 `docs/experiments/`，包含目的、設定、題目、答案與判讀重點、紀錄表、觀察、限制。
- 結果照實記錄。未實測的項目寫「推論通過、未實測」，不寫成通過。
- 含答案的檔案不能被受測 Agent 讀到。受測時不要在本 repo 的 Claude Code 中執行。
- 建立測試記憶時，不要虛構使用者可能真的有經歷的主題，否則會和真實記憶衝突。虛構資料必須標示「測試資料」。

## Notion 操作

- 記憶位置只有 `Personal Brain Lab` 與其子頁，不使用 Notion Memory 或其他資料庫。
- 觀點改變時保留舊觀點與日期，追加修正段落，不改寫舊內容。
- 刪除、覆蓋或大量修改 Notion 頁面前，先取得使用者同意。寫入後讀回確認。

## Security

禁止保存客戶個資與帳務識別（客戶 ID、身分證字號、統編、帳號、姓名、地址、電話、真實案件資料與金額），以及 password、API key、token、private key、connection string（規格第 6 節）。除此之外，其餘內容皆可依未來參考價值保存至 Personal Brain，包括公司內部技術資訊、business logic、architecture 與專有程式碼。混有禁止項目時先移除再保存。repo 仍不得存放私人記憶；允許保存至 Personal Brain 不代表允許公開或提交至 Git repository。

## Git Workflow

修改前：

- 執行 `git status`，了解既有的未提交變更。
- 不要覆蓋或還原與當前任務無關的使用者變更。
- 開始開發前先建立工作分支，預設使用 `codex/` 前綴，不直接在 `main` 修改。

開發中：

- 變更範圍限於當前任務，不混入無關的重構。
- 完成前用 `git diff` 檢查變更。

完成後：

- 執行 `git status`，檢查最終 `git diff`。
- 回報所有新增、修改、刪除的檔案，並建議 commit message。
- 變更透過工作分支 commit、push 並開 PR，檢查完成後再合併至 `main`，不直接 push 至 `main`；commit、push 與合併仍須有使用者授權。

除非使用者明確要求，不要執行：

- `git commit`
- `git push`
- `git reset --hard`
- `git clean`
- force push
- 改寫歷史

未經使用者同意，不得丟棄使用者既有的變更。

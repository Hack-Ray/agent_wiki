# AGENTS.md

## Project

`agent_wiki` V2 是跨 AI、跨裝置、跨 Session 的個人記憶系統。記憶存在使用者的 Notion，各 AI 用自己的官方 Notion connector 存取，本 repo 只放共用的行為規則（Skill）、文件與實驗紀錄。

權威規格是 [`spec.md`](spec.md)。本檔與規格衝突時以規格為準，除非使用者明確變更需求。

V1（本機 Python MCP + SQLite）已凍結，基線為 git tag `v1-baseline`，V1 文件在 [`docs/v1/`](docs/v1/)。

## Repository 內容

| 路徑 | 狀態 | 說明 |
|---|---|---|
| `spec.md` | V2 | 權威規格 |
| `skills/personal-memory/` | V2 | 共用的記憶 Skill，也是要發布的產物 |
| `docs/experiments/` | V2 | 實驗計畫與結果 |
| `docs/v1/` | V1 凍結 | V1 規格、README、AGENTS |
| `src/`、`tests/`、`pyproject.toml` | V1 凍結 | 不再擴充，V2 驗收完成後再決定是否刪除 |
| `skills/personal-ai-brain/`、`scripts/` | V1 凍結 | V1 Skill 與 Windows 安裝腳本 |

不要修改 V1 凍結的檔案，除非使用者明確要求。

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
- 修改後，提醒使用者重新上傳 Skill 並更新各平台的 Project 指令。

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

不得在 repo 或 Notion 保存憑證、客戶資料、公司內部資料或專有程式碼（規格第 6 節）。公司工作的經驗即使去掉名稱，也要評估技術細節是否能還原非公開資訊，不確定就不存。

## Git Workflow

修改前：

- 執行 `git status`，了解既有的未提交變更。
- 不要覆蓋或還原與當前任務無關的使用者變更。

開發中：

- 變更範圍限於當前任務，不混入無關的重構。
- 完成前用 `git diff` 檢查變更。

完成後：

- 執行 `git status`，檢查最終 `git diff`。
- 回報所有新增、修改、刪除的檔案，並建議 commit message。

除非使用者明確要求，不要執行：

- `git commit`
- `git push`
- `git reset --hard`
- `git clean`
- force push
- 改寫歷史

未經使用者同意，不得丟棄使用者既有的變更。

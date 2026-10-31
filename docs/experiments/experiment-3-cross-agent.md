# Experiment 3: Cross-Agent Access

## 目的

Notion 相對於平台內建記憶的主要價值，是不同 AI 能讀寫同一份記憶。本實驗驗證：

- A. Claude 寫入的記憶，ChatGPT 在全新 Session 中找得到、讀得對。
- B. ChatGPT 能否寫入 Personal Brain，且 Claude 讀得回來。

V2 規格把跨 AI 讀取列為第一優先，自動寫入列為需要實驗確認的能力；寫入失敗也是有效的結果，記錄下來即可。

## 前置：Claude 寫入（已完成）

2026-10-31 由 Claude Code 在「Agent Wiki 架構反思」頁尾新增「2026-10-31 檢索實驗結果」段落，並讀回確認。內容包含第 1 輪 0/3、第 3 輪 10/10、996 字 Skill、Agent 會把口語轉回技術術語再搜尋。

## 設定

1. ChatGPT 設定中接上 Notion connector，登入同一個個人 Notion。
2. 建立 ChatGPT Project，把 `skills/personal-memory/SKILL.md` frontmatter 之後的全文貼進 Project 指令。
3. ChatGPT 內建記憶保持開啟。
4. 記下設定時遇到的步驟與限制，例如 connector 是否只能讀、是否需要額外開啟寫入權限。

## A. 讀取測試

在 Project 開新對話，貼上以下題目。

```text
A1. 我後來有測過 AI 會不會自己去翻我的筆記嗎？結果怎樣？
A2. 一開始 AI 回答我過去的事情時，為什麼沒有用到我的筆記？
A3. 我的個人記憶系統需要自己做一套搜尋功能嗎？為什麼？
A4. 我原本打算怎麼從外面連進部落格的文章管理後台？後來有沒有換做法？當時是怎麼考量的？
A5. 之前把部落格部署到亞馬遜雲端時，系統一直不讓部署流程取得臨時權限，那次到底是哪裡設定錯了？
A6. 我的文章管理後台明明只開放自己電腦連線，為什麼當時還是覺得有安全風險？
A7. 我之前是不是有遇過某個系統內部的服務接口偶爾回應很慢？當時猜是什麼問題？後來有找到真正原因嗎？
A8. 我之前有沒有實際處理過那種管理一整群容器的系統版本更新？
```

### 答案與判讀重點

「正確」需同時滿足：附上 Notion 頁面連結或標題、內容正確、時間性判斷正確。

| # | 預期來源頁面 | 判讀重點 |
|---|---|---|
| A1 | Agent Wiki 架構反思（Claude 新寫入段落） | 第 1 輪 0/3、第 3 輪加 Skill 後 10/10 |
| A2 | 同上 | 沒有指示時用內建記憶，Agent 不知道要去 Notion |
| A3 | 同上 | 不需要，Agent 會自己改寫查詢；另可提到 V1 曾自建 FTS5 屬於過去的做法 |
| A4 | Personal Blog 架構決策與演進 | 10-22 Tailscale 為舊觀點，10-29 改 Cloudflare Access，放棄 Tailscale 的原因沒有紀錄 |
| A5 | Personal Blog 踩坑紀錄 | OIDC 不可變 subject claim 格式與 IAM 信任條件不符 |
| A6 | Personal Blog 踩坑紀錄 | DNS rebinding，Host 白名單 |
| A7 | 未解假設：API 偶發變慢（🧪） | 懷疑連線池，未證實 |
| A8 | 無 | 說找不到 |

A1 到 A3 是本實驗的核心：只有 Claude 寫入後才存在的內容。

### 紀錄表

| # | 查了 Notion | 正確 | 備註 |
|---|---|---|---|
| A1 | ✅ | ✅ | 正確讀到 Claude 寫入的段落：第 1 輪 0/3、第 3 輪 10/10、996 字 Skill |
| A2 | ✅ | ✅ | 指出瓶頸是檢索觸發，不是搜尋失效 |
| A3 | ✅ | ✅ | 把 V1 自建 FTS5 標為過去做法，並補充「只證明目前測試案例，不代表大量筆記」 |
| A4 | ✅ | ✅ | 舊觀點、修正、放棄 Tailscale 的原因沒有紀錄，三者都正確 |
| A5 | ✅ | ✅ | 附 Notion 頁面與 commit 連結 |
| A6 | ✅ | ✅ | |
| A7 | ✅ | ✅ | 指出是虛構測試資料，且原因未證實 |
| A8 | ✅ | ✅ | 說找不到。另外補了「你研究過 Kubernetes、有 Docker Compose 經驗」，這句來自 ChatGPT 內建記憶，沒有標出來源 |

## B. 寫入測試

在同一個 Project 開新對話，用自然語氣請 ChatGPT 記下一段**真實**的經驗。建議主題是剛才接 ChatGPT Notion connector 的過程，例如遇到哪些設定步驟、哪裡卡住。

記錄：

- ChatGPT 是否寫入成功，寫到哪一頁（新頁或更新既有頁）。
- 是否先搜尋既有頁面、是否讀回確認。
- 若失敗，錯誤訊息或它怎麼說明。是否宣稱成功但其實沒寫入。

之後由 Claude 在另一個 Session 讀回確認內容。

## 結果

執行環境：ChatGPT Project（Project 指令為 `SKILL.md` 本文），Notion connector，內建記憶開啟
執行日期：2026-10-31
A 讀取正確：8 / 8，全部附 Notion 頁面連結
B 寫入：成功，Claude Code 讀回確認

### B 寫入紀錄

- 請求：使用者在新對話中整理 V2 設計草案 v0.1 的討論，最後說「幫我把這段討論成果記下來」。
- ChatGPT 找到既有的「Agent Wiki 架構反思」，在頁尾追加「2026-10-31 設計基線：agent_wiki V2 — Design Draft v0.1」段落，沒有另開新頁。
- ChatGPT 回報已讀回確認。Claude Code 讀回 Notion，內容確實存在；V1、V2、Claude 寫入的檢索實驗段落都完整保留，沒有被覆蓋。
- ChatGPT 主動加上「與同日實際進度對照」，說明 Experiment 1 已執行，避免草案中的實驗計畫被誤讀成尚未進行。
- ChatGPT 主動說明內建記憶這次沒有同步更新，沒有誇大保存結果。

### 觀察

- 跨 AI 讀寫兩個方向都成立：Claude 寫、ChatGPT 讀；ChatGPT 寫、Claude 讀。不需要任何自建服務或橋接。
- 同一份 Skill 在 Claude 與 ChatGPT 上都有效，不需要為平台改寫。
- ChatGPT 寫入的段落很長，接近整份設計草案的摘要。「Agent Wiki 架構反思」已經成為單一大頁。目前不影響檢索，頁面持續變大時可能需要整理（V2 規格 4.4 Consolidation）。
- A8 混入一句來自 ChatGPT 內建記憶的內容，沒有標出來源。Skill 可補一條：引用內建記憶時要說明來源不是 Personal Brain。

## 追加：Project 以外的日常對話

使用者在兩邊的一般對話（不在 Project 內）問「我最近部落格專案的進展如何」，再說「幫我記錄下來」。

| 嘗試 | Claude 結果 |
|---|---|
| 沒有任何設定 | 只用內建記憶，答案過時（說「GitHub Actions 部署還在規劃」）。「記錄下來」只寫進內建記憶 |
| 上傳 `personal-memory` Skill 並啟用 | Skill 沒有被啟用，結果同上，另外建議「透過 SSH 部署」，違反主機不放 SSH 金鑰的設計 |
| 個人偏好設定 | 設定介面沒有 Notion 工具，Claude 拒絕存入規則 |
| 在一般對話請 Claude 把路由規則記進內建記憶 | ✅ 先查 Notion，答案正確並列出參考頁面，主動指出內建記憶的舊規劃和 Notion 衝突。「記錄下來」寫入 Notion 新頁「Personal Blog 進展紀錄 2026-10-31」，Claude Code 讀回確認 |

ChatGPT 改用外掛程式後（Plugin Creator 從 repo 建立私人外掛「Agent Wiki」0.1.0，貼出的 `SKILL.md` 與 repo 版本 `diff` 完全相同），一般對話問「我最近部落格專案的進展如何」：查了 Personal Brain、引用兩個來源頁面、內容正確，並說明「這次沒有重新檢查 repo 或線上運作狀態」。ChatGPT 的外掛程式 Skill 在 Project 以外會被觸發，Claude 的不會。

更早之前，同樣的兩句話，ChatGPT 在沒有 Project 的一般對話中就會查 Notion 並寫入。推測是先前執行 Notion 官方 setup 流程時，ChatGPT 把相關設定存進了內建記憶（未驗證）。

### 觀察

- 在 Claude 上，讓內建記憶負責「去哪裡找」、Notion 負責「記憶內容」，可以讓 Project 以外的對話也查 Notion。上傳的 Skill 沒有被觸發，可能是內建記憶先處理了與使用者有關的問題。
- Claude 在用過 Notion connector 的對話中，無法寫入內建記憶（回覆說系統擋下寫入）。之後內建記憶與 Notion 的內容會逐漸分歧，Notion 更適合當正式來源。
- 新頁是日期型頁面，內容幾乎都是「Personal Blog 專案總覽」的複述，只多一條待確認事項。違反 Skill「已有相關頁面就更新它」的規則。

### 限制

- 只跑一次，未記錄設定 ChatGPT connector 的步驟與耗時。
- 寫入測試使用明確指令「幫我記下來」，尚未測試沒有明確指令時是否會主動保存。
- 執行裝置未記錄；手機上的讀寫屬於 Experiment 4。

# Experiment 1 第 3 輪：Skill 引導下的主動檢索

## 目的

第 1 輪顯示沒有指示時，Agent 會用平台內建記憶，不會去查 Notion。第 2 輪在提示中限定只查 Notion，10/10 正確，但題目用詞與頁面原文重疊。

這一輪驗證兩件事：

1. 加入 `skills/personal-memory/SKILL.md` 後，問題裡不提 Notion，Agent 是否會主動查 Personal Brain。
2. 題目由第三方（ChatGPT）改寫、避開原文用詞後，Notion 搜尋是否仍找得到。

## 測試資料

`Personal Brain Lab` 下新增 3 頁真實資料，2026-10-31 整理自 `Hack-Ray/personal-blog` repo：

- Personal Blog 專案總覽
- Personal Blog 架構決策與演進
- Personal Blog 踩坑紀錄

加上第 2 輪既有的「Agent Wiki 架構反思」（真實）與 5 頁 🧪 虛構頁面。

## 設定

1. 在 claude.ai 建立新的 Project。
2. 把 `skills/personal-memory/SKILL.md` 中 frontmatter 之後的全文貼進 Project 指令。
3. 內建記憶保持開啟。
4. 不要在這個 repo 的 Claude Code 中執行，本檔含答案。

## 原始題目

以下題目交給 ChatGPT 改寫，再把改寫後的版本貼進 Project 的新對話，一次一題。

```text
Q1. 我的部落格公開網站為什麼不用 SSR？
Q2. 部落格的 CMS 上雲時，一開始打算用什麼方式連線？後來有改嗎？為什麼？
Q3. 部落格的 CMS 主機為什麼選 EC2 而不是 Lightsail？
Q4. 部署到 AWS 時一直出現 AssumeRoleWithWebIdentity 被拒絕，那次是什麼原因？
Q5. 部落格的 CMS 遇過什麼和中文輸入法有關的問題？
Q6. 本機 CMS 只綁 127.0.0.1，為什麼還是不夠安全？
Q7. 我是怎麼把容器映像檔變小的？
Q8. 有個內部 API 偶爾變很慢，我之前懷疑過原因嗎？確定了嗎？
Q9. 我的 AI 記憶系統為什麼從本機資料庫改成 Notion？
Q10. 我有記錄過 Kubernetes 叢集升級的經驗嗎？
```

### 給 ChatGPT 的改寫提示

```text
請把下面 10 個問題改寫成平常聊天會問的口語說法。
規則：
- 意思不變，編號不變。
- 盡量不要沿用原句的關鍵詞。技術名詞改用同義詞、口語描述或換個角度問，例如不要直接寫出 SSR、Lightsail、AssumeRoleWithWebIdentity、127.0.0.1、Kubernetes 這些詞。
- 不要提到 Notion、記憶系統的資料來源或「去查」。
- 只輸出改寫後的 10 個問題。

<貼上原始題目>
```

## 答案與判讀重點

「正確」需同時滿足：答案附上 Notion 頁面連結（代表來自 Personal Brain）、內容正確、時間性判斷正確。只來自內建記憶、沒有 Notion 連結的答案，即使內容正確也記為「未查 Notion」。

| # | 預期來源頁面 | 判讀重點 |
|---|---|---|
| 1 | Personal Blog 架構決策與演進 | 預算約 NT$500、不要常駐後端、後端停機不能影響閱讀，規格明確排除 SSR |
| 2 | Personal Blog 架構決策與演進 | 10-22 選 Tailscale 是**過去的觀點**；10-29 改成 Cloudflare Tunnel + Access，並說明否決理由被兩層驗證取代；為何放棄 Tailscale**沒有紀錄** |
| 3 | Personal Blog 架構決策與演進 | SSM 與 IAM instance role 在 EC2 上內建 |
| 4 | Personal Blog 踩坑紀錄 | repo 啟用不可變 subject claim，OIDC sub 變成帶 `@<id>` 的格式，IAM role 信任條件不符 |
| 5 | Personal Blog 踩坑紀錄 | 注音／拼音選字的 Enter 被當成選取標籤；完全相符的 slug 沒排在前面 |
| 6 | Personal Blog 踩坑紀錄 | DNS rebinding 讓外部網頁能打到登入 API，可猜密碼或觸發鎖定；用 Host 白名單修正 |
| 7 | Docker 映像檔瘦身經驗（🧪） | multi-stage build、`.dockerignore`、slim base image；應指出是測試資料 |
| 8 | 未解假設：API 偶發變慢（🧪） | 懷疑連線池，**未證實** |
| 9 | Agent Wiki 架構反思 | 手機與跨 AI 無法存取、lifecycle 與 compile 成本高 |
| 10 | 無 | 必須說找不到 |

## 紀錄表

| # | 改寫後的題目 | 查了 Notion | 正確 | 備註 |
|---|---|---|---|---|
| 1 | 為什麼沒有選擇讓伺服器每次收到請求才產生網頁？ | ✅ | ✅ | 區分文件證據與推論 |
| 2 | 原本打算怎麼從外面連進文章管理後台？後來有沒有換做法？ | ✅ | ✅ | 標出 10-22 舊觀點、10-29 修正，並說明「為何放棄 Tailscale 沒有紀錄」 |
| 3 | 為什麼放在亞馬遜的虛擬主機上，而不是比較簡單的主機方案？ | ✅ | ✅ | |
| 4 | 部署流程一直不能取得臨時權限，是哪裡設定錯了？ | ✅ | ✅ | 附 commit 編號 |
| 5 | 在部落格後台打中文時遇到什麼奇怪的狀況？ | ✅ | ✅ | |
| 6 | 後台只開放自己電腦連線，為什麼還是有安全風險？ | ✅ | ✅ | |
| 7 | 用了哪些方法讓部落格後端打包出來的執行環境沒那麼肥？ | ✅ | ✅ | ChatGPT 改寫時加了「部落格後端」，偏離原題。Agent 指出部落格頁面沒有這項紀錄，只有一頁虛構測試資料，不能當成部落格做過 |
| 8 | 內部服務接口偶爾回應很慢，猜是什麼問題？有找到原因嗎？ | ✅ | ✅ | 標為未證實，指出筆記停在下一步 |
| 9 | 為什麼不繼續用電腦裡的資料庫，改放線上筆記平台？ | ✅ | ✅ | 區分 V1 舊觀點與 V2 修正 |
| 10 | 有沒有處理過管理一整群容器的系統版本更新？ | ✅ | ✅ | 自行把口語改回「Kubernetes」、「k8s cluster upgrade」、「EKS」三組關鍵字搜尋，皆無結果 |

執行環境：claude.ai Project（Project 指令為 `SKILL.md` 本文 996 字），內建記憶開啟，Opus 5.5
執行日期：2026-10-31
主動查 Notion：10 / 10
正確題數：10 / 10

### 觀察

- 改寫後的題目幾乎不含頁面原文用詞，Agent 仍全部找到。第 10 題的搜尋紀錄顯示，是 Agent 把口語描述轉回技術術語再搜尋。換句話說的能力來自 Agent 改寫查詢，不需要 Notion 做語意搜尋，也不需要自建索引。
- 回答主動以 Personal Brain 為來源，沒有混入內建記憶的內容。

### 限制

- 10 題一次貼進同一則訊息，不是一題一則。
- 只跑一次、只測 Claude，資料共 12 頁。
- 回答以 Claude Docs 文件呈現，貼回時遺失了頁面連結，只保留頁面標題；依標題判定來源。

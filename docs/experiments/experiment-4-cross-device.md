# Experiment 4: Cross-Device Access

## 狀態

**推論通過，未實測。**（2026-10-31，使用者決定不另外實測）

## 推論依據

- 手機與電腦使用同一個 claude.ai 與 ChatGPT 帳號。官方 Notion connector 綁在帳號上，不是綁在裝置上。
- Claude 的 Project 指令、已上傳的 Skill，以及存在 Claude 內建記憶裡的路由規則，都屬於帳號層級設定。
- 整套架構沒有本機服務，手機不需要額外安裝或手動同步。驗收項目「手機使用：不需要自架本機服務」在架構上成立。

## 尚未排除的風險

- V2 規格 5.3 指出，部分 AI client 可能無法在手機上執行寫入。手機上的 Notion 寫入沒有實測。
- 同一天已有兩次推論與實測不符：上傳的 Skill 沒有被觸發；Claude 在用過 connector 的對話中無法寫入內建記憶。

## 補測方式

在手機 Claude App 或 ChatGPT App 開新對話：

1. 問「我最近部落格專案的進展如何」，確認有查 Notion 並附頁面連結。
2. 說「記一下：手機測試成功」，確認回覆附上 Personal Brain 頁面連結，再從電腦讀回。
3. 測完刪除該筆測試資料。

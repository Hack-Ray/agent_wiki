# Experiment 5: Portability

## 目的

確認 Notion 原生 Markdown 匯出能否在沒有 Notion 的情況下閱讀，且內容沒有遺失（V2 規格第 8 節）。

## 執行

- 日期：2026-10-31
- 方式：使用者從 Notion 匯出 `Personal Brain Lab`（Markdown，含子頁），取得 zip。
- 檢查：Claude Code 解壓後，與同日透過 Notion connector 讀到的頁面內容比對。

## 結果

| 檢查項目 | 結果 |
|---|---|
| 頁面數量 | ✅ 根頁面加 10 個子頁，與 Notion 一致 |
| 頁面階層 | ✅ 子頁放在與根頁面同名的資料夾，根頁面以相對路徑連到每個子頁 |
| 文字內容 | ✅ 抽查「Agent Wiki 架構反思」6 個段落標題、「Personal Blog 踩坑紀錄」12 個段落與 10 個 commit 連結，皆完整 |
| 表格 | ✅ 轉成 Markdown pipe table |
| 外部連結 | ✅ GitHub 連結保留 |
| 離線可讀 | ✅ 一般文字編輯器可直接閱讀 |

## 需要注意的地方

- **zip 內的中文檔名沒有標記 UTF-8。** macOS 終端機的 `unzip` 會出現 `Illegal byte sequence`，無法解壓中文檔名的頁面。用 Finder 雙擊解壓沒有問題：使用者用 Finder 解出的 11 個檔案，與 Claude Code 用 UTF-8 腳本解出的結果 `diff -r` 完全相同。
- Callout 轉成 `<aside>` HTML 標籤，可讀但不是純 Markdown。
- 檔名與連結帶有 Notion page ID，例如 `Agent Wiki 架構反思 40ab1f333e9d81c79a68c6a1f6c2e2e3.md`。可以用來對回原頁，但檔名較長。
- 只匯出 `Personal Brain Lab`。若有 Agent 把記憶存到 Notion Memory 或其他資料庫，這份匯出不會包含。這也是記憶應集中在單一位置的理由之一。
- 頁面之間的 Notion mention 轉換未測到：匯出當下的頁面沒有 mention。

## 結論

通過。重要內容可以離線閱讀，沒有發現遺失。目前不需要自動化 Export Utility；手動匯出時要注意解壓工具的中文檔名問題。

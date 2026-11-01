# Skill 0.2.0：實際整理後的回饋

## 來源

2026-11-01，使用者在 `personal-blog` repo 的 Claude Code session 中，請 Claude 用 `personal-memory` Skill 把部落格專案至今的開發過程整理進 Personal Brain。完成後請它檢討 Skill 在查詢與整理上不方便的地方。

整理結果：更新「20 — Personal Blog 專案總覽」、補齊踩坑紀錄 16 項與架構決策，新建 3 個子頁（開發歷程、工作規則與偏好、學習與面試準備）。Claude Code 讀回確認總覽頁結構與內容。遇到 repo 與早期對話對 AdSense 說法不一致時，兩種都記下，沒有自行選邊。

## 回饋與對應修改

| 回饋 | 0.2.0 的修改 |
|---|---|
| 沒有規定頁面結構，子頁分法靠猜 | 「頁面組織」：每個專案一個總覽頁，細節放子頁；查詢時先從根頁面主題入口找總覽頁 |
| 「只存新增內容」需要每次讀完全文去重，頁面越大越貴 | 頁面開頭標「整理到：日期與來源位置」，下次從那裡往後補 |
| 剛寫入的內容搜不到，讀回只能直接讀頁面 | 寫入後直接讀取該頁確認，不用搜尋結果判斷 |
| 中文關鍵字常搜到不相關頁面 | 每頁都有「搜尋關鍵字：」一行 |
| 日期時區不一致（台灣時間與 UTC 混用） | 日期一律用 Asia/Taipei，格式 YYYY-MM-DD |
| 來源標法不一致 | 固定說法：使用者確認、repo、對話整理、平台內建記憶 |
| 個資規則只針對客戶，自己的公開資訊能否存不明 | 不另加規則。0.1.2 已把禁止項目限定為客戶個資、帳務識別與憑證，使用者自己的資訊不在其中 |
| 與平台內建記憶的分工沒寫 | 內建記憶只放短期待辦與當下脈絡，長期內容寫進 Personal Brain |

本次修改以 0.1.2（PR #1 精簡版）為基礎，沿用其資料邊界，只加上述頁面組織與讀回規則。

## 結構調整：漸進式載入

使用者要求 Skill 改成目錄形式，外層只放通用規則與摘要，細節分檔，避免每次觸發都把全部內容讀進 context。

| 檔案 | 內容 | 字數 |
|---|---|---:|
| `SKILL.md` | 摘要、路由表、核心規則 | 808 |
| `references/retrieve.md` | 怎麼查、怎麼回答 | 383 |
| `references/capture.md` | 何時存、存什麼、怎麼存 | 633 |
| `references/update.md` | 補充進度、觀點修正、安全 | 336 |
| `references/page-format.md` | 頁面組織、每頁必備、寫法 | 385 |

觸發時固定載入的內容從 1,466 字降到 808 字。最常見的查詢情境讀 `SKILL.md` 加 `retrieve.md`，共 1,191 字。保存新頁面要讀 `capture.md` 與 `page-format.md`，共 1,826 字，比單檔版多，因為核心規則在 `SKILL.md` 與參考檔各寫一次；查詢遠比保存頻繁，整體仍省。

待驗證：

- Claude 與 ChatGPT 是否會依路由表讀取參考檔，尤其保存時是否讀 `capture.md` 並照做讀回確認。
- ChatGPT Plugin Creator 重新同步時，快照是否包含 `references/`。

## 追加：「更新回記憶」被當成內建記憶

2026-11-01，使用者在 claude.ai 一般對話討論 VM Sandbox 的 runner timeout 問題後說「先更新回記憶吧」。Claude 嘗試寫入內建記憶的「VM Sandbox」檔案，因對話用過 Notion connector 而被系統擋下。失敗後它提議開新對話重寫內建記憶或存成本機檔案，沒有寫進 Personal Brain。當時 claude.ai 上的 Skill 仍是 0.1.x，回覆中也沒有提到 Personal Brain，Skill 可能未被觸發（推測）。

修改：觸發詞加入「更新記憶」、「存到記憶」，並規定「記憶」一律指 Personal Brain；內建記憶寫入失敗時照常寫進 Personal Brain，不改提議其他替代方案。claude.ai 內建記憶裡的路由規則也需同步更新為包含這些說法。

使用者隨後在同一對話要求寫進 Notion。Claude 寫入成功，但建立在 Personal Brain Lab 以外的私人草稿，並請使用者指定位置。原因推測：Notion connector 的說明要求「使用者沒指定位置時建立私人草稿」，而 Skill 未被觸發，路由規則也沒說要放在哪一頁。實際上 Personal Brain 已有「VM Sandbox：測試環境演進與踩坑」，其中列為讀碼推論的「長 job 阻塞 Runner 主迴圈」正是這次發生的問題。Claude Code 將草稿內容以追加段落合併進該頁並讀回確認。

修改：核心規則與 `capture.md` 明定不建立私人草稿或 Personal Brain 以外的頁面，沒指定位置時自行找最相關的既有頁面更新。

## 追加：claude.ai 一般對話如何載入 Skill

2026-11-01 在 claude.ai 一般對話的觀察：

| 嘗試 | 結果 |
|---|---|
| 只安裝外掛程式 | Skill 從未被觸發。「之前的討論」這類問法改用內建的過去對話搜尋，找到已刪除頁面的舊網址，未查 Personal Brain |
| 內建記憶裡存「去 Notion 查」的路由規則 | 會查 Notion，但不讀 Skill；只搜一次就停，漏掉總覽頁上的 PR #127 內容 |
| 使用者以 `/personal-memory` 手動載入，並請 Claude 記住「處理和我有關的事前先載入最新版 personal-memory skill」 | ✅ 新對話中自動出現「已載入技能 personal-memory」，從專案總覽頁開始查，找到 PR #127、`cms-v1.2.0` 與待確認事項 |

結論：claude.ai 可以讀取 Skill，問題是 Claude 不會主動想到要讀。內建記憶每次對話都會載入，適合負責「先讀 Skill」這一步；Skill 負責怎麼查、怎麼存。Skill 改版後不需要更新記憶裡的規則。README 的 Claude 設定步驟改用這個做法。

同一次測試中，Claude 仍說頁面日期是 UTC。「日期用台灣時間」只寫在 `page-format.md`（寫入時才讀），查詢時讀的 `retrieve.md` 沒有。0.2.2 在 `retrieve.md` 補上日期解讀規則。

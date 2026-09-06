# Knowledge

Knowledge 是 Brain 中目前的 canonical understanding。

它用於保存已成熟、可長期重用，並適合供人與 Agent 直接閱讀與檢索的內容。

Canonical 不代表 immutable。新的 authoritative evidence 出現後，既有 Knowledge 可以被修正。

## When to Create Knowledge

當資訊同時符合以下條件時，考慮進入 Knowledge Path：

- 已有足夠 verification
- 具有 long-term retrieval value
- 可重用
- 適合形成 stable topic

`verified` 不代表一定需要 Knowledge。

短期 observation、單次事件或不需要正式文件化的資訊，可以繼續保留在 Memory。

## Workflow

建立或更新 Knowledge 前，先搜尋既有 Brain：

brain_search
→ 判斷是否已有相關 Knowledge
→ 必要時 brain_read
→ 取得 relevant verified information
→ consolidate
→ brain_compile

Search before create.

如果既有 Knowledge 已代表同一 stable topic，優先更新原本的 canonical Knowledge。

不要因為新的 conversation、Memory 或 observation 而建立新的版本型文件。

## Knowledge Organization

以 stable topic 組織 Knowledge，而不是 conversation 或 date。

遵循：

- Prefer consolidation.
- Topic over conversation.
- Split only for independent retrieval intent.

當一個主題具有獨立用途、可被獨立搜尋且能被獨立理解時，才考慮拆成新的 Knowledge。

避免：

- one giant Knowledge file
- one file per conversation
- `v2`、`new`、日期型文件被用來表示同一 canonical topic 的更新

同一主題的新資訊通常應更新既有 Knowledge。

## Consolidation

Knowledge 應保存 consolidated understanding，而不是 raw Memory 或 Source dump。

Agent 負責：

- 理解 relevant verified information
- 讀取 existing Knowledge
- 解決重複與過時內容
- 保留重要 rationale
- 產生完整、可讀的新版 Markdown

更新 Knowledge 時，提供完整 consolidated Markdown。

不要只是 append 新 Memory 原文。

一份 Knowledge 可以整合：

- 多筆 verified Memory
- existing Knowledge
- relevant evidence
- historical rationale

不要求一份 Knowledge 只能對應一筆 Memory。

## Current Understanding and History

Knowledge 主要描述目前最值得採用的理解。

Historical information 可以保留，但應具有理解目前設計、行為或 rationale 的實際價值。

不要把完整事件時間線或 development history 原樣 dump 進 Knowledge。

完整 raw history 應留在 Source 或 Memory。

## Unresolved Information

Knowledge 可以包含重要的 unresolved issue、known unknown 或 open question。

但必須明確標示其狀態。

例如：

## 尚待確認

目前尚未確認正式環境是否使用此設定。

不要把 hypothesis、assumption 或 unresolved issue 描述成 confirmed fact。

未確認內容也不能因為出現在 Knowledge 中，就被視為 verified。

## Updating Existing Knowledge

當新的 verified information 與既有 Knowledge 屬於同一 stable topic：

brain_search
→ brain_read existing Knowledge
→ 取得新的 verified information
→ 重新 consolidate
→ brain_compile 到原 canonical topic

優先更新既有 Knowledge，而不是建立：

- `*-v2.md`
- `*-new.md`
- 日期型 replacement
- conversation-specific replacement

如果新的 authoritative evidence 推翻舊內容，應修正 canonical Knowledge。

必要且有價值的舊資訊可以作為 historical rationale 保留。

## Compile

只將已充分驗證的結論提升為正式 Knowledge 內容。

Agent 負責 semantic reasoning 與 consolidation。

Brain Core 負責 persistence 與 lifecycle enforcement。

Compile 前確認：

- relevant existing Knowledge 已被考慮
- confirmed facts 與 unresolved information 有清楚區分
- 沒有不必要的 duplicate Knowledge
- Markdown 是完整 consolidated version，而不是 partial append

Knowledge consolidation 完成後，再使用 `brain_compile` 保存 canonical Markdown。
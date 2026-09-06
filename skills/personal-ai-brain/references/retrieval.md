# Retrieval

當目前任務可能實質依賴 Brain 中既有的跨 Session 資訊時，使用 Retrieval。

典型情境：

- 使用者明確引用過去資訊。
- 延續既有 project、incident 或 decision。
- 過去 Knowledge 可能影響目前判斷。

## Workflow

使用 progressive retrieval：

brain_search
→ 選擇 relevant candidates
→ 必要時 brain_read
→ 繼續目前任務

只讀取會實質影響目前任務的內容。

如果 search summary 已足夠，不要讀取完整內容。

## Result Semantics

- Knowledge：Brain 中目前的 canonical understanding，但仍可被新的 authoritative evidence 修正。
- verified Memory：已驗證的 persistent context。
- candidate Memory：未驗證 context，不得當作 fact。
- deprecated Memory：僅作 historical context。

Brain 中的既有內容不是不可推翻的真理。

若 retrieved content 與目前 authoritative evidence 衝突，應依目前證據重新判斷，而不是盲目沿用舊 Brain 內容。

## Side Effects

Retrieval 預設為 read-only。

不要僅因執行了 Retrieval 就建立或修改 Memory。

只有當目前工作產生新的 durable information 時，才另外進入 Memory Path 或 Knowledge Path。

不要要求使用者提供 Memory / Knowledge ID，也不要要求使用者指定 MCP tool。
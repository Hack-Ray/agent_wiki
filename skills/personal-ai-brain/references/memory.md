# Memory

Memory 用於保存具有未來 retrieval value 的 persistent context。

Memory 可以保存尚未成熟的資訊，也不等於 canonical Knowledge。

## When to Remember

當資訊很可能在未來另一個 Session 影響判斷或工作，而且目前 Brain 尚未充分保存時，建立 Memory。

常見情境：

- decision、requirement、business rule
- 重要 observation、incident、hypothesis
- 可重用的 project context 或 learning
- 使用者明確要求「記住這個」

通常不要保存：

- 臨時或低價值資訊
- 沒有未來 retrieval value 的中間過程
- Brain 已充分表示的重複資訊

Hypothesis 可以保存；是否值得保存取決於 future retrieval value，而不是它目前是否已被證實。

## Workflow

優先判斷是否已有代表同一件事情的 Memory。

如果已有：

brain_update
→ 必要時更新 verification state
→ stop

如果沒有：

brain_remember
→ 必要時 verify
→ stop

不要僅因 Memory 成為 `verified` 就自動 compile。

只有當資訊已成熟並適合成為 canonical Knowledge 時，才進入 Knowledge Path。

## Candidate and Verification

Agent 產生的新結論預設保持 `candidate`，除非 verification 已有充分依據。

Memory 只有在以下任一條件成立時才可成為 `verified`：

- `evidence`
- `explicit_user_confirmation`

Verification 時保存：

- `verification_basis`
- `verification_evidence`

結論看起來合理，不構成 verification。

Evidence 只能驗證它實際支持的結論。

## User Authority

當使用者對資訊具有定義或直接確認的 authority 時，可以使用 `explicit_user_confirmation`。

例如：

> 「我們決定 M7 使用一週後再評估。」

這是使用者自己的 project decision，可以直接確認。

但使用者對外部 technical / factual claim 的陳述本身不構成 verification。

例如：

> 「我覺得 parameter sniffing 是 root cause。」

除非另有 evidence，否則保持 `candidate`。

## Provenance

當 Memory 來自可追溯的 Source 時，保留對應的 `source_refs`。

Provenance 與 verification 是不同概念。

有 Source reference 不代表該 Memory 已被驗證。

Source 的詳細使用與 trust rules 見 `sources.md`。

## Memory Granularity

不要把需要不同 verification state 的獨立結論混在同一筆 Memory。

當資訊同時包含：

- 已確認的結論
- 尚未確認的 hypothesis

而兩者具有獨立 retrieval value 時，應拆成不同 Memory。

例如：

confirmed architecture
→ verified Memory

unresolved production assumption
→ candidate Memory

不要因此走向一個 observation 一筆 Memory。

是否拆分取決於：

- verification state 是否不同
- 是否具有獨立 retrieval intent

## Update vs. New Memory

同一個 decision、observation 或 hypothesis 的補充，
是否更新原 Memory，取決於既有 Memory 的 lifecycle state。

### Existing candidate

如果既有 Memory 仍為 `candidate`，且新資訊只是同一件事情的補充、
修正或新增 evidence，優先使用 `brain_update` 更新原 Memory。

例如：

parameter sniffing may be the root cause
→ candidate

後續取得更多 observation
→ update 原 candidate Memory

若 evidence 已足夠，可再將同一 Memory 更新為 `verified`。

### Existing verified or compiled

不要改寫既有 `verified` 或 `compiled` Memory 的已確認內容。

如果新的資訊修正、取代或重新解釋原本已驗證的結論：

建立新的 Memory
→ 預設 candidate
→ 依新的 evidence 驗證
→ 必要時 deprecated 被取代的舊 Memory
→ 若已有相關 Knowledge，進入 Knowledge Path 更新 canonical understanding

這樣可以保留 verification history，而不是用新資訊覆蓋舊的已驗證紀錄。

### New Memory Boundary

只有當新的資訊：

- 不能安全地寫回既有 Memory，或
- 具有獨立 retrieval intent

時，才建立新的 Memory。

避免 duplicate，但不要為了避免 duplicate 而破壞 lifecycle safety。

## Memory to Knowledge

`verified` 不代表必須成為 Knowledge。

Memory 可以長期保持為 Memory。

只有當內容已成熟、可重用，且適合成為 canonical long-term documentation 時，才進入 Knowledge Path。

Knowledge consolidation 與 organization 規則見 `knowledge.md`。

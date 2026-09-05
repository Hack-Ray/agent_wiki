# Personal AI Brain (`agent_wiki`)

Personal AI Brain 是一套 local-first 的持久化記憶系統，讓 AI Agent 即使在新的 Session
中沒有舊 Conversation Context，仍可主動搜尋並取回先前保存的重要資訊。

目前專案已實作至 Milestone 5：Codex 可以透過 MCP stdio 管理持久化 Memory、將
`verified` Memory 整合為本機 Markdown Knowledge，並以單一 `brain_search` 搜尋兩者。
Memory 支援 `candidate`、`verified`、`compiled`、`deprecated` lifecycle。

詳細產品需求、Milestone 與 Non-Goals 以 [brain-spec.md](brain-spec.md) 為準；開發與
architecture 規則請參考 [AGENTS.md](AGENTS.md)。README 只提供專案概覽與本機 setup。

## Architecture

```text
Codex
  ↓ MCP stdio
Brain MCP Adapter
  ↓
Brain Service
  ├─ Memory Repository → memory/brain.db (Memory + Memory FTS)
  ├─ Knowledge Index Repository → memory/brain.db (derived Knowledge FTS)
  └─ Knowledge Repository → knowledge/**/*.md (canonical Knowledge)
```

- MCP layer 只負責 tool adapter，不直接操作 SQLite。
- Service layer 負責 validation、typed identifier 與 Memory policy。
- Repository layer 負責 SQLite persistence、FTS5 Memory search、WAL 與 transaction，以及
  UTF-8 Markdown Knowledge 的 atomic filesystem write。
- Brain Core 不依賴 Codex-specific SDK；Codex 只是目前的主要 MCP client。

## Requirements

- Windows
- Python 3.11 或更新版本
- Codex Desktop、Codex CLI 或其他支援 MCP stdio 的 client

## Python environment

在 repository root 建立專案專用 `.venv`，並依 `pyproject.toml` 安裝 package 與 dependency：

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e .
```

確認環境：

```powershell
.venv\Scripts\python --version
.venv\Scripts\python -m pip check
```

`.venv/` 已被 Git ignore，不應提交到 repository。

## MCP stdio server

安裝完成後，可直接啟動 stdio server：

```powershell
.venv\Scripts\brain-mcp.exe
```

MCP client 一般會自行啟動與管理此 process，不需要建立常駐服務。Database 預設位置為
`memory/brain.db`，Knowledge root 預設為 `knowledge/`；若測試需要隔離 storage，可分別
設定 `BRAIN_DB_PATH` 與 `BRAIN_KNOWLEDGE_PATH` 覆寫。

## Register with Codex

使用 Codex CLI 註冊 global MCP server。請依實際 checkout location 調整 absolute path：

```powershell
codex mcp add personal-ai-brain -- "D:\agent_wiki\.venv\Scripts\brain-mcp.exe"
```

等價的 `~/.codex/config.toml` 設定如下：

```toml
[mcp_servers.personal-ai-brain]
command = "D:\\agent_wiki\\.venv\\Scripts\\brain-mcp.exe"
cwd = "D:\\agent_wiki"
```

CLI registration 已使用 absolute executable path，因此 `cwd` 不是必要欄位；只有手動維護
config 且希望固定 working directory 時才需要加入。

確認 registration：

```powershell
codex mcp get personal-ai-brain --json
codex mcp list
```

新增或修改 MCP server 後，重新啟動 Codex Desktop 或 IDE extension。接著輸入 `/mcp`，
確認 `personal-ai-brain` 已連線，並確認可用 tools 包含：

- `brain_remember`
- `brain_search`
- `brain_read`
- `brain_update`
- `brain_compile`
- `brain_rebuild_index`

`brain_read` 接受 `memory:<id>` 或 `knowledge:<relative-path.md>`。`brain_compile` 只接受
`verified` Memory，且呼叫端必須提供安全的 relative `.md` path 與完整新版 Markdown；
詳細 lifecycle 與 compile contract 以 `brain-spec.md` 為準。

`brain_search` 回傳 Memory 與 Knowledge 的 unified lightweight results；完整內容仍需透過
typed identifier 呼叫 `brain_read`。Knowledge Markdown 是 canonical source，SQLite Knowledge
index 可隨時由下列 MCP tool 重建：

```text
brain_rebuild_index()
```

Codex MCP 設定方式亦可參考
[OpenAI Model Context Protocol documentation](https://learn.chatgpt.com/zh-Hant/docs/extend/mcp)。

## Tests

執行完整 test suite：

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

Tests 包含：

- `brain_remember → brain_search → brain_read`
- SQLite connection 關閉並重新建立後的 persistence
- Memory typed identifier validation
- FTS5 search 與 compact search result
- WAL 與 `busy_timeout`
- Memory lifecycle、Knowledge path validation、schema migration 與 compile failure recovery
- UTF-8 Knowledge 建立、完整替換及跨 connection persistence
- Unified Memory/Knowledge search、canonical suppression、filtering、priority 與 final limit
- Knowledge index clear/rebuild 與 transactional failure safety
- MCP client 實際啟動 stdio server，呼叫 Knowledge search/read/rebuild flow

Milestone 2 的人工跨 Session 驗證結果記錄於
[docs/validation/milestone-2.md](docs/validation/milestone-2.md)。

## Repository guidance

- [brain-spec.md](brain-spec.md)：authoritative specification，定義產品目標、architecture、
  milestones、acceptance criteria 與 V1 Non-Goals。
- [AGENTS.md](AGENTS.md)：開發規則、dependency boundaries、data ownership、testing、security
  與 Git workflow。

修改 architecture 或 behavior 前必須先閱讀兩份文件；若內容衝突，以 `brain-spec.md` 為準，
除非使用者明確修改需求。

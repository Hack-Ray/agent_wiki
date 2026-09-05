# MCP stdio setup

Python 3.11 or newer is required.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e .
```

Configure Codex to spawn the installed process:

```toml
[mcp_servers.personal-ai-brain]
command = "D:\\agent_wiki\\.venv\\Scripts\\brain-mcp.exe"
cwd = "D:\\agent_wiki"
```

The database defaults to `memory/brain.db`. `BRAIN_DB_PATH` can override it.

Run tests with:

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```


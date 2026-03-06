# Metabase MCP Server

MCP server that exposes **Metabase** operations (alerts, pulses, dashboards, questions, databases, collections, search) as tools. Built from the [mcp-server-template](https://github.com/your-org/mcp-server-template) and backed by `MetabaseSourceManager` from [drdroid-debug-toolkit](https://github.com/your-org/drdroid-debug-toolkit).

## Tools

The server exposes each Metabase operation as its own MCP tool, with names and parameters taken from the drdroid-debug-toolkit task map. Examples:

- **metabase_list_alerts**, **metabase_get_alert**, **metabase_create_alert**, **metabase_update_alert**, **metabase_delete_alert**
- **metabase_list_dashboards**, **metabase_list_databases**, **metabase_list_collections**
- **metabase_execute_question**, **metabase_execute_sql_query**, **metabase_search**
- …and the rest (pulses, questions, etc.), each with descriptions and parameters from the toolkit’s form fields.

## Requirements

- Python 3.11+
- Access to a Metabase instance (URL + API key)
- [drdroid-debug-toolkit](https://github.com/DrDroidLab/drdroid-debug-toolkit) (installed automatically via `uv sync` or `pip install -e .`)

## Setup

### 1. Clone and install

```bash
git clone https://github.com/your-org/metabase-mcp-server.git
cd metabase-mcp-server
uv venv .venv && source .venv/bin/activate   # or: python -m venv .venv && source .venv/bin/activate
uv sync   # or: pip install -e .
```

This installs the app and its dependencies, including **drdroid-debug-toolkit** (and Django, which the toolkit uses at import time). No manual `PYTHONPATH` is needed when using this install.

### 2. Configure Metabase

Copy the example env and set your instance URL and API key:

```bash
cp .env.example .env
# Edit .env and set:
#   METABASE_URL=https://your-metabase.example.com
#   METABASE_API_KEY=your-api-key
```

Or set the same variables in your shell or your MCP client config.

## Running the server

- **Stdio** (for Cursor, Claude Desktop, etc.):

  ```bash
  uv run metabase-mcp-server
  # or
  MCP_TRANSPORT=stdio uv run metabase-mcp-server
  ```

- **HTTP / streamable HTTP** (e.g. MCP Inspector, port 8000):

  ```bash
  MCP_TRANSPORT=streamable-http uv run metabase-mcp-server
  ```

Override port with `MCP_PORT`, name with `MCP_SERVER_NAME`. See `.env.example` for all options.

## Testing

Install the package with dev dependencies (pytest), then run tests:

```bash
uv sync --extra dev
uv run pytest
```

Or with pip:

```bash
pip install -e ".[dev]"
pytest
```

Tests live in `tests/`: one always runs (config); two require `METABASE_URL` and `METABASE_API_KEY` and a venv with the toolkit. Conftest loads `.env` from the **repo root** (the folder that contains `src/` and `pyproject.toml`). **If the credential tests are skipped:** create a file named `.env` in that repo root, copy contents from `.env.example`, and set `METABASE_URL` and `METABASE_API_KEY` to your real Metabase URL and API key. Run pytest from the repo root (e.g. `cd metabase-mcp-server && pytest tests/`). Use a venv that has the toolkit and Django (e.g. `pip install -e ".[dev]"` or the drdroid-debug-toolkit venv with the server installed).

## MCP client configuration (Cursor)

In Cursor, add the Metabase MCP server so you can call tools from the chat.

1. Open Cursor MCP settings:
   - **macOS:** Cursor → Settings → Cursor Settings → Features → MCP (or edit `~/.cursor/mcp.json`).
   - Or in your project: `.cursor/mcp.json` (project-specific).

2. Add a stdio server entry. **Important:** `command` must be an executable Cursor can find (e.g. `uv` or the **full path** to your venv’s Python). Do **not** use `"command": "metabase-mcp-server"` by itself—that binary only exists inside the project’s venv and will cause “No such file or directory”.

**Option A – using uv (if `uv` is on your PATH when Cursor starts):**

```json
{
  "mcpServers": {
    "metabase": {
      "command": "uv",
      "args": ["run", "metabase-mcp-server"],
      "cwd": "/path/to/metabase-mcp-server",
      "env": {
        "METABASE_URL": "https://your-metabase.example.com",
        "METABASE_API_KEY": "your-api-key"
      }
    }
  }
}
```

**Option B – using the venv’s Python (most reliable; replace the path with your repo and venv):**

```json
{
  "mcpServers": {
    "metabase": {
      "command": "/path/to/metabase-mcp-server/venv/bin/python",
      "args": ["-m", "metabase_mcp_server.server"],
      "cwd": "/path/to/metabase-mcp-server"
    }
  }
}
```

On Windows use `venv\\Scripts\\python.exe` and adjust paths.

- Set `cwd` to your **metabase-mcp-server repo root** (the folder that contains `src/`, `pyproject.toml`, and `.env`). The server loads `.env` from the process working directory only—so **do not** set `cwd` to a subfolder.
- Set `METABASE_URL` and `METABASE_API_KEY` in `env`, or rely on `.env` when `cwd` is the repo root.
- Restart Cursor or reload MCP so it picks up the config.

1. In chat, use the tools panel to see Metabase tools (e.g. `metabase_list_databases`, `metabase_list_alerts`). Run a specific operation to test.

**MCP not working?** Ensure `cwd` is the repo root (e.g. `/Users/you/projects/metabase-mcp-server`). Run `uv run metabase-mcp-server` from that directory in a terminal to confirm the server starts and that `.env` is in that directory.

### Claude Desktop

1. Open the Claude Desktop config file:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - Or in Claude Desktop: **Settings → Developer → Edit Config**.

2. Add the Metabase MCP server to `mcpServers` (replace `cwd` with your repo path; you can omit `env` if you rely on `.env` in the repo):

```json
{
  "mcpServers": {
    "metabase": {
      "command": "uv",
      "args": ["run", "metabase-mcp-server"],
      "cwd": "/Users/jayeshsadhwani/projects/metabase-mcp-server",
      "env": {
        "METABASE_URL": "https://your-metabase.example.com",
        "METABASE_API_KEY": "your-api-key"
      }
    }
  }
}
```

If you already have a `.env` in the repo root, you can leave `env` out and the server will load it when started with that `cwd`.

1. Save the file and **fully quit and reopen Claude Desktop** (restart so it reloads MCP).

2. In a new chat, click the **🔨 (tools)** icon to see available tools (e.g. `metabase_list_databases`, `metabase_list_alerts`). Run one to test.

### HTTP (remote server)

If the server is already running (e.g. with `MCP_TRANSPORT=streamable-http`):

```json
{
  "mcpServers": {
    "metabase": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## Creating MCP servers for other tools

This repo is an **example** of a tool-specific MCP server created from the [mcp-server-template](https://github.com/your-org/mcp-server-template). To create one for another tool (e.g. SigNoz, Grafana):

1. **Copy the template** (or this repo) into a new directory, e.g. `signoz-mcp-server`.
2. **Rename the package**: replace `metabase_mcp_server` with e.g. `signoz_mcp_server` in `src/`, `pyproject.toml`, and all imports.
3. **Point to the right SourceManager**: in the new repo, use the toolkit’s `SignozSourceManager` (or the right manager), build a connector from env (URL, API key, etc.), and implement a `ToolProvider` that:
   - Uses `extract_tools_from_source_manager(manager, prefix="signoz")` for `list_tools()`.
   - Implements `call_tool(name, arguments)` by building a `PlaybookTask` and calling `manager.execute_task(...)` (or by calling the manager’s executors directly with a connector built from config).
4. **Config and README**: add env vars and a README for that tool (required vars, how to run, example MCP config).

The template’s README describes the same flow and the abstract `ToolProvider` interface; this Metabase server is a concrete implementation you can mirror for other sources.

## Layout

```txt
metabase-mcp-server/
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
├── src/
│   └── metabase_mcp_server/
│       ├── __init__.py
│       ├── config.py
│       ├── connector.py
│       ├── drd_extractor.py
│       ├── manager.py
│       ├── metabase_provider.py
│       ├── server.py
│       └── tool_provider.py
└── tests/
    ├── conftest.py
    └── test_server.py
```

## License

Same as the template / your organization.

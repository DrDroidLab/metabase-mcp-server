# Metabase MCP Server

MCP server that exposes **Metabase** operations (alerts, pulses, dashboards, questions, databases, collections, search) as tools. Built from the [mcp-server-template](https://github.com/your-org/mcp-server-template) and backed by `MetabaseSourceManager` from [drdroid-debug-toolkit](https://github.com/your-org/drdroid-debug-toolkit).

## Tools

The server exposes three MCP tools:

- **ping** – Health check.
- **list_tools** – Returns all Metabase operations with name, description, and parameter schema (e.g. `metabase_list_alerts`, `metabase_get_alert`, `metabase_list_dashboards`, `metabase_execute_question`, …).
- **execute_tool** – Runs a Metabase operation by name with a dict of arguments (use `list_tools` to discover names and parameters).

## Requirements

- Python 3.11+
- Access to a Metabase instance (URL + API key)
- [drdroid-debug-toolkit](https://github.com/your-org/drdroid-debug-toolkit) installed and importable with `core` on `PYTHONPATH` (see below)

## Setup

### 1. Clone and install

```bash
git clone https://github.com/your-org/metabase-mcp-server.git
cd metabase-mcp-server
uv venv .venv && source .venv/bin/activate   # or: python -m venv .venv && source .venv/bin/activate
uv sync   # or: pip install -e .
```

### 2. Install the drdroid-debug-toolkit

The server uses the toolkit’s `MetabaseSourceManager` and protos. The toolkit expects a top-level `core` package on `PYTHONPATH`.

**Option A – Toolkit as sibling (e.g. same `projects/` folder):**

```bash
# From repo root
cd /path/to/projects
# If drdroid-debug-toolkit is at projects/drdroid-debug-toolkit:
export PYTHONPATH="/path/to/projects/drdroid-debug-toolkit/drdroid_debug_toolkit:$PYTHONPATH"
cd metabase-mcp-server
uv sync
```

The server also tries to add a sibling `drdroid-debug-toolkit/drdroid_debug_toolkit` to `sys.path` automatically when that path exists.

**Option B – Install toolkit in editable mode and set PYTHONPATH:**

```bash
pip install -e /path/to/drdroid-debug-toolkit
export PYTHONPATH="/path/to/drdroid-debug-toolkit/drdroid_debug_toolkit:$PYTHONPATH"
```

### 3. Configure Metabase

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

## MCP client configuration

### Cursor (stdio)

In Cursor MCP settings (e.g. `~/.cursor/mcp.json` or project MCP config):

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

Or use your `.env` by running from the repo directory and not overriding `env`.

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

```
metabase-mcp-server/
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
└── src/
    └── metabase_mcp_server/
        ├── __init__.py
        ├── config.py
        ├── connector.py
        ├── drd_extractor.py
        ├── manager.py
        ├── server.py
        ├── tool_definitions.py
        └── tool_provider.py
```

## License

Same as the template / your organization.

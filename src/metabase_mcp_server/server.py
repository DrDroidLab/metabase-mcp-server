from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# Load .env from current working directory (e.g. repo root) so config sees METABASE_* and MCP_*.
try:
    from dotenv import load_dotenv
    load_dotenv(Path.cwd() / ".env")
except ImportError:
    pass

from .config import load_config
from .metabase_provider import MetabaseToolProvider
from .tool_provider import ToolDefinition, ToolProvider

# Create the FastMCP server instance.
app_config = load_config()
mcp = FastMCP(app_config.server.name, json_response=True)

# Optional: set this to expose dynamic tools from a backend (e.g. drd SourceManager).
_provider: Optional[ToolProvider] = None

if app_config.backend.metabase and app_config.backend.metabase.url and app_config.backend.metabase.api_key:
    _provider = MetabaseToolProvider(app_config.backend.metabase.url, app_config.backend.metabase.api_key)


def set_tool_provider(provider: ToolProvider) -> None:
    """Set the tool provider used by list_tools and execute_tool. Call this from your server setup."""
    global _provider
    _provider = provider


@mcp.tool()
def ping() -> str:
    """Simple health check tool for the MCP server template."""
    return "pong"


@mcp.tool()
def echo(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Echo back a JSON payload.

    This is mainly useful as a sanity check when wiring up new MCP
    clients or testing transports.
    """
    return {"received": payload}


@mcp.tool()
def list_tools() -> List[Dict[str, Any]]:
    """
    List all tools provided by the backend (e.g. from a drd SourceManager).

    Returns a list of tool definitions with name, description, and inputSchema.
    Only populated when a tool provider has been set via set_tool_provider().
    """
    if _provider is None:
        return [
            {
                "message": "No tool provider configured. Set a ToolProvider in server.py with set_tool_provider(provider) to expose backend tools.",
                "tools": [],
            }
        ]
    tools = _provider.list_tools()
    return [
        {
            "name": t.name,
            "description": t.description,
            "inputSchema": t.parameters_schema,
        }
        for t in tools
    ]


@mcp.tool()
def execute_tool(name: str, arguments: Dict[str, Any]) -> Any:
    """
    Execute a backend tool by name with the given arguments.

    Use list_tools() to discover available tool names and their parameter schemas.
    Only works when a tool provider has been set via set_tool_provider().
    """
    if _provider is None:
        return {
            "error": "No tool provider configured. Set a ToolProvider in server.py with set_tool_provider(provider).",
        }
    try:
        return _provider.call_tool(name, arguments)
    except Exception as e:
        return {"error": str(e)}


def main() -> None:
    """
    Entry point for running the MCP server.

    Transport is controlled via MCP_TRANSPORT:
    - "stdio" (default)
    - "streamable-http"
    - "http"
    """

    transport = app_config.server.transport
    if transport not in {"stdio", "streamable-http", "http"}:
        # Fall back to stdio if an unknown value is provided.
        transport = "stdio"

    mcp.run(transport=transport)


if __name__ == "__main__":
    main()

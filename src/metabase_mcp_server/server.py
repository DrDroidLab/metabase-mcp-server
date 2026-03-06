from __future__ import annotations

import importlib.util
import logging
import sys
from inspect import Parameter, Signature
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

from pydantic import Field

# drdroid-debug-toolkit uses "from core.xxx"; ensure its package root is on path before any toolkit import.
if "core" not in sys.modules:
    _server_root = Path(__file__).resolve().parent.parent.parent
    _toolkit_root = None
    spec = importlib.util.find_spec("drdroid_debug_toolkit")
    if spec is not None and getattr(spec, "origin", None) and "drdroid_debug_toolkit" in (spec.origin or ""):
        _toolkit_root = Path(spec.origin).resolve().parent
    if _toolkit_root and _toolkit_root.is_dir() and str(_toolkit_root) not in sys.path:
        sys.path.insert(0, str(_toolkit_root))
    else:
        _drd = _server_root.parent / "drdroid-debug-toolkit" / "drdroid_debug_toolkit"
        if _drd.is_dir() and str(_drd) not in sys.path:
            sys.path.insert(0, str(_drd))

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

logger = logging.getLogger(__name__)

# Create the FastMCP server instance.
app_config = load_config()
mcp = FastMCP(app_config.server.name, json_response=True)

# Optional: set this to expose dynamic tools from a backend (e.g. drd SourceManager).
_provider: Optional[ToolProvider] = None

if app_config.backend.metabase and app_config.backend.metabase.url and app_config.backend.metabase.api_key:
    _provider = MetabaseToolProvider(app_config.backend.metabase.url, app_config.backend.metabase.api_key)
    logger.info("Metabase tool provider configured; tools will be registered.")
else:
    logger.warning(
        "Metabase not configured (METABASE_URL and METABASE_API_KEY required). No tools will be exposed."
    )

# Map JSON Schema types to Python types for FastMCP parameter introspection.
_JSON_TYPE_TO_PY: Dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _make_tool_fn(tool_name: str) -> Any:
    """Return a callable that executes the given provider tool by name."""
    def _call(**kwargs: Any) -> Any:
        if _provider is None:
            logger.warning("Tool %s called but no provider configured.", tool_name)
            return {"error": "No tool provider configured."}
        try:
            return _provider.call_tool(tool_name, kwargs)
        except Exception as e:
            logger.exception("Tool %s failed: %s", tool_name, e)
            return {"error": str(e)}
    return _call


def _register_provider_tools() -> None:
    """Register each provider tool as its own MCP tool with name, description, and parameters from the schema."""
    if _provider is None:
        return
    for t in _provider.list_tools():
        schema = t.parameters_schema or {}
        properties = schema.get("properties") or {}
        required = set(schema.get("required") or [])
        params: List[Parameter] = []
        annotations: Dict[str, Any] = {}
        for key in properties:
            prop = properties[key]
            if not isinstance(prop, dict):
                continue
            js_type = prop.get("type", "string")
            py_type = _JSON_TYPE_TO_PY.get(js_type, Any)
            desc = prop.get("description") or prop.get("title") or key
            title = prop.get("title") or key
            field_kwargs: Dict[str, Any] = {"description": desc}
            if title and title != key:
                field_kwargs["title"] = title
            annotations[key] = Annotated[py_type, Field(**field_kwargs)]
            default = Parameter.empty if key in required else None
            params.append(Parameter(key, Parameter.KEYWORD_ONLY, default=default, annotation=annotations[key]))
        fn = _make_tool_fn(t.name)
        fn.__name__ = t.name.replace("-", "_")
        fn.__doc__ = t.description
        fn.__annotations__ = annotations
        fn.__signature__ = Signature(params)
        mcp.add_tool(fn, name=t.name, description=t.description)


def set_tool_provider(provider: ToolProvider) -> None:
    """Set the tool provider (e.g. for testing). Normally the provider is set at startup from config."""
    global _provider
    _provider = provider


# Register each backend tool (e.g. metabase_list_databases, metabase_get_alert) as its own MCP tool.
_register_provider_tools()
if _provider:
    logger.info("Registered %d MCP tool(s).", len(_provider.list_tools()))


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

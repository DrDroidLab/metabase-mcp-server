import pytest

from metabase_mcp_server import config


def test_load_config_defaults():
    app_config = config.load_config()

    assert app_config.server.name == "Metabase MCP Server"
    assert app_config.server.transport in {"stdio", "streamable-http", "http"}
    assert app_config.server.port == 8000
    assert app_config.backend.metabase is not None


def _metabase_creds():
    """Return (url, api_key) from config; (None, None) if not set."""
    app_config = config.load_config()
    mb = app_config.backend.metabase
    if not mb or not (mb.url and mb.api_key):
        return None, None
    return mb.url.strip().rstrip("/"), mb.api_key


def test_metabase_connection_works():
    """Verify Metabase credentials by calling the manager's connection test."""
    url, api_key = _metabase_creds()
    if not url or not api_key:
        pytest.skip(
            "METABASE_URL and METABASE_API_KEY must be set. Copy .env.example to .env in the repo root and set both."
        )
    try:
        from metabase_mcp_server.connector import build_metabase_connector
        from metabase_mcp_server.manager import MetabaseMCPManager
    except ImportError as e:
        pytest.skip(f"drdroid-debug-toolkit not available: {e}")
    connector = build_metabase_connector(url, api_key)
    manager = MetabaseMCPManager(url, api_key)
    success, message = manager.test_connector_processor(connector)
    assert success, message


def test_metabase_list_databases():
    """Verify we can call a real Metabase tool (list databases) with current creds."""
    url, api_key = _metabase_creds()
    if not url or not api_key:
        pytest.skip(
            "METABASE_URL and METABASE_API_KEY must be set. Copy .env.example to .env in the repo root and set both."
        )
    try:
        from metabase_mcp_server.metabase_provider import MetabaseToolProvider
    except ImportError as e:
        pytest.skip(f"drdroid-debug-toolkit not available: {e}")
    provider = MetabaseToolProvider(url, api_key)
    result = provider.call_tool("metabase_list_databases", {})
    assert not result.get("error"), result
    assert isinstance(result, dict), result

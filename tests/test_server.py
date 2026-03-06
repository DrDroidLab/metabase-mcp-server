import pytest

from metabase_mcp_server import config


def test_load_config_defaults():
    app_config = config.load_config()

    assert app_config.server.name == "Metabase MCP Server"
    assert app_config.server.transport in {"stdio", "streamable-http", "http"}
    assert app_config.server.port == 8000
    assert app_config.backend.metabase is not None

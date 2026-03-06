"""
MetabaseSourceManager wrapper that uses env-based credentials.

The base execute_task() calls get_active_connectors(connector_name, connector_id)
without passing loaded_connections. We override to return our connector when
name/id match the MCP connector.
"""
from __future__ import annotations

from core.integrations.source_managers.metabase_source_manager import MetabaseSourceManager
from core.protos.connectors.connector_pb2 import Connector as ConnectorProto

from .connector import MCP_CONNECTOR_ID, MCP_CONNECTOR_NAME, build_metabase_connector


class MetabaseMCPManager(MetabaseSourceManager):
    """Metabase source manager that uses a single env-based connector for MCP."""

    def __init__(self, metabase_url: str, metabase_api_key: str) -> None:
        super().__init__()
        self._metabase_url = metabase_url.rstrip("/")
        self._metabase_api_key = metabase_api_key

    def get_active_connectors(
        self,
        connector_name: str,
        connector_id: int,
        loaded_connections: dict | None = None,
    ) -> ConnectorProto:
        if loaded_connections is None and connector_name == MCP_CONNECTOR_NAME and connector_id == MCP_CONNECTOR_ID:
            return build_metabase_connector(self._metabase_url, self._metabase_api_key)
        return super().get_active_connectors(connector_name, connector_id, loaded_connections)

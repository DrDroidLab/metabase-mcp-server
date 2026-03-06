"""Metabase MCP tools: thin wrapper around the generic drd source provider."""
from __future__ import annotations

from core.protos.base_pb2 import Source

from .connector import MCP_CONNECTOR_ID, MCP_CONNECTOR_NAME
from .drd_source_provider import DrdSourceToolProvider
from .manager import MetabaseMCPManager


class MetabaseToolProvider(DrdSourceToolProvider):
    """Exposes MetabaseSourceManager tasks as MCP tools (metabase_list_databases, etc.)."""

    def __init__(self, metabase_url: str, metabase_api_key: str) -> None:
        manager = MetabaseMCPManager(metabase_url, metabase_api_key)
        super().__init__(
            manager,
            Source.METABASE,
            connector_name=MCP_CONNECTOR_NAME,
            connector_id=MCP_CONNECTOR_ID,
            prefix="metabase",
        )

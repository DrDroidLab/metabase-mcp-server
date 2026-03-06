"""
Build a ConnectorProto for Metabase from URL and API key.

The drd toolkit expects connectors to come from get_active_connectors();
we build one from env so the source manager can run without a DB.
"""
from __future__ import annotations

import os
import sys

# Ensure toolkit "core" is importable (toolkit uses "from core.xxx" internally).
def _ensure_toolkit_path() -> None:
    if "core" in sys.modules:
        return
    try:
        import core.protos.base_pb2  # noqa: F401
        return
    except ImportError:
        pass
    # The directory that contains "core" must be on path: .../drdroid_debug_toolkit
    _this_dir = os.path.dirname(os.path.abspath(__file__))
    _pkg = os.path.dirname(_this_dir)
    _projects = os.path.dirname(_pkg)
    _drd_pkg = os.path.join(_projects, "drdroid-debug-toolkit", "drdroid_debug_toolkit")
    if os.path.isdir(_drd_pkg):
        if _drd_pkg not in sys.path:
            sys.path.insert(0, _drd_pkg)


_ensure_toolkit_path()

from google.protobuf.wrappers_pb2 import StringValue, UInt64Value

from core.protos.base_pb2 import Source, SourceKeyType
from core.protos.connectors.connector_pb2 import Connector as ConnectorProto, ConnectorKey


MCP_CONNECTOR_NAME = "mcp"
MCP_CONNECTOR_ID = 0


def build_metabase_connector(metabase_url: str, metabase_api_key: str) -> ConnectorProto:
    """Build a ConnectorProto for Metabase from URL and API key."""
    return ConnectorProto(
        type=Source.METABASE,
        name=StringValue(value=MCP_CONNECTOR_NAME),
        id=UInt64Value(value=MCP_CONNECTOR_ID),
        keys=[
            ConnectorKey(
                key_type=SourceKeyType.METABASE_URL,
                key=StringValue(value=metabase_url.rstrip("/")),
            ),
            ConnectorKey(
                key_type=SourceKeyType.METABASE_API_KEY,
                key=StringValue(value=metabase_api_key),
            ),
        ],
    )

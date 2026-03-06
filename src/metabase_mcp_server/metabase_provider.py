"""ToolProvider implementation that lists and executes Metabase tools via the drd SourceManager."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from google.protobuf.struct_pb2 import Struct

from core.protos.base_pb2 import Source, TimeRange
from core.protos.playbooks.playbook_pb2 import PlaybookTask
from core.utils.proto_utils import dict_to_proto, proto_to_dict

from .connector import MCP_CONNECTOR_ID, MCP_CONNECTOR_NAME
from .drd_extractor import extract_tools_from_source_manager
from .manager import MetabaseMCPManager
from .tool_provider import ToolDefinition

logger = logging.getLogger(__name__)


class MetabaseToolProvider:
    """Exposes MetabaseSourceManager tasks as MCP tools."""

    def __init__(self, metabase_url: str, metabase_api_key: str) -> None:
        self._manager = MetabaseMCPManager(metabase_url, metabase_api_key)
        self._tools: List[ToolDefinition] = extract_tools_from_source_manager(
            self._manager, prefix="metabase"
        )

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools)

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        tool = next((t for t in self._tools if t.name == name), None)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        task_type_name = tool.metadata.get("task_type")
        task_type_value = tool.metadata.get("task_type_value")
        if task_type_name is None or task_type_value is None:
            raise ValueError(f"Tool {name} missing task_type metadata")
        task_field = task_type_name.lower()
        # Pass arguments as plain scalars; protobuf ParseDict expects scalars for Int64Value/StringValue, not {"value": ...}.
        task_payload = dict(arguments) if arguments else {}
        now_ns = int(__import__("time").time() * 1_000_000_000)
        time_range = TimeRange(time_geq=now_ns - 86400 * 1_000_000_000, time_lt=now_ns)
        task_dict = {
            "source": Source.METABASE,
            "task_connector_sources": [
                {
                    "name": MCP_CONNECTOR_NAME,
                    "id": MCP_CONNECTOR_ID,
                    "source": Source.METABASE,
                }
            ],
            "metabase": {
                "type": task_type_value,
                task_field: task_payload,
            },
        }
        playbook_task = dict_to_proto(task_dict, PlaybookTask)
        global_variable_set = Struct()
        try:
            result = self._manager.execute_task(time_range, global_variable_set, playbook_task)
        except Exception as e:
            logger.exception("execute_task failed for %s", name)
            return {"error": str(e)}
        return _result_to_json(result)


def _result_to_json(result: Any) -> Any:
    """Convert PlaybookTaskResult (or list) to JSON-serializable dict."""
    if result is None:
        return {"result": None}
    if isinstance(result, list):
        return {"results": [_result_to_json(r) for r in result]}
    if hasattr(result, "api_response") and result.api_response and result.api_response.response_body:
        return proto_to_dict(result.api_response.response_body)
    if hasattr(result, "text") and result.text and result.text.output:
        return {"text": result.text.output.value}
    if hasattr(result, "error") and result.error:
        return {"error": result.error.value}
    return proto_to_dict(result) if hasattr(result, "DESCRIPTOR") else {"result": str(result)}

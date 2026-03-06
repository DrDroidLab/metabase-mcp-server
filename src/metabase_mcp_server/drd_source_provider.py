"""
Generic ToolProvider for any drd SourceManager.

Use this to expose a drd source (Metabase, Signoz, etc.) as MCP tools with
minimal code: pass a manager instance, source enum, connector name/id, and
optional tool name prefix. No need to duplicate task-building or execution logic.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from google.protobuf.struct_pb2 import Struct

from core.protos.base_pb2 import Source, TimeRange
from core.protos.playbooks.playbook_pb2 import PlaybookTask
from core.utils.proto_utils import dict_to_proto, proto_to_dict

from .drd_extractor import extract_tools_from_source_manager
from .tool_provider import ToolDefinition

logger = logging.getLogger(__name__)


def _normalize_struct_args(value: Any) -> Any:
    """
    Recursively normalize argument values for protobuf ParseDict.
    String values that are JSON objects or arrays are parsed to dict/list
    so that google.protobuf.Struct fields receive a dict, not a string.
    """
    if isinstance(value, str) and value.strip():
        strip = value.strip()
        if (strip.startswith("{") and strip.endswith("}")) or (
            strip.startswith("[") and strip.endswith("]")
        ):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass
    if isinstance(value, dict):
        return {k: _normalize_struct_args(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_struct_args(v) for v in value]
    return value


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


class DrdSourceToolProvider:
    """
    Generic provider that exposes any drd SourceManager as MCP tools.

    Pass a manager (subclass of the drd SourceManager that overrides
    get_active_connectors to return your connector), the source enum,
    connector name/id, and an optional prefix for tool names (e.g. "metabase").
    """

    def __init__(
        self,
        manager: Any,
        source_enum: int,
        connector_name: str = "mcp",
        connector_id: int = 0,
        prefix: Optional[str] = None,
    ) -> None:
        self._manager = manager
        self._source_enum = source_enum
        self._connector_name = connector_name
        self._connector_id = connector_id
        self._prefix = prefix or Source.Name(source_enum).lower()
        self._tools: List[ToolDefinition] = extract_tools_from_source_manager(
            manager, prefix=self._prefix
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
        task_payload = _normalize_struct_args(dict(arguments)) if arguments else {}
        now_ns = int(__import__("time").time() * 1_000_000_000)
        time_range = TimeRange(time_geq=now_ns - 86400 * 1_000_000_000, time_lt=now_ns)
        source_key = Source.Name(self._source_enum).lower()
        task_dict = {
            "source": self._source_enum,
            "task_connector_sources": [
                {
                    "name": self._connector_name,
                    "id": self._connector_id,
                    "source": self._source_enum,
                }
            ],
            source_key: {
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

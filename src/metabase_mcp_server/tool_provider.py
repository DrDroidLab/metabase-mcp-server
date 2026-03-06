from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class ToolDefinition:
    """
    Description of a single MCP tool.

    This is intentionally backend-agnostic. Concrete integrations
    (e.g., drdroid-debug-toolkit, direct Metabase API, etc.) can
    populate these fields however they like.
    """

    name: str
    description: str
    parameters_schema: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolProvider(Protocol):
    """
    Simple interface for backends that expose tools to the MCP layer.

    The MCP server only needs two operations:
    - List: what tools exist, with parameter schemas.
    - Call: execute one tool with a dict of arguments.
    """

    def list_tools(self) -> List[ToolDefinition]:
        ...

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        ...


class InMemoryToolProvider:
    """
    A trivial ToolProvider implementation that dispatches to a mapping
    of callables. This is mostly useful for tests and very small
    integrations.
    """

    def __init__(
        self,
        tools: List[ToolDefinition],
        callables: Dict[str, Any],
    ) -> None:
        self._tools = tools
        self._callables = callables

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools)

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        fn = self._callables.get(name)
        if fn is None:
            raise ValueError(f"Unknown tool: {name}")
        return fn(**arguments)

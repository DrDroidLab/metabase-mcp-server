"""
Hooks for integrating with drdroid-debug-toolkit source managers.

The goal of this module is to provide a *generic extractor* that can
look at a SourceManager (for example, MetabaseSourceManager) and
convert its task metadata plus form fields into ToolDefinition
instances that the MCP layer can expose.

This keeps the MCP plumbing generic, while all the integration-specific
logic (what tasks exist, what parameters they take) continues to live
inside the source managers in the drd toolkit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    from core.protos.ui_definition_pb2 import FormField
    from core.protos.literal_pb2 import LiteralType
except ImportError:
    FormField = None  # type: ignore[assignment]
    LiteralType = None  # type: ignore[assignment]

from .tool_provider import ToolDefinition


@dataclass
class ExtractedParameter:
    name: str
    description: str
    json_schema: Dict[str, Any]
    required: bool


def _form_field_to_schema(field: "FormField") -> ExtractedParameter:
    """
    Convert a drd FormField into a JSON Schema property description.

    The mapping is intentionally simple and can be refined later.
    """

    # Fallbacks if the optional drd imports are not available.
    if FormField is None or LiteralType is None:
        return ExtractedParameter(
            name="unknown",
            description="FormField (drd toolkit not installed)",
            json_schema={"type": "string"},
            required=False,
        )

    key_name = field.key_name.value or ""
    description = field.description.value or ""

    # Map LiteralType to JSON Schema type.
    literal_type = field.data_type
    if literal_type == LiteralType.LONG:
        json_type = "integer"
    elif literal_type == LiteralType.DOUBLE:
        json_type = "number"
    elif literal_type == LiteralType.BOOLEAN:
        json_type = "boolean"
    elif literal_type == LiteralType.STRING_ARRAY:
        json_type = "array"
    else:
        json_type = "string"

    schema: Dict[str, Any] = {"type": json_type}
    if description:
        schema["description"] = description

    return ExtractedParameter(
        name=key_name,
        description=description,
        json_schema=schema,
        required=not getattr(field, "is_optional", False),
    )


def extract_tools_from_source_manager(source_manager: Any, prefix: Optional[str] = None) -> List[ToolDefinition]:
    """
    Inspect a drd SourceManager and produce ToolDefinition instances.

    Expected SourceManager shape (based on existing managers like
    MetabaseSourceManager):
    - .task_proto: a protobuf message class with an inner TaskType enum.
    - .task_type_callable_map: dict[int, dict] where each value may
        contain:
        - 'display_name': str
        - 'category': str
        - 'form_fields': list[FormField]

    This function does **not** execute tools; it only extracts their
    metadata and parameters for MCP exposure.
    """

    tools: List[ToolDefinition] = []

    task_proto = getattr(source_manager, "task_proto", None)
    task_map = getattr(source_manager, "task_type_callable_map", None)

    if task_proto is None or task_map is None:
        return tools

    # The TaskType enum is used to convert the numeric key into a stable name.
    task_type_enum = getattr(task_proto, "TaskType", None)
    if task_type_enum is None:
        return tools

    for task_type_value, info in task_map.items():
        try:
            task_type_name = task_type_enum.Name(task_type_value)
        except Exception:
            # Fallback to raw numeric name if enum lookup fails.
            task_type_name = f"TASK_{task_type_value}"

        display_name = info.get("display_name", task_type_name)
        category = info.get("category", "Tasks")
        form_fields = info.get("form_fields", []) or []

        # Build JSON Schema from form fields.
        properties: Dict[str, Any] = {}
        required: List[str] = []

        for ff in form_fields:
            if FormField is not None and not isinstance(ff, FormField):
                continue
            param = _form_field_to_schema(ff)
            if not param.name:
                continue
            properties[param.name] = param.json_schema
            if param.required:
                required.append(param.name)

        parameters_schema: Dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            parameters_schema["required"] = required

        # Tool name convention: optional prefix + task type name in lower snake case.
        base_name = task_type_name.lower()
        tool_name = f"{prefix}_{base_name}" if prefix else base_name

        description = f"{display_name} (category: {category})"

        tools.append(
            ToolDefinition(
                name=tool_name,
                description=description,
                parameters_schema=parameters_schema,
                metadata={
                    "task_type": task_type_name,
                    "task_type_value": task_type_value,
                    "category": category,
                },
            )
        )

    return tools

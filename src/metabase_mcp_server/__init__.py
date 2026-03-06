"""
Core package for the MCP server template.

This package is intentionally minimal. It provides:
- A FastMCP server entrypoint (`server.py`).
- Simple config helpers (`config.py`).
- Abstractions for describing and executing tools (`tool_provider.py`).
- Optional hooks for drdroid-debug-toolkit integration (`drd_extractor.py`).
"""

__version__ = "0.1.0"

__all__ = [
    "config",
    "tool_provider",
]

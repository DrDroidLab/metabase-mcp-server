import os
from dataclasses import dataclass
from typing import Literal, Optional


TransportType = Literal["stdio", "streamable-http", "http"]


@dataclass
class MetabaseConfig:
    url: str = ""
    api_key: str = ""
    verify_ssl: bool = True


@dataclass
class ServerConfig:
    """Configuration for the MCP server itself."""

    name: str = "Metabase MCP Server"
    transport: TransportType = "stdio"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


@dataclass
class BackendConfig:
    """
    Generic backend configuration.

    For drdroid-debug-toolkit usage, this is a good place to store
    things like:
    - Which SourceManager to load (module + class).
    - Any fixed connector or account identifiers.
    """

    # Example placeholders – concrete repos typically override these.
    drd_source_manager_module: Optional[str] = None
    drd_source_manager_class: Optional[str] = None
    metabase: Optional[MetabaseConfig] = None


@dataclass
class AppConfig:
    server: ServerConfig
    backend: BackendConfig


def _get_bool(env_name: str, default: bool) -> bool:
    raw = os.getenv(env_name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> AppConfig:
    """
    Build an AppConfig from environment variables.

    This keeps the template flexible and easy to copy into new repos:
    individual MCP servers can extend this function with more
    integration-specific settings as needed.
    """

    server = ServerConfig(
        name=os.getenv("MCP_SERVER_NAME", "Metabase MCP Server"),
        transport=os.getenv("MCP_TRANSPORT", "stdio"),  # type: ignore[assignment]
        host=os.getenv("MCP_HOST", "0.0.0.0"),
        port=int(os.getenv("MCP_PORT", "8000")),
        debug=_get_bool("MCP_DEBUG", False),
    )

    metabase = MetabaseConfig(
        url=os.getenv("METABASE_URL", "").rstrip("/"),
        api_key=os.getenv("METABASE_API_KEY", ""),
        verify_ssl=_get_bool("METABASE_VERIFY_SSL", True),
    )

    backend = BackendConfig(
        drd_source_manager_module=os.getenv("DRD_SOURCE_MANAGER_MODULE"),
        drd_source_manager_class=os.getenv("DRD_SOURCE_MANAGER_CLASS"),
        metabase=metabase,
    )

    return AppConfig(server=server, backend=backend)

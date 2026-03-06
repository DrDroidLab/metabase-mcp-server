"""Pytest config: add src to path so metabase_mcp_server is importable without pip install -e ."""
import importlib.util
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
_src = _root / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

# drdroid-debug-toolkit uses "from core.xxx"; need its package root on path. Prefer installed package (has Django etc).
if "core" not in sys.modules:
    _toolkit_root = None
    spec = importlib.util.find_spec("drdroid_debug_toolkit")
    if spec is not None and getattr(spec, "origin", None) and "drdroid_debug_toolkit" in (spec.origin or ""):
        _toolkit_root = Path(spec.origin).resolve().parent
    if _toolkit_root and _toolkit_root.is_dir() and str(_toolkit_root) not in sys.path:
        sys.path.insert(0, str(_toolkit_root))
    else:
        _drd = _root.parent / "drdroid-debug-toolkit" / "drdroid_debug_toolkit"
        if _drd.is_dir() and str(_drd) not in sys.path:
            sys.path.insert(0, str(_drd))

# Load .env so credential tests see METABASE_URL / METABASE_API_KEY
try:
    from dotenv import load_dotenv
    load_dotenv(_root / ".env")
except ImportError:
    pass

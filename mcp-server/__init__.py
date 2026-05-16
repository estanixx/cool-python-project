def __getattr__(name: str):
    """Lazy import to avoid ModuleNotFoundError when mcp package is not installed."""
    if name == "mcp":
        from .mcp_server import mcp

        return mcp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["mcp"]

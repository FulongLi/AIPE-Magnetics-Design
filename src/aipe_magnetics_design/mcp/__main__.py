"""``python -m aipe_magnetics_design.mcp`` starts the stdio MCP server (same as ``python -m aipe_magnetics_design.mcp.server``)."""

from aipe_magnetics_design.mcp.server import main

if __name__ == "__main__":
    raise SystemExit(main())

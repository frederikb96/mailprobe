"""Mailprobe - IMAP email MCP server with hybrid full-text body search."""

from mailprobe.server import mcp


def main() -> None:
    """Run the MCP server."""
    mcp.run()

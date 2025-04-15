"""Entry point for the TestRail MCP server when run as a module."""
import sys
import asyncio

from testrail_mcp.mcp_server import TestRailMCPServer

def main():
    """Run the TestRail MCP server."""
    print("Starting TestRail MCP server in stdio mode", file=sys.stderr)
    server = TestRailMCPServer()
    asyncio.run(server.run_stdio_async())

if __name__ == "__main__":
    main()

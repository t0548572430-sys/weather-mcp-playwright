"""Generic MCP Client: connects to any MCP server script over stdio."""
import sys
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Holds one stdio session to one MCP server."""

    def __init__(self):
        self.session: ClientSession | None = None
        self._stack = AsyncExitStack()

    async def connect_to_server(self, server_script_path: str):
        """Launch the server script as a subprocess and open an MCP session over stdio."""
        params = StdioServerParameters(command=sys.executable, args=[server_script_path])
        read, write = await self._stack.enter_async_context(stdio_client(params))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()

    async def list_tools(self):
        """Discover the tools this server exposes."""
        return (await self.session.list_tools()).tools

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Invoke a tool and return its text output."""
        result = await self.session.call_tool(name, arguments)
        return "\n".join(c.text for c in result.content if c.type == "text")

    async def close(self):
        await self._stack.aclose()

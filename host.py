"""Host: terminal chat that connects Claude to the MCP servers."""
import asyncio
import os
import sys

from anthropic import Anthropic
from dotenv import load_dotenv

from client import MCPClient

load_dotenv()

MODEL = "claude-opus-4-8"

SERVER_SCRIPTS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_USA.py"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_Israel.py"),
]


class Host:
    def __init__(self):
        self.anthropic = Anthropic()
        self.clients: list[MCPClient] = []
        self.tool_to_client: dict[str, MCPClient] = {}
        self.tools: list[dict] = []

    async def connect(self):
        for script in SERVER_SCRIPTS:
            client = MCPClient()
            await client.connect_to_server(script)
            self.clients.append(client)
            for tool in await client.list_tools():
                self.tool_to_client[tool.name] = client
                self.tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                })
        print(f"Connected. Available tools: {', '.join(self.tool_to_client)}\n")

    async def process_query(self, messages: list) -> None:
        """Agentic loop: call Claude, execute requested tools, repeat until done."""
        while True:
            response = self.anthropic.messages.create(
                model=MODEL,
                max_tokens=4096,
                tools=self.tools,
                messages=messages,
            )
            messages.append({"role": "assistant", "content": response.content})

            for block in response.content:
                if block.type == "text":
                    print(block.text)

            if response.stop_reason != "tool_use":
                return

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [tool: {block.name} {block.input}]")
                    result = await self.tool_to_client[block.name].call_tool(
                        block.name, block.input
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})

    async def chat(self):
        print("Weather chat — ask about the forecast in the US or Israel. 'quit' to exit.\n")
        messages = []
        while True:
            try:
                query = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not query or query.lower() in ("quit", "exit"):
                break
            messages.append({"role": "user", "content": query})
            await self.process_query(messages)
            print()

    async def close(self):
        for client in self.clients:
            await client.close()


async def main():
    host = Host()
    try:
        await host.connect()
        await host.chat()
    finally:
        await host.close()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())

"""Host: terminal chat that connects Google Gemini to the MCP servers."""
import asyncio
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

from client import MCPClient

load_dotenv()

MODEL = "gemini-2.5-flash"

SERVER_SCRIPTS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_USA.py"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_Israel.py"),
]

# Gemini accepts only a subset of JSON Schema in function declarations
SCHEMA_KEYS = {"type", "description", "properties", "required", "items", "enum"}


def clean_schema(schema: dict) -> dict:
    out = {k: v for k, v in schema.items() if k in SCHEMA_KEYS}
    if "properties" in out:
        out["properties"] = {k: clean_schema(v) for k, v in out["properties"].items()}
    if "items" in out:
        out["items"] = clean_schema(out["items"])
    return out


class Host:
    def __init__(self):
        self.llm = genai.Client()  # reads GEMINI_API_KEY from env
        self.clients: list[MCPClient] = []
        self.tool_to_client: dict[str, MCPClient] = {}
        self.declarations: list[dict] = []

    async def connect(self):
        for script in SERVER_SCRIPTS:
            client = MCPClient()
            await client.connect_to_server(script)
            self.clients.append(client)
            for tool in await client.list_tools():
                self.tool_to_client[tool.name] = client
                self.declarations.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": clean_schema(tool.inputSchema),
                })
        print(f"Connected. Available tools: {', '.join(self.tool_to_client)}\n")

    async def process_query(self, contents: list) -> None:
        """Agentic loop: call Gemini, execute requested tools, repeat until done."""
        config = types.GenerateContentConfig(
            tools=[types.Tool(function_declarations=self.declarations)],
        )
        while True:
            response = self.llm.models.generate_content(
                model=MODEL, contents=contents, config=config
            )
            contents.append(response.candidates[0].content)

            if response.text:
                print(response.text)
            if not response.function_calls:
                return

            result_parts = []
            for fc in response.function_calls:
                print(f"  [tool: {fc.name} {dict(fc.args)}]")
                result = await self.tool_to_client[fc.name].call_tool(fc.name, dict(fc.args))
                result_parts.append(
                    types.Part.from_function_response(name=fc.name, response={"result": result})
                )
            contents.append(types.Content(role="user", parts=result_parts))

    async def chat(self):
        print("Weather chat — ask about the forecast in the US or Israel. 'quit' to exit.\n")
        contents = []
        while True:
            try:
                query = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not query or query.lower() in ("quit", "exit"):
                break
            contents.append(types.Content(role="user", parts=[types.Part(text=query)]))
            try:
                await self.process_query(contents)
            except APIError as e:
                print(f"API error: {e.message}")
                contents.pop()  # drop the failed turn so the conversation stays valid
            print()

    async def close(self):
        for client in self.clients:
            try:
                await client.close()
            except (Exception, asyncio.CancelledError):
                pass  # ponytail: mcp stdio teardown is noisy on Windows; we're exiting anyway


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

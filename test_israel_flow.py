"""Smoke test: exercises the Israel weather MCP tools end-to-end via a real MCP session.
Run: uv run test_israel_flow.py
"""
import asyncio
import os
import sys

from client import MCPClient


async def main():
    client = MCPClient()
    await client.connect_to_server(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_Israel.py")
    )
    try:
        tools = await client.list_tools()
        names = [t.name for t in tools]
        print("tools:", names)
        assert "open_weather_forecast_israel" in names

        print(await client.call_tool("open_weather_forecast_israel", {}))
        print(await client.call_tool("enter_weather_forecast_city_israel", {"city": "תל אביב"}))
        print(await client.call_tool("select_weather_forecast_city_israel", {}))
        content = await client.call_tool("get_weather_forecast_content_israel", {})
        print(content[:800])
        assert "תל אביב" in content or "tel-aviv" in content.lower()
        print("\nOK — full flow works")
    finally:
        await client.close()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())

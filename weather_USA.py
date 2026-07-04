"""MCP Server: US weather forecasts and alerts via api.weather.gov."""
import httpx
import truststore
from mcp.server.fastmcp import FastMCP

truststore.inject_into_ssl()  # use the OS certificate store (plays nice with corporate proxies)

mcp = FastMCP("weather-usa")

NWS_API = "https://api.weather.gov"
HEADERS = {"User-Agent": "weather-mcp/0.1", "Accept": "application/geo+json"}


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get the weather forecast for a US location by coordinates.

    Args:
        latitude: Latitude of the location (US only)
        longitude: Longitude of the location (US only)
    """
    async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
        points = (await client.get(f"{NWS_API}/points/{latitude},{longitude}")).json()
        forecast_url = points["properties"]["forecast"]
        forecast = (await client.get(forecast_url)).json()

    periods = forecast["properties"]["periods"][:5]
    return "\n---\n".join(
        f"{p['name']}: {p['temperature']}°{p['temperatureUnit']}, "
        f"wind {p['windSpeed']} {p['windDirection']}. {p['detailedForecast']}"
        for p in periods
    )


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get active weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
        data = (await client.get(f"{NWS_API}/alerts/active/area/{state}")).json()

    features = data.get("features", [])
    if not features:
        return f"No active alerts for {state}."
    return "\n---\n".join(
        f"{f['properties']['event']}: {f['properties'].get('headline', '')}\n"
        f"{f['properties'].get('description', '')[:300]}"
        for f in features[:10]
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")

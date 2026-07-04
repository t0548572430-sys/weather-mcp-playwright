"""MCP Server: Israeli weather forecasts via browser automation (Playwright).

Instead of a weather API, these tools drive a real Chromium browser through
https://www.weather2day.co.il/forecast — open the site, type a city name,
pick it from the autocomplete list, and read the forecast off the page.
"""
import re

from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

mcp = FastMCP("weather-israel")

FORECAST_URL = "https://www.weather2day.co.il/forecast"
SEARCH_INPUT = "#city_search_forecast"
AUTOCOMPLETE_ITEM = "div.autocomplete-items > div"

# ponytail: module-level browser state — one browser per server process is all we need
state: dict = {}


async def _page():
    if "page" not in state:
        raise RuntimeError("Browser is not open. Call open_weather_forecast_israel first.")
    return state["page"]


@mcp.tool()
async def open_weather_forecast_israel() -> str:
    """Open a browser and navigate to the Israeli weather forecast site (weather2day.co.il).
    This must be called first, before entering or selecting a city."""
    if "page" in state:
        await state["page"].goto(FORECAST_URL)
        return "Browser already open — navigated back to the forecast page."

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False)
    page = await browser.new_page()
    await page.goto(FORECAST_URL)
    state.update(pw=pw, browser=browser, page=page)
    return "Browser opened at the weather2day.co.il forecast page."


@mcp.tool()
async def enter_weather_forecast_city_israel(city: str) -> str:
    """Type a city name into the search field on the forecast page.

    Args:
        city: City name in Hebrew (e.g. 'תל אביב', 'ירושלים', 'חיפה')
    """
    page = await _page()
    search = page.locator(SEARCH_INPUT)
    await search.click()
    await search.fill("")
    # type character-by-character so the site's autocomplete fires
    await search.press_sequentially(city, delay=100)
    await page.wait_for_selector(f"{AUTOCOMPLETE_ITEM}:visible", timeout=5000)
    items = await page.locator(f"{AUTOCOMPLETE_ITEM}:visible").all_inner_texts()
    return f"Typed '{city}'. Autocomplete suggestions: {items[:5]}"


@mcp.tool()
async def select_weather_forecast_city_israel() -> str:
    """Select the first city in the autocomplete suggestions list and load its forecast page."""
    page = await _page()
    first = page.locator(f"{AUTOCOMPLETE_ITEM}:visible").first
    selected = await first.inner_text()
    await first.click()
    await page.wait_for_load_state("domcontentloaded")
    return f"Selected '{selected}'. Forecast page loaded: {page.url}"


@mcp.tool()
async def get_weather_forecast_content_israel() -> str:
    """Extract the forecast content from the currently open city forecast page,
    so it can be used to answer the user's weather question directly."""
    page = await _page()
    await page.wait_for_load_state("domcontentloaded")
    text = await page.locator("body").inner_text()
    # ponytail: crude cleanup — collapse whitespace and trim site chrome; good enough for LLM context
    text = re.sub(r"\n{2,}", "\n", re.sub(r"[ \t]+", " ", text)).strip()
    return f"Page: {page.url}\n\n{text[:6000]}"


if __name__ == "__main__":
    mcp.run(transport="stdio")

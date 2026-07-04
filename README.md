# 🌦️ Weather MCP — Israel via Browser Automation, USA via API

An MCP (Model Context Protocol) project demonstrating two ways to extend an LLM's context with live weather data:

- **`weather_USA.py`** — a "classic" MCP server: fetches forecasts and alerts from the US National Weather Service API (api.weather.gov).
- **`weather_Israel.py`** — an MCP server that puts the LLM's hand on the mouse 🖱️: it launches a real Chromium browser with **Playwright**, navigates to [weather2day.co.il](https://www.weather2day.co.il/forecast), types a city name into the search box, picks it from the autocomplete list — and extracts the page content so the LLM can answer the question itself (RAG).

## 🧩 Project Structure

```
├── client.py           # Generic MCP client — connects to any MCP server over stdio
├── host.py             # Terminal chat: connects Gemini to all MCP servers
├── weather_USA.py      # MCP server for US forecasts (API)
├── weather_Israel.py   # MCP server for Israeli forecasts (Playwright)
└── test_israel_flow.py # Smoke test for the full Israeli flow
```

### The Israeli Server's Tools

| Tool | What it does |
|---|---|
| `open_weather_forecast_israel` | Opens a browser and navigates to the forecast page |
| `enter_weather_forecast_city_israel` | Types a city name into the search field (and reports the suggestions) |
| `select_weather_forecast_city_israel` | Selects the first item in the autocomplete list |
| `get_weather_forecast_content_israel` | Extracts the forecast page content and feeds it to the LLM |

## 🚀 Setup & Run

Prerequisites: Python 3.11+, [uv](https://docs.astral.sh/uv/).

```bash
# 1. Install dependencies
uv sync

# 2. Install Chromium for Playwright
uv run playwright install chromium

# 3. Gemini API key (free, no credit card) — https://aistudio.google.com/apikey
copy .env.example .env    # then edit: GEMINI_API_KEY=...

# 4. Run the chat
uv run host.py
```

Quick check of the Israeli server without an LLM:

```bash
uv run test_israel_flow.py
```

## 💬 Example Questions

- `מה התחזית להיום בתל אביב?` (What's today's forecast in Tel Aviv?)
- `כדאי לקחת מטריה מחר בירושלים?` (Should I take an umbrella tomorrow in Jerusalem?)
- `מה מזג האוויר בחיפה בסוף השבוע?` (What's the weather in Haifa this weekend?)
- `What's the forecast in Chicago?` (routed to the US server)
- `Are there weather alerts in California?`

While the question is being processed you'll see the browser open, type the city name, and select it from the list — then the model answers based on the page content.

## ⚙️ How It Works

1. The **Host** (`host.py`) launches each MCP server as a child process and opens a stdio session with it (via the generic **Client** in `client.py`).
2. The Host discovers each server's tools and attaches them to every LLM (Gemini) call.
3. When the model detects a question about weather in Israel, it invokes the four tools one after another: open browser → type city → select from list → extract content.
4. The page content comes back to the model as a tool result, and it composes an answer from it — RAG over a live web page.

## 🔗 Connecting to Other Hosts (e.g. ChatBox)

The MCP servers are host-agnostic. Connect one to any MCP-capable app with a command like:

```
uv --directory C:\path\to\project run weather_Israel.py
```

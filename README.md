# 🌦️ Weather MCP — ישראל בדפדפן, ארה"ב ב-API

פרויקט MCP (Model Context Protocol) שמדגים שתי דרכים להרחיב את הקונטקסט של LLM עם מידע מזג אוויר עדכני:

- **`weather_USA.py`** — MCP Server "קלאסי": שולף תחזית והתראות מ-API של שירות מזג האוויר האמריקאי (api.weather.gov).
- **`weather_Israel.py`** — MCP Server ששם ל-LLM יד על העכבר 🖱️: פותח דפדפן אמיתי עם **Playwright**, גולש ל-[weather2day.co.il](https://www.weather2day.co.il/forecast), מקליד שם עיר בשדה החיפוש, בוחר אותה מהרשימה הנפתחת — ומחלץ את תוכן הדף כדי שה-LLM יענה על השאלה בעצמו (RAG).

## 🧩 מבנה הפרויקט

```
├── client.py          # MCP Client גנרי — מתחבר לכל שרת MCP דרך stdio
├── host.py            # צ'אט טרמינל: מחבר את Gemini לכל שרתי ה-MCP
├── weather_USA.py     # MCP Server לתחזית בארה"ב (API)
├── weather_Israel.py  # MCP Server לתחזית בישראל (Playwright)
└── test_israel_flow.py # בדיקת עשן לזרימה הישראלית המלאה
```

### ה-Tools של השרת הישראלי

| Tool | מה הוא עושה |
|---|---|
| `open_weather_forecast_israel` | פותח דפדפן ומנווט לדף התחזית |
| `enter_weather_forecast_city_israel` | מקליד שם עיר בשדה החיפוש (ומדווח על ההשלמות) |
| `select_weather_forecast_city_israel` | בוחר את הפריט הראשון ברשימת הערים |
| `get_weather_forecast_content_israel` | מחלץ את תוכן דף התחזית ומזרים אותו ל-LLM |

## 🚀 התקנה והרצה

דרישות מקדימות: Python 3.11+, [uv](https://docs.astral.sh/uv/).

```bash
# 1. התקנת תלויות
uv sync

# 2. התקנת דפדפן כרומיום עבור Playwright
uv run playwright install chromium

# 3. מפתח API של Gemini (חינמי, בלי כרטיס אשראי) — https://aistudio.google.com/apikey
copy .env.example .env    # ולערוך: GEMINI_API_KEY=...

# 4. הרצת הצ'אט
uv run host.py
```

לבדיקה מהירה של השרת הישראלי בלי LLM:

```bash
uv run test_israel_flow.py
```

## 💬 דוגמאות לשאלות

- `מה התחזית להיום בתל אביב?`
- `כדאי לקחת מטריה מחר בירושלים?`
- `מה מזג האוויר בחיפה בסוף השבוע?`
- `What's the forecast in Chicago?` (יופנה לשרת האמריקאי)
- `Are there weather alerts in California?`

בזמן שהשאלה מעובדת תראו את הדפדפן נפתח, מקליד את שם העיר ובוחר אותה מהרשימה — ואז המודל עונה על סמך תוכן הדף.

## ⚙️ איך זה עובד

1. **Host** (`host.py`) מריץ כל שרת MCP כתהליך-בן ופותח מולו session דרך stdio (באמצעות ה-**Client** הגנרי ב-`client.py`).
2. ה-Host מגלה את ה-Tools של כל שרת ומצרף אותם לכל קריאה ל-LLM (Gemini).
3. כשהמודל מזהה שאלה על מזג אוויר בישראל, הוא מפעיל את ארבעת ה-Tools בזה אחר זה: פתיחת דפדפן ← הקלדת עיר ← בחירה מהרשימה ← חילוץ תוכן.
4. תוכן הדף חוזר למודל כ-tool result, והוא מנסח מתוכו תשובה — RAG על דף אינטרנט חי.

## 🔗 חיבור לאפליקציות אחרות (למשל ChatBox)

אפשר לחבר את השרת לכל Host תומך MCP עם פקודה כזו:

```
uv --directory C:\path\to\project run weather_Israel.py
```

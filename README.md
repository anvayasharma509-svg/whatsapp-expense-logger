# Telegram Expense Logger

A personal Telegram bot that turns casual messages into a structured expense log in Google Sheets.

Send `flight 8977 delhi trip` to your bot → it logs the entry and replies `Logged. Flight | 8977 | Delhi trip | 25 Jun`.

## How it works

1. You send a message to your Telegram bot
2. Telegram POSTs the update to this Flask webhook
3. Claude (`claude-sonnet-4-6`) parses the message into structured JSON
4. The server writes a row to the correct month tab in your Google Sheet
5. The bot replies confirming what was logged (or answering your query)

## Folder structure

```
whatsapp-expense-logger/
  app.py              # Flask app, /webhook endpoint
  parser.py           # Claude API call, intent detection
  sheets.py           # Google Sheets read/write
  queries.py          # Query handlers (totals, filters, recent)
  config.py           # Env var loader
  requirements.txt
  .env                # Not committed — copy from .env.example
  .env.example
  credentials.json    # Google service account key — not committed
  README.md
```

## Message formats

### Logging an expense
```
flight 8977 delhi trip
lunch 450
hotel 12000 goa june 28
fuel 2200
```

### Querying your data
```
total this month
show flights
total food june
last 5
list hotels
```

## Google Sheet structure

One tab per calendar month, named `Mon YYYY` (e.g. `Jun 2026`). New tabs are created automatically.

| A — Date | B — Category | C — Amount | D — Note |
|----------|-------------|------------|----------|
| 25 Jun   | Flight      | 8977       | Delhi trip |
| 25 Jun   | Lunch       | 450        |          |

## One-time setup

### 1. Telegram bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`, pick a name and a username ending in `bot`
3. Copy the **bot token** it gives you (looks like `123456789:AAxxxxxxxx`)
4. Get your numeric **chat ID**: message [@userinfobot](https://t.me/userinfobot) — it replies with your ID

### 2. Google Cloud & Sheets

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → create a new project
2. Enable the **Google Sheets API** (APIs & Services → Enable APIs)
3. Create a **Service Account** (IAM & Admin → Service Accounts → Create)
4. Download the JSON key → save as `credentials.json` in the project root
5. Create a blank Google Sheet at [sheets.google.com](https://sheets.google.com)
6. Share the sheet with the service account email (from `credentials.json`) as **Editor**
7. Copy the Sheet ID from the URL: `https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit`

### 3. Anthropic

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)

### 4. Local setup

```bash
git clone <repo>
cd whatsapp-expense-logger
pip install -r requirements.txt
cp .env.example .env
# Fill in all values in .env
# Place credentials.json in project root
python app.py
```

### 5. Deploy to Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
3. In Railway dashboard → Variables, add all env vars from `.env.example`
4. Upload `credentials.json` contents as the env var `GOOGLE_CREDENTIALS_JSON` **or** include the file in the repo (not recommended)
5. Copy the Railway public URL (e.g. `https://your-app.up.railway.app`)

### 6. Register the Telegram webhook

Tell Telegram where to send messages. Run this once (replace the token and URL):
```
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-app.up.railway.app/webhook"
```
You should get back `{"ok":true,"result":true,...}`.

### 7. Test it

Open your bot in Telegram, hit **Start**, and send `flight 8977 test`. A row should appear in your Google Sheet and the bot should reply:
```
Logged. Flight | 8977 | Test | 25 Jun
```

## Environment variables

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `ALLOWED_CHAT_IDS` | Comma-separated numeric chat IDs allowed to use the bot |
| `GOOGLE_SHEET_IDS` | Comma-separated Sheet IDs, positionally matched to `ALLOWED_CHAT_IDS` |
| `ANTHROPIC_API_KEY` | From console.anthropic.com |
| `GOOGLE_CREDENTIALS_FILE` | Path to credentials.json (default: `./credentials.json`) |
| `GOOGLE_CREDENTIALS_JSON` | Full service-account JSON (used on Railway instead of the file) |

> `ALLOWED_CHAT_IDS` and `GOOGLE_SHEET_IDS` are matched by position: the first chat ID uses the first sheet, the second uses the second, and so on.

## Error responses

| Situation | Bot reply |
|---|---|
| Amount missing | `What was the amount for that?` |
| Unrecognisable message | `Could not parse that. Try: flight 8977 delhi trip` |
| Google Sheets error | `Something went wrong saving that. Try again in a moment.` |
| Claude API error | `Could not parse that right now. Try again in a moment.` |
| Message from unknown chat | Silently ignored (HTTP 200) |
| Query with no results | `No [category] entries found for [month].` |

## Out of scope (v1)

- Multi-user support
- Currency conversion
- Budget alerts
- Receipt image parsing
- Editing or deleting entries via WhatsApp
- Charts or visual summaries

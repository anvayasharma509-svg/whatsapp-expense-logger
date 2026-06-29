# WhatsApp Expense Logger

A personal WhatsApp bot that turns casual messages into a structured expense log in Google Sheets.

Send `flight 8977 delhi trip` from your WhatsApp → bot logs it and replies `Logged. Flight | 8977 | Delhi trip | 25 Jun`.

## How it works

1. You send a WhatsApp message to your Twilio sandbox number
2. Twilio POSTs it to this Flask webhook
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

### 1. Twilio

1. Sign up at [twilio.com](https://twilio.com)
2. Go to **Messaging → Try it out → Send a WhatsApp message**
3. Note your **Account SID**, **Auth Token**, and the **sandbox number** (`whatsapp:+14155238886`)

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

### 6. Connect Twilio webhook

1. In Twilio console → Messaging → Settings → WhatsApp Sandbox Settings
2. Set **When a message comes in** to: `https://your-app.up.railway.app/webhook`
3. Method: `HTTP POST`

### 7. Activate sandbox on your phone

Send this message from your WhatsApp to the Twilio sandbox number:
```
join <sandbox-word>
```
(The sandbox word is shown in your Twilio console)

### 8. Test it

Send `flight 8977 test` from your WhatsApp. A row should appear in your Google Sheet and the bot should reply:
```
Logged. Flight | 8977 | Test | 25 Jun
```

## Environment variables

| Variable | Description |
|---|---|
| `TWILIO_ACCOUNT_SID` | From your Twilio console |
| `TWILIO_AUTH_TOKEN` | From your Twilio console |
| `TWILIO_WHATSAPP_NUMBER` | Twilio sandbox number (`whatsapp:+14155238886`) |
| `YOUR_WHATSAPP_NUMBER` | Your personal number in E.164 format (`whatsapp:+91XXXXXXXXXX`) |
| `ANTHROPIC_API_KEY` | From console.anthropic.com |
| `GOOGLE_SHEET_ID` | Sheet ID from the Google Sheet URL |
| `GOOGLE_CREDENTIALS_FILE` | Path to credentials.json (default: `./credentials.json`) |

## Error responses

| Situation | Bot reply |
|---|---|
| Amount missing | `What was the amount for that?` |
| Unrecognisable message | `Could not parse that. Try: flight 8977 delhi trip` |
| Google Sheets error | `Something went wrong saving that. Try again in a moment.` |
| Claude API error | `Could not parse that right now. Try again in a moment.` |
| Message from unknown number | Silently ignored (HTTP 200) |
| Query with no results | `No [category] entries found for [month].` |

## Out of scope (v1)

- Multi-user support
- Currency conversion
- Budget alerts
- Receipt image parsing
- Editing or deleting entries via WhatsApp
- Charts or visual summaries

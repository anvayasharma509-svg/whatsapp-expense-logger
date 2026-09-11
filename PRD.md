# Product Requirements Document — Telegram Expense Logger

## Overview

Telegram Expense Logger is a personal finance bot that converts casual Telegram messages into structured expense records in Google Sheets. Users log spending by typing naturally ("lunch 450" or "flight 8977 delhi trip"), and the bot uses Claude to parse intent, extract structured data, and write it to the right month tab automatically. Queries work the same way — ask "total this month" or "show flights" and the bot replies instantly.

---

## Problem Statement

Manual expense tracking requires switching apps, opening a spreadsheet, finding the right tab, and typing into cells. Most people skip it entirely because the friction is too high. This bot removes that friction: the user is already in Telegram, so logging an expense is as easy as sending a message.

---

## Goals

- Zero-friction expense capture: log an expense in under 5 seconds.
- No app to install beyond Telegram, which the user already has.
- Data lives in a Google Sheet the user owns and can open at any time.
- Natural language input — no commands to memorize, no strict formats.
- Instant query answers without leaving the chat.

---

## User Personas

**Primary: The casual tracker**
Someone who wants a record of their spending but finds dedicated budgeting apps too heavy. They want to send a quick message and forget about it, and occasionally ask "how much did I spend on food this month?"

**Secondary: The traveller**
Someone on a trip who logs flights, hotels, and meals in real time. They care about per-category totals at the end of the trip. The Swiggy screenshot feature is particularly useful for grocery orders.

---

## Features

### 1. Natural-Language Expense Logging

**What it does:** The user sends a plain-text message. Claude parses it into a structured entry (category, amount, note, date) and appends a row to the correct month tab in their Google Sheet.

**Input formats:**
```
flight 8977 delhi trip
lunch 450
hotel 12000 goa june 28
fuel 2200
coffee 180 airport
```

**How Claude extracts fields:**
- **Category** — mapped to the nearest canonical category (see list below). If nothing fits, Claude invents a sensible Title Case label.
- **Amount** — first number found; commas and currency symbols stripped.
- **Note** — everything after the amount that isn't a date.
- **Date** — any date mentioned ("june 28", "28 Jun"), otherwise today.

**Canonical categories:**
Food, Groceries, Transport, Flight, Hotel, Entertainment, Shopping, Health, Utilities, Subscriptions, Personal Care, Education, Miscellaneous

**Bot reply:**
```
Logged: Flight | 8977 | Delhi trip | 25 Jun. Reply 'undo' to reverse.
```

---

### 2. Screenshot Parsing (Swiggy Instamart Orders)

**What it does:** The user sends a photo of a Swiggy Instamart order confirmation screenshot. Claude reads the image, extracts every line item and its final price, and logs them all as individual Groceries entries in one batch write.

**Behaviour:**
- All items are logged under the Groceries category.
- Discounted items use the final paid price, not the original.
- Delivery fees, platform fees, taxes, and order totals are ignored.
- The bot replies with a summary: `Logged 4 items:` followed by each item and price.
- If the image cannot be read or contains no items, a clear error message is returned.

**Use case:** A user receives their grocery order confirmation and photographs the screen. In one message they've logged the entire shop rather than typing each item individually.

---

### 3. Query System

The bot recognises five query types, all expressed in natural language.

#### 3a. Monthly Total

**Trigger phrases:** "total this month", "june total", "how much did I spend", "september spending"

**Returns:** Total amount spent in the given month (or the current month if none specified).

```
Jun 2026 total: 42,350
```

---

#### 3b. Category Total

**Trigger phrases:** "total food", "flight expenses", "how much on hotels june", "transport this month"

**Returns:** Total for a specific category, optionally filtered to a month.

```
Flight total for Jun 2026: 18,977
```

---

#### 3c. Recent Entries

**Trigger phrases:** "last 5", "show recent", "last entries", "recent 10"

**Returns:** The last N entries from the current month (default 5), showing date, category, amount, and note.

```
Last 5 entries:
9 Sep - Food 320 (biryani)
9 Sep - Transport 250
10 Sep - Flight 8977 (Delhi trip)
10 Sep - Hotel 12000 (Goa)
11 Sep - Groceries 1450
```

---

#### 3d. Category Listing

**Trigger phrases:** "show flights", "list hotels", "all food entries", "show transport"

**Returns:** All entries for a category in the current (or specified) month with dates and amounts.

```
Flight this month:
5 Sep - 8977 (Delhi trip)
10 Sep - 14500 (Mumbai)
```

---

#### 3e. Freeform / AI Query

**Trigger:** Any spending question not covered by the four types above.

**How it works:** Claude reads three months of expense data from the sheet and answers the question in plain text. Examples:

```
which category did I spend most on last month?
compare food vs transport over the last 3 months
what was my biggest single expense?
how is this month's spending compared to last month?
```

**Returns:** A concise plain-text answer from Claude based on the actual data.

---

### 4. Undo

**Trigger phrases:** "undo", "delete last", "undo last"

**What it does:** Deletes the most recently logged row from the current month's tab in the sheet.

**Bot reply:**
```
Deleted: Flight | 8977 | 25 Jun
```

If there's nothing to delete: `Nothing to undo this month.`

**Note:** Undo works on the current month's tab only.

---

### 5. Multi-User Support

**What it does:** Multiple users can share a single deployment. Each Telegram chat ID is mapped to a separate Google Sheet via environment variables. Messages from unknown chat IDs are silently ignored.

**Configuration:** `ALLOWED_CHAT_IDS` and `GOOGLE_SHEET_IDS` are comma-separated lists matched by position. The first chat ID uses the first sheet, the second uses the second, and so on.

---

### 6. Automatic Sheet Management

**What it does:** The bot creates month tabs automatically. When a new expense is logged for a month that doesn't yet have a tab (e.g. July expenses in late June), the bot creates the tab, adds column headers, and writes the row — no manual setup needed.

**Sheet structure:**

| A — Date | B — Category | C — Amount | D — Note |
|----------|-------------|------------|----------|
| 25 Jun   | Flight      | 8977       | Delhi trip |
| 25 Jun   | Lunch       | 450        |          |

Tab names follow the `Mon YYYY` format (e.g. `Jun 2026`).

---

### 7. Usage Logging

**What it does:** Every bot interaction (log, query, screenshot) is recorded in a `Usage` tab in the user's Google Sheet. Columns: `Timestamp`, `Intent`, `Category`.

**Purpose:** Lets the user see how often they're using the bot and which categories they log most.

---

### 8. Deduplication

**What it does:** Telegram occasionally re-delivers the same webhook update if the server doesn't respond fast enough. The bot maintains a rolling window of the last 200 update IDs and silently ignores duplicates.

---

### 9. Typing Indicator

**What it does:** As soon as a valid message arrives, the bot sends a "typing…" indicator to Telegram before making API calls. This gives the user immediate feedback that the bot received their message.

---

## Error Handling

| Situation | Bot reply |
|-----------|-----------|
| Message looks like a log entry but has no amount | `What was the amount for that?` |
| Intent cannot be determined | `Could not parse that. Try: flight 8977 delhi trip` |
| Google Sheets write fails | `Something went wrong saving that. Try again in a moment.` |
| Claude API call fails | `Could not parse that right now. Try again in a moment.` |
| Message from unrecognised chat | Silently ignored (HTTP 200 returned to Telegram) |
| Query returns no results | `No [category] entries found for [month].` |
| Screenshot unreadable | `Could not read that image. Try a clearer screenshot.` |
| Screenshot has no items | `No items found in the screenshot.` |
| Screenshot parsed but sheet write fails | `Parsed the image but could not log items. Try again.` |
| Empty message body | `Please send a message to log an expense or query your data.` |

---

## Technical Architecture

```
Telegram  →  Flask /webhook  →  parser.py (Claude)  →  sheets.py (Google Sheets API)
                                      ↓
                               queries.py (Claude, for freeform)
```

| Component | Role |
|-----------|------|
| `app.py` | Flask app, `/webhook` POST endpoint, update routing |
| `parser.py` | Claude API calls for text parsing and image parsing |
| `queries.py` | Query handlers: totals, category filters, recent, freeform |
| `sheets.py` | Google Sheets read/write, tab management, usage logging |
| `config.py` | Env var loading, chat ID → sheet ID mapping |

**AI model:** `claude-sonnet-4-6` for all parsing and freeform queries.

**Deployment:** Flask on Railway. Telegram webhooks post to the `/webhook` endpoint.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `ALLOWED_CHAT_IDS` | Comma-separated numeric chat IDs allowed to use the bot |
| `GOOGLE_SHEET_IDS` | Comma-separated Sheet IDs, positionally matched to `ALLOWED_CHAT_IDS` |
| `ANTHROPIC_API_KEY` | From console.anthropic.com |
| `GOOGLE_CREDENTIALS_FILE` | Path to credentials.json (default: `./credentials.json`) |
| `GOOGLE_CREDENTIALS_JSON` | Full service-account JSON as a string (used on Railway) |

---

## Out of Scope (v1)

- Currency conversion or multi-currency support
- Budget limits and overspend alerts
- Recurring / scheduled expenses
- Editing a past entry (only "undo last" is supported)
- Charts or visual spending summaries
- Receipt image parsing for non-Swiggy formats
- Exporting data to PDF or CSV from the bot
- Reminders or scheduled reports

---

## Future Considerations

- **Budget alerts:** user sets a monthly budget per category; bot warns when 80% is reached.
- **Receipt OCR:** extend screenshot parsing to any receipt photo, not just Swiggy.
- **Edit command:** let users correct a logged entry by referencing it by date or category.
- **Weekly digest:** scheduled summary sent to the user every Sunday.
- **Multi-currency:** detect currency from message and convert at the time of logging.
- **Expense splitting:** log a shared expense and split it across people.

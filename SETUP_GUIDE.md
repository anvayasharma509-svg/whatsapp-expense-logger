# Setup Guide — For Non-Technical Users

This guide will get the expense bot running on your phone. You do not need to know anything about coding. Follow each step in order and you will be done in about 30–45 minutes.

**What you'll need:**
- A phone with Telegram installed (free, from your app store)
- A Google account (Gmail)
- A computer with a web browser

---

## What you're setting up

By the end of this guide, you will have a personal Telegram bot. You send it messages like "lunch 450" and it saves the expense to a Google spreadsheet that belongs to you. Nobody else can see your data.

Here's the big picture of what you're about to create:

```
Your Telegram message  →  Bot  →  Your Google Sheet
```

There are 5 accounts/services you need to set up. We'll do them one at a time.

---

## Part 1 — Create your Telegram bot

Telegram lets you create "bots" — automated accounts that respond to messages. You'll create one that belongs to you.

1. Open Telegram on your phone.

2. In the search bar at the top, search for **BotFather** (it's an official Telegram account with a blue checkmark).

3. Tap on it and tap **Start** (or type `/start`).

4. Type `/newbot` and send it.

5. BotFather will ask: *"Alright, a new bot. How are we going to call it?"*
   Type any name you like, for example: **My Expense Bot**

6. It will then ask for a username. This must end in the word `bot`.
   Try something like: **myexpenses_anvaya_bot** (make it unique, like your name + expenses + bot)

7. BotFather will reply with a long token that looks like this:
   `7823456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   
   **Copy this and save it somewhere safe** (notes app, email to yourself). This is your **Bot Token**. You'll need it later.

8. Now find your own Telegram ID. Search for **userinfobot** in Telegram, tap Start, and it will reply with a number like `1234567890`. **Save this number too** — it's your **Chat ID**.

---

## Part 2 — Create your Google Sheet

This is where your expenses will be saved. It's just a regular Google spreadsheet.

1. Go to **sheets.google.com** (type that into your browser).

2. Click the big **+** button to create a new blank spreadsheet.

3. Give it a name at the top — something like **My Expenses 2026**.

4. Look at the address bar in your browser. It will look like:
   `https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit`
   
   The long string of letters and numbers between `/d/` and `/edit` is your **Sheet ID**.
   In the example above: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms`
   
   **Copy and save your Sheet ID.**

---

## Part 3 — Give the bot permission to write to your sheet

Google needs you to create a special "service account" — think of it as a robot Google employee that the bot will use to save data to your sheet. This sounds scary but it's just clicking through a few screens.

### Step 3a — Create a Google Cloud project

1. Go to **console.cloud.google.com** in your browser. Sign in with your Google account.

2. At the top of the page, click where it says **Select a project** (it might also show an existing project name).

3. In the window that appears, click **New Project** (top right corner).

4. Give it any name, like **Expense Bot**. Click **Create**.

5. After a few seconds, click **Select Project** on the notification that appears, or click the project selector again and choose your new project.

### Step 3b — Turn on the Google Sheets API

1. In the search bar at the top of the page, type **Google Sheets API** and press Enter.

2. Click on **Google Sheets API** in the results.

3. Click the blue **Enable** button.

### Step 3c — Create the service account

1. In the search bar, type **Service Accounts** and click the result that says "Service Accounts" (under IAM & Admin).

2. Click **+ Create Service Account** near the top.

3. In the "Service account name" box, type **expense-bot** (or anything you like).

4. Click **Create and Continue**.

5. On the next screen ("Grant this service account access"), click **Continue** without changing anything.

6. On the next screen, click **Done**.

7. You'll now see your new service account in the list. It will have an email address that looks like:
   `expense-bot@your-project-id.iam.gserviceaccount.com`
   
   **Click on that service account** to open it.

8. Click the **Keys** tab at the top.

9. Click **Add Key** → **Create new key**.

10. Choose **JSON** and click **Create**.

11. A file will download to your computer. It will be named something like `your-project-id-abc123.json`.
    **Keep this file safe.** You'll need it shortly. Don't share it with anyone.

### Step 3d — Share your sheet with the service account

1. Copy the service account email address (from step 7 above — looks like `expense-bot@...gserviceaccount.com`).

2. Open your Google Sheet (from Part 2).

3. Click the green **Share** button (top right).

4. Paste the service account email address into the "Add people and groups" box.

5. Make sure it says **Editor** in the dropdown next to it.

6. Click **Send** (it may warn that this isn't a Google account — that's fine, click Send anyway).

---

## Part 4 — Get an Anthropic API key

Anthropic makes the AI (Claude) that understands your messages. You need an account to use it.

1. Go to **console.anthropic.com** in your browser.

2. Click **Sign Up** and create a free account.

3. Once you're logged in, click **API Keys** in the left menu.

4. Click **Create Key**. Give it any name, like **Expense Bot**.

5. A key will appear — it starts with `sk-ant-`. **Copy it and save it.** You won't be able to see it again after you close this screen.

> **Cost note:** Anthropic charges a small fee per message. For personal expense logging (a few messages a day), this will be less than $1 per month. You'll need to add a payment method in your Anthropic account settings.

---

## Part 5 — Deploy the bot to Railway

Railway is a website that runs the bot 24/7 on a computer in the cloud, so you don't need to leave your own computer on. It has a free tier that's enough for personal use.

### Step 5a — Put the code on GitHub

GitHub is a website that stores code. The bot's code needs to live there so Railway can find it.

1. Go to **github.com** and create a free account.

2. Once logged in, click the **+** button (top right) → **New repository**.

3. Give it a name: **expense-bot**. Leave everything else as default. Click **Create repository**.

4. You now have an empty repository. You need to copy the bot's code into it.

   On your computer, open the folder containing the bot files (`app.py`, `requirements.txt`, etc.). You should have received or downloaded these.

5. Click **uploading an existing file** on the GitHub page (it's a link in the middle of the screen).

6. Drag all the files from the bot folder into the GitHub upload area. **Do not upload the `.env` file or `credentials.json`** — those contain secrets. Upload everything else.

7. Click **Commit changes** at the bottom.

### Step 5b — Deploy on Railway

1. Go to **railway.app** and sign up using your GitHub account.

2. Click **New Project** → **Deploy from GitHub repo**.

3. Choose the **expense-bot** repository you just created.

4. Railway will start setting it up. You'll see a project dashboard appear.

### Step 5c — Add your settings to Railway

Railway needs all the secret values you've been collecting. Here's how to add them:

1. In your Railway project, click on your service (the box with your app name).

2. Click the **Variables** tab.

3. Click **New Variable** and add each of the following, one at a time:

   | Variable name | What to paste in |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | The bot token from Part 1 (e.g. `7823456789:AAFxxx...`) |
   | `ALLOWED_CHAT_IDS` | Your Chat ID from Part 1 (e.g. `1234567890`) |
   | `GOOGLE_SHEET_IDS` | Your Sheet ID from Part 2 (the long string from the URL) |
   | `ANTHROPIC_API_KEY` | The key from Part 4 (starts with `sk-ant-`) |
   | `GOOGLE_CREDENTIALS_JSON` | See instructions below |

4. For `GOOGLE_CREDENTIALS_JSON`: Open the `.json` file you downloaded in Part 3c in any text editor (Notepad on Windows, TextEdit on Mac). Select **all** the text inside it (Ctrl+A or Cmd+A), copy it, and paste it as the value for this variable.

5. After adding all variables, Railway will automatically redeploy your app.

### Step 5d — Get your Railway URL

1. In your Railway project, click on your service.

2. Click the **Settings** tab.

3. Under **Networking**, click **Generate Domain**. Railway will give you a URL like:
   `https://expense-bot-production.up.railway.app`
   
   **Copy this URL.**

---

## Part 6 — Connect Telegram to your bot

You need to tell Telegram "when someone messages my bot, send it to this Railway URL". You do this once.

1. Open your browser and paste this URL, replacing the two placeholders:

   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_RAILWAY_URL>/webhook
   ```

   Example (with fake values):
   ```
   https://api.telegram.org/bot7823456789:AAFxxxxxx/setWebhook?url=https://expense-bot-production.up.railway.app/webhook
   ```

2. Press Enter. The page should show:
   ```json
   {"ok":true,"result":true,"description":"Webhook was set"}
   ```

   If you see `"ok":true`, you're done. If not, double-check that you replaced both placeholders correctly.

---

## Part 7 — Test it

1. Open Telegram and search for the bot username you created in Part 1 (e.g. `@myexpenses_anvaya_bot`).

2. Tap **Start**.

3. Send this message:
   ```
   coffee 180 test
   ```

4. The bot should reply within a few seconds:
   ```
   Logged: Food | 180 | Test | 11 Sep. Reply 'undo' to reverse.
   ```

5. Open your Google Sheet. A new tab called **Sep 2026** (or whichever month it is) should have appeared, with a row containing your entry.

If the bot doesn't reply within 10 seconds, go back and check that all the variables in Railway are correct, especially the `TELEGRAM_BOT_TOKEN` and `ALLOWED_CHAT_IDS`.

---

## You're done! Here's what to do next

Send the bot a few real expenses to get started:

```
lunch 350 biryani
uber 180
groceries 2400
flight 8977 mumbai trip
```

Try a query:

```
total this month
show food
last 5
```

To undo a mistake:

```
undo
```

---

## Troubleshooting

**Bot doesn't reply at all**
- Check that `TELEGRAM_BOT_TOKEN` in Railway matches exactly what BotFather gave you.
- Check that `ALLOWED_CHAT_IDS` in Railway matches your Chat ID from userinfobot.
- Make sure the Railway URL in the webhook URL (Part 6) is correct.

**Bot replies "Could not parse that right now"**
- Your `ANTHROPIC_API_KEY` might be wrong. Double-check it in Railway variables.
- Make sure you've added a payment method in your Anthropic account.

**Bot replies but nothing appears in the sheet**
- Check that `GOOGLE_SHEET_IDS` in Railway is the correct Sheet ID.
- Check that you shared the sheet with the service account email (Part 3d).
- Make sure `GOOGLE_CREDENTIALS_JSON` is the full contents of the JSON file with no extra spaces.

**Railway says the app crashed**
- Click on your service in Railway, then click **Deployments** → click the failed deployment → view the logs. Look for a red error message and compare it against the variable names in the table above.

---

## Keeping your data safe

- Your Google Sheet belongs to your Google account. Only you (and the service account) can access it.
- If you want to revoke the bot's access to your sheet, go to the sheet → Share → remove the service account email.
- Your expense data is never sent to Anthropic in identifiable form — only the raw message text is sent to parse it.
- The Anthropic API key, bot token, and credentials file are stored only in Railway's encrypted environment variables. Never share these with anyone.

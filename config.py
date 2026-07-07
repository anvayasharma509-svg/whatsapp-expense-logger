import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GOOGLE_CREDENTIALS_FILE = os.environ.get("GOOGLE_CREDENTIALS_FILE", "./credentials.json")

# Comma-separated, positionally matched: chat_id[i] -> sheet_id[i]
_chat_ids = [c.strip() for c in os.environ["ALLOWED_CHAT_IDS"].split(",")]
_sheets = [s.strip() for s in os.environ["GOOGLE_SHEET_IDS"].split(",")]

if len(_chat_ids) != len(_sheets):
    raise ValueError("ALLOWED_CHAT_IDS and GOOGLE_SHEET_IDS must have the same count")

# Keys are strings so lookups against str(chat_id) match
USER_SHEETS: dict[str, str] = dict(zip(_chat_ids, _sheets))

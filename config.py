import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_NUMBER = os.environ["TWILIO_WHATSAPP_NUMBER"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GOOGLE_CREDENTIALS_FILE = os.environ.get("GOOGLE_CREDENTIALS_FILE", "./credentials.json")

# Comma-separated, positionally matched: number[i] -> sheet_id[i]
_numbers = [n.strip() for n in os.environ["ALLOWED_NUMBERS"].split(",")]
_sheets = [s.strip() for s in os.environ["GOOGLE_SHEET_IDS"].split(",")]

if len(_numbers) != len(_sheets):
    raise ValueError("ALLOWED_NUMBERS and GOOGLE_SHEET_IDS must have the same count")

USER_SHEETS: dict[str, str] = dict(zip(_numbers, _sheets))

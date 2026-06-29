import os
import json
from datetime import date, datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
import config

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADERS = ["Date", "Category", "Amount", "Note"]


def _get_service():
    # Prefer env var (Railway/production), fall back to file (local)
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        info = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        creds = service_account.Credentials.from_service_account_file(
            config.GOOGLE_CREDENTIALS_FILE, scopes=SCOPES
        )
    return build("sheets", "v4", credentials=creds)


def _current_month_tab() -> str:
    return date.today().strftime("%b %Y")


def _tab_from_entry_date(entry_date: str) -> str:
    try:
        d = datetime.strptime(f"{entry_date} {date.today().year}", "%d %b %Y")
        return d.strftime("%b %Y")
    except (ValueError, TypeError):
        return _current_month_tab()


def _ensure_tab(service, sheet_id: str, tab_name: str) -> None:
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    existing = {s["properties"]["title"] for s in spreadsheet["sheets"]}

    if tab_name not in existing:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
        ).execute()
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"'{tab_name}'!A1:D1",
            valueInputOption="RAW",
            body={"values": [HEADERS]},
        ).execute()


def append_expense(entry: dict, sheet_id: str) -> None:
    service = _get_service()
    tab_name = _tab_from_entry_date(entry.get("date", ""))
    _ensure_tab(service, sheet_id, tab_name)

    row = [
        entry.get("date", ""),
        entry.get("category", ""),
        entry.get("amount", 0),
        entry.get("note") or "",
    ]
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"'{tab_name}'!A:D",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ).execute()


def get_month_rows(sheet_id: str, month: str = None) -> list:
    service = _get_service()
    tab_name = month or _current_month_tab()

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"'{tab_name}'!A2:D",
        ).execute()
        return result.get("values", [])
    except Exception:
        return []

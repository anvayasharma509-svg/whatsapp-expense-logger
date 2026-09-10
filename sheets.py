import os
import json
from datetime import date, datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
import config

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADERS = ["Date", "Category", "Amount", "Note"]

_service = None


def _get_service():
    global _service
    if _service is None:
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if creds_json:
            info = json.loads(creds_json)
            creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        else:
            creds = service_account.Credentials.from_service_account_file(
                config.GOOGLE_CREDENTIALS_FILE, scopes=SCOPES
            )
        _service = build("sheets", "v4", credentials=creds)
    return _service


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


def _ensure_usage_tab(service, sheet_id: str) -> None:
    tab_name = "Usage"
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    existing = {s["properties"]["title"] for s in spreadsheet["sheets"]}

    if tab_name not in existing:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
        ).execute()
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range="'Usage'!A1:C1",
            valueInputOption="RAW",
            body={"values": [["Timestamp", "Intent", "Category"]]},
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


def batch_append_expenses(entries: list, sheet_id: str) -> None:
    """Append multiple expense rows, grouping by tab to minimise API calls."""
    if not entries:
        return
    from collections import defaultdict
    service = _get_service()
    by_tab = defaultdict(list)
    for entry in entries:
        tab = _tab_from_entry_date(entry.get("date", ""))
        by_tab[tab].append([
            entry.get("date", ""),
            entry.get("category", ""),
            entry.get("amount", 0),
            entry.get("note") or "",
        ])
    for tab_name, rows in by_tab.items():
        _ensure_tab(service, sheet_id, tab_name)
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"'{tab_name}'!A:D",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": rows},
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


def get_months_data(sheet_id: str, months: list) -> dict:
    """Fetch data from multiple month tabs. Returns {month: [rows]}."""
    service = _get_service()
    result = {}
    for month in months:
        try:
            r = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"'{month}'!A2:D",
            ).execute()
            result[month] = r.get("values", [])
        except Exception:
            result[month] = []
    return result


def delete_last_row(sheet_id: str):
    """Delete the last data row from the current month tab. Returns the deleted row or None."""
    service = _get_service()
    tab_name = _current_month_tab()

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"'{tab_name}'!A:D",
        ).execute()
        values = result.get("values", [])
    except Exception:
        return None

    # values[0] is header row; need at least one data row
    if len(values) <= 1:
        return None

    last_row = values[-1]
    last_row_index = len(values) - 1  # 0-based index in the sheet

    # Get the numeric sheet ID (sheetId) for the tab
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheet_gid = None
    for s in spreadsheet["sheets"]:
        if s["properties"]["title"] == tab_name:
            sheet_gid = s["properties"]["sheetId"]
            break

    if sheet_gid is None:
        return None

    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={
            "requests": [{
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_gid,
                        "dimension": "ROWS",
                        "startIndex": last_row_index,
                        "endIndex": last_row_index + 1,
                    }
                }
            }]
        },
    ).execute()

    return {
        "date": last_row[0] if len(last_row) > 0 else "",
        "category": last_row[1] if len(last_row) > 1 else "",
        "amount": last_row[2] if len(last_row) > 2 else "",
        "note": last_row[3] if len(last_row) > 3 else "",
    }


def log_usage(sheet_id: str, intent: str, category: str = None) -> None:
    """Append a row to the Usage tab tracking message activity per user."""
    try:
        service = _get_service()
        _ensure_usage_tab(service, sheet_id)
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range="'Usage'!A:C",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [[now, intent, category or ""]]},
        ).execute()
    except Exception:
        pass  # usage logging must never break the main flow

import threading
from collections import deque
import requests
from flask import Flask, request
import config
import parser as expense_parser
import sheets
import queries

app = Flask(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"

# Deduplication: remember last 200 update IDs to ignore Telegram retries
_seen_updates: deque = deque(maxlen=200)
_seen_lock = threading.Lock()


def _send_message(chat_id, text: str) -> None:
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10,
    )


def _send_typing(chat_id) -> None:
    requests.post(
        f"{TELEGRAM_API}/sendChatAction",
        json={"chat_id": chat_id, "action": "typing"},
        timeout=5,
    )


def _handle_query(query: dict, sheet_id: str) -> str:
    q_type = query.get("type")
    category = query.get("category")
    month = query.get("month")
    n = int(query.get("n") or 5)
    question = query.get("question") or ""

    if q_type == "total_month":
        return queries.total_month(sheet_id, month)
    if q_type == "total_category" and category:
        return queries.total_category(sheet_id, category, month)
    if q_type == "recent":
        return queries.recent(sheet_id, n, month)
    if q_type == "list_category" and category:
        return queries.list_category(sheet_id, category, month)
    if q_type == "freeform" and question:
        return queries.freeform_query(sheet_id, question)
    return "Could not parse that. Try: flight 8977 delhi trip"


def _handle_undo(chat_id: int, sheet_id: str) -> None:
    deleted = sheets.delete_last_row(sheet_id)
    if deleted:
        _send_message(
            chat_id,
            f"Deleted: {deleted['category']} | {deleted['amount']} | {deleted['date']}",
        )
    else:
        _send_message(chat_id, "Nothing to undo this month.")


def process_update(update: dict) -> None:
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    body = (message.get("text") or "").strip()

    if chat_id is None:
        return

    sheet_id = config.USER_SHEETS.get(str(chat_id))
    if not sheet_id:
        return

    if not body:
        _send_message(chat_id, "Please send a message to log an expense or query your data.")
        return

    # Typing indicator fires immediately so the user sees the bot is alive
    _send_typing(chat_id)

    # Catch undo before calling Claude to save a round-trip
    if body.lower() in ("undo", "delete last", "undo last"):
        _handle_undo(chat_id, sheet_id)
        return

    try:
        parsed = expense_parser.parse_message(body)
    except Exception:
        _send_message(chat_id, "Could not parse that right now. Try again in a moment.")
        return

    error = parsed.get("error")
    if error == "no_amount":
        _send_message(chat_id, "What was the amount for that?")
        return
    if error == "unrecognisable":
        _send_message(chat_id, "Could not parse that. Try: flight 8977 delhi trip")
        return

    intent = parsed.get("intent")

    if intent == "undo":
        _handle_undo(chat_id, sheet_id)

    elif intent == "log":
        entry = parsed.get("entry", {})
        try:
            sheets.append_expense(entry, sheet_id)
            sheets.log_usage(sheet_id, "log", entry.get("category"))
        except Exception:
            _send_message(chat_id, "Something went wrong saving that. Try again in a moment.")
            return
        note = entry.get("note")
        note_part = f" | {note}" if note else ""
        reply = (
            f"Logged: {entry.get('category')} | {entry.get('amount')}{note_part} | {entry.get('date')}."
            " Reply 'undo' to reverse."
        )
        _send_message(chat_id, reply)

    elif intent == "query":
        try:
            sheets.log_usage(sheet_id, "query")
            reply = _handle_query(parsed.get("query", {}), sheet_id)
        except Exception:
            reply = "Something went wrong reading that. Try again in a moment."
        _send_message(chat_id, reply)

    else:
        _send_message(chat_id, "Could not parse that. Try: flight 8977 delhi trip")


@app.route("/", methods=["GET"])
def health():
    return "OK", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}
    update_id = update.get("update_id")

    # Return 200 immediately so Telegram does not retry during cold-start processing
    if update_id is not None:
        with _seen_lock:
            if update_id in _seen_updates:
                return "", 200
            _seen_updates.append(update_id)

    threading.Thread(target=process_update, args=(update,), daemon=True).start()
    return "", 200


if __name__ == "__main__":
    app.run(debug=False)

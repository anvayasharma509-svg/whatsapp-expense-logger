import requests
from flask import Flask, request
import config
import parser as expense_parser
import sheets
import queries

app = Flask(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"


def _send_message(chat_id, text: str) -> None:
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10,
    )


def _handle_query(query: dict, sheet_id: str) -> str:
    q_type = query.get("type")
    category = query.get("category")
    month = query.get("month")
    n = int(query.get("n") or 5)

    if q_type == "total_month":
        return queries.total_month(sheet_id, month)
    if q_type == "total_category" and category:
        return queries.total_category(sheet_id, category, month)
    if q_type == "recent":
        return queries.recent(sheet_id, n, month)
    if q_type == "list_category" and category:
        return queries.list_category(sheet_id, category, month)
    return "Could not parse that. Try: flight 8977 delhi trip"


@app.route("/", methods=["GET"])
def health():
    return "OK", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    body = (message.get("text") or "").strip()

    # Nothing actionable in this update
    if chat_id is None:
        return "", 200

    # Silently ignore messages from unknown chats
    sheet_id = config.USER_SHEETS.get(str(chat_id))
    if not sheet_id:
        return "", 200

    if not body:
        _send_message(chat_id, "Please send a message to log an expense or query your data.")
        return "", 200

    # Parse with Claude
    try:
        parsed = expense_parser.parse_message(body)
    except Exception:
        _send_message(chat_id, "Could not parse that right now. Try again in a moment.")
        return "", 200

    error = parsed.get("error")
    if error == "no_amount":
        _send_message(chat_id, "What was the amount for that?")
        return "", 200
    if error == "unrecognisable":
        _send_message(chat_id, "Could not parse that. Try: flight 8977 delhi trip")
        return "", 200

    intent = parsed.get("intent")

    if intent == "log":
        entry = parsed.get("entry", {})
        try:
            sheets.append_expense(entry, sheet_id)
        except Exception:
            _send_message(chat_id, "Something went wrong saving that. Try again in a moment.")
            return "", 200
        note = entry.get("note")
        note_part = f" | {note}" if note else ""
        reply = f"Logged. {entry.get('category')} | {entry.get('amount')}{note_part} | {entry.get('date')}"
        _send_message(chat_id, reply)

    elif intent == "query":
        try:
            reply = _handle_query(parsed.get("query", {}), sheet_id)
        except Exception:
            reply = "Something went wrong reading that. Try again in a moment."
        _send_message(chat_id, reply)

    else:
        _send_message(chat_id, "Could not parse that. Try: flight 8977 delhi trip")

    return "", 200


if __name__ == "__main__":
    app.run(debug=False)

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import config
import parser as expense_parser
import sheets
import queries

app = Flask(__name__)


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


@app.route("/webhook", methods=["POST"])
def webhook():
    sender = request.form.get("From", "")
    body = request.form.get("Body", "").strip()

    resp = MessagingResponse()

    # Silently ignore messages from unknown numbers
    sheet_id = config.USER_SHEETS.get(sender)
    if not sheet_id:
        return str(resp), 200

    if not body:
        resp.message("Please send a message to log an expense or query your data.")
        return str(resp), 200

    # Parse with Claude
    try:
        parsed = expense_parser.parse_message(body)
    except Exception:
        resp.message("Could not parse that right now. Try again in a moment.")
        return str(resp), 200

    error = parsed.get("error")
    if error == "no_amount":
        resp.message("What was the amount for that?")
        return str(resp), 200
    if error == "unrecognisable":
        resp.message("Could not parse that. Try: flight 8977 delhi trip")
        return str(resp), 200

    intent = parsed.get("intent")

    if intent == "log":
        entry = parsed.get("entry", {})
        try:
            sheets.append_expense(entry, sheet_id)
        except Exception:
            resp.message("Something went wrong saving that. Try again in a moment.")
            return str(resp), 200
        note = entry.get("note")
        note_part = f" | {note}" if note else ""
        reply = f"Logged. {entry.get('category')} | {entry.get('amount')}{note_part} | {entry.get('date')}"
        resp.message(reply)

    elif intent == "query":
        try:
            reply = _handle_query(parsed.get("query", {}), sheet_id)
        except Exception:
            reply = "Something went wrong reading that. Try again in a moment."
        resp.message(reply)

    else:
        resp.message("Could not parse that. Try: flight 8977 delhi trip")

    return str(resp), 200


if __name__ == "__main__":
    app.run(debug=False)

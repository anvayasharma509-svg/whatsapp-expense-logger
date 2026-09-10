import json
from datetime import date
import anthropic
import config

_client = None

CANONICAL_CATEGORIES = [
    "Food", "Groceries", "Transport", "Flight", "Hotel",
    "Entertainment", "Shopping", "Health", "Utilities",
    "Subscriptions", "Personal Care", "Education", "Miscellaneous",
]


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


SYSTEM_PROMPT = """\
You are an expense parser for a personal expense logger. Parse the incoming message and return ONLY a JSON object, with no explanation, no markdown, no code block.

Today is {today_full}. Current month is {current_month}.

CANONICAL CATEGORIES - always map to the nearest one:
{categories}
If none fits, invent a sensible Title Case label.

INTENT RULES:
- "log": message describes a new expense (has a recognisable category)
- "query": message asks about existing expenses
- "undo": message says undo, delete last, reverse, or cancel last entry

FIELD EXTRACTION FOR LOG:
- category: map to the nearest canonical category (Title Case)
- amount: first number found, stripped of commas/currency symbols, stored as a plain number
- note: everything after the amount that is not a date (null if absent)
- date: parse any mentioned date to "D Mon" format (e.g. "25 Jun", "5 Jul"). Use today ({today}) if no date is mentioned.

QUERY TYPES:
- "total_month": "total this month", "june total", "how much did I spend"
- "total_category": "total food", "flight expenses", "how much on hotels june"
- "recent": "last 5", "show recent", "last entries"
- "list_category": "show flights", "list hotels", "all food entries"
- "freeform": any other spending question - comparisons, trends, biggest category, multi-month, anything not covered above

For queries with a specific month (e.g. "june", "last month"), set month as "Mon YYYY" (e.g. "Jun 2026"). Set to null for current month.
For freeform queries, copy the user's question verbatim into the question field.

ERROR CODES:
- "no_amount": message looks like a log entry but has no number
- "unrecognisable": cannot determine intent at all

Return EXACTLY one of these JSON shapes:

For a log entry:
{{"intent": "log", "entry": {{"category": "Flight", "amount": 8977, "note": "Delhi trip", "date": "25 Jun"}}, "error": null}}

For a standard query:
{{"intent": "query", "query": {{"type": "total_month", "category": null, "month": null, "n": 5, "question": null}}, "error": null}}

For a freeform query:
{{"intent": "query", "query": {{"type": "freeform", "category": null, "month": null, "n": null, "question": "how much on food last 3 months"}}, "error": null}}

For undo:
{{"intent": "undo", "entry": null, "error": null}}

For an error:
{{"intent": null, "error": "unrecognisable"}}
"""


def parse_message(message: str) -> dict:
    today = date.today()
    today_str = f"{today.day} {today.strftime('%b')}"
    today_full = today.strftime("%A, %d %B %Y")
    current_month = today.strftime("%b %Y")

    system = SYSTEM_PROMPT.format(
        today=today_str,
        today_full=today_full,
        current_month=current_month,
        categories=", ".join(CANONICAL_CATEGORIES),
    )

    response = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": message}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)

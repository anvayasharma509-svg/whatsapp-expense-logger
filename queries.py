import anthropic
from datetime import date
import config
import sheets

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _current_month() -> str:
    return date.today().strftime("%b %Y")


def _prev_months(n: int) -> list:
    """Return the last n month strings including the current month."""
    today = date.today()
    year, month = today.year, today.month
    result = []
    for _ in range(n):
        result.append(date(year, month, 1).strftime("%b %Y"))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return result


def _safe_sum(rows: list) -> float:
    total = 0.0
    for row in rows:
        if len(row) > 2 and row[2]:
            try:
                total += float(row[2])
            except ValueError:
                pass
    return total


def total_month(sheet_id: str, month: str = None) -> str:
    month = month or _current_month()
    rows = sheets.get_month_rows(sheet_id, month)
    if not rows:
        return f"No entries found for {month}."
    return f"{month} total: {int(_safe_sum(rows)):,}"


def total_category(sheet_id: str, category: str, month: str = None) -> str:
    month = month or _current_month()
    rows = sheets.get_month_rows(sheet_id, month)
    filtered = [r for r in rows if len(r) > 1 and r[1].lower() == category.lower()]
    if not filtered:
        return f"No {category} entries found for {month}."
    return f"{category} total for {month}: {int(_safe_sum(filtered)):,}"


def recent(sheet_id: str, n: int = 5, month: str = None) -> str:
    month = month or _current_month()
    rows = sheets.get_month_rows(sheet_id, month)
    if not rows:
        return f"No entries found for {month}."
    last_n = rows[-n:]
    lines = []
    for row in last_n:
        date_str = row[0] if len(row) > 0 else ""
        cat = row[1] if len(row) > 1 else ""
        amt = row[2] if len(row) > 2 else ""
        note = row[3] if len(row) > 3 else ""
        line = f"{date_str} - {cat} {amt}"
        if note:
            line += f" ({note})"
        lines.append(line)
    return f"Last {len(last_n)} entries:\n" + "\n".join(lines)


def list_category(sheet_id: str, category: str, month: str = None) -> str:
    month = month or _current_month()
    rows = sheets.get_month_rows(sheet_id, month)
    filtered = [r for r in rows if len(r) > 1 and r[1].lower() == category.lower()]
    if not filtered:
        return f"No {category} entries found for {month}."
    lines = []
    for row in filtered:
        date_str = row[0] if len(row) > 0 else ""
        amt = row[2] if len(row) > 2 else ""
        note = row[3] if len(row) > 3 else ""
        line = f"{date_str} - {amt}"
        if note:
            line += f" ({note})"
        lines.append(line)
    return f"{category} this month:\n" + "\n".join(lines)


def freeform_query(sheet_id: str, question: str) -> str:
    """Answer any spending question by passing 3 months of data to Claude."""
    months = _prev_months(3)
    all_data = sheets.get_months_data(sheet_id, months)

    data_lines = []
    for month in months:
        rows = all_data.get(month, [])
        if rows:
            data_lines.append(f"{month}:")
            for row in rows:
                d = row[0] if len(row) > 0 else ""
                cat = row[1] if len(row) > 1 else ""
                amt = row[2] if len(row) > 2 else ""
                note = row[3] if len(row) > 3 else ""
                line = f"  {d} | {cat} | {amt}"
                if note:
                    line += f" | {note}"
                data_lines.append(line)

    if not data_lines:
        return "No data found for the last 3 months."

    data_text = "\n".join(data_lines)
    response = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=(
            "You are a personal expense analyst. Answer the user's question about their spending data concisely. "
            "Use plain text only, no markdown. Format amounts as plain numbers without currency symbols."
        ),
        messages=[{"role": "user", "content": f"My expense data:\n{data_text}\n\nQuestion: {question}"}],
    )
    return response.content[0].text.strip()

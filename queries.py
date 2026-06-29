from datetime import date
import sheets


def _current_month() -> str:
    return date.today().strftime("%b %Y")


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

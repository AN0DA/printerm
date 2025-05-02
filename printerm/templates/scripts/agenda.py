import datetime
from typing import Any


def compute_variables() -> dict[str, Any]:
    """Compute variables for the agenda template."""
    today = datetime.date.today()
    _, week_number, _ = today.isocalendar()
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)
    days = []
    for i in range(7):
        day_date = week_start + datetime.timedelta(days=i)
        day_name = day_date.strftime("%A")
        date_str = day_date.strftime("%Y-%m-%d")
        days.append({"day_name": day_name, "date": date_str})
    return {
        "week_number": week_number,
        "week_start_date": week_start.strftime("%Y-%m-%d"),
        "week_end_date": week_end.strftime("%Y-%m-%d"),
        "days": days,
    }

"""Agenda generator script for weekly agenda templates."""

import datetime
from typing import Any

from .base import TemplateScript


class AgendaGeneratorScript(TemplateScript):
    """Template script for generating weekly agenda variables."""

    @property
    def name(self) -> str:
        """Return the unique name of this script."""
        return "agenda_generator"

    @property
    def description(self) -> str:
        """Return a human-readable description of what this script does."""
        return "Generates variables for weekly agenda templates including dates and day names"

    def generate_context(self, **kwargs: Any) -> dict[str, Any]:
        """Generate context variables for agenda template rendering.

        Args:
            **kwargs: Optional parameters:
                - date: Specific date to generate agenda for (defaults to today)
                - week_offset: Number of weeks to offset from the base date (default: 0)

        Returns:
            Dictionary containing:
                - week_number: ISO week number
                - week_start_date: Start date of the week (Monday)
                - week_end_date: End date of the week (Sunday)
                - days: List of day objects with day_name and date
        """
        # Get base date (default to today)
        base_date = kwargs.get("date")
        if base_date is None:
            base_date = datetime.date.today()
        elif isinstance(base_date, str):
            base_date = datetime.date.fromisoformat(base_date)

        # Apply week offset if specified
        week_offset = kwargs.get("week_offset", 0)
        if week_offset != 0:
            base_date = base_date + datetime.timedelta(weeks=week_offset)

        # Calculate week information
        _, week_number, _ = base_date.isocalendar()

        # Calculate week start (Monday) and end (Sunday)
        week_start = base_date - datetime.timedelta(days=base_date.weekday())
        week_end = week_start + datetime.timedelta(days=6)

        # Generate day information for each day of the week
        days = []
        for i in range(7):
            day_date = week_start + datetime.timedelta(days=i)
            day_name = day_date.strftime("%A")
            date_str = day_date.strftime("%Y-%m-%d")
            days.append(
                {
                    "day_name": day_name,
                    "date": date_str,
                    "short_name": day_date.strftime("%a"),
                    "day_number": day_date.day,
                    "month_name": day_date.strftime("%B"),
                    "month_short": day_date.strftime("%b"),
                }
            )

        context = {
            "week_number": week_number,
            "week_start_date": week_start.strftime("%Y-%m-%d"),
            "week_end_date": week_end.strftime("%Y-%m-%d"),
            "days": days,
            "year": base_date.year,
            "month": base_date.month,
            "current_date": base_date.strftime("%Y-%m-%d"),
        }

        self.logger.debug(f"Generated agenda context for week {week_number}, {week_start} to {week_end}")
        return context

    def get_optional_parameters(self) -> list[str]:
        """Return list of optional parameter names for this script."""
        return ["date", "week_offset"]

    def validate_context(self, context: dict[str, Any]) -> bool:
        """Validate the generated context."""
        required_keys = ["week_number", "week_start_date", "week_end_date", "days"]

        # Check all required keys are present
        if not all(key in context for key in required_keys):
            self.logger.error(f"Context missing required keys: {required_keys}")
            return False

        # Validate days structure
        days = context.get("days", [])
        if not isinstance(days, list) or len(days) != 7:
            self.logger.error("Days must be a list of 7 items")
            return False

        # Validate each day has required fields
        for day in days:
            if not isinstance(day, dict) or not all(key in day for key in ["day_name", "date"]):
                self.logger.error("Each day must have day_name and date")
                return False

        return True

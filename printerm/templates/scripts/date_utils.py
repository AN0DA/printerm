"""Example date utilities script for templates."""

import datetime
from typing import Any

from .base import TemplateScript


class DateUtilsScript(TemplateScript):
    """Template script for generating various date-related variables."""

    @property
    def name(self) -> str:
        """Return the unique name of this script."""
        return "date_utils"

    @property
    def description(self) -> str:
        """Return a human-readable description of what this script does."""
        return "Provides various date and time utilities for templates"

    def generate_context(self, **kwargs: Any) -> dict[str, Any]:
        """Generate date and time context variables.

        Args:
            **kwargs: Optional parameters:
                - date: Specific date to use (defaults to today)
                - timezone: Timezone to use (defaults to system timezone)
                - format_style: Date format style ('short', 'medium', 'long', 'full')

        Returns:
            Dictionary containing various date and time variables
        """
        # Get base date
        base_date = kwargs.get("date")
        if base_date is None:
            base_date = datetime.date.today()
        elif isinstance(base_date, str):
            base_date = datetime.date.fromisoformat(base_date)

        # Get current time
        now = datetime.datetime.now()

        # Generate comprehensive date context
        context = {
            # Basic date info
            "current_date": base_date.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M:%S"),
            "current_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            # Date components
            "year": base_date.year,
            "month": base_date.month,
            "day": base_date.day,
            "weekday": base_date.weekday(),  # 0=Monday, 6=Sunday
            # Formatted dates
            "date_short": base_date.strftime("%m/%d/%Y"),
            "date_medium": base_date.strftime("%b %d, %Y"),
            "date_long": base_date.strftime("%B %d, %Y"),
            "date_full": base_date.strftime("%A, %B %d, %Y"),
            # Month names
            "month_name": base_date.strftime("%B"),
            "month_short": base_date.strftime("%b"),
            # Day names
            "day_name": base_date.strftime("%A"),
            "day_short": base_date.strftime("%a"),
            # Week info
            "week_number": base_date.isocalendar()[1],
            # Time components
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
            "hour_12": now.strftime("%I"),
            "ampm": now.strftime("%p"),
            # Timestamps
            "timestamp": int(now.timestamp()),
            "iso_datetime": now.isoformat(),
            # Relative dates
            "yesterday": (base_date - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            "tomorrow": (base_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
        }

        self.logger.debug(f"Generated date utils context for {base_date}")
        return context

    def get_optional_parameters(self) -> list[str]:
        """Return list of optional parameter names for this script."""
        return ["date", "timezone", "format_style"]

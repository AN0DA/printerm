"""Tests for agenda generator script."""

import datetime
from unittest.mock import patch

import pytest

from printerm.templates.scripts.agenda_generator import AgendaGeneratorScript


class TestAgendaGeneratorScript:
    """Test cases for AgendaGeneratorScript."""

    def test_script_name(self) -> None:
        """Test that script returns correct name."""
        script = AgendaGeneratorScript()
        assert script.name == "agenda_generator"

    def test_script_description(self) -> None:
        """Test that script returns meaningful description."""
        script = AgendaGeneratorScript()
        assert "weekly agenda" in script.description.lower()
        assert "dates" in script.description.lower()

    def test_generate_context_default_today(self) -> None:
        """Test generating context with default date (today)."""
        script = AgendaGeneratorScript()

        with patch("printerm.templates.scripts.agenda_generator.datetime") as mock_datetime:
            # Mock today as a specific Monday for predictable testing
            mock_date = datetime.date(2025, 7, 7)  # Monday, 2025-07-07
            mock_datetime.date.today.return_value = mock_date
            mock_datetime.date.side_effect = datetime.date
            mock_datetime.timedelta = datetime.timedelta

            context = script.generate_context()

            assert "week_number" in context
            assert "week_start_date" in context
            assert "week_end_date" in context
            assert "days" in context

            # Week 28 of 2025
            assert context["week_number"] == 28
            assert context["week_start_date"] == "2025-07-07"  # Monday
            assert context["week_end_date"] == "2025-07-13"  # Sunday
            assert len(context["days"]) == 7

    def test_generate_context_specific_date(self) -> None:
        """Test generating context with specific date."""
        script = AgendaGeneratorScript()

        # Use a specific Wednesday date
        test_date = datetime.date(2025, 7, 9)  # Wednesday
        context = script.generate_context(date=test_date)

        # Should still get the Monday-Sunday week containing the Wednesday
        assert context["week_start_date"] == "2025-07-07"  # Monday of that week
        assert context["week_end_date"] == "2025-07-13"  # Sunday of that week
        assert len(context["days"]) == 7

    def test_generate_context_string_date(self) -> None:
        """Test generating context with date as string."""
        script = AgendaGeneratorScript()

        context = script.generate_context(date="2025-07-09")

        assert context["week_start_date"] == "2025-07-07"
        assert context["week_end_date"] == "2025-07-13"

    def test_generate_context_week_offset_positive(self) -> None:
        """Test generating context with positive week offset."""
        script = AgendaGeneratorScript()

        test_date = datetime.date(2025, 7, 7)  # Monday
        context = script.generate_context(date=test_date, week_offset=1)

        # Should be next week
        assert context["week_start_date"] == "2025-07-14"  # Monday of next week
        assert context["week_end_date"] == "2025-07-20"  # Sunday of next week
        assert context["week_number"] == 29

    def test_generate_context_week_offset_negative(self) -> None:
        """Test generating context with negative week offset."""
        script = AgendaGeneratorScript()

        test_date = datetime.date(2025, 7, 14)  # Monday of week 29
        context = script.generate_context(date=test_date, week_offset=-1)

        # Should be previous week
        assert context["week_start_date"] == "2025-07-07"  # Monday of previous week
        assert context["week_end_date"] == "2025-07-13"  # Sunday of previous week
        assert context["week_number"] == 28

    def test_generate_context_days_structure(self) -> None:
        """Test that days list has correct structure."""
        script = AgendaGeneratorScript()

        test_date = datetime.date(2025, 7, 7)  # Monday
        context = script.generate_context(date=test_date)

        days = context["days"]
        assert len(days) == 7

        # Check first day (Monday)
        monday = days[0]
        assert monday["day_name"] == "Monday"
        assert monday["date"] == "2025-07-07"

        # Check last day (Sunday)
        sunday = days[6]
        assert sunday["day_name"] == "Sunday"
        assert sunday["date"] == "2025-07-13"

        # Check all days have required keys
        for day in days:
            assert "day_name" in day
            assert "date" in day

    def test_generate_context_all_day_names(self) -> None:
        """Test that all day names are correctly generated."""
        script = AgendaGeneratorScript()

        test_date = datetime.date(2025, 7, 7)  # Monday
        context = script.generate_context(date=test_date)

        expected_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        actual_days = [day["day_name"] for day in context["days"]]

        assert actual_days == expected_days

    def test_generate_context_week_number_calculation(self) -> None:
        """Test week number calculation for different dates."""
        script = AgendaGeneratorScript()

        # Test first week of year
        context = script.generate_context(date=datetime.date(2025, 1, 6))  # Week 2
        assert context["week_number"] == 2

        # Test last week of year
        context = script.generate_context(date=datetime.date(2024, 12, 30))  # Week 1 of 2025
        assert context["week_number"] == 1

    def test_generate_context_year_boundary(self) -> None:
        """Test agenda generation across year boundaries."""
        script = AgendaGeneratorScript()

        # Date near year end
        test_date = datetime.date(2024, 12, 30)  # Monday
        context = script.generate_context(date=test_date)

        # Should handle year boundary correctly
        assert context["week_start_date"] == "2024-12-30"
        assert context["week_end_date"] == "2025-01-05"

    def test_generate_context_no_parameters(self) -> None:
        """Test generating context with no parameters uses reasonable defaults."""
        script = AgendaGeneratorScript()

        with patch("printerm.templates.scripts.agenda_generator.datetime") as mock_datetime:
            mock_date = datetime.date(2025, 7, 9)  # Wednesday
            mock_datetime.date.today.return_value = mock_date
            mock_datetime.date.side_effect = datetime.date
            mock_datetime.timedelta = datetime.timedelta

            context = script.generate_context()

            # Should still generate valid context
            assert isinstance(context["week_number"], int)
            assert isinstance(context["week_start_date"], str)
            assert isinstance(context["week_end_date"], str)
            assert isinstance(context["days"], list)
            assert len(context["days"]) == 7

    def test_generate_context_invalid_date_format(self) -> None:
        """Test behavior with invalid date format."""
        script = AgendaGeneratorScript()

        with pytest.raises(ValueError):
            script.generate_context(date="invalid-date")

    def test_generate_context_future_date(self) -> None:
        """Test generating agenda for future dates."""
        script = AgendaGeneratorScript()

        # Far future date
        future_date = datetime.date(2030, 12, 16)  # Monday
        context = script.generate_context(date=future_date)

        assert context["week_start_date"] == "2030-12-16"
        assert context["week_end_date"] == "2030-12-22"
        assert len(context["days"]) == 7

    def test_generate_context_multiple_week_offsets(self) -> None:
        """Test multiple week offsets."""
        script = AgendaGeneratorScript()

        base_date = datetime.date(2025, 7, 7)  # Monday

        # Test various offsets
        for offset in [-5, -2, 0, 3, 10]:
            context = script.generate_context(date=base_date, week_offset=offset)

            expected_start = base_date + datetime.timedelta(weeks=offset)
            # Adjust to Monday of that week
            expected_start = expected_start - datetime.timedelta(days=expected_start.weekday())

            assert context["week_start_date"] == expected_start.strftime("%Y-%m-%d")
            assert len(context["days"]) == 7

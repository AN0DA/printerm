"""Tests for printer service."""

from unittest.mock import MagicMock, patch

import pytest

from printerm.exceptions import ConfigurationError, PrinterError
from printerm.services.printer_service import PrinterServiceImpl


class TestPrinterServiceImpl:
    """Test cases for PrinterServiceImpl."""

    def test_init(self, mock_config_service: MagicMock, mock_template_service: MagicMock) -> None:
        """Test initialization of printer service."""
        service = PrinterServiceImpl(mock_config_service, mock_template_service)

        assert service.config_service == mock_config_service
        assert service.template_service == mock_template_service
        assert service._printer is None

    @patch("printerm.services.printer_service.Network")
    def test_context_manager_enter_success(
        self, mock_network: MagicMock, mock_config_service: MagicMock, mock_template_service: MagicMock
    ) -> None:
        """Test successful context manager entry."""
        mock_config_service.get_printer_ip.return_value = "192.168.1.100"
        mock_printer_instance = MagicMock()
        mock_network.return_value = mock_printer_instance

        service = PrinterServiceImpl(mock_config_service, mock_template_service)

        with service as printer_service:
            assert printer_service._printer == mock_printer_instance
            mock_config_service.get_printer_ip.assert_called_once()
            mock_network.assert_called_once_with("192.168.1.100", timeout=10)

    @patch("printerm.services.printer_service.Network")
    def test_context_manager_enter_config_error(
        self, mock_network: MagicMock, mock_config_service: MagicMock, mock_template_service: MagicMock
    ) -> None:
        """Test context manager entry with configuration error."""
        mock_config_service.get_printer_ip.side_effect = ConfigurationError("IP not set")

        service = PrinterServiceImpl(mock_config_service, mock_template_service)

        with pytest.raises(PrinterError, match="Failed to connect to printer"), service:
            pass

    @patch("printerm.services.printer_service.Network")
    def test_context_manager_enter_network_error(
        self, mock_network: MagicMock, mock_config_service: MagicMock, mock_template_service: MagicMock
    ) -> None:
        """Test context manager entry with network error."""
        mock_config_service.get_printer_ip.return_value = "192.168.1.100"
        mock_network.side_effect = Exception("Connection failed")

        service = PrinterServiceImpl(mock_config_service, mock_template_service)

        with pytest.raises(PrinterError, match="Failed to connect to printer"), service:
            pass

    @patch("printerm.services.printer_service.Network")
    def test_context_manager_exit_success(
        self, mock_network: MagicMock, mock_config_service: MagicMock, mock_template_service: MagicMock
    ) -> None:
        """Test successful context manager exit."""
        mock_config_service.get_printer_ip.return_value = "192.168.1.100"
        mock_printer_instance = MagicMock()
        mock_network.return_value = mock_printer_instance

        service = PrinterServiceImpl(mock_config_service, mock_template_service)

        with service:
            pass

        mock_printer_instance.close.assert_called_once()

    @patch("printerm.services.printer_service.Network")
    def test_context_manager_exit_close_error(
        self, mock_network: MagicMock, mock_config_service: MagicMock, mock_template_service: MagicMock
    ) -> None:
        """Test context manager exit with close error."""
        mock_config_service.get_printer_ip.return_value = "192.168.1.100"
        mock_printer_instance = MagicMock()
        mock_printer_instance.close.side_effect = Exception("Close failed")
        mock_network.return_value = mock_printer_instance

        service = PrinterServiceImpl(mock_config_service, mock_template_service)

        # Should not raise exception even if close fails
        with service:
            pass

        mock_printer_instance.close.assert_called_once()

    def test_print_segments_success(
        self, mock_config_service: MagicMock, mock_template_service: MagicMock, sample_segments: list
    ) -> None:
        """Test successful printing of segments."""
        service = PrinterServiceImpl(mock_config_service, mock_template_service)
        mock_printer = MagicMock()
        service._printer = mock_printer

        service.print_segments(sample_segments)

        # Verify printer methods were called for each segment
        assert mock_printer.set_with_default.call_count == len(sample_segments)
        assert mock_printer.text.call_count == len(sample_segments)

        # Verify final reset call
        mock_printer.set.assert_called_once_with(
            align="left",
            font="a",
            bold=False,
            underline=False,
            invert=False,
            double_width=False,
            double_height=False,
        )

    def test_print_segments_no_printer(
        self, mock_config_service: MagicMock, mock_template_service: MagicMock, sample_segments: list
    ) -> None:
        """Test printing segments without printer connection."""
        service = PrinterServiceImpl(mock_config_service, mock_template_service)

        with pytest.raises(PrinterError, match="Printer connection is not open"):
            service.print_segments(sample_segments)

    def test_print_segments_printer_error(
        self, mock_config_service: MagicMock, mock_template_service: MagicMock, sample_segments: list
    ) -> None:
        """Test printing segments with printer error."""
        service = PrinterServiceImpl(mock_config_service, mock_template_service)
        mock_printer = MagicMock()
        mock_printer.set_with_default.side_effect = Exception("Printer error")
        service._printer = mock_printer

        with pytest.raises(PrinterError, match="Failed to print segments"):
            service.print_segments(sample_segments)

    def test_print_segments_styles(self, mock_config_service: MagicMock, mock_template_service: MagicMock) -> None:
        """Test printing segments with various styles."""
        service = PrinterServiceImpl(mock_config_service, mock_template_service)
        mock_printer = MagicMock()
        service._printer = mock_printer

        segments = [
            {
                "text": "Bold centered text",
                "styles": {
                    "bold": True,
                    "align": "center",
                    "font": "b",
                    "underline": True,
                    "italic": True,
                    "double_width": True,
                    "double_height": True,
                },
            }
        ]

        service.print_segments(segments)

        # Verify styles were applied correctly
        mock_printer.set_with_default.assert_called_with(
            align="center",
            font="b",
            bold=True,
            underline=True,
            invert=True,  # italic maps to invert
            double_width=True,
            double_height=True,
        )

    def test_print_segments_default_styles(
        self, mock_config_service: MagicMock, mock_template_service: MagicMock
    ) -> None:
        """Test printing segments with default styles."""
        service = PrinterServiceImpl(mock_config_service, mock_template_service)
        mock_printer = MagicMock()
        service._printer = mock_printer

        segments = [{"text": "Plain text", "styles": {}}]

        service.print_segments(segments)

        # Verify default styles were applied
        mock_printer.set_with_default.assert_called_with(
            align="left",
            font="a",
            bold=False,
            underline=False,
            invert=False,
            double_width=False,
            double_height=False,
        )

    def test_print_template_success(
        self, mock_config_service: MagicMock, mock_template_service: MagicMock, sample_context: dict
    ) -> None:
        """Test successful template printing."""
        service = PrinterServiceImpl(mock_config_service, mock_template_service)
        mock_printer = MagicMock()
        service._printer = mock_printer

        # Mock template service response
        mock_segments = [{"text": "Rendered text", "styles": {}}]
        mock_template_service.render_template.return_value = mock_segments

        service.print_template("test_template", sample_context)

        # Verify template rendering was called
        mock_template_service.render_template.assert_called_once_with("test_template", sample_context)

        # Verify printing was called
        mock_printer.set_with_default.assert_called_once()
        mock_printer.text.assert_called_once_with("Rendered text")
        mock_printer.cut.assert_called_once()

    def test_print_template_no_printer(
        self, mock_config_service: MagicMock, mock_template_service: MagicMock, sample_context: dict
    ) -> None:
        """Test template printing without printer connection."""
        service = PrinterServiceImpl(mock_config_service, mock_template_service)

        with pytest.raises(PrinterError, match="Printer connection is not open"):
            service.print_template("test_template", sample_context)

    def test_print_template_render_error(
        self, mock_config_service: MagicMock, mock_template_service: MagicMock, sample_context: dict
    ) -> None:
        """Test template printing with render error."""
        service = PrinterServiceImpl(mock_config_service, mock_template_service)
        mock_printer = MagicMock()
        service._printer = mock_printer

        # Mock template service to raise error
        mock_template_service.render_template.side_effect = Exception("Render failed")

        with pytest.raises(PrinterError, match="Failed to print template 'test_template'"):
            service.print_template("test_template", sample_context)

    def test_print_template_printer_error(
        self, mock_config_service: MagicMock, mock_template_service: MagicMock, sample_context: dict
    ) -> None:
        """Test template printing with printer error."""
        service = PrinterServiceImpl(mock_config_service, mock_template_service)
        mock_printer = MagicMock()
        mock_printer.cut.side_effect = Exception("Cut failed")
        service._printer = mock_printer

        # Mock template service response
        mock_segments = [{"text": "Rendered text", "styles": {}}]
        mock_template_service.render_template.return_value = mock_segments

        with pytest.raises(PrinterError, match="Failed to print template 'test_template'"):
            service.print_template("test_template", sample_context)

    def test_print_template_existing_printer_error(
        self, mock_config_service: MagicMock, mock_template_service: MagicMock, sample_context: dict
    ) -> None:
        """Test template printing that propagates existing PrinterError."""
        service = PrinterServiceImpl(mock_config_service, mock_template_service)
        mock_printer = MagicMock()
        service._printer = mock_printer

        # Mock print_segments to raise PrinterError
        with patch.object(service, "print_segments") as mock_print_segments:
            mock_print_segments.side_effect = PrinterError("Original printer error")

            mock_segments = [{"text": "Rendered text", "styles": {}}]
            mock_template_service.render_template.return_value = mock_segments

            with pytest.raises(PrinterError, match="Original printer error"):
                service.print_template("test_template", sample_context)

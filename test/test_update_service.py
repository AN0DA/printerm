"""Tests for update service."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from printerm.exceptions import NetworkError
from printerm.services.update_service import UpdateServiceImpl


class TestUpdateServiceImpl:
    """Test cases for UpdateServiceImpl."""

    def test_init_default_url(self) -> None:
        """Test initialization with default PyPI URL."""
        service = UpdateServiceImpl()
        assert "pypi.org/pypi/printerm/json" in service.pypi_url

    def test_init_custom_url(self) -> None:
        """Test initialization with custom PyPI URL."""
        custom_url = "https://test.pypi.org/pypi/printerm/json"
        service = UpdateServiceImpl(custom_url)
        assert service.pypi_url == custom_url

    @patch("printerm.services.update_service.requests.get")
    def test_get_latest_version_success(self, mock_get: MagicMock, mock_requests_response: MagicMock) -> None:
        """Test successful retrieval of latest version."""
        mock_get.return_value = mock_requests_response

        service = UpdateServiceImpl()
        version = service.get_latest_version()

        assert version == "2.0.0"
        mock_get.assert_called_once_with(service.pypi_url, timeout=10)
        mock_requests_response.json.assert_called_once()

    @patch("printerm.services.update_service.requests.get")
    def test_get_latest_version_http_error(self, mock_get: MagicMock) -> None:
        """Test error when HTTP request fails."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = requests.HTTPError("404 Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        service = UpdateServiceImpl()

        with pytest.raises(NetworkError, match="PyPI returned HTTP 404"):
            service.get_latest_version()

    @patch("printerm.services.update_service.requests.get")
    def test_get_latest_version_request_exception(self, mock_get: MagicMock) -> None:
        """Test error when requests raises exception."""
        mock_get.side_effect = requests.RequestException("Connection error")

        service = UpdateServiceImpl()

        with pytest.raises(NetworkError, match="Error while fetching latest version"):
            service.get_latest_version()

    @patch("printerm.services.update_service.requests.get")
    def test_get_latest_version_timeout(self, mock_get: MagicMock) -> None:
        """Test error when request times out."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        service = UpdateServiceImpl()

        with pytest.raises(NetworkError, match="Request to PyPI timed out"):
            service.get_latest_version()

    @patch("printerm.services.update_service.requests.get")
    def test_get_latest_version_json_error(self, mock_get: MagicMock) -> None:
        """Test error when JSON parsing fails."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        service = UpdateServiceImpl()

        with pytest.raises(NetworkError, match="Invalid response from PyPI"):
            service.get_latest_version()

    @patch("printerm.services.update_service.requests.get")
    def test_get_latest_version_malformed_response(self, mock_get: MagicMock) -> None:
        """Test error when response doesn't have expected structure."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"unexpected": "structure"}
        mock_get.return_value = mock_response

        service = UpdateServiceImpl()

        with pytest.raises(NetworkError, match="Error while fetching latest version"):
            service.get_latest_version()

    @patch.object(UpdateServiceImpl, "get_latest_version")
    def test_is_new_version_available_true(self, mock_get_latest: MagicMock) -> None:
        """Test when newer version is available."""
        mock_get_latest.return_value = "2.0.0"

        service = UpdateServiceImpl()
        is_new = service.is_new_version_available("1.5.0")

        assert is_new is True
        mock_get_latest.assert_called_once()

    @patch.object(UpdateServiceImpl, "get_latest_version")
    def test_is_new_version_available_false_same_version(self, mock_get_latest: MagicMock) -> None:
        """Test when current version is the same as latest."""
        mock_get_latest.return_value = "2.0.0"

        service = UpdateServiceImpl()
        is_new = service.is_new_version_available("2.0.0")

        assert is_new is False
        mock_get_latest.assert_called_once()

    @patch.object(UpdateServiceImpl, "get_latest_version")
    def test_is_new_version_available_false_newer_current(self, mock_get_latest: MagicMock) -> None:
        """Test when current version is newer than latest."""
        mock_get_latest.return_value = "2.0.0"

        service = UpdateServiceImpl()
        is_new = service.is_new_version_available("2.1.0")

        assert is_new is False
        mock_get_latest.assert_called_once()

    @patch.object(UpdateServiceImpl, "get_latest_version")
    def test_is_new_version_available_error_handling(self, mock_get_latest: MagicMock) -> None:
        """Test error handling in version check."""
        mock_get_latest.side_effect = NetworkError("Network error")

        service = UpdateServiceImpl()
        is_new = service.is_new_version_available("1.5.0")

        # Should return False on error and not raise exception
        assert is_new is False
        mock_get_latest.assert_called_once()

    @patch.object(UpdateServiceImpl, "get_latest_version")
    def test_is_new_version_available_invalid_version_format(self, mock_get_latest: MagicMock) -> None:
        """Test error handling with invalid version format."""
        mock_get_latest.return_value = "invalid.version.format"

        service = UpdateServiceImpl()
        is_new = service.is_new_version_available("1.5.0")

        # Should return False on version parsing error
        assert is_new is False
        mock_get_latest.assert_called_once()

    @patch.object(UpdateServiceImpl, "get_latest_version")
    def test_is_new_version_available_complex_versions(self, mock_get_latest: MagicMock) -> None:
        """Test version comparison with complex version numbers."""
        mock_get_latest.return_value = "2.1.0"

        service = UpdateServiceImpl()

        # Test various version comparisons
        assert service.is_new_version_available("2.0.9") is True
        assert service.is_new_version_available("2.1.0") is False
        assert service.is_new_version_available("2.1.1") is False

    @patch.object(UpdateServiceImpl, "get_latest_version")
    def test_is_new_version_available_prerelease_versions(self, mock_get_latest: MagicMock) -> None:
        """Test version comparison with pre-release versions."""
        mock_get_latest.return_value = "2.0.0"

        service = UpdateServiceImpl()

        # Test pre-release version comparison
        assert service.is_new_version_available("2.0.0a1") is True
        assert service.is_new_version_available("2.0.0rc1") is True
        assert service.is_new_version_available("1.9.9") is True

    @patch("printerm.services.update_service.requests.get")
    def test_get_latest_version_custom_timeout(self, mock_get: MagicMock, mock_requests_response: MagicMock) -> None:
        """Test that request uses correct timeout."""
        mock_get.return_value = mock_requests_response

        service = UpdateServiceImpl()
        service.get_latest_version()

        # Verify timeout parameter
        mock_get.assert_called_once_with(service.pypi_url, timeout=10)

    @patch("printerm.services.update_service.requests.get")
    def test_get_latest_version_response_structure(self, mock_get: MagicMock) -> None:
        """Test that service correctly parses PyPI JSON response structure."""
        # Mock realistic PyPI response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {"version": "1.2.3", "author": "Test Author", "description": "Test package"},
            "releases": {},
            "urls": [],
        }
        mock_get.return_value = mock_response

        service = UpdateServiceImpl()
        version = service.get_latest_version()

        assert version == "1.2.3"

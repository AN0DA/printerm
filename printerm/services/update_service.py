"""Update service implementation."""

import logging

import requests
from packaging import version

from printerm.exceptions import NetworkError

logger = logging.getLogger(__name__)


class UpdateServiceImpl:
    """Update service implementation."""

    def __init__(self, pypi_url: str = "https://pypi.org/pypi/printerm/json") -> None:
        self.pypi_url = pypi_url

    def get_latest_version(self) -> str:
        """Get the latest version of printerm from PyPI."""
        try:
            response = requests.get(self.pypi_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data["info"]["version"]
            else:
                raise NetworkError(f"Failed to fetch latest version: HTTP {response.status_code}")
        except requests.RequestException as e:
            raise NetworkError("Failed to fetch latest version from PyPI", str(e)) from e
        except Exception as e:
            raise NetworkError("Error while fetching latest version", str(e)) from e

    def is_new_version_available(self, current_version: str) -> bool:
        """Check if a newer version is available on PyPI."""
        try:
            latest_version = self.get_latest_version()
            return version.parse(latest_version) > version.parse(current_version)
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False

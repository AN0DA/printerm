"""Update service implementation."""

import logging
import time

import requests
from packaging import version

from printerm.exceptions import NetworkError

logger = logging.getLogger(__name__)


class UpdateServiceImpl:
    """Update service implementation."""

    def __init__(self, pypi_url: str = "https://pypi.org/pypi/printerm/json", cache_ttl: int = 3600) -> None:
        self.pypi_url = pypi_url
        self.cache_ttl = cache_ttl  # Cache TTL in seconds (default 1 hour)
        self._cache: dict | None = None
        self._cache_time: float = 0

    def _get_cached_version(self) -> str | None:
        """Get cached version if still valid."""
        if self._cache and (time.time() - self._cache_time) < self.cache_ttl:
            return self._cache.get("version")
        return None

    def _set_cached_version(self, version: str) -> None:
        """Cache the version with current timestamp."""
        self._cache = {"version": version}
        self._cache_time = time.time()

    def get_latest_version(self) -> str:
        """Get the latest version of printerm from PyPI."""
        # Check cache first
        cached_version = self._get_cached_version()
        if cached_version:
            logger.debug(f"Using cached version: {cached_version}")
            return cached_version

        logger.info(f"Fetching latest version from PyPI: {self.pypi_url}")
        try:
            response = requests.get(self.pypi_url, timeout=10)
            response.raise_for_status()  # Raise exception for bad status codes

            data = response.json()
            if "info" not in data or "version" not in data["info"]:
                raise NetworkError("Invalid response format from PyPI")

            latest_version = data["info"]["version"]
            logger.info(f"Latest version from PyPI: {latest_version}")

            # Cache the result
            self._set_cached_version(latest_version)
            return latest_version

        except requests.Timeout:
            logger.error("Request to PyPI timed out")
            raise NetworkError("Request to PyPI timed out") from None
        except requests.ConnectionError:
            logger.error("Connection error when fetching from PyPI")
            raise NetworkError("Unable to connect to PyPI") from None
        except requests.HTTPError as e:
            logger.error(f"HTTP error when fetching from PyPI: {e}")
            status_code = getattr(e.response, "status_code", "unknown") if e.response else "unknown"
            raise NetworkError(f"PyPI returned HTTP {status_code}") from e
        except ValueError as e:
            logger.error(f"Invalid JSON response from PyPI: {e}")
            raise NetworkError("Invalid response from PyPI") from e
        except Exception as e:
            logger.error(f"Unexpected error fetching version: {e}")
            raise NetworkError("Error while fetching latest version") from e

    def is_new_version_available(self, current_version: str) -> bool:
        """Check if a newer version is available on PyPI."""
        try:
            latest_version = self.get_latest_version()
            is_newer = version.parse(latest_version) > version.parse(current_version)
            if is_newer:
                logger.info(f"New version available: {latest_version} (current: {current_version})")
            else:
                logger.debug(f"No update available. Latest: {latest_version}, Current: {current_version}")
            return is_newer
        except Exception as e:
            logger.warning(f"Failed to check for updates: {e}")
            return False

    def check_for_updates_with_retry(self, current_version: str, max_retries: int = 2) -> bool:
        """Check for updates with retry logic for network failures."""
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                return self.is_new_version_available(current_version)
            except NetworkError as e:
                last_error = e
                if attempt < max_retries:
                    logger.info(f"Update check failed (attempt {attempt + 1}/{max_retries + 1}), retrying: {e}")
                    # Clear cache to force fresh request on retry
                    self.clear_cache()
        # If we get here, all attempts failed
        logger.error(f"Update check failed after {max_retries + 1} attempts: {last_error}")
        return False

    def clear_cache(self) -> None:
        """Clear the version cache."""
        self._cache = None
        self._cache_time = 0

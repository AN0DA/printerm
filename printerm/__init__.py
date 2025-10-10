"""Printerm thermal printer application."""

import tomllib
from pathlib import Path

# Read version from pyproject.toml
_pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
try:
    with _pyproject_path.open("rb") as f:
        _pyproject_data = tomllib.load(f)
    __version__ = _pyproject_data["project"]["version"]
except (FileNotFoundError, KeyError, ValueError):
    # Fallback version if pyproject.toml can't be read
    __version__ = "0.0.0-dev"

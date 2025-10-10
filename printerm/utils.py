"""Utility functions for the printerm application."""

import os
import sys


def is_running_via_pipx() -> bool:
    """Check if the application is running via pipx."""
    # Check if PIPX_HOME environment variable is set
    if os.environ.get("PIPX_HOME"):
        return True

    # Check if executable name is 'pipx' or 'pipx.exe'
    exe_basename = os.path.basename(sys.executable)
    if exe_basename in ("pipx", "pipx.exe"):
        return True

    # Check if we're in a pipx venv directory structure
    pipx_home = os.path.expanduser("~/.local/pipx")
    try:
        # Use commonpath to check if executable is under pipx_home
        common = os.path.commonpath([os.path.normpath(sys.executable), os.path.normpath(pipx_home)])
        if common == os.path.normpath(pipx_home):
            return True
    except ValueError:
        # commonpath raises ValueError if paths have no common prefix
        pass

    return False

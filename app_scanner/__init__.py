# src/app_scanner/__init__.py

"""
A cross-platform utility to find installed applications.
"""

import sys
from typing import List, Dict

# Import platform-specific implementations
from . import _linux
from . import _macos
from . import _windows

__version__ = "0.1.0"

def get_installed_apps() -> List[Dict[str, str]]:
    """
    Gets a list of installed applications based on the current operating system.

    Each application is represented by a dictionary containing at least a 'name' key.
    The dictionary may also contain a 'path' or 'appid' key depending on the OS.

    :return: A list of application dictionaries.
    """
    platform = sys.platform

    if platform == "win32":
        return _windows.get_apps()
    elif platform == "darwin":  # macOS
        return _macos.get_apps()
    elif platform.startswith("linux"):
        return _linux.get_apps()
    else:
        # Return an empty list for unsupported platforms
        return []

__all__ = ["get_installed_apps"]

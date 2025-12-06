# src/app_scanner/_macos.py

import logging
import os
import platform
import plistlib
import subprocess
from typing import List, Dict, Optional, Set

# Default directories where .app bundles are usually located
DEFAULT_APP_DIRS = [
    "/Applications",
    "/Applications/Utilities",
    "/System/Applications",
    "/System/Library/CoreServices",
    os.path.expanduser("~/Applications"),
]


def _is_macos() -> bool:
    return platform.system() == "Darwin"


def _read_info_plist(app_path: str) -> Dict[str, Optional[str]]:
    """
    Reads Info.plist inside an .app bundle and extracts useful metadata.
    """
    info = {"name": None, "bundle_id": None, "version": None, "executable": None, "icon": None}
    try:
        plist_path = os.path.join(app_path, "Contents", "Info.plist")
        with open(plist_path, "rb") as f:
            data = plistlib.load(f)
        info["name"] = data.get("CFBundleDisplayName") or data.get("CFBundleName") or os.path.splitext(os.path.basename(app_path))[0]
        info["bundle_id"] = data.get("CFBundleIdentifier")
        info["version"] = data.get("CFBundleShortVersionString") or data.get("CFBundleVersion")
        info["executable"] = data.get("CFBundleExecutable")
        icon = data.get("CFBundleIconFile")
        if icon:
            if not icon.lower().endswith(".icns"):
                icon += ".icns"
            candidate = os.path.join(app_path, "Contents", "Resources", icon)
            if os.path.exists(candidate):
                info["icon"] = candidate
            else:
                info["icon"] = icon
    except FileNotFoundError:
        logging.debug(f"No Info.plist at {app_path}")
    except Exception as e:
        logging.warning(f"Failed to read Info.plist for {app_path}: {e}")
    return info


def _scan_dirs_for_apps(dirs: List[str]) -> List[str]:
    """
    Recursively scans given directories for .app bundles.
    """
    found = []
    for base in dirs:
        if not os.path.exists(base):
            continue
        for root, dirnames, _ in os.walk(base):
            for d in list(dirnames):
                if d.endswith(".app"):
                    full = os.path.join(root, d)
                    found.append(full)
                    dirnames.remove(d)  # prevent descending into .app bundle
    return found


def _spotlight_find_apps() -> List[str]:
    """
    Uses Spotlight (mdfind) to locate .app bundles.
    """
    try:
        cmd = ["mdfind", "kMDItemContentType == 'com.apple.application-bundle'"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        paths = [p for p in result.stdout.splitlines() if p.strip() and p.endswith(".app")]
        return paths
    except FileNotFoundError:
        logging.debug("'mdfind' not found on system")
        return []
    except subprocess.CalledProcessError as e:
        logging.warning(f"mdfind failed: {e}")
        return []
    except Exception as e:
        logging.warning(f"Unexpected error while running mdfind: {e}")
        return []


def get_apps(use_spotlight: bool = True, extra_dirs: Optional[List[str]] = None) -> List[Dict[str, Optional[str]]]:
    """
    Scans for installed macOS applications.

    :param use_spotlight: Whether to use Spotlight (mdfind) for scanning.
    :param extra_dirs: Additional directories to scan manually.
    :return: A list of dictionaries with application metadata:
             - name: application name
             - path: full path to .app bundle
             - bundle_id: CFBundleIdentifier
             - version: CFBundleShortVersionString / CFBundleVersion
             - executable: CFBundleExecutable
             - icon: path to .icns file if found
             - source: 'spotlight' or 'scan'
    """
    apps = []
    if not _is_macos():
        logging.warning("Not running on macOS — get_apps will return an empty list.")
        return apps

    discovered: List[str] = []
    seen: Set[str] = set()

    # 1) Spotlight
    spotlight_paths = []
    if use_spotlight:
        spotlight_paths = _spotlight_find_apps()
        discovered.extend(spotlight_paths)

    # 2) Manual scan
    dirs_to_scan = DEFAULT_APP_DIRS.copy()
    if extra_dirs:
        dirs_to_scan = extra_dirs + dirs_to_scan
    scanned = _scan_dirs_for_apps(dirs_to_scan)
    discovered.extend(scanned)

    # Deduplicate and enrich with metadata
    for path in discovered:
        norm = os.path.normpath(path)
        if norm in seen:
            continue
        seen.add(norm)
        meta = _read_info_plist(norm)
        app_entry = {
            "name": meta.get("name") or os.path.splitext(os.path.basename(norm))[0],
            "path": norm,
            "bundle_id": meta.get("bundle_id"),
            "version": meta.get("version"),
            "executable": meta.get("executable"),
            "icon": meta.get("icon"),
            "source": "spotlight" if norm in spotlight_paths else "scan"
        }
        apps.append(app_entry)

    apps.sort(key=lambda x: (x["name"] or "").lower())
    return apps
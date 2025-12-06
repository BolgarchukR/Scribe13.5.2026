# src/app_scanner/_windows.py

import base64
import json
import logging
import os
import subprocess
import sys
from typing import List, Dict

# Cache configuration
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "app-scanner")
CACHE_FILE = os.path.join(CACHE_DIR, "app_cache_windows.json")

def _get_powershell_command() -> str:
    """Returns the appropriate PowerShell command based on the Windows version."""
    if sys.platform != 'win32':
        return ""

    # Get-StartApps is available on Windows 8.1 and newer.
    # For Windows 8.0, a fallback to Get-AppxPackage is needed.
    win_ver = sys.getwindowsversion()
    if win_ver.major == 6 and win_ver.minor == 2: # Windows 8.0
        logging.info("Running on Windows 8.0, using Get-AppxPackage.")
        return """
            Get-AppxPackage | ForEach-Object {
                if ($_.InstallLocation -and (Get-AppxPackageManifest $_).Package.Applications.Application.Id) {
                    $name = $_.Name;
                    $appId = ($_.PackageFamilyName + "!" + (Get-AppxPackageManifest $_).Package.Applications.Application.Id);
                    $nameBase64 = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($name));
                    $idBase64 = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($appId));
                    Write-Output "$($nameBase64)`t$($idBase64)";
                }
            }
        """
    else: # Windows 8.1 or newer
        logging.info("Running on Windows 8.1 or newer, using Get-StartApps.")
        return """
            Get-StartApps | ForEach-Object {
                $name = $_.Name -replace "`t", " ";
                $id = $_.AppID;
                if ($name -and $id) {
                    $nameBase64 = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($name));
                    $idBase64 = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($id));
                    Write-Output "$($nameBase64)`t$($idBase64)"
                }
            }
        """

def _scan_and_cache() -> List[Dict[str, str]]:
    """
    Executes the PowerShell command, parses the output, and saves it to a cache file.
    """
    command = _get_powershell_command()
    if not command:
        logging.warning("Application scanning is only supported on Windows.")
        return []

    apps_data = []
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        process = subprocess.Popen(
            ['powershell', '-ExecutionPolicy', 'Bypass', '-NoProfile', '-Command', command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        stdout_bytes, stderr_bytes = process.communicate(timeout=60)
        stdout = stdout_bytes.decode('utf-8', errors='ignore')
        stderr = stderr_bytes.decode('utf-8', errors='ignore')

        if process.returncode != 0:
            logging.error(f"PowerShell command failed with code {process.returncode}: {stderr}")
            return []

        if stdout and stdout.strip():
            for line in stdout.strip().splitlines():
                if not line.strip():
                    continue
                parts = line.strip().split('\t', 1)
                if len(parts) == 2:
                    try:
                        name_b64, appid_b64 = parts
                        name = base64.b64decode(name_b64).decode('utf-8')
                        appid = base64.b64decode(appid_b64).decode('utf-8')
                        apps_data.append({"name": name, "appid": appid})
                    except Exception as e:
                        logging.warning(f"Skipping malformed line: {line}. Error: {e}")
        
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(apps_data, f, indent=4)
        logging.info(f"Successfully cached {len(apps_data)} applications to {CACHE_FILE}")

    except subprocess.TimeoutExpired:
        logging.error("PowerShell command timed out after 60 seconds.")
    except Exception as e:
        logging.error(f"An error occurred during the scan and cache process: {e}")
    
    return apps_data

def _load_from_cache() -> List[Dict[str, str]]:
    """Loads the list of applications from the cache file."""
    if not os.path.exists(CACHE_FILE):
        return []
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return []

def get_apps(use_cache: bool = True) -> List[Dict[str, str]]:
    """
    Returns the list of installed applications on Windows.

    :param use_cache: If True, returns cached results if available. Otherwise, forces a rescan.
    :return: A list of application dictionaries with 'name' and 'appid' keys.
    """
    if use_cache:
        cached_apps = _load_from_cache()
        if cached_apps:
            logging.info(f"Loaded {len(cached_apps)} apps from cache.")
            return cached_apps
    
    return _scan_and_cache()

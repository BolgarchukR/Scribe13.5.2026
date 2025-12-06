# src/app_scanner/_linux.py

import logging
import os
import shlex
from typing import List, Dict

def _parse_desktop_file(filepath: str) -> Dict[str, str]:
    """
    Parses a .desktop file to extract GUI application information.
    Filters for applications with graphical interfaces.
    """
    app_info: Dict[str, str] = {}
    # Track fields to decide after parsing the section
    type_val = None
    terminal_val = None
    nodisplay_val = None
    hidden_val = None
    is_variant = False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            in_desktop_entry = False
            for raw_line in f:
                line = raw_line.strip()
                if line == '[Desktop Entry]':
                    in_desktop_entry = True
                    continue
                # Stop parsing when leaving the [Desktop Entry] section
                if line.startswith('[') and line != '[Desktop Entry]':
                    if in_desktop_entry:
                        break
                    else:
                        continue

                if not in_desktop_entry:
                    continue

                if '=' not in line:
                    continue

                key, value = line.split('=', 1)

                # Capture raw gating fields to evaluate after parse
                if key == 'Type':
                    type_val = value
                    continue
                if key == 'Terminal':
                    terminal_val = value.lower()
                    continue
                if key == 'NoDisplay':
                    nodisplay_val = value.lower()
                    continue
                if key == 'Hidden':
                    hidden_val = value.lower()
                    continue

                if key == 'Name':
                    # Tag specialized launcher names that are not the main app
                    skip_patterns = [
                        'profile manager', 'new window', 'new empty window',
                        'private browsing', 'incognito', 'safe mode'
                    ]
                    name_lower = value.lower()
                    if any(pattern in name_lower for pattern in skip_patterns):
                        is_variant = True
                    app_info['name'] = value
                elif key == 'Exec':
                    # Robustly extract the main command using shlex (handles quotes)
                    try:
                        parts = shlex.split(value)
                    except Exception:
                        parts = value.split()
                    # Drop field codes like %U, %u, %F, %f etc if they appear as separate tokens
                    parts = [p for p in parts if not p.startswith('%')]

                    # Skip 'env' and any VAR=value assignments
                    i = 0
                    if i < len(parts) and parts[i] == 'env':
                        i += 1
                        while i < len(parts) and '=' in parts[i]:
                            i += 1

                    # Handle shell wrappers like "bash -c 'actual command...'"
                    if i < len(parts) and parts[i] in ('sh', 'bash'):
                        if i + 1 < len(parts) and parts[i + 1] == '-c' and i + 2 < len(parts):
                            try:
                                nested = shlex.split(parts[i + 2])
                            except Exception:
                                nested = parts[i + 2].split()
                            # Replace parts with the nested command + remaining
                            parts = nested + parts[i + 3:]
                            i = 0

                    # Detect gtk-launch (uses desktop-id rather than a direct binary)
                    if i < len(parts) and parts[i] == 'gtk-launch':
                        if i + 1 < len(parts):
                            desktop_id = parts[i + 1]
                            app_info['package'] = f'gtk-launch:{desktop_id}'
                            # Use package key as path surrogate for de-dup and identification
                            app_info['path'] = app_info['package']
                    # Detect flatpak run <appid>
                    elif i < len(parts) and (parts[i].endswith('/flatpak') or parts[i] == 'flatpak'):
                        j = i + 1
                        appid = None
                        while j < len(parts):
                            if parts[j] == 'run' and j + 1 < len(parts):
                                appid = parts[j + 1]
                                break
                            j += 1
                        if appid:
                            app_info['path'] = f'flatpak:{appid}'
                            app_info['package'] = f'flatpak:{appid}'
                        else:
                            app_info['path'] = parts[i]
                    # Detect snap run <appname> or /usr/bin/snap run <appname>
                    elif i < len(parts) and (parts[i].endswith('/snap') or parts[i] == 'snap'):
                        j = i + 1
                        appname = None
                        if j < len(parts) and parts[j] == 'run' and j + 1 < len(parts):
                            appname = parts[j + 1]
                        elif j < len(parts):
                            appname = parts[j]
                        if appname:
                            app_info['path'] = f'/snap/bin/{appname}'
                            app_info['package'] = f'snap:{appname}'
                        else:
                            app_info['path'] = parts[i]
                    else:
                        # Regular command (first non-wrapper token)
                        if i < len(parts):
                            app_info['path'] = parts[i]
                            # Normalize bare commands that are snap shims in /snap/bin
                            cmd = app_info['path']
                            base = os.path.basename(cmd)
                            if '/' not in cmd and os.path.exists(os.path.join('/snap/bin', base)):
                                app_info['path'] = os.path.join('/snap/bin', base)
                                app_info['package'] = f'snap:{base}'
                            # Filter out known non-GUI helper commands that may have .desktop files
                            blocklist = {'xdg-open', 'canberra-gtk-play', 'vboxclient-all', 'vboxclient'}
                            if base.lower() in blocklist:
                                return {}
                elif key == 'Icon':
                    app_info['icon'] = value
                elif key == 'Categories':
                    app_info['categories'] = value
                elif key == 'Comment' or key == 'GenericName':
                    if 'description' not in app_info:
                        app_info['description'] = value
                elif key == 'StartupWMClass':
                    app_info['wm_class'] = value

        # Attach desktop id for diagnostics and better grouping
        desktop_basename = os.path.basename(filepath)
        if desktop_basename.endswith('.desktop'):
            app_info['desktop_id'] = desktop_basename[:-8]

        # Evaluate gating conditions after parsing
        if type_val is not None and type_val != 'Application':
            return {}
        if terminal_val == 'true':
            return {}
        if nodisplay_val == 'true':
            return {}
        if hidden_val == 'true':
            return {}

        if 'name' in app_info and 'path' in app_info:
            if is_variant:
                app_info['variant'] = True
            return app_info

    except Exception as e:
        logging.warning(f"Could not parse {filepath}: {e}")

    return {}

def get_apps() -> List[Dict[str, str]]:
    """
    Scans for .desktop files in standard directories on Linux.

    :return: A list of application dictionaries with 'name' and 'path' keys.
    """
    apps = []
    # Use a dictionary to prevent duplicate applications based on name
    # (e.g., if a user has a local override of a system-wide .desktop file)
    app_map = {}

    search_paths = [
        "/usr/share/applications",
        "/usr/local/share/applications",
        os.path.expanduser("~/.local/share/applications"),
        # Snap applications
        "/var/lib/snapd/desktop/applications",
        "/snap",
        # Flatpak applications
        "/var/lib/flatpak/exports/share/applications",
        os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
        # AppImage and other portable apps
        os.path.expanduser("~/Applications"),
        "/opt",
        "/usr/local/opt",
        # NixOS
        "/run/current-system/sw/share/applications",
        os.path.expanduser("~/.nix-profile/share/applications"),
        # Guix
        "/run/current-system/profile/share/applications",
        os.path.expanduser("~/.guix-profile/share/applications"),
        # KDE specific
        "/usr/share/applications/kde4",
        "/usr/share/applications/kde5",
        # GNOME specific
        "/usr/share/applications/gnome",
    ]
    
    logging.info(f"Scanning for .desktop files in: {search_paths}")

    for path in search_paths:
        if not os.path.isdir(path):
            continue
        try:
            # Recursively walk all directories to ensure we don't miss nested .desktop files
            for root, _dirs, files in os.walk(path):
                for filename in files:
                    if filename.endswith(".desktop"):
                        filepath = os.path.join(root, filename)
                        app_info = _parse_desktop_file(filepath)
                        if app_info:
                            # Use the app name as the key to avoid duplicates by name
                            app_map[app_info['name']] = app_info
        except OSError as e:
            logging.error(f"Could not read directory {path}: {e}")

    # Filter out specialized launchers and prefer main applications
    filtered_apps = []
    seen_names = set()
    
    # Build groups using a canonical key to avoid collapsing Snap/Flatpak apps under /usr/bin/snap or flatpak
    groups = {}
    for app in app_map.values():
        raw_path = app.get('path', '') or ''
        package = app.get('package', '')
        # Derive canonical key
        if package:
            key = package  # e.g., snap:firefox, flatpak:org.mozilla.firefox, gtk-launch:firefox_firefox
        else:
            # Normalize common cases
            if raw_path.startswith('/snap/bin/'):
                key = f"snap:{os.path.basename(raw_path)}"
            elif raw_path.startswith('flatpak:'):
                key = raw_path
            else:
                key = os.path.basename(raw_path) if raw_path else ''
        if not key:
            continue
        groups.setdefault(key, []).append(app)
    
    # Choose the best representative per group
    for key, apps_list in groups.items():
        if len(apps_list) == 1:
            best_app = apps_list[0]
        else:
            # Prefer non-variant entries, then those with Categories/Icon, then shortest name
            def has_meta(a: Dict[str, str]) -> int:
                return 1 if ('categories' in a or 'icon' in a) else 0
            best_app = sorted(
                apps_list,
                key=lambda a: (1 if a.get('variant', False) else 0, -has_meta(a), len(a.get('name', ''))),
            )[0]
        name = best_app['name']
        if name not in seen_names:
            filtered_apps.append(best_app)
            seen_names.add(name)
    
    # Improve naming for common applications
    for app in filtered_apps:
        path_lower = (app.get('path') or '').lower()
        name = app['name']
        package = (app.get('package') or '').lower()
        base = os.path.basename(path_lower)
        
        if 'firefox' in path_lower or 'snap:firefox' in package or 'org.mozilla.firefox' in package or base == 'firefox':
            app['name'] = 'Firefox'
        elif ('code' in path_lower or 'snap:code' in package or 'com.visualstudio.code' in package or base == 'code'):
            app['name'] = 'Visual Studio Code'
        elif base == 'nautilus' or 'nautilus' in path_lower:
            app['name'] = 'Files'
        elif 'snap-store' in path_lower or 'snap:snap-store' in package or base == 'snap-store':
            app['name'] = 'App Center'
        elif 'google-chrome' in path_lower or 'chrome' in path_lower:
            app['name'] = 'Google Chrome'
        elif 'chromium' in path_lower:
            app['name'] = 'Chromium'
        elif 'libreoffice' in path_lower:
            app['name'] = 'LibreOffice'
        elif 'gimp' in path_lower:
            app['name'] = 'GIMP'
        elif 'inkscape' in path_lower:
            app['name'] = 'Inkscape'
        elif 'vlc' in path_lower:
            app['name'] = 'VLC Media Player'
    
    logging.info(f"Found {len(filtered_apps)} unique GUI applications on Linux.")
    return filtered_apps

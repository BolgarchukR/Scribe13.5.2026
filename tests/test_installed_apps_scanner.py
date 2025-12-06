import sys
import os

try:
    # Add parent directory to path to allow importing scribe modules if run from tests/
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    from app_scanner import get_installed_apps
    print("Successfully imported 'app_scanner'.")
    print("Attempting to get installed apps...")
    apps = get_installed_apps()
    print(f"Found {len(apps)} installed applications.")
    if apps:
        print("First 5 apps:")
        for app in apps[:5]:
            print(f"  - Name: {app.get('name')}, Path/AppID: {app.get('path') or app.get('appid')}")
    else:
        print("No applications found or scanner returned an empty list.")
except ModuleNotFoundError as e:
    print(f"ERROR: ModuleNotFoundError: {e}")
    print("'installed_apps_scanner' module could not be found. Please ensure it is installed in your virtual environment.")
    print(f"Current sys.path: {sys.path}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()
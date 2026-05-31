"""Entry point for development: launches the main Scribe application."""
import os
import sys

# Check if running under Wayland and set QT_QPA_PLATFORM accordingly
if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    #os.environ['QT_QPA_PLATFORM'] = 'wayland'
    print("Not work under Wayland yet.")
    exit(1)

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from scribe.app_initializer import initialize_app
from scribe.application import Application
from scribe.logging_config import setup_logging
from scribe.ui.styles import DEFAULT_APP_STYLE
from scribe.utils import get_app_data_path, get_models_path, resource_path, is_frozen

if __name__ == '__main__':
    # Set AppUserModelID for correct icon display in the Windows taskbar
    if sys.platform == 'win32':
        import ctypes
        myappid = 'Scribe.1' # any unique ID
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # Create QApplication before any Qt widgets!
    qt_app = QApplication(sys.argv)
    qt_app.setWindowIcon(QIcon(resource_path('resources/icon.ico')))

    # Load and apply global styles
    qt_app.setStyleSheet(DEFAULT_APP_STYLE)
    
    # Debug: write detection info to a file next to executable (portable)
    exe_dir = os.path.dirname(sys.executable) if hasattr(sys, 'executable') else os.path.abspath(".")
    debug_info = [
        f"sys.executable = {sys.executable}",
        f"sys.frozen = {getattr(sys, 'frozen', False)}",
        f"has _MEIPASS = {hasattr(sys, '_MEIPASS')}",
        f"exe_dir = {exe_dir}",
        f"_internal exists = {os.path.exists(os.path.join(exe_dir, '_internal'))}",
        f"is_frozen() = {is_frozen()}",
    ]
    debug_path = os.path.join(exe_dir, 'debug_frozen.txt')
    try:
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(debug_info) + '\n')
    except Exception:
        pass  # ignore if cannot write
    
    # Centralized initialization: settings, language, translations, model path, etc.
    if is_frozen():
        # Running as compiled executable — use folder next to exe for all data
        app_data_path = exe_dir
    else:
        # Development mode — use standard app data path
        app_data_path = get_app_data_path()
    
    settings_path = os.path.join(app_data_path, 'settings.json')
    models_dir = get_models_path()
    
    settings_manager, settings, ui_lang, texts, recognition_language, model_path = initialize_app(settings_path, models_dir)
    
    # Setup logging with log_to_file and log_level parameters from settings
    log_file_path = "app.log"
    if is_frozen():
        # When running as frozen executable, place log file next to the executable
        log_file_path = os.path.join(app_data_path, log_file_path)
    setup_logging(
        log_to_file=settings.get('log_to_file', False),
        log_file_path=log_file_path,
        log_level=settings.get('log_level', 'INFO')
    )
    
    # Log the paths for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Frozen mode: {is_frozen()}")
    logger.info(f"App data path: {app_data_path}")
    logger.info(f"Settings path: {settings_path}")
    logger.info(f"Models dir: {models_dir}")
    logger.info(f"Loaded language: {recognition_language}")
    logger.info(f"Model path: {model_path}")
    
    # Create and run the main application object
    app = Application(settings_manager, settings, ui_lang, texts, recognition_language, model_path)
    app.run()

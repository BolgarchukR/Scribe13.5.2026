# hotkey_manager.py
import logging
import platform

from pynput import keyboard
from PyQt5.QtCore import QObject

logger = logging.getLogger(__name__)

class HotkeyManager(QObject):
    """Manages global hotkeys for the application using pynput."""

    def __init__(self, settings_manager, controller):
        super().__init__()
        self.settings_manager = settings_manager
        self.controller = controller
        self.listener = None
        self._last_registered_hotkeys = {}
        self.register_hotkeys()
        self.settings_manager.settings_changed.connect(self.on_settings_changed)

    def on_settings_changed(self, new_settings):
        """Re-registers hotkeys if they have changed in the settings."""
        new_modes = new_settings.get('modes', self.settings_manager.DEFAULTS['modes'])
        new_models_hotkeys = new_settings.get('models_hotkeys', self.settings_manager.DEFAULTS['models_hotkeys'])

        last_modes = self._last_registered_hotkeys.get('modes', {})
        last_models_hotkeys = self._last_registered_hotkeys.get('models_hotkeys', {})

        if new_modes != last_modes or new_models_hotkeys != last_models_hotkeys:
            logger.info("Hotkey settings changed, re-registering...")
            self.register_hotkeys()

    def _to_pynput_format(self, key_str: str):
        """Converts a hotkey string like 'Ctrl+Shift+Q' to pynput format '<ctrl>+<shift>+q'."""
        if not key_str:
            return None

        keys = key_str.lower().split('+')
        formatted_keys = []

        key_map = {
            'ctrl': 'ctrl',
            'alt': 'alt',
            'shift': 'shift',
            'cmd': 'cmd',
            'win': 'cmd',
            'super': 'cmd'
        }

        for key in keys:
            key = key.strip()
            if key in key_map:
                formatted_keys.append(f"<{key_map[key]}>")
            else:
                formatted_keys.append(key)

        return "+".join(formatted_keys)

    def register_hotkeys(self):
        """Stops the old listener and registers new hotkeys from settings."""
        self.stop()

        hotkey_map = {}

        # Mode hotkeys
        modes = self.settings_manager.get('modes', {})
        transcribe_hotkey = modes.get('transcribe_mode', 'Ctrl+Shift+Q')
        command_hotkey = modes.get('command_mode', 'Ctrl+Alt+Q')

        pynput_transcribe = self._to_pynput_format(transcribe_hotkey)
        if pynput_transcribe:
            hotkey_map[pynput_transcribe] = self.controller.switch_to_transcribe_mode
            logger.info(f"Press {transcribe_hotkey} for transcription mode.")

        pynput_command = self._to_pynput_format(command_hotkey)
        if pynput_command:
            hotkey_map[pynput_command] = self.controller.switch_to_command_mode
            logger.info(f"Press {command_hotkey} for command mode.")

        # Model switching hotkeys
        models_dict = self.settings_manager.get('models', {})
        models_hotkeys = self.settings_manager.get('models_hotkeys', {})
        model_names = set()
        for lang_models in models_dict.values():
            for model in lang_models:
                name = model.get('name')
                if name:
                    model_names.add(name)

        for model_name in model_names:
            hotkey = models_hotkeys.get(model_name, '')
            if hotkey:
                pynput_hotkey = self._to_pynput_format(hotkey)
                if pynput_hotkey:
                    def make_switch_model(name):
                        return lambda: self._switch_model(name)
                    hotkey_map[pynput_hotkey] = make_switch_model(model_name)
                    logger.info(f"Press {hotkey} to select model: {model_name}")

        if hotkey_map:
            try:
                self.listener = keyboard.GlobalHotKeys(hotkey_map)
                self.listener.start()
                logger.info("Hotkey listener started with new hotkeys.")
            except Exception as e:
                # This can happen on Wayland or if there are permission issues
                logger.error(f"Failed to start GlobalHotKeys listener: {e}", exc_info=True)
                if platform.system() == "Linux":
                    logger.error("On Linux, you may need to install 'python3-xlib' and run as root.")
                self.listener = None

        self._last_registered_hotkeys = {
            'modes': modes.copy(),
            'models_hotkeys': models_hotkeys.copy()
        }

    def _switch_model(self, model_name):
        """Changes the current model and language via settings_manager."""
        logger.info(f"Switching to model: {model_name}")
        models_dict = self.settings_manager.get('models', {})
        model_lang = None
        for lang, lang_models in models_dict.items():
            for model in lang_models:
                if model.get('name') == model_name:
                    model_lang = model.get('language', lang)
                    break
            if model_lang:
                break

        if model_lang is None:
            logger.error(f"Failed to determine language for model {model_name}")
            return

        self.settings_manager.set('current_model', model_name)
        self.settings_manager.set('language', model_lang)

    def stop(self):
        """Stops the hotkey listener thread."""
        if self.listener and self.listener.is_alive():
            logger.info("Stopping hotkey listener.")
            self.listener.stop()
            self.listener.join()
        self.listener = None

    def __del__(self):
        """Ensure the listener is stopped when the manager is deleted."""
        self.stop()

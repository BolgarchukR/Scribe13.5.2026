# command_handler.py
import json
import logging

from pynput.keyboard import Controller, Key

from scribe.app_launcher import CrossPlatformAppLauncher
from scribe.text_utils import fuzzy_match, normalize_text

logger = logging.getLogger(__name__)


def command_mode(settings_manager, lang=None):
    """Returns a handler for command mode."""
    launcher = CrossPlatformAppLauncher()
    keyboard = Controller()

    def send_hotkey(hotkey_str):
        """Parses a hotkey string and sends it using pynput."""
        try:
            keys = hotkey_str.lower().split('+')
            special_keys = {
                'ctrl': Key.ctrl, 'alt': Key.alt, 'shift': Key.shift,
                'win': Key.cmd, 'cmd': Key.cmd, 'super': Key.cmd,
                'enter': Key.enter, 'tab': Key.tab, 'space': Key.space,
                'backspace': Key.backspace, 'esc': Key.esc
            }

            modifiers = [special_keys[k.strip()] for k in keys[:-1] if k.strip() in special_keys]
            regular_key = keys[-1].strip()

            for mod in modifiers:
                keyboard.press(mod)

            # Check if the last key is a special key or a regular character
            if regular_key in special_keys:
                keyboard.press(special_keys[regular_key])
                keyboard.release(special_keys[regular_key])
            else:
                keyboard.press(regular_key)
                keyboard.release(regular_key)

            for mod in reversed(modifiers):
                keyboard.release(mod)

            logger.info(f"[COMMAND] Simulated hotkey: {hotkey_str}")
        except Exception as e:
            logger.error(f"[COMMAND][ERROR] Failed to send hotkey '{hotkey_str}': {e}")

    def handler(text):
        settings = settings_manager.all() if hasattr(settings_manager, 'all') else {}
        lang_code = lang or settings.get('language', 'en')
        text_norm = normalize_text(text)
        logger.info(f"[COMMAND] Recognized text: '{text_norm}'")

        # 1. Check commands_hotkey
        fuzzy_threshold_hotkey = float(settings.get('fuzzy_match_hotkey', 90)) / 100.0
        hotkey_cmds = settings.get('commands_hotkey', {}).get(lang_code, [])
        for cmd in hotkey_cmds:
            trigger = normalize_text(cmd.get('trigger', ''))
            hotkey = cmd.get('hotkey', '').strip()
            if trigger and (trigger == text_norm or fuzzy_match(trigger, text_norm, threshold=fuzzy_threshold_hotkey)):
                if hotkey:
                    send_hotkey(hotkey)
                return

        # 2. Check commands_openfile
        fuzzy_threshold_openfile = float(settings.get('fuzzy_match_openfile', 90)) / 100.0
        openfile_cmds = settings.get('commands_openfile', {}).get(lang_code, [])
        for cmd in openfile_cmds:
            trigger = normalize_text(cmd.get('trigger', ''))
            app_info_str = cmd.get('app_info', '').strip()
            path = cmd.get('path', '').strip()
            args = cmd.get('args', '').strip()

            if trigger and (trigger == text_norm or fuzzy_match(trigger, text_norm, threshold=fuzzy_threshold_openfile)):
                try:
                    # Prefer launching with rich app_info if available
                    if app_info_str:
                        app_info = json.loads(app_info_str)
                        app_info['args'] = args
                        launcher.launch(json.dumps(app_info))
                    # Fallback to simple path for manually added entries
                    elif path:
                        # Create a minimal app_info for the launcher
                        minimal_info = json.dumps({"path": path, "name": trigger, "args": args})
                        launcher.launch(minimal_info)
                except Exception as e:
                    logger.error(f"[COMMAND][ERROR] Failed to launch '{trigger}': {e}")
                return

    return handler

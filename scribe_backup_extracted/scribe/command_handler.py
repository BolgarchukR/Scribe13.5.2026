# command_handler.py
import json
import logging

from pynput.keyboard import Controller, Key

from scribe.app_launcher import CrossPlatformAppLauncher
from scribe.text_utils import fuzzy_match, normalize_text
from scribe.macro_executor import MacroExecutor

logger = logging.getLogger(__name__)

# Global dictation mode state
DICTATION_MODE_ACTIVE = False


def command_mode(settings_manager, lang=None):
    """Returns a handler for command mode."""
    launcher = CrossPlatformAppLauncher()
    keyboard = Controller()
    macro_executor = MacroExecutor()

    def send_hotkey(hotkey_str):
        """Parses a hotkey string and sends it via Windows keybd_event API."""
        import time
        import threading
        import ctypes
        try:
            if "нажмите" in hotkey_str.lower() or "натисніть" in hotkey_str.lower():
                logger.warning(f"[COMMAND] Invalid hotkey configured: '{hotkey_str}'")
                return

            keys = [k.strip().lower() for k in hotkey_str.split('+') if k.strip()]

            # Resolve each key to a Virtual-Key code via MacroExecutor's proven VK dict
            vk_list = []
            for k in keys:
                vk = macro_executor.resolve_vk(k)
                if vk is None and len(k) == 1:
                    # For single chars not in dict, ask Windows (layout-aware fallback)
                    scan = ctypes.windll.user32.VkKeyScanW(ord(k))
                    if scan != -1:
                        vk = scan & 0xFF
                if vk is not None:
                    vk_list.append(vk)
                else:
                    logger.warning(f"[COMMAND] Could not resolve key: '{k}' in hotkey '{hotkey_str}'")

            if not vk_list:
                return

            mod_vks = vk_list[:-1]
            main_vk = vk_list[-1]

            def _fire():
                try:
                    # Press modifiers (with delay between each for OS to register)
                    for vk in mod_vks:
                        macro_executor.press_vk(vk)
                        time.sleep(0.04)
                    # Press + release main key
                    macro_executor.press_vk(main_vk)
                    time.sleep(0.05)
                    macro_executor.release_vk(main_vk)
                    time.sleep(0.04)
                    # Release modifiers in reverse
                    for vk in reversed(mod_vks):
                        macro_executor.release_vk(vk)
                        time.sleep(0.03)
                except Exception as e:
                    logger.error(f"[COMMAND][ERROR] _fire failed for '{hotkey_str}': {e}")

            # Give the voice engine 150ms to finish, then fire in a background thread
            time.sleep(0.15)
            threading.Thread(target=_fire, daemon=True).start()
            logger.info(f"[COMMAND] Sending hotkey via WinAPI: {hotkey_str}")
        except Exception as e:
            logger.error(f"[COMMAND][ERROR] Failed to send hotkey '{hotkey_str}': {e}")


    def handler(text):
        global DICTATION_MODE_ACTIVE
        settings = settings_manager.all() if hasattr(settings_manager, 'all') else {}
        lang_code = lang or settings.get('language', 'en')
        text_norm = normalize_text(text)
        logger.info(f"[COMMAND] Recognized text: '{text_norm}'")

        if text_norm in ["включить диктовку", "включи диктовку"]:
            DICTATION_MODE_ACTIVE = True
            if hasattr(settings_manager, 'set'): settings_manager.set('dictation_mode_active', True)
            logger.info("Dictation mode ON")
            return (lambda: None, "Dictation Mode ON")
        elif text_norm in ["выключить диктовку", "выключи диктовку"]:
            DICTATION_MODE_ACTIVE = False
            if hasattr(settings_manager, 'set'): settings_manager.set('dictation_mode_active', False)
            logger.info("Dictation mode OFF")
            return (lambda: None, "Dictation Mode OFF")

        if hasattr(settings_manager, 'get'):
            DICTATION_MODE_ACTIVE = settings_manager.get('dictation_mode_active', DICTATION_MODE_ACTIVE)

        if DICTATION_MODE_ACTIVE:
            return False

        if text_norm.startswith("напечатай ") or text_norm == "напечатай":
            return text_norm.replace("напечатай ", "", 1) if text_norm != "напечатай" else ""

        # 1. Check commands_hotkey
        fuzzy_threshold_hotkey = float(settings.get('fuzzy_match_hotkey', 90)) / 100.0
        hotkey_cmds = settings.get('commands_hotkey', {}).get(lang_code, [])
        for cmd in hotkey_cmds:
            trigger_str = cmd.get('trigger', '')
            triggers = [normalize_text(t.strip()) for t in trigger_str.split(',')]
            hotkey = cmd.get('hotkey', '').strip()
            for trigger in triggers:
                if trigger:
                    is_isolated = len(text_norm.split()) <= len(trigger.split()) + 1
                    if trigger == text_norm or (is_isolated and fuzzy_match(trigger, text_norm, threshold=fuzzy_threshold_hotkey)):
                        if hotkey:
                            return (lambda h=hotkey: send_hotkey(h), trigger_str)
                        return (True, trigger_str)

        # 2. Check commands_openfile
        fuzzy_threshold_openfile = float(settings.get('fuzzy_match_openfile', 90)) / 100.0
        openfile_cmds = settings.get('commands_openfile', {}).get(lang_code, [])
        for cmd in openfile_cmds:
            trigger_str = cmd.get('trigger', '')
            triggers = [normalize_text(t.strip()) for t in trigger_str.split(',')]
            app_info_str = cmd.get('app_info', '').strip()
            path = cmd.get('path', '').strip()
            args = cmd.get('args', '').strip()

            for trigger in triggers:
                if trigger:
                    is_isolated = len(text_norm.split()) <= len(trigger.split()) + 1
                    if trigger == text_norm or (is_isolated and fuzzy_match(trigger, text_norm, threshold=fuzzy_threshold_openfile)):
                        if app_info_str:
                            app_info = json.loads(app_info_str)
                            app_info['args'] = args
                            return (lambda info=json.dumps(app_info), t=trigger: _safe_launch(launcher, info, t), trigger_str)
                        elif path:
                            minimal_info = json.dumps({"path": path, "name": trigger, "args": args})
                            return (lambda info=minimal_info, t=trigger: _safe_launch(launcher, info, t), trigger_str)
                        return (True, trigger_str)

        # 3. Check commands_macro
        fuzzy_threshold_macro = float(settings.get('fuzzy_match_macro', 90)) / 100.0
        macro_cmds = settings.get('commands_macro', {}).get(lang_code, [])
        for cmd in macro_cmds:
            if not cmd.get('enabled', True):
                continue
            trigger_str = cmd.get('trigger', '')
            triggers = [normalize_text(t.strip()) for t in trigger_str.split(',')]
            actions = cmd.get('actions', [])
            for trigger in triggers:
                if trigger:
                    is_isolated = len(text_norm.split()) <= len(trigger.split()) + 1
                    if trigger == text_norm or (is_isolated and fuzzy_match(trigger, text_norm, threshold=fuzzy_threshold_macro)):
                        return (lambda acts=actions: macro_executor.execute(acts), trigger_str)

        return False

    return handler

def _safe_launch(launcher, info_str, trigger):
    try:
        launcher.launch(info_str)
    except Exception as e:
        logger.error(f"[COMMAND][ERROR] Failed to launch '{trigger}': {e}")

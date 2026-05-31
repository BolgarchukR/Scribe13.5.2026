import ctypes
import time
import logging
import json
from pynput.keyboard import Controller
from scribe.app_launcher import CrossPlatformAppLauncher

logger = logging.getLogger(__name__)

# Virtual-Key Codes mapping for Windows
VK = {
    'backspace': 0x08, 'back': 0x08, 'tab': 0x09, 'enter': 0x0D, 'return': 0x0D,
    'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12, 'pause': 0x13, 'capslock': 0x14, 'capital': 0x14,
    'esc': 0x1B, 'escape': 0x1B, 'space': 0x20, 'pageup': 0x21, 'pgup': 0x21, 'prior': 0x21,
    'pagedown': 0x22, 'pgdn': 0x22, 'next': 0x22, 'end': 0x23, 'home': 0x24,
    'left': 0x25, 'up': 0x26, 'right': 0x27, 'down': 0x28, 'printscreen': 0x2C,
    'insert': 0x2D, 'ins': 0x2D, 'delete': 0x2E, 'del': 0x2E,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34, '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'd0': 0x30, 'd1': 0x31, 'd2': 0x32, 'd3': 0x33, 'd4': 0x34, 'd5': 0x35, 'd6': 0x36, 'd7': 0x37, 'd8': 0x38, 'd9': 0x39,
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
    'lwin': 0x5B, 'win': 0x5B, 'cmd': 0x5B, 'rwin': 0x5C,
    'numpad0': 0x60, 'numpad1': 0x61, 'numpad2': 0x62, 'numpad3': 0x63, 'numpad4': 0x64,
    'numpad5': 0x65, 'numpad6': 0x66, 'numpad7': 0x67, 'numpad8': 0x68, 'numpad9': 0x69,
    'multiply': 0x6A, 'add': 0x6B, 'separator': 0x6C, 'subtract': 0x6D, 'decimal': 0x6E, 'divide': 0x6F,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
    'lshift': 0xA0, 'rshift': 0xA1, 'lctrl': 0xA2, 'rctrl': 0xA3, 'lalt': 0xA4, 'ralt': 0xA5,
    'volumemute': 0xAD, 'volumedown': 0xAE, 'volumeup': 0xAF, 'medianexttrack': 0xB0,
    'mediaprevioustrack': 0xB1, 'mediastop': 0xB2, 'mediaplaypause': 0xB3,
    'oemminus': 0xBD, 'oemperiod': 0xBE
}

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001


class MacroExecutor:
    """Executes a sequence of automation actions natively via Windows API."""
    
    def __init__(self, application=None):
        self.keyboard_text = Controller() # keep pynput exclusively for unicode raw text insertion
        self.launcher = CrossPlatformAppLauncher()
        self._application = application

    def _abort_check(self):
        if ctypes.windll.user32.GetAsyncKeyState(VK['esc']) & 0x8000:
            logger.warning("[MACRO WINAPI] Execution aborted by user (Esc pressed)")
            raise RuntimeError("Macro aborted by user (Esc)")

    def _sleep_with_abort(self, duration):
        import time
        start = time.time()
        while time.time() - start < duration:
            self._abort_check()
            time.sleep(min(0.05, duration - (time.time() - start)))

    def resolve_vk(self, k_str):
        if not k_str:
            return None
        k_str = str(k_str).lower().strip()
        return VK.get(k_str, None)

    def press_vk(self, vk):
        if vk is not None:
            scan_code = ctypes.windll.user32.MapVirtualKeyA(vk, 0)
            flags = KEYEVENTF_EXTENDEDKEY if vk in (0x5B, 0x5C, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E, 0xA3, 0xA5) else 0x0000
            ctypes.windll.user32.keybd_event(vk, scan_code, flags, 0)
            
    def release_vk(self, vk):
        if vk is not None:
            scan_code = ctypes.windll.user32.MapVirtualKeyA(vk, 0)
            flags = KEYEVENTF_EXTENDEDKEY if vk in (0x5B, 0x5C, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E, 0xA3, 0xA5) else 0x0000
            ctypes.windll.user32.keybd_event(vk, scan_code, flags | KEYEVENTF_KEYUP, 0)

    def _resolve_pynput_key(self, k_str):
        if not k_str: return None
        k_lower = str(k_str).lower().strip()
        from pynput.keyboard import Key, KeyCode
        _key_mapping = {
            'ctrl': Key.ctrl, 'lctrl': Key.ctrl_l, 'rctrl': Key.ctrl_r,
            'shift': Key.shift, 'lshift': Key.shift_l, 'rshift': Key.shift_r,
            'alt': Key.alt, 'lalt': Key.alt_l, 'ralt': Key.alt_gr,
            'win': Key.cmd, 'lwin': Key.cmd, 'rwin': Key.cmd_r, 'cmd': Key.cmd,
            'enter': Key.enter, 'esc': Key.esc, 'escape': Key.esc, 'space': Key.space,
            'tab': Key.tab, 'backspace': Key.backspace, 'delete': Key.delete,
            'up': Key.up, 'down': Key.down, 'left': Key.left, 'right': Key.right,
            'home': Key.home, 'end': Key.end, 'pageup': Key.page_up, 'pagedown': Key.page_down,
            'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4, 'f5': Key.f5, 'f6': Key.f6,
            'f7': Key.f7, 'f8': Key.f8, 'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12
        }
        if k_lower in _key_mapping:
            return _key_mapping[k_lower]
        if hasattr(Key, k_lower):
            return getattr(Key, k_lower)
        if len(k_lower) == 1:
            # Fallback to character handling
            return KeyCode.from_char(k_lower)
        # Final fallback via Virtual-Key code mapping if explicit (e.g. printscreen)
        return KeyCode.from_vk(self.resolve_vk(k_lower) or 0)

    def execute(self, macro_actions):
        """Executes a list of macro actions sequentially."""
        logger.info(f"[MACRO WINAPI] Executing macro with {len(macro_actions)} actions")
        for idx, action in enumerate(macro_actions):
            try:
                self._abort_check()
                self._execute_action(action)
            except RuntimeError as e:
                if "aborted" in str(e):
                    break
                logger.error(f"[MACRO] Error executing action {idx+1} ({action}): {e}")
            except Exception as e:
                logger.error(f"[MACRO] Error executing action {idx+1} ({action}): {e}")

    def _execute_action(self, action):
        t = action.get('type')
        logger.debug(f"[MACRO WINAPI] -> {action}")
        
        if t in ['key_down', 'key_up', 'key_press']:
            k_str = action.get('key', '')
            vk = self.resolve_vk(k_str)
            if vk is None and len(k_str) == 1:
                scan = ctypes.windll.user32.VkKeyScanW(ord(k_str))
                if scan != -1: vk = scan & 0xFF
            
            if vk:
                if t == 'key_down':
                    self.press_vk(vk)
                elif t == 'key_up':
                    self.release_vk(vk)
                else: # key_press
                    self.press_vk(vk)
                    time.sleep(0.04)
                    self.release_vk(vk)
            time.sleep(0.01)
            
        elif t == 'hotkey':
            raw_keys = action.get('keys', [])
            if not raw_keys: return
            
            if isinstance(raw_keys, str):
                raw_keys = [raw_keys]
                
            keys = []
            for k in raw_keys:
                if '+' in k:
                    keys.extend([x.strip() for x in k.split('+') if x.strip()])
                elif ',' in k:
                    keys.extend([x.strip() for x in k.split(',') if x.strip()])
                else:
                    keys.append(k.strip())
            
            vks = []
            for k in keys:
                vk = self.resolve_vk(k)
                if vk is None and len(k) == 1:
                    scan = ctypes.windll.user32.VkKeyScanW(ord(k))
                    if scan != -1: vk = scan & 0xFF
                if vk: vks.append(vk)
            
            if not vks: return
            
            modifiers = vks[:-1]
            main_key = vks[-1]
            
            try:
                for m in modifiers:
                    self.press_vk(m)
                    self._sleep_with_abort(0.03)
                
                self.press_vk(main_key)
                self._sleep_with_abort(0.05)
            finally:
                self.release_vk(main_key)
                time.sleep(0.01)
                for m in reversed(modifiers):
                    self.release_vk(m)
                    time.sleep(0.02)
                
        elif t == 'delay':
            ms = int(action.get('ms', 0))
            if ms > 0:
                self._sleep_with_abort(ms / 1000.0)
                
        elif t == 'run_app':
            path = action.get('path', '')
            args = action.get('args', '')
            payload = json.dumps({"path": path, "args": args})
            self.launcher.launch(payload)
            
        elif t == 'type_text':
            text = action.get('text', '')
            self.keyboard_text.type(text)

        elif t == 'javascript':
            # Execute JS in browser via Bookmarklet method:
            # 1. Focus address bar (Alt+D)
            # 2. Type "javascript:" + code
            # 3. Press Enter
            code = action.get('code', '')
            if not code.startswith('javascript:'):
                code = 'javascript:' + code
            
            # Focus URL bar (Alt+D)
            self.press_vk(VK['alt'])
            time.sleep(0.05)
            self.press_vk(0x44) # 'D'
            time.sleep(0.05)
            self.release_vk(0x44)
            self.release_vk(VK['alt'])
            time.sleep(0.2) # Wait for browser focus
            
            # Type code
            self.keyboard_text.type(code)
            time.sleep(0.1)
            
            # Press Enter
            self.press_vk(VK['enter'])
            time.sleep(0.05)
            self.release_vk(VK['enter'])

        elif t == 'scribe_action':
            action_name = action.get('action', '')
            if self._application and hasattr(self._application, 'controller') and self._application.controller:
                ctrl = self._application.controller
                if action_name == 'toggle_transcription':
                    logger.info("[MACRO] Scribe action: toggle_transcription")
                    ctrl.switch_to_transcribe_mode()
                elif action_name == 'toggle_command':
                    logger.info("[MACRO] Scribe action: toggle_command")
                    ctrl.switch_to_command_mode()
                elif action_name == 'stop_all':
                    logger.info("[MACRO] Scribe action: stop_all")
                    ctrl.stop()
                else:
                    logger.warning(f"[MACRO] Unknown scribe_action: {action_name}")
            else:
                logger.warning("[MACRO] scribe_action: no application/controller available")

        else:
            logger.warning(f"[MACRO WINAPI] Unknown Macro Action: {t}")

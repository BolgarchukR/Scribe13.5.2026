# inserters/linux_clipboard_text_inserter.py
import logging
import queue
import threading
import time
import copykitten
from pynput.keyboard import Controller, Key

from scribe.inserters.text_inserter import TextInserter

logger = logging.getLogger(__name__)


class LinuxClipboardTextInserter(TextInserter):
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self._orig_clipboard = None
        self._queue = queue.Queue()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._running = False
        self._keyboard = Controller()
        self._update_settings(self.settings_manager.all())
        self.settings_manager.settings_changed.connect(self._update_settings)

    def _update_settings(self, settings):
        cb = settings.get('clipboard_settings', self.settings_manager.DEFAULTS['clipboard_settings'])
        self.clipboard_delay = cb.get('clipboard_delay_ms', 10) / 1000.0

    def start(self):
        try:
            self._orig_clipboard = copykitten.paste()
            if self._orig_clipboard is not None:
                snippet = self._orig_clipboard[:50] + ("..." if len(self._orig_clipboard) > 50 else "")
                logger.info(f"Original buffer saved (start): '{snippet}'")
            else:
                logger.info("The original buffer is empty or not text")
        except Exception as e:
            self._orig_clipboard = None
            logger.error(f"Failed to get buffer on startup: {e}")
        self._running = True
        if not self._worker.is_alive():
            self._worker = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker.start()

    def stop(self):
        logger.info("stop() called")
        self._running = False
        self._queue.put(('__STOP__', None))
        if self._worker.is_alive():
            self._worker.join(timeout=1)

    def insert_text(self, text: str):
        logger.info(f"insert_text() called with text: {text!r}")
        self._queue.put(('insert_text', text))

    def erase_chars(self, count: int):
        logger.info(f"erase_chars() called with count: {count}")
        self._queue.put(('erase_chars', count))

    def _worker_loop(self):
        while self._running:
            try:
                cmd, arg = self._queue.get()
                if cmd == '__STOP__':
                    break
                if cmd == 'insert_text':
                    copykitten.copy(arg)
                    with self._keyboard.pressed(Key.ctrl):
                        self._keyboard.press('v')
                        self._keyboard.release('v')
                    time.sleep(self.clipboard_delay * len(arg))
                elif cmd == 'insert_actions':
                    buf = ''
                    for action in arg:
                        if action['type'] == 'text' and action['value']:
                            buf += action['value']
                        elif action['type'] == 'key' and action['value']:
                            key = action['value']
                            if key.lower() == 'space':
                                buf += ' '
                            elif key.lower() == 'tab':
                                buf += '\t'
                            elif key.lower() == 'enter':
                                buf += '\n'
                            elif key.lower() == 'backspace':
                                buf = buf[:-1] if buf else buf
                    copykitten.copy(buf)
                    with self._keyboard.pressed(Key.ctrl):
                        self._keyboard.press('v')
                        self._keyboard.release('v')
                    time.sleep(self.clipboard_delay * len(buf))
                elif cmd == 'erase_chars':
                    for _ in range(arg):
                        self._keyboard.press(Key.backspace)
                        self._keyboard.release(Key.backspace)
                        time.sleep(0.01)
            except Exception as e:
                logger.error(f"{e}")

    def insert_actions(self, actions: list):
        """Pastes a list of actions (text/key) via the clipboard, supporting special keys."""
        logger.info(f"called with actions: {actions!r}")
        self._queue.put(('insert_actions', actions))

    def wait_until_idle(self, timeout=2.0):
        """Waits until the command queue and worker thread are completely empty."""
        start_time = time.time()
        while self._worker.is_alive():
            if self._queue.empty():
                break
            if time.time() - start_time > timeout:
                logger.warning("wait_until_idle: timeout")
                break
            time.sleep(0.01)

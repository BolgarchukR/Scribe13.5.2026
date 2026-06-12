# log_handler.py
import logging
from PyQt5.QtCore import QObject, pyqtSignal

class LogSignaler(QObject):
    """Bridge between logging and Qt signals."""
    log_emitted = pyqtSignal(logging.LogRecord)

class QtSignalingHandler(logging.Handler):
    """Custom logging handler that emits entries via Qt signals."""
    def __init__(self, signaler):
        super().__init__()
        self.signaler = signaler

    def emit(self, record):
        # We emit the record itself; the UI will parse it.
        self.signaler.log_emitted.emit(record)

# Global signaler instance to be used across the app
log_signaler = LogSignaler()

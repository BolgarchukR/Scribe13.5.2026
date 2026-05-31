import logging
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSlot

logger = logging.getLogger(__name__)

class FloatingHUD(QWidget):
    def __init__(self):
        super().__init__()
        # Frameless, transparent, on top, not focusable
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.label = QLabel("")
        # Sleek overlay style
        self.label.setStyleSheet("""
            QLabel {
                color: #f0f0f0;
                background-color: rgba(20, 20, 20, 190);
                padding: 12px 24px;
                border-radius: 10px;
                font-size: 18px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.hide()
        self.layout.addWidget(self.label)
        
        self.hide_timer = QTimer(self)
        self.hide_timer.timeout.connect(self._clear_text)

        # Initial positioning
        self.adjustSize()
        self.moveToTopCenter()

    def moveToTopCenter(self):
        if hasattr(self, 'screen'):
            screen_geom = self.screen().geometry()
            x = (screen_geom.width() - self.width()) // 2
            self.move(int(x), 50)  # 50px from top

    @pyqtSlot(str, bool)
    @pyqtSlot(str, bool, str)
    def update_text(self, text, is_command=False, command_name=None):
        if not text or not text.strip():
            return
            
        display_text = text
        if is_command:
            if command_name and command_name.strip():
                display_text = f"{text} \u2794 {command_name}"
            
            self.label.setStyleSheet("""
                QLabel {
                    color: #fff;
                    background-color: rgba(60, 160, 60, 210);
                    padding: 12px 24px;
                    border-radius: 10px;
                    font-size: 18px;
                    font-weight: bold;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
        else:
            self.label.setStyleSheet("""
                QLabel {
                    color: #f0f0f0;
                    background-color: rgba(20, 20, 20, 190);
                    padding: 12px 24px;
                    border-radius: 10px;
                    font-size: 18px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
            
        # Ensure UI updates run smoothly
        self.label.setText(display_text)
        self.label.show()
        self.adjustSize()
        self.moveToTopCenter()
        self.show()
        
        # Hide after 3 seconds
        self.hide_timer.start(3000)

    @pyqtSlot()
    def _clear_text(self):
        self.label.hide()
        self.hide()

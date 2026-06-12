# ui/console_page.py
import logging
from datetime import datetime
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLineEdit, 
    QPushButton, QLabel, QMenu
)

class ConsolePageWidget(QWidget):
    def __init__(self, texts, settings_manager, parent=None):
        super().__init__(parent)
        self.texts = texts
        self.settings_manager = settings_manager
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Search / Filter Bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.texts.get('console_search_placeholder', 'Search...'))
        self.search_input.textChanged.connect(self._filter_table)
        search_layout.addWidget(QLabel(self.texts.get('console_filter', 'Filter:')))
        search_layout.addWidget(self.search_input)
        
        self.clear_btn = QPushButton(self.texts.get('console_clear', 'Clear'))
        self.clear_btn.clicked.connect(self._clear_console)
        search_layout.addWidget(self.clear_btn)
        
        self.layout.addLayout(search_layout)

        # Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            self.texts.get('console_col_time', 'Время'),
            self.texts.get('console_col_phrase', 'Голосовая фраза'),
            self.texts.get('console_col_type', 'Тип'),
            self.texts.get('console_col_param', 'Параметр')
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Time
        header.setSectionResizeMode(1, QHeaderView.Interactive)      # Heard
        header.setSectionResizeMode(2, QHeaderView.Interactive)      # Command
        header.setSectionResizeMode(3, QHeaderView.Stretch)          # Action
        
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Appearance
        self.table.setStyleSheet("gridline-color: #444;")
        self.table.horizontalHeader().setSortIndicator(0, Qt.DescendingOrder)
        
        self.layout.addWidget(self.table)

        # Buffering for synchronization
        self._current_row_data = {}
        self._flush_timer = QTimer()
        self._flush_timer.setSingleShot(True)
        self._flush_timer.timeout.connect(self._flush_row)
        self._buffer_window_ms = 1200 # Time window to group logs into one row

        # Connect to log signaler
        from scribe.log_handler import log_signaler
        log_signaler.log_emitted.connect(self.on_log_received)

    @pyqtSlot(logging.LogRecord)
    def on_log_received(self, record):
        msg = record.getMessage()
        
        # We check for structured logs to fill columns
        is_structured = False
        if msg.startswith("[SPEECH]"):
            val = msg.replace("[SPEECH] Recognized: ", "").strip("'").strip('"')
            self._update_buffer('speech', val, record)
            is_structured = True
        elif msg.startswith("[COMMAND] Hit:"):
            content = msg.replace("[COMMAND] Hit: ", "").strip()
            if " | Param: " in content:
                cmd_part, param_part = content.split(" | Param: ", 1)
                self._update_buffer('command', cmd_part, record)
                self._update_buffer('action', param_part, record)
            else:
                self._update_buffer('command', content, record)
            is_structured = True
        elif msg.startswith("[REPLACE]"):
            # Format: [REPLACE] Find: ... | Replace: ...
            content = msg.replace("[REPLACE] ", "").strip()
            if " | Replace: " in content:
                find_part, replace_part = content.split(" | Replace: ", 1)
                find_val = find_part.replace("Find: ", "").strip()
                replace_val = replace_part.strip()
                self._update_buffer('speech', find_val, record)
                self._update_buffer('command', replace_val, record)
                self._update_buffer('action', self.texts.get('console_system_replace', "Замена слов"), record)
            is_structured = True
        elif msg.startswith("[ACTION]"):
            val = msg.replace("[ACTION]", "").strip()
            self._update_buffer('action', val, record)
            is_structured = True
        
        if not is_structured:
            # technical logs are ignored in the UI to prevent fragmentation
            # only show Warnings/Errors or logs that are NOT technical pollution
            ignore_keywords = ["Macro execution started", "[✓]", "[Final->apply]", "Erasing partial_prev"]
            if record.levelno < logging.WARNING:
                for kw in ignore_keywords:
                    if kw in msg:
                        return
            
            if record.levelno >= logging.WARNING or not any(kw in msg for kw in ignore_keywords):
                if self._flush_timer.isActive():
                    self._flush_row()
                self._add_raw_row(record)

    def _update_buffer(self, key, value, record):
        # Always restart reset timer when receiving new data for current row
        self._flush_timer.start(self._buffer_window_ms)
        
        # Initialize metadata if this is a new row
        if not self._current_row_data:
            self._current_row_data['time'] = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
            self._current_row_data['level'] = record.levelno

        # If the key is already present (e.g. second speech log), flush if it's different and not an action
        if key in self._current_row_data:
            if key == 'action':
                # Append if not duplicate, limit extra clutter
                existing = self._current_row_data.get(key, "")
                if value not in existing:
                    if existing:
                        self._current_row_data[key] = f"{existing}; {value}"
                    else:
                        self._current_row_data[key] = value
            elif key == 'command' or key == 'speech':
                # If we get a more specific command/speech, we might want to update or append
                if value != self._current_row_data[key]:
                    # For command, we prefer the "trigger" text over technical info
                    if key == 'command':
                        if len(value) > len(self._current_row_data[key]):
                           self._current_row_data[key] = value
                    else:
                        # For speech, if we get a new transcription result while one is pending, flush it
                        self._flush_row()
                        # Start new row with this new speech
                        self._current_row_data['time'] = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
                        self._current_row_data['level'] = record.levelno
                        self._current_row_data[key] = value
            else:
                self._flush_row()
                self._current_row_data['time'] = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
                self._current_row_data['level'] = record.levelno
                self._current_row_data[key] = value
        else:
            self._current_row_data[key] = value

    def _flush_row(self):
        if not self._current_row_data:
            return
        
        data = self._current_row_data
        self._current_row_data = {}
        
        self.table.setSortingEnabled(False)
        row_idx = 0
        self.table.insertRow(row_idx)
        
        items = [
            QTableWidgetItem(data.get('time', '')),
            QTableWidgetItem(data.get('speech', '')),
            QTableWidgetItem(data.get('command', '')),
            QTableWidgetItem(data.get('action', ''))
        ]
        
        color = self._get_color_for_level(data.get('level', logging.INFO))
        for i, item in enumerate(items):
            item.setForeground(color)
            self.table.setItem(row_idx, i, item)
            
        self.table.setSortingEnabled(True)
        self._limit_rows()

    def _add_raw_row(self, record):
        time_str = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        msg = record.getMessage()
        
        self.table.setSortingEnabled(False)
        row_idx = 0
        self.table.insertRow(row_idx)
        
        items = [
            QTableWidgetItem(time_str),
            QTableWidgetItem(""), # Speech
            QTableWidgetItem(""), # Command
            QTableWidgetItem(msg) # Action/General
        ]
        
        color = self._get_color_for_level(record.levelno)
        for i, item in enumerate(items):
            item.setForeground(color)
            self.table.setItem(row_idx, i, item)
            
        self.table.setSortingEnabled(True)
        self._limit_rows()

    def _limit_rows(self):
        if self.table.rowCount() > 500:
            self.table.removeRow(self.table.rowCount() - 1)

    def _get_color_for_level(self, level):
        if level >= logging.CRITICAL:
            return QColor(255, 0, 0) # Bright Red
        if level >= logging.ERROR:
            return QColor(200, 50, 50) # Red
        if level >= logging.WARNING:
            return QColor(100, 150, 255) # Blue
        # ALL OTHER LOGS (INFO, DEBUG, etc.) -> Pure White
        return QColor(255, 255, 255) 

    def _filter_table(self, text):
        text = text.lower()
        for i in range(self.table.rowCount()):
            match = False
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(i, not match)

    def _clear_console(self):
        self.table.setRowCount(0)

    def _show_context_menu(self, pos):
        menu = QMenu()
        copy_action = menu.addAction(self.texts.get('console_copy', "Копировать"))
        clear_action = menu.addAction(self.texts.get('console_clear', 'Очистить'))
        
        action = menu.exec_(self.table.mapToGlobal(pos))
        if action == clear_action:
            self._clear_console()
        elif action == copy_action:
            selected_ranges = self.table.selectedRanges()
            if not selected_ranges:
                return
            
            text_lines = []
            rows = set()
            for r in selected_ranges:
                for row in range(r.topRow(), r.bottomRow() + 1):
                    rows.add(row)
            
            for row in sorted(list(rows)):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                text_lines.append("\t".join(row_data))
            
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText("\n".join(text_lines))

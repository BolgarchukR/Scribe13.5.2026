import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget, QCheckBox,
    QWidget, QPushButton, QLabel, QTextEdit, QComboBox, QTableWidget, QLineEdit,
    QHeaderView, QAbstractItemView, QSpinBox
)
from PyQt5.QtCore import Qt
import copy

logger = logging.getLogger(__name__)

AVAILABLE_KEYS = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
    'space', 'enter', 'tab', 'esc', 'backspace', 'delete', 'up', 'down', 'left', 'right', 'home', 'end', 'pageup', 'pagedown',
    'lshift', 'rshift', 'lctrl', 'rctrl', 'lalt', 'ralt', 'lwin', 'rwin', 'printscreen', 'insert'
]

class MacroEditorDialog(QDialog):
    def __init__(self, settings_manager, texts, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.texts = texts
        self.setWindowTitle(self.texts.get('macro_editor_title', 'Macro Editor (Laitis Import)'))
        self.resize(850, 550)
        
        self.lang_code = self.settings_manager.get('language', 'ru')
        self.all_macros = self.settings_manager.get('commands_macro', {})
        self.macros = self.all_macros.get(self.lang_code, [])

        self.undo_stack = []
        self.redo_stack = []

        from scribe.ui.styles import DARK_THEME_STYLESHEET, LIGHT_THEME_STYLESHEET, is_system_in_dark_mode
        main_theme = self.settings_manager.all().get('main_window', {}).get('theme', 'auto')
        is_dark = is_system_in_dark_mode() if main_theme == 'auto' else (main_theme == 'dark')
        if is_dark:
            self.setStyleSheet(DARK_THEME_STYLESHEET)
        else:
            self.setStyleSheet(LIGHT_THEME_STYLESHEET)

        self._setup_ui()
        self._populate_macro_list()
        
    def _push_undo(self):
        self.undo_stack.append(copy.deepcopy(self.macros))
        self.redo_stack.clear()  # Clear redo on any new action
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

    def _undo(self):
        if self.undo_stack:
            self.redo_stack.append(copy.deepcopy(self.macros))
            self.macros = copy.deepcopy(self.undo_stack.pop())
            if self.current_macro_idx >= len(self.macros):
                self.current_macro_idx = len(self.macros) - 1
            self._populate_macro_list()
            if self.current_macro_idx >= 0:
                self.macro_list.setCurrentRow(self.current_macro_idx)
            else:
                self.actions_table.setRowCount(0)
                self.trigger_edit.clear()

    def _redo(self):
        if hasattr(self, 'redo_stack') and self.redo_stack:
            self.undo_stack.append(copy.deepcopy(self.macros))
            self.macros = copy.deepcopy(self.redo_stack.pop())
            if self.current_macro_idx >= len(self.macros):
                self.current_macro_idx = len(self.macros) - 1
            self._populate_macro_list()
            if self.current_macro_idx >= 0:
                self.macro_list.setCurrentRow(self.current_macro_idx)
            else:
                self.actions_table.setRowCount(0)
                self.trigger_edit.clear()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0,0,0,0)
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск команды...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)

        left_layout.addWidget(QLabel("База Команд (484+):"))
        self.macro_list = QListWidget()
        self.macro_list.currentRowChanged.connect(self._on_macro_selected)
        left_layout.addWidget(self.macro_list)
        
        btn_layout_left = QHBoxLayout()
        self.btn_add_cmd = QPushButton("+ Команда")
        self.btn_dup_cmd = QPushButton("+ Копия")
        self.btn_del_cmd = QPushButton("- Удалить")
        self.btn_add_cmd.clicked.connect(self._add_macro)
        self.btn_dup_cmd.clicked.connect(self._duplicate_macro)
        self.btn_del_cmd.clicked.connect(self._delete_macro)
        btn_layout_left.addWidget(self.btn_add_cmd)
        btn_layout_left.addWidget(self.btn_dup_cmd)
        btn_layout_left.addWidget(self.btn_del_cmd)
        left_layout.addLayout(btn_layout_left)
        
        # Right Panel
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0,0,0,0)
        
        trigger_layout = QHBoxLayout()
        trigger_layout.addWidget(QLabel("Голосовые фразы (запятая):"))
        self.trigger_edit = QTextEdit()
        self.trigger_edit.setMaximumHeight(60)
        self.trigger_edit.textChanged.connect(self._on_trigger_changed)
        trigger_layout.addWidget(self.trigger_edit)
        
        # Enabled/Disabled Toggle
        self.enabled_cb = QCheckBox("Включен")
        self.enabled_cb.stateChanged.connect(self._on_enabled_changed)
        trigger_layout.addWidget(self.enabled_cb)
        
        right_layout.addLayout(trigger_layout)
        
        from PyQt5.QtWidgets import QSlider
        precision_layout = QHBoxLayout()
        precision_label = QLabel("Точность совпадения речи (Fuzzy Match):")
        self.fuzzy_match_slider = QSlider(Qt.Horizontal)
        self.fuzzy_match_slider.setRange(50, 100)
        self.fuzzy_match_slider.setValue(int(self.settings_manager.get('fuzzy_match_macro', 90)))
        
        self.fuzzy_val_label = QLabel(str(self.fuzzy_match_slider.value()) + "%")
        self.fuzzy_match_slider.valueChanged.connect(lambda v: self.fuzzy_val_label.setText(f"{v}%"))
        
        precision_layout.addWidget(precision_label)
        precision_layout.addWidget(self.fuzzy_match_slider)
        precision_layout.addWidget(self.fuzzy_val_label)
        right_layout.addLayout(precision_layout)
        
        
        right_layout.addWidget(QLabel("Действия макроса:"))
        self.actions_table = QTableWidget(0, 2)
        self.actions_table.setHorizontalHeaderLabels(["Тип", "Параметр"])
        self.actions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.actions_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        right_layout.addWidget(self.actions_table)
        
        action_btn_layout = QHBoxLayout()
        self.btn_add_action = QPushButton("➕")
        self.btn_add_action.setToolTip("Добавить новый шаг макроса")
        self.btn_del_action = QPushButton("➖")
        self.btn_del_action.setToolTip("Удалить выбранный шаг макроса")
        self.btn_add_action.clicked.connect(self._add_action)
        self.btn_del_action.clicked.connect(self._delete_action)
        
        action_btn_layout.addWidget(self.btn_add_action)
        action_btn_layout.addWidget(self.btn_del_action)
        
        action_btn_layout.addStretch()
        
        # Test Macro section
        action_btn_layout.addWidget(QLabel("Запуск через (сек):"))
        self.test_delay_spin = QSpinBox()
        self.test_delay_spin.setRange(0, 30)
        self.test_delay_spin.setValue(3)
        action_btn_layout.addWidget(self.test_delay_spin)
        
        self.btn_test_macro = QPushButton("🚀 ТЕСТ")
        self.btn_test_macro.setToolTip("Запустить текущий макрос с задержкой.\nОстановить при нажатии Esc")
        self.btn_test_macro.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 5px 15px;")
        self.btn_test_macro.clicked.connect(self._test_macro)
        action_btn_layout.addWidget(self.btn_test_macro)
        
        right_layout.addLayout(action_btn_layout)
        
        bottom_layout = QHBoxLayout()
        self.btn_undo = QPushButton("↩")
        self.btn_undo.setToolTip("Отменить последнее действие (Undo)")
        self.btn_undo.clicked.connect(self._undo)
        
        self.btn_redo = QPushButton("↻")
        self.btn_redo.setToolTip("Повторить отменённое действие (Redo)")
        self.btn_redo.clicked.connect(self._redo)
        
        bottom_layout.addWidget(self.btn_undo)
        bottom_layout.addWidget(self.btn_redo)
        
        bottom_layout.addStretch()
        self.btn_save = QPushButton("💾 Применить")
        self.btn_save.setToolTip("Сохранить изменения и закрыть")
        self.btn_save.setStyleSheet("font-weight: bold;")
        self.btn_save.clicked.connect(self._save_and_close)
        bottom_layout.addWidget(self.btn_save)

        right_layout.addLayout(bottom_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])
        main_layout.addWidget(splitter)
        
        self.current_macro_idx = -1

    def _populate_macro_list(self):
        # We temporarily disconnect self.macro_list to prevent random trigger overwrites during repopulation
        self.macro_list.blockSignals(True)
        self.macro_list.clear()
        for m in self.macros:
            t = m.get('trigger', 'Empty')
            en = m.get('enabled', True)
            self.macro_list.addItem(t if en else f"🛇 {t}")
        if hasattr(self, 'search_input'):
            self._apply_search()
        self.macro_list.blockSignals(False)

    def _add_macro(self):
        self._push_undo()
        new_macro = {"trigger": "новая команда", "context": [], "actions": [], "enabled": True}
        self.macros.append(new_macro)
        self._populate_macro_list()
        self.macro_list.setCurrentRow(len(self.macros)-1)
        
    def _delete_macro(self):
        r = self.macro_list.currentRow()
        if r >= 0:
            self._push_undo()
            del self.macros[r]
            self._populate_macro_list()

    def _duplicate_macro(self):
        r = self.macro_list.currentRow()
        if r >= 0:
            self._push_undo()
            cloned = copy.deepcopy(self.macros[r])
            orig_t = cloned.get('trigger', 'команда')
            cloned['trigger'] = orig_t + " (копия)"
            self.macros.insert(r + 1, cloned)
            self._populate_macro_list()
            self.macro_list.setCurrentRow(r + 1)
            self._apply_search()

    def _on_search_changed(self, text):
        self._apply_search()

    def _apply_search(self):
        query = self.search_input.text().lower().strip()
        for i in range(self.macro_list.count()):
            item = self.macro_list.item(i)
            if not query or query in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def _on_trigger_changed(self):
        if self.current_macro_idx >= 0:
            text = self.trigger_edit.toPlainText()
            self.macros[self.current_macro_idx]['trigger'] = text
            en = self.macros[self.current_macro_idx].get('enabled', True)
            self.macro_list.item(self.current_macro_idx).setText(text if en else f"🛇 {text}")

    def _on_enabled_changed(self, state):
        if self.current_macro_idx >= 0:
            # We don't push undo here because it's a minor toggle, but it could be 
            self.macros[self.current_macro_idx]['enabled'] = (state == Qt.Checked)
            self._on_trigger_changed()

    def _on_macro_selected(self, row):
        if row < 0 or row >= len(self.macros):
            self.actions_table.setRowCount(0)
            self.trigger_edit.clear()
            self.current_macro_idx = -1
            return
            
        self.current_macro_idx = row
        macro = self.macros[row]
        
        self.trigger_edit.blockSignals(True)
        self.trigger_edit.setText(macro.get('trigger', ''))
        self.trigger_edit.blockSignals(False)
        
        self.enabled_cb.blockSignals(True)
        self.enabled_cb.setChecked(macro.get('enabled', True))
        self.enabled_cb.blockSignals(False)
        
        self._render_actions()
        
    def _render_actions(self):
        macro = self.macros[self.current_macro_idx]
        actions = macro.get('actions', [])
        
        self.actions_table.setRowCount(len(actions))
        for i, a in enumerate(actions):
            t = a.get('type')
            
            type_combo = QComboBox()
            options = [
                ('key_press', 'Нажатие клавиши'),
                ('key_down', 'Зажать клавишу'),
                ('key_up', 'Отпустить клавишу'),
                ('delay', 'Пауза/Задержка (мс)'),
                ('type_text', 'Печатать текст'),
                ('hotkey', 'Сочетание клавиш (Hotkey)'),
                ('run_app', 'Запуск программы'),
                ('javascript', 'JS Скрипт (Браузер)'),
                ('scribe_action', 'Действие Scribe')
            ]
            for val, text in options:
                type_combo.addItem(text, val)
                
            idx = next((i for i, (v, _) in enumerate(options) if v == t), 0)
            type_combo.setCurrentIndex(idx)
            type_combo.currentIndexChanged.connect(lambda _, row=i: self._change_action_type(row))
            self.actions_table.setCellWidget(i, 0, type_combo)
            
            if t in ['key_press', 'key_down', 'key_up']:
                w = QComboBox()
                w.setEditable(True)
                w.addItems(AVAILABLE_KEYS)
                w.setCurrentText(str(a.get('key', '')))
                w.currentTextChanged.connect(lambda txt, row=i: self._update_action_val(row, 'key', txt))
                self.actions_table.setCellWidget(i, 1, w)
            elif t == 'delay':
                w = QSpinBox()
                w.setMaximum(100000)
                w.setValue(int(a.get('ms', 0)))
                w.valueChanged.connect(lambda val, row=i: self._update_action_val(row, 'ms', val))
                self.actions_table.setCellWidget(i, 1, w)
            elif t == 'type_text':
                w = QLineEdit(a.get('text', ''))
                w.textChanged.connect(lambda txt, row=i: self._update_action_val(row, 'text', txt))
                self.actions_table.setCellWidget(i, 1, w)
            elif t == 'hotkey':
                w = QLineEdit('+'.join(a.get('keys', [])))
                w.textChanged.connect(lambda txt, row=i: self._update_action_val(row, 'keys', [x.strip() for x in txt.replace(',', '+').split('+') if x.strip()]))
                self.actions_table.setCellWidget(i, 1, w)
            elif t == 'run_app':
                w = QLineEdit(a.get('path', ''))
                w.textChanged.connect(lambda txt, row=i: self._update_action_val(row, 'path', txt))
                self.actions_table.setCellWidget(i, 1, w)
            elif t == 'javascript':
                w = QLineEdit(a.get('code', ''))
                w.setPlaceholderText("document.querySelector('video').currentTime -= 5")
                w.textChanged.connect(lambda txt, row=i: self._update_action_val(row, 'code', txt))
                self.actions_table.setCellWidget(i, 1, w)
            elif t == 'scribe_action':
                w = QComboBox()
                scribe_actions = [
                    ('toggle_transcription', 'Старт/стоп транскрипции'),
                    ('toggle_command', 'Старт/стоп командного режима'),
                    ('stop_all', 'Остановить всё'),
                ]
                for val, text in scribe_actions:
                    w.addItem(text, val)
                current_action = a.get('action', 'toggle_transcription')
                idx_sa = next((j for j, (v, _) in enumerate(scribe_actions) if v == current_action), 0)
                w.setCurrentIndex(idx_sa)
                w.currentIndexChanged.connect(lambda _, row=i, combo=w: self._update_action_val(row, 'action', combo.currentData()))
                self.actions_table.setCellWidget(i, 1, w)

    def _update_action_val(self, row, key, val):
        if self.current_macro_idx >= 0:
            actions = self.macros[self.current_macro_idx].get('actions', [])
            if 0 <= row < len(actions):
                # Don't push undo on every keystroke, too spammy
                actions[row][key] = val

    def _change_action_type(self, row):
        if self.current_macro_idx >= 0:
            self._push_undo()
            actions = self.macros[self.current_macro_idx].get('actions', [])
            if 0 <= row < len(actions):
                new_t = self.actions_table.cellWidget(row, 0).currentData()
                if new_t == 'delay': actions[row] = {'type': new_t, 'ms': 100}
                elif new_t == 'type_text': actions[row] = {'type': new_t, 'text': ''}
                elif new_t == 'hotkey': actions[row] = {'type': new_t, 'keys': []}
                elif new_t == 'run_app': actions[row] = {'type': new_t, 'path': ''}
                elif new_t == 'javascript': actions[row] = {'type': new_t, 'code': ''}
                elif new_t == 'scribe_action': actions[row] = {'type': new_t, 'action': 'toggle_transcription'}
                else: actions[row] = {'type': new_t, 'key': 'esc'}
                self._render_actions()

    def _add_action(self):
        if self.current_macro_idx >= 0:
            self._push_undo()
            actions = self.macros[self.current_macro_idx].setdefault('actions', [])
            actions.append({"type": "key_press", "key": "enter"})
            self._render_actions()

    def _delete_action(self):
        if self.current_macro_idx >= 0:
            self._push_undo()
            actions = self.macros[self.current_macro_idx].get('actions', [])
            r = self.actions_table.currentRow()
            if r >= 0 and r < len(actions):
                del actions[r]
                self._render_actions()

    def _test_macro(self):
        if self.current_macro_idx < 0:
            return
            
        from PyQt5.QtCore import QTimer
        delay_sec = self.test_delay_spin.value()
        actions = copy.deepcopy(self.macros[self.current_macro_idx].get('actions', []))
        
        self.btn_test_macro.setEnabled(False)
        self.btn_test_macro.setText(f"ЖДЕМ {delay_sec}с...")
        
        def _run():
            from scribe.macro_executor import MacroExecutor
            ex = MacroExecutor()
            ex.execute(actions)
            self.btn_test_macro.setEnabled(True)
            self.btn_test_macro.setText("🚀 ТЕСТ")
            
        QTimer.singleShot(delay_sec * 1000, _run)

    def _save_and_close(self):
        self.all_macros[self.lang_code] = self.macros
        self.settings_manager.set('commands_macro', self.all_macros)
        self.settings_manager.set('fuzzy_match_macro', self.fuzzy_match_slider.value())
        logger.info("Saved macros via IDE")
        self.accept()

# Scribe

> A powerful, offline, real-time voice-to-text application for Windows.

![Scribe Main Window](docs/images/main_window_feature.png)

Scribe is a versatile tool designed to integrate voice commands and transcription seamlessly into your workflow. Powered by the Vosk Offline Speech Recognition Toolkit, it ensures that all your data remains private by processing everything locally on your machine. Whether you need to dictate text, control applications with your voice, or automate repetitive tasks, Scribe provides a flexible and powerful solution.

## Key Features

*   **Real-Time Transcription:** Dictate text directly into any application with high accuracy.
*   **Command Mode:** Execute actions using custom voice commands.
*   **Offline and Private:** All voice processing happens locally on your machine. No data is ever sent to the cloud.
*   **Lightweight Performance:** Low CPU usage, especially when using small Vosk models, ensuring smooth operation without slowing down your system.
*   **Multi-Language Support:** Easily download and switch between different language models.
*   **Customizable Hotkeys:** Configure global hotkeys to start/stop modes and switch between active models.
*   **Text Replacements:** Define custom words or phrases that automatically expand into longer text snippets (e.g., "my email" -> "my.address@example.com").
*   **Voice-Activated Program Launch:** Set up voice commands to open any application or file on your computer.
*   **Flexible Configuration:** Fine-tune input methods (keyboard typing vs. clipboard paste), tray icon appearance, and window behavior to match your preferences.

## Getting Started

### Prerequisites

*   Windows 7 (64-bit) or newer.
*   Linux support (version 1.2.0 and later) with X11 graphical interface. Wayland is not currently supported.

### Installation

1.  Go to the [**Releases**](https://github.com/AIgrator/Scribe/releases) page.
2.  Download the latest `scribe-x64.exe` file from the "Assets" section.
3.  Run the executable. No installation is required.

## Building from Source

If you want to build the project from the source code, please follow the instructions in our [**BUILDING.md**](BUILDING.md) file.

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.

## Acknowledgments

This project relies on the excellent [Vosk Offline Speech Recognition Toolkit](https://alphacephei.com/vosk/).

Хронология изменений проекта Scribe (Март — Июнь 2026)
1. Начало: Внедрение Гибридного режима (Март 2026)
Это было первое и самое существенное изменение, призванное устранить главный недостаток оригинальной версии — невозможность выполнять команды во время диктовки.
•	26 марта 2026 г. — Начало работы над проектом, анализ оригинального Scribe v1.2.0.
•	29 марта 2026 г. — Реализация Гибридного режима: Переписана логика файлов command_handler.py, voice_typer_controller.py и vosk_recognizer.py. Программа начала работать «потоком»: если фраза совпадает с командой — она выполняется (с удалением промежуточного текста), если нет — печатается как текст.
•	29 марта 2026 г. — Исправлена ошибка библиотеки pynput, которая не видела функциональные клавиши (F1–F12). Код адаптирован для их корректного нажатия.
•	30 марта 2026 г. — Внедрена логика «изолированного совпадения»: команды срабатывают только при наличии пауз, чтобы они не выполнялись случайно посреди длинного предложения.
2. Архитектурные правки и интерфейс HUD (Апрель 2026)
•	02 апреля 2026 г. — Создан файл build_scribe.bat для автоматической сборки проекта в .exe. Исправлен баг «пулеметной печати» (race condition) путем принудительной очистки очереди при остановке микрофона.
•	06 апреля 2026 г. — Внедрен HUD-интерфейс (floating_hud.py): полупрозрачное окно вверху экрана, отображающее распознанный текст в реальном времени.
•	06 апреля 2026 г. — возможность  импорт команд из Laitis (Save.json) в формат Scribe. Тестовый режим. 
•	08 апреля 2026 г. — Решена проблема вставки буквы «v» на русской раскладке: стандартный Ctrl+V заменен на низкоуровневую комбинацию Shift+Insert.
•	09 апреля 2026 г. — Создан Графический редактор макросов (macro_editor_dialog.py), позволяющий визуально настраивать цепочки действий.
•	10–12 апреля 2026 г. — В редактор добавлены функции Undo (отмена) до 20 шагов, поиск по командам, дублирование («+ Копия») и чекбокс «Включен» для каждой команды.
•	13–14 апреля 2026 г. — Реализована сквозная темная тема для всех окон. HUD теперь мигает зеленым цветом при успешном распознавании команды.
•	21 апреля 2026 г. — В редакторе макросов появилась кнопка «🚀 ТЕСТ» с задержкой и поддержка JavaScript-команд для браузера.
•	29 апреля 2026 г. — Введена экстренная остановка макроса по клавише Esc. Исправлен критический UnboundLocalError, блокировавший работу распознавателя.
3. Портативность и программное управление (Май 2026)
•	09 мая 2026 г. — Создан скрипт backup_scribe.bat для быстрого создания архивов исходного кода.
•	11 мая 2026 г. — Полный Portable-режим: Изменен run.py, чтобы настройки (settings.json), логи (app.log) и словари всегда находились в папке с .exe, а не в %APPDATA%.
•	11 мая 2026 г. — Создан улучшенный компилятор build_scribe_fixed.bat, работающий на разных компьютерах.
•	22 мая 2026 г. — Исправлен баг «бесшумной смерти» потока распознавания. Введена блокировка гонки аудио-буфера (threading.Event) при переключении режимов.
•	30 мая 2026 г. — Горячие клавиши переключения режимов заменены на более стабильные Ctrl+Shift+6 и Ctrl+Shift+7.
•	31 мая 2026 г. — В макросы добавлен тип действия scribe_action: теперь голосовые команды могут управлять самой программой (переключать режимы) напрямую через код, минуя эмуляцию клавиш.
4. Интеллектуальная обработка и Консоль отладки (Июнь 2026)
•	01 июня 2026 г. — Словари автозамен вынесены в отдельный файл replacements.json.
•	01–03 июня 2026 г. — Внедрен модуль words_to_numbers.py для автоматического превращения слов в цифры (например, «тридцать пять» → «35»).
•	03 июня 2026 г. — Добавлена поддержка масок со звездочкой (например, гривн* → грн.) и перечисления вариантов через запятую в словаре.
•	11 июня 2026 г. — В настройки добавлен пункт «Автостарт распознавания при запуске».
•	11 июня 2026 г. — Создан интерактивный «Журнал событий» (Консоль отладки) с четырьмя колонками («Время», «Голосовая фраза», «Тип», «Параметр») и цветовой индикацией событий.
•	11 июня 2026 г. — Добавлен сверхкомпактный масштаб интерфейса — режим окна «Микро» (коэффициент 0.35).
Программа все ещё требует  серьёзных доработок хотя лично я её сейчас даже активно использую и с помощью неё говорю  вот эти строки. А также выполняю наиболее распространённые команды. Но снимаю с себя всякую ответственность использование на свой страх и риск. Задумок много, но как всегда нет времени.  

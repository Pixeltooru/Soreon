import os
import sys
import subprocess
import shutil

# Основные настройки
MAIN_SCRIPT = "main.py"  # Главный файл приложения
OUTPUT_DIR = "dist"      # Папка для итогового EXE
ICON_PATH = ""           # Путь к иконке (если есть)

# Проверяем иконку
icon_option = f"--windows-icon-from-ico={ICON_PATH}" if ICON_PATH and os.path.exists(ICON_PATH) else ""

# Формируем команду компиляции
command = [
    sys.executable, "-m", "nuitka",
    "--standalone",      # Создать автономный EXE
    "--onefile",         # Упаковать всё в один файл
    "--windows-console-mode=disable",  # Отключить консольное окно (только для GUI-приложений)
    "--enable-plugin=pyqt5",  # Поддержка PyQt5
    "--follow-imports",  # Включить все зависимости
    "--assume-yes-for-downloads",  # Автоматически загружать нужные зависимости
    f"--output-dir={OUTPUT_DIR}",  # Папка для результата
    icon_option,  # Добавляем иконку, если она есть
    MAIN_SCRIPT
]

# Удаляем пустые аргументы
command = [arg for arg in command if arg]

# Очистка старых файлов перед сборкой (опционально)
if os.path.exists("build"):
    shutil.rmtree("build")
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)

# Запуск компиляции
print("Компиляция началась...")
subprocess.run(command, check=True)
print(f"Компиляция завершена! EXE-файл находится в папке {OUTPUT_DIR}.")

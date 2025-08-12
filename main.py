import eel
import subprocess
import threading
import time
import os

# --- Функция для запуска Flask-сервера ---
def run_server():
    os.system("python server.py")

# --- Запускаем сервер в отдельном потоке ---
threading.Thread(target=run_server, daemon=True).start()

# Даём серверу немного времени, чтобы он успел запуститься
time.sleep(1)

# --- Запуск Eel (интерфейс админ-панели) ---
eel.init("web")  # Папка с HTML/CSS/JS
eel.start("main.html", size=(900, 700))
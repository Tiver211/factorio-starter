from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for
import subprocess
import os
from utils import *

app = Flask(__name__)

# Путь к директории сервера Factorio
FACTORIO_PATH = "../server"
SAVES_DIR = os.path.join(FACTORIO_PATH, "saves")
LOG_FILE = os.path.join(FACTORIO_PATH, "factorio.log")
SETTINGS_FILE = os.path.join(FACTORIO_PATH, "factorio-settings.json")

# Хранение текущего процесса сервера
server_process = None
status = False


# Главная страница
@app.route("/")
def home():
    # Пример данных
    if not status:
        send_status = "Сервер выключен"

    elif status:
        send_status = "сервер включен"

    else:
        send_status = "ошибка данных"

    saves = get_saves(SAVES_DIR)

    # Передача данных в шаблон
    return render_template("index.html", status=status, saves=saves)


# Запуск сервера
@app.route("/start", methods=["POST"])
def start_server():
    global status
    global server_process
    save_name = request.form.get("save")
    if not save_name:
        return jsonify({"error": "Не указан сейв"}), 400

    save_path = os.path.join(SAVES_DIR, save_name)
    if not save_exists(SAVES_DIR, save_name):
        return jsonify({"error": "Сейв не найден"}), 404

    if status:
        return jsonify({"error": "Сервер уже запущен"}), 400

    # Запуск сервера
    server_process = subprocess.Popen(
        [
            "./factorio",
            "--start-server", save_path,
            "--server-settings", os.path.join(FACTORIO_PATH, "server-settings.json")
        ],
        cwd=FACTORIO_PATH,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    status = True
    return jsonify({"message": f"Сервер запущен с сейвом {save_name}"})


# Остановка сервера
@app.route("/stop", methods=["POST"])
def stop_server():
    global status
    global server_process
    if not status:
        return jsonify({"error": "Сервер не запущен"}), 400

    server_process.terminate()
    server_process = None
    status = False
    return jsonify({"message": "Сервер остановлен"})


# Список доступных сейвов
@app.route("/saves", methods=["GET"])
def list_saves():
    saves = get_saves(SAVES_DIR)
    return jsonify({"saves": saves})


# Логи сервера
@app.route("/logs", methods=["GET"])
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify({"error": "Лог-файл не найден"}), 404

    with open(LOG_FILE, "r") as log_file:
        logs = log_file.readlines()
    return jsonify({"logs": logs[-50:]})  # Возвращаем последние 50 строк


# Загрузка нового сейва
@app.route("/upload", methods=["POST"])
def upload_save():
    if "file" not in request.files:
        return jsonify({"error": "Файл не найден в запросе"}), 400

    save_file = request.files["file"]
    save_path = os.path.join(SAVES_DIR, save_file.filename)
    if save_exists(SAVES_DIR, save_file.filename):
        save_file.save(save_path)
        return jsonify({"message": f"Сейв {save_file.filename} загружен"})

    else:
        return jsonify({"error": f"Сейв{save_file.filename} уже существует"})


@app.route("/settings", methods=["GET", "POST"])
def show_settings():
    if request.method == "POST":
        # Получаем данные из формы
        updated_settings = request.form.to_dict()

        # Преобразуем значения обратно в нужные типы
        for key, value in updated_settings.items():
            if value.isdigit():
                updated_settings[key] = int(value)  # Преобразуем числа
            elif value.lower() in ["true", "false"]:
                updated_settings[key] = value.lower() == "true"  # Преобразуем булевы значения\

        settings = read_server_settings(SETTINGS_FILE) | updated_settings

        # Сохраняем обновлённые настройки
        update_server_settings(SETTINGS_FILE, settings)

        return redirect(url_for("show_settings"))

    # Чтение настроек для отображения
    settings = read_server_settings(SETTINGS_FILE)
    return render_template("settings_display.html", settings=settings)

@app.route("/settings/add", methods=["POST"])
def add_setting():
    """Добавляет новый ключ и значение."""
    key = request.form.get("new_key")
    value = request.form.get("new_value")

    if key and value:
        settings = read_server_settings(SETTINGS_FILE)

        # Преобразуем значение в нужный тип
        if value.isdigit():
            value = int(value)
        elif value.lower() in ["true", "false"]:
            value = value.lower() == "true"

        # Добавляем новый ключ и значение
        settings[key] = value
        update_server_settings(SETTINGS_FILE, settings)

    return redirect(url_for("show_settings"))

@app.route("/settings/delete/<key>")
def delete_setting(key):
    """Удаляет указанный ключ."""
    settings = read_server_settings(SETTINGS_FILE)

    # Удаляем ключ, если он существует
    if key in settings:
        del settings[key]
        update_server_settings(SETTINGS_FILE, settings)

    return redirect(url_for("show_settings"))



# Запуск приложения
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

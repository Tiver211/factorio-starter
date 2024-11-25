from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for
import subprocess
import os

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

from utils import *

app = Flask(__name__)



# Путь к директории сервера Factorio
FACTORIO_PATH = "../server"
SAVES_DIR = os.path.join(FACTORIO_PATH, "saves")
LOG_FILE = os.path.join(FACTORIO_PATH, "factorio.log")
SETTINGS_FILE = os.path.join(FACTORIO_PATH, "factorio-settings.json")
WEBSITE_SETTINGS_FILE = "settings.json"
MODS_DIR = os.path.join(FACTORIO_PATH, "mods")

files = [FACTORIO_PATH, SAVES_DIR, LOG_FILE, SETTINGS_FILE, WEBSITE_SETTINGS_FILE, MODS_DIR]

if not check_files(files):
    print("Something went wrong")
    create_missing_files(files)

with open("settings.json", "r") as f:
    secrets = json.load(f)["secretkey"]
app.secret_key = secrets

# Хранение текущего процесса сервера
server_process = None
status = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Главная страница
@app.route("/")
@login_required
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
@login_required
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
            "sudo", "/home/tiver211/factorio/bin/x64/factorio",
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
@login_required
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
@login_required
def list_saves():
    saves = get_saves(SAVES_DIR)
    return jsonify({"saves": saves})


# Логи сервера
@app.route("/logs", methods=["GET"])
@login_required
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify({"error": "Лог-файл не найден"}), 404

    with open(LOG_FILE, "r") as log_file:
        logs = log_file.readlines()
    return jsonify({"logs": logs[-50:]})  # Возвращаем последние 50 строк


# Загрузка нового сейва
@app.route("/upload", methods=["POST"])
@login_required
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
@login_required
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
@login_required
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
@login_required
def delete_setting(key):
    """Удаляет указанный ключ."""
    settings = read_server_settings(SETTINGS_FILE)

    # Удаляем ключ, если он существует
    if key in settings:
        del settings[key]
        update_server_settings(SETTINGS_FILE, settings)

    return redirect(url_for("show_settings"))


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        if check_enter(request.form.get("password"), request.form.get("username")):
            user = User(request.form.get("username"))
            login_user(user)
            return redirect("/")
        return 'Неверные данные!'

    return render_template("login.html")

@login_manager.user_loader
def load_user(user_id):
    if check_user_valid(user_id):
        return User(user_id)
    return None


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Запуск приложения
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

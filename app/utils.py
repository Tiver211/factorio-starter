import os
import json
import subprocess
from datetime import datetime

# Путь к директории сервера Factorio
FACTORIO_PATH = "../server"
SAVES_DIR = os.path.join(FACTORIO_PATH, "saves")
LOG_FILE = os.path.join(FACTORIO_PATH, "factorio.log")
SETTINGS_FILE = os.path.join(FACTORIO_PATH, "factorio-settings.json")
WEBSITE_SETTINGS_FILE = "settings.json"
MODS_DIR = os.path.join(FACTORIO_PATH, "mods")

files = [FACTORIO_PATH, SAVES_DIR, LOG_FILE, SETTINGS_FILE, WEBSITE_SETTINGS_FILE, MODS_DIR]

def get_saves(folder):
    return [a for a in os.listdir(folder) if a.endswith('.zip')]


def save_exists(save_dir, save_name):
    """Проверяет, существует ли сейв с указанным именем."""
    save_path = os.path.join(save_dir, f"{save_name}")
    return os.path.exists(save_path)


def read_server_settings(settings_path):
    """
    Читает настройки сервера Factorio из JSON-файла.

    :param settings_path: Путь к файлу настроек (server-settings.json).
    :return: Словарь с настройками.
    """
    if not os.path.exists(settings_path):
        raise FileNotFoundError(f"Файл настроек {settings_path} не найден.")
    try:
        with open(settings_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка чтения JSON: {e}")


def update_server_settings(settings_path, data):
    """
    Обновляет указанное поле в файле настроек сервера.

    :param settings_path: Путь к файлу настроек.
    :param key: Ключ, который нужно обновить.
    :param value: Новое значение.
    """
    settings = data

    # Сохраняем изменения
    with open(settings_path, 'w', encoding='utf-8') as file:
        json.dump(settings, file, indent=4, ensure_ascii=False)


def check_enter(password, login):
    with open("settings.json", 'r', encoding='utf-8') as file:
        data = json.load(file)
        real_password = data["password"]
        real_login = data["username"]

    if password == real_password and real_login == login:
        return True

    return False


def check_user_valid(username):
    with open("settings.json", 'r', encoding='utf-8') as file:
        if username in json.load(file).values():
            return True

    return False


def check_files(files_need):
    for file in files_need:
        if not os.path.exists(file):
            return False


def create_missing_files(files_need):
    for file in files_need:
        if not os.path.exists(file):
            if is_file_path(file):
                with open(file, 'w', encoding='utf-8') as f:
                    if file == 'settings.json':
                        f.write(json.dumps({
                                  "username": "admin",
                                  "password": "password123",
                                  "secretkey": "test1324"
                                            }))

                    elif file == SETTINGS_FILE:
                        f.write(json.dumps({}))
                    pass

            else:
                os.mkdir(file)


def is_file_path(path):
    # Считаем, что файл имеет расширение, отделённое точкой
    # И путь не заканчивается на `/` или `\`, что характерно для директорий
    if not path or path.endswith(('/', '\\')):
        return False  # Путь явно выглядит как директория
    # Проверим на наличие расширения
    if '.' in path.split('/')[-1]:  # Берём последнюю часть пути и ищем в ней точку
        return True
    return False


def start_factorio_server(save_path: str, config_path: str, log_path: str):
    """
    Запускает сервер Factorio с указанными аргументами.

    :param save_path: Путь к файлу сохранения (сейву).
    :param config_path: Путь к файлу настроек сервера.
    :param log_path: Путь для записи логов сервера.
    """
    try:
        # Команда для запуска сервера
        command = [
            "factorio",  # Убедитесь, что сервер Factorio добавлен в PATH или укажите полный путь к исполняемому файлу
            "--start-server", save_path,
            "--server-settings", config_path,
            "--console-log", log_path
        ]

        # Запуск сервера
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


        return process  # Вернем объект процесса для дальнейшего контроля
    except FileNotFoundError:
        print("Ошибка: исполняемый файл Factorio не найден. Проверьте, установлен ли сервер и добавлен ли путь к нему.")
    except Exception as e:
        print(f"Ошибка при запуске сервера: {e}")
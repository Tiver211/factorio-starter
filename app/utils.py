import os
import json


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

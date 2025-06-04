import os
from datetime import datetime


# def dict_to_json_string(data, indent=0):
#     """
#     Рекурсивно преобразует словарь в JSON-подобную строку.
#
#     :param data: Словарь или список для преобразования.
#     :param indent: Уровень отступа (используется для форматирования).
#     :return: JSON-подобная строка.
#     """
#     if isinstance(data, dict):
#         items = []
#         for key, value in data.items():
#             items.append(f'"{key}": {dict_to_json_string(value, indent)}')
#         return "{" + ", ".join(items) + "}"
#     elif isinstance(data, list):
#         items = []
#         for item in data:
#             items.append(dict_to_json_string(item, indent))
#         return "[" + ", ".join(items) + "]"
#     elif isinstance(data, str):
#         return f'"{data}"'
#     elif isinstance(data, (int, float, bool)):
#         return str(data).lower() if isinstance(data, bool) else str(data)
#     elif data is None:
#         return "null"
#     else:
#         raise TypeError(f"Неподдерживаемый тип данных: {type(data)}")
#
# def build_folder_structure(paths, max_depth=None, current_depth=0, base_paths=None):
#     """
#     Строит JSON-структуру папок и файлов с относительными путями.
#     Первые пути из списка добавляются как абсолютные, вложенные — как относительные.
#
#     :param paths: Список путей для обхода.
#     :param max_depth: Максимальная глубина вложенности (None — без ограничений).
#     :param current_depth: Текущая глубина вложенности (используется для рекурсии).
#     :param base_paths: Исходный список путей (для определения, какой путь является базовым).
#     :return: Словарь, представляющий структуру папок и файлов.
#     """
#     if base_paths is None:
#         base_paths = paths  # Сохраняем исходные пути для проверки
#
#     structure = {}
#
#     for path in paths:
#         # Проверяем, существует ли путь
#         if not os.path.exists(path):
#             print(f"Путь не существует: {path}")
#             continue
#
#         # Определяем, является ли текущий путь базовым (из исходного списка)
#         is_base_path = path in base_paths
#
#         # Получаем имя папки или файла
#         name = os.path.basename(path)
#
#         # Если это файл, добавляем его в структуру
#         if os.path.isfile(path):
#             if is_base_path:
#                 structure[path] = None  # Абсолютный путь для базовых файлов
#             else:
#                 structure[f"\\{name}"] = None  # Относительный путь для вложенных файлов
#             continue
#
#         # Если это директория, рекурсивно обходим её
#         if os.path.isdir(path):
#             contents = []
#             for entry in os.scandir(path):
#                 if entry.is_file():
#                     # Добавляем файл в структуру
#                     contents.append(f"\\{entry.name}")
#                 elif entry.is_dir():
#                     # Рекурсивно обходим вложенную папку, увеличивая глубину
#                     if max_depth is None or current_depth < max_depth:
#                         subfolder_structure = build_folder_structure(
#                             [entry.path], max_depth, current_depth + 1, base_paths
#                         )
#                         # Добавляем папку и её содержимое
#                         contents.append({f"\\{entry.name}": subfolder_structure})
#
#             # Добавляем текущую папку и её содержимое в структуру
#             if is_base_path:
#                 structure[path] = contents  # Абсолютный путь для базовых папок
#             else:
#                 structure[f"\\{name}"] = contents  # Относительный путь для вложенных папок
#
#
#     return dict_to_json_string(structure)


def collect_all_paths(paths, max_depth=None):
    all_paths = []

    def walk_directory(current_path, current_depth):
        if max_depth is not None and current_depth > max_depth:
            return  # Прекращаем обход, если достигнута максимальная глубина

        all_paths.append(current_path)

        # Обходим содержимое текущей папки
        with os.scandir(current_path) as entries:
            for entry in entries:
                if entry.is_dir():
                    # Рекурсивно обходим поддиректорию
                    walk_directory(entry.path, current_depth + 1)
                elif entry.is_file():
                    # Добавляем файл
                    all_paths.append(entry.path)

    # Обходим каждый из указанных путей
    for root_path in paths:
        if os.path.exists(root_path):
            walk_directory(root_path, current_depth=0)
        else:
            print(f"Путь не существует: {root_path}")

    return all_paths


def ensure_logs_dir_exists():
    if not os.path.exists('logs'):
        os.makedirs('logs')


def log_message(user_id: int, sender: str, message: str):
    ensure_logs_dir_exists()

    log_filename = f"logs/{user_id}.log"

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    log_entry = f"[{timestamp}] {sender.upper()}: {message}\n"

    with open(log_filename, 'a', encoding='utf-8') as log_file:
        log_file.write(log_entry)

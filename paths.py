# -*- coding: utf-8 -*-
"""Пути проекта и хранение пользовательских настроек.

Раньше аддоны и файлы искались относительно текущей папки (os.getcwd()),
поэтому IDE ломалась при запуске из ярлыка. Теперь всё считается от файлов
пакета, а настройки лежат в %APPDATA%/LppIDE/config.json.
"""

import json
import os

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(PACKAGE_DIR)
ADDONS_DIR = os.path.join(APP_DIR, "addons")
EXAMPLES_DIR = os.path.join(APP_DIR, "examples")

CONFIG_DIR = os.path.join(
    os.environ.get("APPDATA") or os.path.expanduser("~"), "LppIDE"
)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULTS = {
    "theme": "GitHub Dark",
    "edition": "Ultimate",
    "font_size": 14,
    "show_welcome": True,
    "first_run": True,
    "last_file": None,
}


def load_config():
    """Читает настройки, подставляя значения по умолчанию."""
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for key in DEFAULTS:
                if key in data:
                    cfg[key] = data[key]
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    """Сохраняет настройки. Ошибки записи не должны ронять IDE."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp = CONFIG_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CONFIG_FILE)
        return True
    except OSError:
        return False

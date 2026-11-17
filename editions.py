# -*- coding: utf-8 -*-
"""Издания L++: ограничения и возможности каждого варианта."""

EDITIONS = {
    "Home": {
        "max_lines": 200,
        "allow_addons": False,
        "allow_themes": False,
        "watermark": "HOME",
        "description": "Пробная: до 200 строк, без аддонов, без смены тем.",
    },
    "Ultimate": {
        "max_lines": 0,
        "allow_addons": True,
        "allow_themes": True,
        "watermark": "",
        "description": "Всё включено: темы, аддоны, без лимитов.",
    },
    "Classic": {
        "max_lines": 0,
        "allow_addons": True,
        "allow_themes": False,
        "watermark": "CLASSIC",
        "description": "Классика: только тёмная тема, аддоны есть.",
    },
}

DEFAULT_EDITION = "Ultimate"

# Порядок карточек в окне выбора издания.
EDITION_ORDER = ("Home", "Ultimate", "Classic")


def get_edition(name):
    return EDITIONS.get(name, EDITIONS[DEFAULT_EDITION])

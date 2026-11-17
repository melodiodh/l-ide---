# -*- coding: utf-8 -*-
"""Цветовые темы IDE. Каждая тема — набор именованных цветов."""

THEMES = {
    "GitHub Dark": {
        "bg_main": "#0D1117", "bg_panel": "#161B22", "bg_editor": "#0D1117",
        "bg_console": "#090C10", "fg_main": "#C9D1D9", "fg_muted": "#8B949E",
        "accent": "#58A6FF", "accent_green": "#238636", "accent_red": "#DA3633",
        "accent_purple": "#BC8CFF", "accent_orange": "#F0883E", "border": "#30363D",
    },
    "Light": {
        "bg_main": "#FFFFFF", "bg_panel": "#F6F8FA", "bg_editor": "#FFFFFF",
        "bg_console": "#F6F8FA", "fg_main": "#24292F", "fg_muted": "#57606A",
        "accent": "#0969DA", "accent_green": "#1A7F37", "accent_red": "#CF222E",
        "accent_purple": "#8250DF", "accent_orange": "#BC4C00", "border": "#D0D7DE",
    },
    "Ocean": {
        "bg_main": "#0F1C2E", "bg_panel": "#16293D", "bg_editor": "#0F1C2E",
        "bg_console": "#0A1522", "fg_main": "#E0F2FE", "fg_muted": "#7DA0C0",
        "accent": "#38BDF8", "accent_green": "#22C55E", "accent_red": "#EF4444",
        "accent_purple": "#A78BFA", "accent_orange": "#F59E0B", "border": "#1E3A54",
    },
    "Dracula": {
        "bg_main": "#282A36", "bg_panel": "#21222C", "bg_editor": "#282A36",
        "bg_console": "#1E1F29", "fg_main": "#F8F8F2", "fg_muted": "#6272A4",
        "accent": "#8BE9FD", "accent_green": "#50FA7B", "accent_red": "#FF5555",
        "accent_purple": "#BD93F9", "accent_orange": "#FFB86C", "border": "#44475A",
    },
}

DEFAULT_THEME = "GitHub Dark"


def get_theme(name):
    """Возвращает тему по имени, не падая на неизвестном имени."""
    return THEMES.get(name, THEMES[DEFAULT_THEME])

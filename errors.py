# -*- coding: utf-8 -*-
"""Ошибки языка L++ с единым форматом сообщений.

Все исключения ядра наследуются от LppError и знают номер строки/колонки,
чтобы IDE могла показать ошибку в понятном виде и подсветить место.
"""


class LppError(Exception):
    """Базовое исключение L++. Хранит сообщение и позицию в исходнике."""

    kind = "Ошибка"

    def __init__(self, message, line=None, col=None):
        self.message = message
        self.line = line
        self.col = col
        super().__init__(self.format())

    def format(self):
        if self.line is None:
            return f"{self.message}"
        if self.col:
            return f"Строка {self.line}, кол {self.col}: {self.message}"
        return f"Строка {self.line}: {self.message}"

    def with_line(self, line):
        """Возвращает копию ошибки с проставленной строкой (если её ещё нет)."""
        if self.line is None:
            return type(self)(self.message, line, self.col)
        return self


class LppSyntaxError(LppError):
    """Синтаксическая ошибка: лексер или парсер."""
    kind = "Синтаксис"


class LppRuntimeError(LppError):
    """Ошибка времени выполнения."""
    kind = "Выполнение"


class LppNameError(LppRuntimeError):
    """Обращение к необъявленной переменной/функции."""
    kind = "Имя"


class LppTypeError(LppRuntimeError):
    """Неверный тип значения."""
    kind = "Тип"


class LppIndexError(LppRuntimeError):
    """Индекс вне диапазона."""
    kind = "Индекс"


class LppInterrupt(LppRuntimeError):
    """Прерывание выполнения пользователем (кнопка «Стоп»)."""
    kind = "Прервано"

    def __init__(self):
        super().__init__("выполнение остановлено пользователем")

# -*- coding: utf-8 -*-
"""Встроенные функции L++ (стандартная библиотека ядра)."""

import math
import random

from .errors import LppIndexError, LppTypeError
from .runtime import LppInstance, LppNative


class CallableInt(int):
    """Целое, которое можно и прочитать, и вызвать.

    Нужно для совместимости: в старом коде встречались оба варианта —
    ``a.длина`` и ``a.длина()``. Теперь работают оба.
    """

    def __call__(self):
        return int(self)


def _as_number(v, what="значение"):
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return v
    raise LppTypeError(f"{what} должно быть числом, получено {type_name(v)}")


def type_name(v):
    """Русское имя типа значения."""
    if isinstance(v, bool):
        return "логическое"
    if isinstance(v, (int, float)):
        return "число"
    if isinstance(v, str):
        return "строка"
    if isinstance(v, list):
        return "массив"
    if isinstance(v, dict):
        return "словарь"
    if isinstance(v, LppInstance):
        return f"объект {v.cls.name}"
    if isinstance(v, LppNative) or callable(v):
        return "функция"
    return "неизвестно"


def to_display(v):
    """Строка для печати (истина/ложь, целые float без .0)."""
    if isinstance(v, bool):
        return "истина" if v else "ложь"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _длина(x):
    if isinstance(x, (str, list, dict)):
        return CallableInt(len(x))
    raise LppTypeError(f"длина не определена для типа {type_name(x)}")


def _тип(x):
    return type_name(x)


def _число(x):
    if isinstance(x, bool):
        return 1 if x else 0
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        s = x.strip()
        try:
            return int(s)
        except ValueError:
            pass
        try:
            f = float(s.replace(",", "."))
        except ValueError:
            raise LppTypeError(f"не удалось преобразовать '{x}' в число")
        return int(f) if f.is_integer() else f
    raise LppTypeError(f"не удалось преобразовать {type_name(x)} в число")


def _строка(x):
    return to_display(x)


def _мин(*args):
    values = _flatten(args)
    if not values:
        raise LppTypeError("мин() нужно хотя бы одно число")
    return min(values)


def _макс(*args):
    values = _flatten(args)
    if not values:
        raise LppTypeError("макс() нужно хотя бы одно число")
    return max(values)


def _flatten(args):
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        return list(args[0])
    return list(args)


def _абс(x):
    return abs(_as_number(x))


def _округ(x, n=0):
    return round(_as_number(x), int(_as_number(n, "точность")))


def _случайное(a=0, b=1):
    a = _as_number(a)
    b = _as_number(b)
    if isinstance(a, int) and isinstance(b, int):
        if a > b:
            a, b = b, a
        return random.randint(a, b)
    lo, hi = (a, b) if a <= b else (b, a)
    return random.uniform(lo, hi)


def _модуль(x):
    return math.fabs(_as_number(x))


def _дел(a, b):
    a = _as_number(a)
    b = _as_number(b)
    if b == 0:
        raise LppTypeError("деление на ноль")
    return a // b


def _степень(a, b):
    return _as_number(a) ** _as_number(b)


def _корень(x):
    x = _as_number(x)
    if x < 0:
        raise LppTypeError("корень из отрицательного числа")
    return math.sqrt(x)


def _срез(x, start=None, end=None):
    if not isinstance(x, (str, list)):
        raise LppTypeError(f"срез не определён для типа {type_name(x)}")
    s = None if start is None else int(_as_number(start))
    e = None if end is None else int(_as_number(end))
    return x[s:e]


def _сумма(*args):
    values = _flatten(args)
    total = 0
    for v in values:
        total += _as_number(v, "элемент массива")
    return total


def _диапазон(a, b=None, step=1):
    """диапазон(5) -> [0..4]; диапазон(2, 6) -> [2..5]; диапазон(0, 10, 2)."""
    if b is None:
        a, b = 0, a
    a = int(_as_number(a, "начало"))
    b = int(_as_number(b, "конец"))
    step = int(_as_number(step, "шаг"))
    if step == 0:
        raise LppTypeError("шаг диапазона не может быть 0")
    return list(range(a, b, step))


def _соединить(items, sep=""):
    if not isinstance(items, (list, tuple)):
        raise LppTypeError(f"соединить ожидает массив, получено {type_name(items)}")
    return str(sep).join(to_display(x) for x in items)


def _среднее(*args):
    values = _flatten(args)
    if not values:
        raise LppTypeError("среднее() нужен хотя бы один элемент")
    total = sum(_as_number(v, "элемент массива") for v in values)
    return total / len(values)


def make_builtins(interp):
    """Собирает словарь встроенных функций для интерпретатора."""
    g = {
        "пи": math.pi,
        "истина": True,
        "ложь": False,
        "вывести": LppNative("вывести", lambda *a: interp.print_values(*a)),
        "ввести": LppNative("ввести", lambda p="": interp.read_input(p)),
        "длина": LppNative("длина", _длина),
        "тип": LppNative("тип", _тип),
        "число": LppNative("число", _число),
        "строка": LppNative("строка", _строка),
        "мин": LppNative("мин", _мин),
        "макс": LppNative("макс", _макс),
        "абс": LppNative("абс", _абс),
        "округ": LppNative("округ", _округ),
        "случайное": LppNative("случайное", _случайное),
        "модуль": LppNative("модуль", _модуль),
        "дел": LppNative("дел", _дел),
        "степень": LppNative("степень", _степень),
        "корень": LppNative("корень", _корень),
        "сумма": LppNative("сумма", _сумма),
        "срез": LppNative("срез", _срез),
        "диапазон": LppNative("диапазон", _диапазон),
        "соединить": LppNative("соединить", _соединить),
        "среднее": LppNative("среднее", _среднее),
    }
    return g

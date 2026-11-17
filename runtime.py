# -*- coding: utf-8 -*-
"""Среда выполнения: области видимости, функции, сигналы управления.

Правила областей видимости L++:
  * блоки (если/пока/для) НЕ создают новую область — переменные видны снаружи;
  * функция создаёт свою область, параметры в ней локальны;
  * присваивание существующей переменной меняет её там, где она объявлена
    (поэтому глобальную переменную можно изменить из функции);
  * НОВАЯ переменная внутри функции остаётся локальной и наружу не утекает.
"""

from .errors import LppNameError, LppRuntimeError, LppTypeError


class Environment:
    def __init__(self, parent=None, is_function_scope=False):
        self.vars = {}
        self.parent = parent
        self.is_function_scope = is_function_scope

    # ---------- чтение ----------

    def get(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise LppNameError(f"переменная '{name}' не объявлена")

    def has(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return True
            env = env.parent
        return False

    # ---------- запись ----------

    def set(self, name, value):
        """Объявить переменную именно в этой области (параметры, счётчики)."""
        self.vars[name] = value

    def assign(self, name, value):
        """Присваивание с учётом областей видимости (см. правила в докстроке)."""
        env = self
        while env is not None:
            if name in env.vars:
                env.vars[name] = value
                return
            env = env.parent

        # переменной ещё нет — создаём в ближайшей «функциональной» области
        env = self
        while env.parent is not None and not env.is_function_scope:
            env = env.parent
        env.vars[name] = value


class LppFunction:
    """Пользовательская функция, определённая в L++."""

    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure

    def call(self, interp, args, line=None):
        if len(args) != len(self.params):
            raise LppTypeError(
                f"функция '{self.name}' ожидает {len(self.params)} арг., "
                f"передано {len(args)}",
                line,
            )
        env = Environment(self.closure, is_function_scope=True)
        for p, a in zip(self.params, args):
            env.set(p, a)
        try:
            interp.exec_block(self.body, env)
        except ReturnSignal as r:
            return r.value
        except (BreakSignal, ContinueSignal):
            return None
        return None

    def __repr__(self):
        return f"<функция {self.name}>"


class LppNative:
    """Встроенная функция (Python-callable), видимая из L++."""

    def __init__(self, name, fn):
        self.name = name
        self.fn = fn

    def __call__(self, *args):
        return self.fn(*args)

    def __repr__(self):
        return f"<встроенная {self.name}>"


class LppClass:
    """Класс, объявленный в L++: набор методов + окружение объявления."""

    def __init__(self, name, methods, closure):
        self.name = name
        self.methods = methods          # имя -> FuncDef
        self.closure = closure

    def __repr__(self):
        return f"<класс {self.name}>"


class LppInstance:
    """Экземпляр класса L++. Поля — обычный словарь."""

    def __init__(self, cls):
        self.cls = cls
        self.fields = {}

    def __repr__(self):
        return f"<{self.cls.name}>"


class ReturnSignal(Exception):
    def __init__(self, v):
        self.value = v

class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass

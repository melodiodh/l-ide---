# -*- coding: utf-8 -*-
"""Интерпретатор L++: обходит AST и выполняет программу."""

import importlib
import os
import sys

from .builtins import CallableInt, make_builtins, to_display, type_name
from .errors import (
    LppError, LppIndexError, LppInterrupt, LppNameError, LppRuntimeError,
    LppTypeError,
)
from .lexer import Lexer
from .nodes import (
    Array, Assign, Attr, BinOp, Bool, Break, Call, ClassDef, Continue, DictLit,
    ExprStmt, For, ForEach, FuncDef, If, Include, Index, MultiAssign, New, Num,
    Return, Str, Switch, TryCatch, UnOp, Var, While,
)
from .parser import Parser
from .runtime import (
    BreakSignal, ContinueSignal, Environment, LppClass, LppFunction,
    LppInstance, LppNative, ReturnSignal,
)

# Модули, которые можно подключить без папки addons/.
STDLIB_MODULES = ("random", "math", "time", "os", "sys", "json", "re")


class Interpreter:
    """Выполняет программу на L++.

    Параметры:
        output      — callable(str), куда уходит вывод ``вывести``;
        input_reader— callable(prompt) -> str для ``ввести``;
        addons_dir  — папка с аддонами (по умолчанию addons/ рядом с проектом);
        should_stop — callable() -> bool, проверяется в циклах (кнопка «Стоп»).
    """

    MAX_ITERATIONS = 5_000_000

    def __init__(self, output=None, input_reader=None, addons_dir=None,
                 should_stop=None, notice=None, base_dir=None):
        self.out = output or (lambda s: print(s, end=""))
        self.input_reader = input_reader or input
        self.addons_dir = addons_dir
        self.should_stop = should_stop
        self.notice = notice
        self.base_dir = base_dir
        self.global_env = Environment()
        self._loaded = {}
        self._loaded_files = set()
        for name, value in make_builtins(self).items():
            self.global_env.set(name, value)

    # ------------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------------

    def run(self, source):
        """Лексер → парсер → выполнение. Ошибки приходят как LppError."""
        try:
            tokens = Lexer(source).tokenize()
            program = Parser(tokens).program()
            self.exec_block(program, self.global_env)
        except LppError:
            raise
        except RecursionError:
            raise LppRuntimeError(
                "слишком глубокая рекурсия (проверьте условие выхода из функции)"
            )

    def parse(self, source):
        """Только разбор без выполнения — полезно для проверки синтаксиса."""
        return Parser(Lexer(source).tokenize()).program()

    # ------------------------------------------------------------------
    # Вывод и ввод
    # ------------------------------------------------------------------

    def print_values(self, *args):
        self.out(" ".join(to_display(a) for a in args) + "\n")

    def read_input(self, prompt=""):
        value = self.input_reader(prompt)
        return "" if value is None else value

    # ------------------------------------------------------------------
    # Выполнение операторов
    # ------------------------------------------------------------------

    def _check_stop(self):
        if self.should_stop is not None and self.should_stop():
            raise LppInterrupt()

    def exec_block(self, body, env):
        self._check_stop()
        for node in body:
            self.exec_node(node, env)

    def exec_node(self, node, env):
        t = type(node)

        if t is ExprStmt:
            self.eval(node.expr, env)
            return

        if t is Assign:
            value = self.eval(node.expr, env)
            self._assign(node.target, value, env)
            return

        if t is MultiAssign:
            value = self.eval(node.expr, env)
            for target in node.targets:
                self._assign(target, value, env)
            return

        if t is If:
            for cond, body in node.branches:
                if self._truthy(self.eval(cond, env)):
                    self.exec_block(body, env)
                    return
            if node.else_body is not None:
                self.exec_block(node.else_body, env)
            return

        if t is While:
            count = 0
            while self._truthy(self.eval(node.cond, env)):
                count += 1
                if count > self.MAX_ITERATIONS:
                    raise LppRuntimeError("бесконечный цикл (слишком много итераций)", node.line)
                if count % 64 == 0:
                    self._check_stop()
                try:
                    self.exec_block(node.body, env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return

        if t is For:
            start = self.eval(node.a, env)
            end = self.eval(node.b, env)
            step = self.eval(node.step, env) if node.step else 1
            if step == 0:
                raise LppRuntimeError("шаг не может быть 0", node.line)
            value = start
            ascending = step > 0
            count = 0
            while (value <= end) if ascending else (value >= end):
                count += 1
                if count > self.MAX_ITERATIONS:
                    raise LppRuntimeError("слишком много итераций в 'для'", node.line)
                if count % 64 == 0:
                    self._check_stop()
                env.set(node.var, value)
                try:
                    self.exec_block(node.body, env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    pass
                value += step
            return

        if t is ForEach:
            iterable = self.eval(node.iterable, env)
            if isinstance(iterable, dict):
                items = list(iterable.keys())
            elif isinstance(iterable, (list, str)):
                items = list(iterable)
            else:
                raise LppTypeError(
                    f"нельзя перебрать {type_name(iterable)}", node.line
                )
            for item in items:
                self._check_stop()
                env.set(node.var, item)
                try:
                    self.exec_block(node.body, env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return

        if t is Switch:
            subject = self.eval(node.subject, env)
            for values, body in node.cases:
                for value_node in values:
                    if self.eval(value_node, env) == subject:
                        self.exec_block(body, env)
                        return
            if node.else_body is not None:
                self.exec_block(node.else_body, env)
            return

        if t is TryCatch:
            try:
                self.exec_block(node.body, env)
            except LppInterrupt:
                raise
            except LppError as exc:
                if node.var:
                    env.set(node.var, str(exc))
                self.exec_block(node.handler, env)
            return

        if t is ClassDef:
            env.set(node.name, LppClass(node.name, node.methods, env))
            return

        if t is FuncDef:
            env.set(node.name, LppFunction(node.name, node.params, node.body, env))
            return

        if t is Return:
            raise ReturnSignal(self.eval(node.expr, env) if node.expr else None)

        if t is Break:
            raise BreakSignal()

        if t is Continue:
            raise ContinueSignal()

        if t is Include:
            self._include(node, env)
            return

        raise LppRuntimeError(f"неизвестный узел: {t.__name__}", getattr(node, "line", None))

    def _assign(self, target, value, env):
        t = type(target)

        if t is Var:
            env.assign(target.n, value)
            return

        if t is Index:
            container = self.eval(target.obj, env)
            key = self.eval(target.idx, env)
            if isinstance(container, dict):
                container[key] = value
                return
            if isinstance(container, list):
                idx = self._to_index(key, target.line)
                if idx < 0:
                    idx += len(container)
                if idx < 0 or idx >= len(container):
                    raise LppIndexError(
                        f"индекс {key} вне диапазона (длина {len(container)})", target.line
                    )
                container[idx] = value
                return
            raise LppTypeError(
                f"нельзя индексировать {type_name(container)}", target.line
            )

        if t is Attr:
            obj = self.eval(target.obj, env)
            if isinstance(obj, LppInstance):
                obj.fields[target.name] = value
                return
            try:
                setattr(obj, target.name, value)
            except Exception as e:
                raise LppRuntimeError(
                    f"не удалось присвоить '{target.name}': {e}", target.line
                )
            return

        raise LppRuntimeError("недопустимая цель присваивания", target.line)

    def _to_index(self, key, line=None):
        if isinstance(key, bool) or not isinstance(key, (int, float)):
            raise LppTypeError(f"индекс должен быть числом, получено {type_name(key)}", line)
        if isinstance(key, float):
            if not key.is_integer():
                raise LppIndexError(f"индекс должен быть целым, получено {key}", line)
            return int(key)
        return key

    # ------------------------------------------------------------------
    # Подключение модулей
    # ------------------------------------------------------------------

    def _include(self, node, env):
        if getattr(node, "is_file", False):
            self._include_file(node.name, env, node.line)
            return
        name = node.name
        root = name.split(".")[0]
        module = self._load_module(name, node.line)
        env.set(root, module)
        if self.notice:
            self.notice(f"[Модуль {name} подключён]\n")

    def _include_file(self, path, env, line=None):
        """включить "файл.lpp" — выполняет файл в текущем окружении."""
        base = self.base_dir or os.getcwd()
        full = path if os.path.isabs(path) else os.path.join(base, path)
        full = os.path.abspath(full)

        if full in self._loaded_files:
            return
        if not os.path.isfile(full):
            raise LppRuntimeError(f"файл '{path}' не найден", line)

        self._loaded_files.add(full)
        try:
            with open(full, "r", encoding="utf-8") as f:
                source = f.read()
        except OSError as e:
            raise LppRuntimeError(f"не удалось прочитать '{path}': {e}", line)

        previous = self.base_dir
        self.base_dir = os.path.dirname(full)
        try:
            program = Parser(Lexer(source).tokenize()).program()
            self.exec_block(program, env)
        finally:
            self.base_dir = previous

        if self.notice:
            self.notice(f"[Файл {path} подключён]\n")

    def _load_module(self, name, line=None):
        if name in self._loaded:
            return self._loaded[name]

        root = name.split(".")[0]
        try:
            if root in STDLIB_MODULES:
                module = importlib.import_module(name)
            else:
                addons = self._addons_dir()
                if not os.path.isdir(addons):
                    raise LppRuntimeError(
                        f"папка аддонов не найдена: {addons}", line
                    )
                if addons not in sys.path:
                    sys.path.insert(0, addons)
                # сбрасываем кэш, чтобы правки в файлах аддонов подхватывались
                for key in [k for k in sys.modules if k == root or k.startswith(root + ".")]:
                    del sys.modules[key]
                module = importlib.import_module(name)
        except LppError:
            raise
        except ImportError as e:
            raise LppRuntimeError(
                f"модуль '{name}' не найден (ищите addons/{name}.py или addons/{name}/)", line
            )
        except Exception as e:
            raise LppRuntimeError(f"ошибка подключения '{name}': {e}", line)

        self._loaded[name] = module
        return module

    def _addons_dir(self):
        if self.addons_dir:
            return self.addons_dir
        try:
            from .paths import ADDONS_DIR
            return ADDONS_DIR
        except Exception:  # pragma: no cover
            return os.path.abspath("addons")

    # ------------------------------------------------------------------
    # Истинность и выражения
    # ------------------------------------------------------------------

    def _truthy(self, v):
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return v != 0
        if isinstance(v, (str, list, dict)):
            return len(v) > 0
        return True

    def eval(self, node, env):
        t = type(node)

        if t is Num:
            return node.v
        if t is Str:
            return node.v
        if t is Bool:
            return node.v
        if t is Var:
            return env.get(node.n)
        if t is Array:
            return [self.eval(x, env) for x in node.items]
        if t is DictLit:
            return {self.eval(k, env): self.eval(v, env) for k, v in node.pairs}

        if t is UnOp:
            value = self.eval(node.e, env)
            if node.op == "-":
                return -self._number(value, node.line)
            if node.op == "+":
                return +self._number(value, node.line)
            if node.op == "не":
                return not self._truthy(value)
            raise LppRuntimeError(f"неизвестный оператор '{node.op}'", node.line)

        if t is BinOp:
            return self._binop(node, env)

        if t is Index:
            container = self.eval(node.obj, env)
            key = self.eval(node.idx, env)
            return self._index(container, key, node.line)

        if t is Attr:
            obj = self.eval(node.obj, env)
            return self._attr(obj, node.name, node.line)

        if t is Call:
            fn = self.eval(node.fn, env)
            args = [self.eval(a, env) for a in node.args]
            return self._call(fn, args, node.line)

        if t is New:
            cls = env.get(node.cls)
            if not isinstance(cls, LppClass):
                raise LppTypeError(f"'{node.cls}' не является классом", node.line)
            instance = LppInstance(cls)
            constructor = cls.methods.get("создать")
            args = [self.eval(a, env) for a in node.args]
            if constructor is not None:
                self._call_method(instance, constructor, args, node.line)
            elif args:
                raise LppTypeError(
                    f"у класса '{node.cls}' нет метода 'создать'", node.line
                )
            return instance

        raise LppRuntimeError(f"неизвестное выражение: {t.__name__}",
                              getattr(node, "line", None))

    def _number(self, v, line=None):
        if isinstance(v, bool):
            return int(v)
        if isinstance(v, (int, float)):
            return v
        raise LppTypeError(f"ожидалось число, получено {type_name(v)}", line)

    def _index(self, container, key, line=None):
        if isinstance(container, (list, str)):
            idx = self._to_index(key, line)
            try:
                return container[idx]
            except IndexError:
                raise LppIndexError(
                    f"индекс {key} вне диапазона (длина {len(container)})", line
                )
        if isinstance(container, dict):
            try:
                return container[key]
            except KeyError:
                raise LppIndexError(f"ключа '{key}' нет в словаре", line)
        raise LppTypeError(f"нельзя индексировать {type_name(container)}", line)

    def _binop(self, node, env):
        op = node.op

        # короткое замыкание
        if op == "и":
            left = self.eval(node.l, env)
            if not self._truthy(left):
                return False
            return self._truthy(self.eval(node.r, env))
        if op == "или":
            left = self.eval(node.l, env)
            if self._truthy(left):
                return True
            return self._truthy(self.eval(node.r, env))

        left = self.eval(node.l, env)
        right = self.eval(node.r, env)
        line = node.line

        try:
            if op == "+":
                return left + right
            if op == "-":
                return self._number(left, line) - self._number(right, line)
            if op == "*":
                return left * right
            if op == "/":
                if self._number(right, line) == 0:
                    raise ZeroDivisionError
                return self._number(left, line) / right
            if op == "%":
                if self._number(right, line) == 0:
                    raise ZeroDivisionError
                return self._number(left, line) % right
            if op == "**":
                return self._number(left, line) ** self._number(right, line)
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == "<":
                return left < right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            if op == ">=":
                return left >= right
        except ZeroDivisionError:
            raise LppRuntimeError("деление на ноль", line)
        except TypeError:
            raise LppTypeError(
                f"нельзя применить '{op}' к {type_name(left)} и {type_name(right)}", line
            )
        except Exception as e:
            raise LppRuntimeError(f"ошибка в '{op}': {e}", line)

        raise LppRuntimeError(f"неизвестный оператор '{op}'", line)

    # ------------------------------------------------------------------
    # Свойства и методы значений
    # ------------------------------------------------------------------

    def _attr(self, obj, name, line=None):
        # объект класса L++
        if isinstance(obj, LppInstance):
            if name in obj.fields:
                return obj.fields[name]
            method = obj.cls.methods.get(name)
            if method is not None:
                return LppNative(
                    name, lambda *a: self._call_method(obj, method, list(a), line)
                )
            raise LppRuntimeError(
                f"у объекта '{obj.cls.name}' нет свойства '{name}'", line
            )

        # строка
        if isinstance(obj, str):
            methods = {
                "верхний": lambda: obj.upper(),
                "нижний": lambda: obj.lower(),
                "разбить": lambda sep=None: obj.split(sep),
                "заменить": lambda a, b: obj.replace(str(a), str(b)),
                "найти": lambda x: obj.find(str(x)),
                "обрезать": lambda: obj.strip(),
                "начать_с": lambda x: obj.startswith(str(x)),
                "кончить_на": lambda x: obj.endswith(str(x)),
                "символ": lambda i: obj[int(i)],
            }
            if name == "длина":
                return CallableInt(len(obj))
            if name in methods:
                return LppNative(name, methods[name])

        # массив
        if isinstance(obj, list):
            methods = {
                "добавить": lambda x: obj.append(x),
                "вставить": lambda i, x: obj.insert(int(i), x),
                "сортировать": lambda: obj.sort(),
                "перевернуть": lambda: obj.reverse(),
                "очистить": lambda: obj.clear(),
                "содержит": lambda x: x in obj,
                "индекс": lambda x: obj.index(x) if x in obj else -1,
                "срез": lambda a, b: obj[int(a):int(b)],
                "копия": lambda: list(obj),
            }
            if name == "длина":
                return CallableInt(len(obj))
            if name == "удалить":
                def _remove(x):
                    try:
                        obj.remove(x)
                        return True
                    except ValueError:
                        return False
                return LppNative(name, _remove)
            if name in methods:
                return LppNative(name, methods[name])

        # словарь
        if isinstance(obj, dict):
            methods = {
                "ключи": lambda: list(obj.keys()),
                "значения": lambda: list(obj.values()),
                "есть": lambda k: k in obj,
                "получить": lambda k, default=None: obj.get(k, default),
                "очистить": lambda: obj.clear(),
            }
            if name == "длина":
                return CallableInt(len(obj))
            if name == "удалить":
                def _remove_key(k):
                    try:
                        del obj[k]
                        return True
                    except KeyError:
                        return False
                return LppNative(name, _remove_key)
            if name in methods:
                return LppNative(name, methods[name])

        # модули, объекты Python, классы
        try:
            value = getattr(obj, name)
        except AttributeError:
            raise LppRuntimeError(
                f"у {type_name(obj)} нет свойства '{name}'", line
            )
        if callable(value):
            return LppNative(name, value)
        return value

    def _call_method(self, instance, fdef, args, line=None):
        """Вызов метода класса: в окружение подставляется 'я'."""
        if len(args) != len(fdef.params):
            raise LppTypeError(
                f"метод '{fdef.name}' ожидает {len(fdef.params)} арг., "
                f"передано {len(args)}", line
            )
        env = Environment(instance.cls.closure, is_function_scope=True)
        env.set("я", instance)
        for p, a in zip(fdef.params, args):
            env.set(p, a)
        try:
            self.exec_block(fdef.body, env)
        except ReturnSignal as r:
            return r.value
        except (BreakSignal, ContinueSignal):
            return None
        return None

    def _call(self, fn, args, line=None):
        if isinstance(fn, LppFunction):
            return fn.call(self, args, line)

        if isinstance(fn, LppNative):
            try:
                return fn.fn(*args)
            except LppError as e:
                raise e.with_line(line)
            except TypeError as e:
                raise LppTypeError(f"неверные аргументы для '{fn.name}': {e}", line)
            except Exception as e:
                raise LppRuntimeError(f"ошибка в '{fn.name}': {e}", line)

        if callable(fn):
            try:
                return fn(*args)
            except LppError as e:
                raise e.with_line(line)
            except TypeError as e:
                raise LppTypeError(f"неверные аргументы: {e}", line)
            except Exception as e:
                raise LppRuntimeError(f"ошибка вызова: {e}", line)

        raise LppTypeError(f"{to_display(fn)} не является функцией", line)

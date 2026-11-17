# -*- coding: utf-8 -*-
"""AST-узлы L++. Простые классы с __slots__ — быстрые и предсказуемые."""


class Node:
    __slots__ = ()


class Num(Node):
    __slots__ = ("v", "line")

    def __init__(self, v, l):
        self.v = v
        self.line = l


class Str(Node):
    __slots__ = ("v", "line")

    def __init__(self, v, l):
        self.v = v
        self.line = l


class Bool(Node):
    __slots__ = ("v", "line")

    def __init__(self, v, l):
        self.v = v
        self.line = l


class Var(Node):
    __slots__ = ("n", "line")

    def __init__(self, n, l):
        self.n = n
        self.line = l


class Array(Node):
    __slots__ = ("items", "line")

    def __init__(self, i, l):
        self.items = i
        self.line = l


class DictLit(Node):
    __slots__ = ("pairs", "line")

    def __init__(self, p, l):
        self.pairs = p
        self.line = l


class BinOp(Node):
    __slots__ = ("op", "l", "r", "line")

    def __init__(self, o, a, b, ln):
        self.op = o
        self.l = a
        self.r = b
        self.line = ln


class UnOp(Node):
    __slots__ = ("op", "e", "line")

    def __init__(self, o, e, ln):
        self.op = o
        self.e = e
        self.line = ln


class Index(Node):
    __slots__ = ("obj", "idx", "line")

    def __init__(self, o, i, ln):
        self.obj = o
        self.idx = i
        self.line = ln


class Attr(Node):
    __slots__ = ("obj", "name", "line")

    def __init__(self, o, n, ln):
        self.obj = o
        self.name = n
        self.line = ln


class Call(Node):
    __slots__ = ("fn", "args", "line")

    def __init__(self, f, a, ln):
        self.fn = f
        self.args = a
        self.line = ln


class Assign(Node):
    """Одиночное присваивание: цель = выражение."""

    __slots__ = ("target", "expr", "line")

    def __init__(self, t, e, ln):
        self.target = t
        self.expr = e
        self.line = ln


class MultiAssign(Node):
    """Цепочка присваиваний: a = b = c = выражение."""

    __slots__ = ("targets", "expr", "line")

    def __init__(self, targets, e, ln):
        self.targets = targets
        self.expr = e
        self.line = ln


class If(Node):
    __slots__ = ("branches", "else_body", "line")

    def __init__(self, b, e, ln):
        self.branches = b
        self.else_body = e
        self.line = ln


class While(Node):
    __slots__ = ("cond", "body", "line")

    def __init__(self, c, b, ln):
        self.cond = c
        self.body = b
        self.line = ln


class For(Node):
    __slots__ = ("var", "a", "b", "step", "body", "line")

    def __init__(self, v, a, b, st, bd, ln):
        self.var = v
        self.a = a
        self.b = b
        self.step = st
        self.body = bd
        self.line = ln


class FuncDef(Node):
    __slots__ = ("name", "params", "body", "line")

    def __init__(self, n, p, b, ln):
        self.name = n
        self.params = p
        self.body = b
        self.line = ln


class Return(Node):
    __slots__ = ("expr", "line")

    def __init__(self, e, ln):
        self.expr = e
        self.line = ln


class Break(Node):
    __slots__ = ("line",)

    def __init__(self, l):
        self.line = l


class Continue(Node):
    __slots__ = ("line",)

    def __init__(self, l):
        self.line = l


class Include(Node):
    __slots__ = ("name", "line", "is_file")

    def __init__(self, n, l, is_file=False):
        self.name = n
        self.line = l
        self.is_file = is_file


class ForEach(Node):
    """для каждого x из коллекция то … конец"""

    __slots__ = ("var", "iterable", "body", "line")

    def __init__(self, v, it, b, ln):
        self.var = v
        self.iterable = it
        self.body = b
        self.line = ln


class Switch(Node):
    """выбрать выражение: вариант 1: … иначе: … конец"""

    __slots__ = ("subject", "cases", "else_body", "line")

    def __init__(self, s, cases, else_body, ln):
        self.subject = s
        self.cases = cases
        self.else_body = else_body
        self.line = ln


class TryCatch(Node):
    """попробовать: … поймать ошибка: … конец"""

    __slots__ = ("body", "handler", "var", "line")

    def __init__(self, b, h, v, ln):
        self.body = b
        self.handler = h
        self.var = v
        self.line = ln


class ClassDef(Node):
    """класс Имя: функция метод(…) … конец … конец"""

    __slots__ = ("name", "methods", "line")

    def __init__(self, n, m, ln):
        self.name = n
        self.methods = m
        self.line = ln


class New(Node):
    """новый Имя(аргументы)"""

    __slots__ = ("cls", "args", "line")

    def __init__(self, c, a, ln):
        self.cls = c
        self.args = a
        self.line = ln


class ExprStmt(Node):
    __slots__ = ("expr", "line")

    def __init__(self, e, l):
        self.expr = e
        self.line = l

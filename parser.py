# -*- coding: utf-8 -*-
"""Парсер L++: строит AST из потока токенов.

Грамматика — рекурсивный спуск с обычной приоритетностью операторов:
    или < и < не < сравнения < +- < */% < унарные < ** < постфиксы.
"""

from .errors import LppSyntaxError
from .nodes import (
    Array, Assign, Attr, BinOp, Bool, Break, Call, ClassDef, Continue, DictLit,
    ExprStmt, For, ForEach, FuncDef, If, Include, Index, MultiAssign, New, Num,
    Return, Str, Switch, TryCatch, UnOp, Var, While,
)

COMPARE_OPS = ("==", "!=", "<", ">", "<=", ">=")
ADD_OPS = ("+", "-")
MUL_OPS = ("*", "/", "%")
ASSIGN_TARGETS = (Var, Index, Attr)


class Parser:
    def __init__(self, toks):
        self.toks = toks
        self.pos = 0

    # ---------- работа с токенами ----------

    def peek(self, o=0):
        i = self.pos + o
        if i >= len(self.toks):
            return self.toks[-1]          # EOF
        return self.toks[i]

    def next(self):
        t = self.toks[self.pos]
        if t.type != "EOF":
            self.pos += 1
        return t

    def check(self, ty, val=None):
        t = self.peek()
        return t.type == ty and (val is None or t.value == val)

    def ckw(self, kw):
        return self.check("KW", kw)

    def cop(self, op):
        return self.check("OP", op)

    def expect(self, ty, val=None, msg=None):
        if not self.check(ty, val):
            t = self.peek()
            raise LppSyntaxError(
                msg or f"ожидалось {val or ty}, получено '{t.value}'", t.line
            )
        return self.next()

    def ekw(self, kw):
        t = self.peek()
        if not self.ckw(kw):
            raise LppSyntaxError(f"ожидалось '{kw}', получено '{t.value}'", t.line)
        return self.next()

    def eop(self, op):
        t = self.peek()
        if not self.cop(op):
            raise LppSyntaxError(f"ожидалось '{op}', получено '{t.value}'", t.line)
        return self.next()

    # ---------- программа и блоки ----------

    def program(self):
        body = []
        while not self.check("EOF"):
            if self.cop(":"):
                self.next()
                continue
            if self.ckw("конец"):
                t = self.peek()
                raise LppSyntaxError("лишний 'конец' — не закрывает ни один блок", t.line)
            body.append(self.stmt())
        return body

    def block_until(self, *end_kws):
        """Читает операторы до одного из завершающих ключевых слов (не съедая его)."""
        start = self.peek().line
        body = []
        while True:
            if self.check("EOF"):
                raise LppSyntaxError(
                    f"не хватает '{end_kws[-1]}' (блок открыт здесь)", start
                )
            if self.check("KW") and self.peek().value in end_kws:
                break
            if self.cop(":"):
                self.next()
                continue
            body.append(self.stmt())
        return body

    # ---------- операторы ----------

    def stmt(self):
        t = self.peek()
        ln = t.line

        if self.ckw("если"):
            return self.parse_if()
        if self.ckw("пока"):
            return self.parse_while()
        if self.ckw("для"):
            return self.parse_for()
        if self.ckw("функция"):
            return self.parse_func()
        if self.ckw("класс"):
            return self.parse_class()
        if self.ckw("выбрать"):
            return self.parse_switch()
        if self.ckw("попробовать"):
            return self.parse_try()

        if self.ckw("вернуть"):
            self.next()
            if self.check("EOF") or (self.check("KW") and self.peek().value in ("конец", "иначе")):
                return Return(None, ln)
            return Return(self.expr(), ln)

        if self.ckw("прервать"):
            self.next()
            return Break(ln)

        if self.ckw("продолжить"):
            self.next()
            return Continue(ln)

        if self.ckw("включить"):
            return self.parse_include()

        # присваивание или выражение
        e = self.expr()
        if self.cop("="):
            targets = [e]
            while self.cop("="):
                self.next()
                targets.append(self.expr())
            value = targets.pop()
            for tgt in targets:
                if not isinstance(tgt, ASSIGN_TARGETS):
                    raise LppSyntaxError("недопустимая цель присваивания", ln)
            if len(targets) == 1:
                return Assign(targets[0], value, ln)
            return MultiAssign(targets, value, ln)
        return ExprStmt(e, ln)

    def parse_include(self):
        ln = self.ekw("включить").line
        # включить "файл.lpp" — подключение другого файла программы
        if self.check("STRING"):
            return Include(self.next().value, ln, is_file=True)
        if not self.check("ID"):
            raise LppSyntaxError("после 'включить' ожидалось имя модуля или файл в кавычках", ln)
        parts = [self.next().value]
        while self.cop("."):
            self.next()
            if not self.check("ID"):
                raise LppSyntaxError("после '.' ожидалось имя", ln)
            parts.append(self.next().value)
        return Include(".".join(parts), ln)

    def parse_if(self):
        ln = self.ekw("если").line
        branches = []
        cond = self.expr()
        self.ekw("то")
        if self.cop(":"):
            self.next()
        branches.append((cond, self.block_until("иначе", "конец")))

        else_body = None
        while self.ckw("иначе"):
            self.next()
            if self.ckw("если"):
                self.next()
                c2 = self.expr()
                self.ekw("то")
                if self.cop(":"):
                    self.next()
                branches.append((c2, self.block_until("иначе", "конец")))
            else:
                if self.cop(":"):
                    self.next()
                else_body = self.block_until("конец")
                break

        self.ekw("конец")
        return If(branches, else_body, ln)

    def parse_while(self):
        ln = self.ekw("пока").line
        cond = self.expr()
        self.ekw("то")
        if self.cop(":"):
            self.next()
        body = self.block_until("конец")
        self.ekw("конец")
        return While(cond, body, ln)

    def parse_for(self):
        ln = self.ekw("для").line

        # для каждого x из коллекция то … конец
        if self.ckw("каждого"):
            self.next()
            if not self.check("ID"):
                raise LppSyntaxError("ожидалось имя переменной после 'каждого'", ln)
            var = self.next().value
            self.ekw("из")
            iterable = self.expr()
            self.ekw("то")
            if self.cop(":"):
                self.next()
            body = self.block_until("конец")
            self.ekw("конец")
            return ForEach(var, iterable, body, ln)

        if not self.check("ID"):
            raise LppSyntaxError("ожидалось имя счётчика", ln)
        var = self.next().value
        self.ekw("от")
        start = self.expr()
        self.ekw("до")
        end = self.expr()
        step = None
        if self.ckw("шаг"):
            self.next()
            step = self.expr()
        self.ekw("то")
        if self.cop(":"):
            self.next()
        body = self.block_until("конец")
        self.ekw("конец")
        return For(var, start, end, step, body, ln)

    def parse_func(self):
        ln = self.ekw("функция").line
        if not self.check("ID"):
            raise LppSyntaxError("ожидалось имя функции", ln)
        name = self.next().value
        self.eop("(")
        params = []
        if not self.cop(")"):
            while True:
                params.append(self.expect("ID", msg="ожидалось имя параметра").value)
                if self.cop(","):
                    self.next()
                    continue
                break
        self.eop(")")
        if self.cop(":"):
            self.next()
        body = self.block_until("конец")
        self.ekw("конец")
        return FuncDef(name, params, body, ln)

    def parse_class(self):
        ln = self.ekw("класс").line
        if not self.check("ID"):
            raise LppSyntaxError("ожидалось имя класса", ln)
        name = self.next().value
        if self.cop(":"):
            self.next()
        body = self.block_until("конец")
        self.ekw("конец")

        methods = {}
        for node in body:
            if not isinstance(node, FuncDef):
                raise LppSyntaxError(
                    "внутри класса могут быть только функции", getattr(node, "line", ln)
                )
            methods[node.name] = node
        return ClassDef(name, methods, ln)

    def parse_switch(self):
        ln = self.ekw("выбрать").line
        subject = self.expr()
        if self.cop(":"):
            self.next()

        cases = []
        else_body = None
        while True:
            if self.ckw("вариант"):
                self.next()
                values = [self.expr()]
                while self.cop(","):
                    self.next()
                    values.append(self.expr())
                if self.cop(":"):
                    self.next()
                cases.append((values, self.block_until("вариант", "иначе", "конец")))
                continue
            if self.ckw("иначе"):
                self.next()
                if self.cop(":"):
                    self.next()
                else_body = self.block_until("конец")
                break
            if self.check("EOF"):
                raise LppSyntaxError("не хватает 'конец' в 'выбрать'", ln)
            break

        self.ekw("конец")
        return Switch(subject, cases, else_body, ln)

    def parse_try(self):
        ln = self.ekw("попробовать").line
        if self.cop(":"):
            self.next()
        body = self.block_until("поймать")
        self.ekw("поймать")
        var = None
        if self.check("ID"):
            var = self.next().value
        if self.cop(":"):
            self.next()
        handler = self.block_until("конец")
        self.ekw("конец")
        return TryCatch(body, handler, var, ln)

    # ---------- выражения ----------

    def expr(self):
        return self.parse_or()
    def parse_or(self):
        left = self.parse_and()
        while self.ckw("или"):
            self.next()
            right = self.parse_and()
            left = BinOp("или", left, right, left.line)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.ckw("и"):
            self.next()
            right = self.parse_not()
            left = BinOp("и", left, right, left.line)
        return left

    def parse_not(self):
        if self.ckw("не"):
            ln = self.next().line
            return UnOp("не", self.parse_not(), ln)
        return self.parse_cmp()

    def parse_cmp(self):
        left = self.parse_add()
        while self.peek().type == "OP" and self.peek().value in COMPARE_OPS:
            op = self.next().value
            right = self.parse_add()
            left = BinOp(op, left, right, left.line)
        return left

    def parse_add(self):
        left = self.parse_mul()
        while self.peek().type == "OP" and self.peek().value in ADD_OPS:
            op = self.next().value
            right = self.parse_mul()
            left = BinOp(op, left, right, left.line)
        return left

    def parse_mul(self):
        left = self.parse_unary()
        while self.peek().type == "OP" and self.peek().value in MUL_OPS:
            op = self.next().value
            right = self.parse_unary()
            left = BinOp(op, left, right, left.line)
        return left

    def parse_unary(self):
        t = self.peek()
        if t.type == "OP" and t.value in ("-", "+"):
            self.next()
            return UnOp(t.value, self.parse_unary(), t.line)
        return self.parse_pow()

    def parse_pow(self):
        left = self.parse_postfix()
        if self.cop("**"):
            self.next()
            right = self.parse_unary()      # право-ассоциативно: 2**3**2 == 512
            return BinOp("**", left, right, left.line)
        return left

    def parse_postfix(self):
        node = self.parse_primary()
        while True:
            if self.cop("("):
                self.next()
                args = []
                if not self.cop(")"):
                    while True:
                        args.append(self.expr())
                        if self.cop(","):
                            self.next()
                            continue
                        break
                self.eop(")")
                node = Call(node, args, node.line)
            elif self.cop("["):
                self.next()
                idx = self.expr()
                self.eop("]")
                node = Index(node, idx, node.line)
            elif self.cop("."):
                self.next()
                if not self.check("ID"):
                    raise LppSyntaxError("ожидалось имя после '.'", self.peek().line)
                node = Attr(node, self.next().value, node.line)
            else:
                break
        return node

    def parse_primary(self):
        t = self.peek()

        if t.type == "NUMBER":
            self.next()
            return Num(t.value, t.line)
        if t.type == "STRING":
            self.next()
            return Str(t.value, t.line)
        if t.type == "KW":
            if t.value == "истина":
                self.next()
                return Bool(True, t.line)
            if t.value == "ложь":
                self.next()
                return Bool(False, t.line)
            if t.value == "я":          # ссылка на текущий объект
                self.next()
                return Var("я", t.line)
            if t.value == "новый":
                self.next()
                if not self.check("ID"):
                    raise LppSyntaxError("после 'новый' ожидалось имя класса", t.line)
                cls = self.next().value
                args = []
                if self.cop("("):
                    self.next()
                    if not self.cop(")"):
                        while True:
                            args.append(self.expr())
                            if self.cop(","):
                                self.next()
                                continue
                            break
                    self.eop(")")
                return New(cls, args, t.line)
        if t.type == "ID":
            self.next()
            return Var(t.value, t.line)
        if self.cop("("):
            self.next()
            e = self.expr()
            self.eop(")")
            return e
        if self.cop("["):
            self.next()
            items = []
            if not self.cop("]"):
                while True:
                    items.append(self.expr())
                    if self.cop(","):
                        self.next()
                        continue
                    break
            self.eop("]")
            return Array(items, t.line)
        if self.cop("{"):
            self.next()
            pairs = []
            if not self.cop("}"):
                while True:
                    k = self.expr()
                    self.eop(":")
                    v = self.expr()
                    pairs.append((k, v))
                    if self.cop(","):
                        self.next()
                        continue
                    break
            self.eop("}")
            return DictLit(pairs, t.line)
        raise LppSyntaxError(f"неожиданный токен '{t.value}'", t.line)

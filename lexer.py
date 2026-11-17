# -*- coding: utf-8 -*-
"""Лексер L++: превращает текст программы в поток токенов."""

from .errors import LppSyntaxError
from .tokens import KEYWORDS, Token

# Двухсимвольные операторы. ВАЖНО: "//" сюда НЕ входит — в L++ это комментарий.
TWO_CHAR_OPS = ("==", "!=", "<=", ">=", "**")
ONE_CHAR_OPS = "+-*/%<>=(),[]{}:."

_ESCAPES = {
    "n": "\n", "t": "\t", "r": "\r", "\\": "\\",
    '"': '"', "'": "'", "0": "\0",
}

_DIGITS = "0123456789"
_HEX = "0123456789abcdefABCDEF"


def _is_ident_start(ch):
    return bool(ch) and (ch.isalpha() or ch == "_")


def _is_ident_part(ch):
    return bool(ch) and (ch.isalnum() or ch == "_")


class Lexer:
    """Поточный лексер. Не падает на конце файла: peek() возвращает ""."""

    def __init__(self, src):
        self.src = src
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []

    # ---------- низкий уровень ----------

    def at_end(self):
        return self.pos >= len(self.src)

    def peek(self, o=0):
        p = self.pos + o
        if 0 <= p < len(self.src):
            return self.src[p]
        return ""

    def adv(self):
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _emit(self, ttype, value, line, col):
        self.tokens.append(Token(ttype, value, line, col))

    # ---------- основной цикл ----------

    def tokenize(self):
        while not self.at_end():
            ch = self.peek()

            if ch in " \t\r\n":
                self.adv()
                continue

            # комментарии: // до конца строки и # до конца строки
            if ch == "/" and self.peek(1) == "/":
                while not self.at_end() and self.peek() != "\n":
                    self.adv()
                continue
            if ch == "#":
                while not self.at_end() and self.peek() != "\n":
                    self.adv()
                continue

            # числа: 123, 1.5, .5, 1e-3, 0xFF
            if ch.isdigit() or (ch == "." and self.peek(1).isdigit()):
                self._num()
                continue

            if ch in "\"'":
                self._str(ch)
                continue

            if _is_ident_start(ch):
                self._ident()
                continue

            two = self.src[self.pos:self.pos + 2]
            if two in TWO_CHAR_OPS:
                self._emit("OP", two, self.line, self.col)
                self.adv()
                self.adv()
                continue

            if ch in ONE_CHAR_OPS:
                self._emit("OP", ch, self.line, self.col)
                self.adv()
                continue

            raise LppSyntaxError(f"неизвестный символ '{ch}'", self.line, self.col)

        self._emit("EOF", None, self.line, self.col)
        return self.tokens

    # ---------- числа ----------

    def _num(self):
        line, col = self.line, self.col
        buf = ""

        # шестнадцатеричное
        if self.peek() == "0" and self.peek(1) in ("x", "X"):
            buf += self.adv()          # 0
            buf += self.adv()          # x
            digits = ""
            while self.peek() and self.peek() in _HEX:
                digits += self.adv()
            if not digits:
                raise LppSyntaxError("после '0x' ожидались шестнадцатеричные цифры", line, col)
            self._emit("NUMBER", int(buf + digits, 16), line, col)
            return

        # целая часть (может отсутствовать для .5)
        while self.peek() and self.peek() in _DIGITS:
            buf += self.adv()

        # дробная часть
        if self.peek() == "." and self.peek(1) and self.peek(1).isdigit():
            buf += self.adv()
            while self.peek() and self.peek() in _DIGITS:
                buf += self.adv()

        # экспонента — только если за 'e' действительно идёт число
        if self.peek() in ("e", "E"):
            nxt = self.peek(1)
            sign = self.peek(1) in ("+", "-")
            digit_after = self.peek(2) if sign else nxt
            if digit_after and digit_after in _DIGITS:
                buf += self.adv()      # e
                if sign:
                    buf += self.adv()  # +/-
                while self.peek() and self.peek() in _DIGITS:
                    buf += self.adv()

        value = float(buf) if ("." in buf or "e" in buf.lower()) else int(buf)
        self._emit("NUMBER", value, line, col)

    # ---------- строки ----------

    def _str(self, quote):
        line, col = self.line, self.col
        self.adv()
        buf = []
        while True:
            if self.at_end():
                raise LppSyntaxError("незакрытая строка", line, col)
            ch = self.adv()
            if ch == quote:
                break
            if ch == "\\":
                if self.at_end():
                    raise LppSyntaxError("незакрытая строка", line, col)
                n = self.adv()
                buf.append(_ESCAPES.get(n, n))
            else:
                buf.append(ch)
        self._emit("STRING", "".join(buf), line, col)

    # ---------- идентификаторы ----------

    def _ident(self):
        line, col = self.line, self.col
        buf = []
        while _is_ident_part(self.peek()):
            buf.append(self.adv())
        name = "".join(buf)
        if name in KEYWORDS:
            self._emit("KW", name, line, col)
        else:
            self._emit("ID", name, line, col)

# -*- coding: utf-8 -*-
"""L++ IDE — точка входа.

Запуск:  python lpp_ide.py        (или двойной клик по run.bat)

Весь код разложен по пакетам:
    lpp/lexer.py        — разбор текста на токены
    lpp/parser.py       — построение AST
    lpp/interpreter.py  — выполнение программы
    lpp/builtins.py     — встроенные функции
    lpp/ui/             — графическая оболочка

Этот файл оставлен для совместимости: старый код вида
``import lpp_ide`` и обращение к ``lpp_ide.Lexer`` продолжают работать.
"""

from lpp import (  # noqa: F401  (реэкспорт для совместимости)
    ADDONS_DIR, APP_DIR, EDITIONS, KEYWORDS, THEMES, Interpreter, Lexer,
    LppError, Parser, Token, run_self_tests,
)
from lpp.ui.app import L_IDE, main

__all__ = [
    "L_IDE", "main", "Interpreter", "Lexer", "Parser", "Token",
    "THEMES", "EDITIONS", "KEYWORDS", "LppError", "run_self_tests",
]

if __name__ == "__main__":
    main()

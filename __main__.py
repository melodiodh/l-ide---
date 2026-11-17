# -*- coding: utf-8 -*-
"""`python -m lpp` — прогон само-тестов ядра из командной строки."""

from .selftests import main

if __name__ == "__main__":
    raise SystemExit(main())

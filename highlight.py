# -*- coding: utf-8 -*-
"""Подсветка синтаксиса L++ для tk.Text.

Один проход по документу вместо прежних 29 отдельных поисков на каждый
символ — так редактор не тормозит на файлах в сотни строк.
"""

import bisect
import re

from ..tokens import BUILTINS, KEYWORDS

TAGS = ("kw", "fn", "str", "num", "cmt")

_STRING = r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\''
_COMMENT = r"//[^\n]*|#[^\n]*"

# Порядок веток важен: строка матчится раньше комментария, поэтому "http://x"
# не превращается в комментарий.
_MASTER = re.compile(rf"(?P<str>{_STRING})|(?P<cmt>{_COMMENT})")


def _alternation(words):
    return "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))


_KEYWORD_RE = re.compile(rf"\b(?:{_alternation(KEYWORDS)})\b")
_BUILTIN_RE = re.compile(rf"\b(?:{_alternation(BUILTINS)})\b")
_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b")


class Highlighter:
    """Раскрашивает документ в редакторе по текущей теме."""

    MAX_CHARS = 400_000  # выше этого подсветку отключаем, чтобы не тормозить

    def __init__(self, editor, theme, font):
        self.editor = editor
        self.configure(theme, font)

    def configure(self, theme, font):
        family, size = font[0], font[1]
        self.editor.tag_configure("kw", foreground=theme["accent_purple"],
                                  font=(family, size, "bold"))
        self.editor.tag_configure("fn", foreground=theme["accent"])
        self.editor.tag_configure("str", foreground=theme["accent_green"])
        self.editor.tag_configure("num", foreground=theme["accent_orange"])
        self.editor.tag_configure("cmt", foreground=theme["fg_muted"],
                                  font=(family, size, "italic"))

    # ------------------------------------------------------------------

    def clear(self):
        for tag in TAGS:
            self.editor.tag_remove(tag, "1.0", "end")

    def apply(self, content=None):
        """Пересчитывает подсветку всего документа."""
        editor = self.editor
        if content is None:
            content = editor.get("1.0", "end-1c")

        self.clear()
        if len(content) > self.MAX_CHARS:
            return

        line_starts = [0]
        for m in re.finditer("\n", content):
            line_starts.append(m.end())

        def to_index(offset):
            line = bisect.bisect_right(line_starts, offset) - 1
            return f"{line + 1}.{offset - line_starts[line]}"

        def add(tag, start, end):
            if end > start:
                editor.tag_add(tag, to_index(start), to_index(end))

        cursor = 0
        for m in _MASTER.finditer(content):
            if m.start() > cursor:
                self._scan_code(content, cursor, m.start(), add)
            tag = "str" if m.group("str") is not None else "cmt"
            add(tag, m.start(), m.end())
            cursor = m.end()

        if cursor < len(content):
            self._scan_code(content, cursor, len(content), add)

    def _scan_code(self, content, start, end, add):
        chunk = content[start:end]
        if not chunk:
            return
        for m in _KEYWORD_RE.finditer(chunk):
            add("kw", start + m.start(), start + m.end())
        for m in _BUILTIN_RE.finditer(chunk):
            add("fn", start + m.start(), start + m.end())
        for m in _NUMBER_RE.finditer(chunk):
            add("num", start + m.start(), start + m.end())

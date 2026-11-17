# -*- coding: utf-8 -*-
"""Окно поиска и замены (Ctrl+F)."""

import tkinter as tk

from .widgets import center, fade_in


class FindReplace(tk.Toplevel):
    """Немодальное окно поиска/замены для редактора."""

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.editor = app.editor
        self.theme = app.theme
        th = self.theme

        self.title("Поиск и замена")
        self.configure(bg=th["bg_main"])
        self.resizable(False, False)
        center(self, 460, 190)
        self.transient(app.root)

        self.editor.tag_configure("find", background=th["accent_orange"], foreground="#000000")

        body = tk.Frame(self, bg=th["bg_main"], padx=14, pady=12)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="Найти:", bg=th["bg_main"], fg=th["fg_main"]).grid(
            row=0, column=0, sticky="w", pady=4)
        self.entry_find = tk.Entry(body, bg=th["bg_panel"], fg=th["fg_main"],
                                   insertbackground=th["fg_main"], relief=tk.FLAT)
        self.entry_find.grid(row=0, column=1, columnspan=3, sticky="we", padx=8, ipady=4)

        tk.Label(body, text="Заменить:", bg=th["bg_main"], fg=th["fg_main"]).grid(
            row=1, column=0, sticky="w", pady=4)
        self.entry_replace = tk.Entry(body, bg=th["bg_panel"], fg=th["fg_main"],
                                      insertbackground=th["fg_main"], relief=tk.FLAT)
        self.entry_replace.grid(row=1, column=1, columnspan=3, sticky="we", padx=8, ipady=4)

        self.var_regex = tk.BooleanVar(value=False)
        self.var_case = tk.BooleanVar(value=False)
        tk.Checkbutton(body, text="regex", variable=self.var_regex, bg=th["bg_main"],
                       fg=th["fg_main"], selectcolor=th["bg_panel"],
                       activebackground=th["bg_main"]).grid(row=2, column=1, sticky="w")
        tk.Checkbutton(body, text="учитывать регистр", variable=self.var_case,
                       bg=th["bg_main"], fg=th["fg_main"], selectcolor=th["bg_panel"],
                       activebackground=th["bg_main"]).grid(row=2, column=2, sticky="w")

        row = tk.Frame(body, bg=th["bg_main"])
        row.grid(row=3, column=0, columnspan=4, sticky="we", pady=(10, 0))

        def btn(text, cmd, color):
            b = tk.Button(row, text=text, command=cmd, bg=color, fg="#fff",
                          relief=tk.FLAT, padx=10, pady=4, cursor="hand2",
                          font=("Segoe UI", 9, "bold"))
            b.pack(side=tk.LEFT, padx=3)
            return b

        btn("Найти далее", lambda: self.find_next(False), th["accent"])
        btn("Назад", lambda: self.find_next(True), th["accent_purple"])
        btn("Заменить", self.replace_one, th["accent_green"])
        btn("Заменить всё", self.replace_all, th["accent_orange"])
        tk.Button(row, text="Закрыть", command=self.close, bg=th["bg_panel"],
                  fg=th["fg_main"], relief=tk.FLAT, padx=10, pady=4,
                  cursor="hand2").pack(side=tk.RIGHT, padx=3)

        body.columnconfigure(1, weight=1)
        self.entry_find.focus_set()
        self.bind("<Return>", lambda e: self.find_next(False))
        self.bind("<Escape>", lambda e: self.close())
        fade_in(self, steps=8, delay=10)

    # ------------------------------------------------------------------

    def close(self):
        self.editor.tag_remove("find", "1.0", "end")
        self.destroy()

    def _pattern(self):
        text = self.entry_find.get()
        if not text:
            return None, text
        return text, text

    def find_next(self, backwards=False):
        needle, _ = self._pattern()
        if not needle:
            return
        self.editor.tag_remove("find", "1.0", "end")
        start = self.editor.index(tk.INSERT)
        if backwards:
            stop = "1.0"
        else:
            stop = "end"

        kwargs = dict(stopindex=stop, backwards=backwards, nocase=not self.var_case.get())
        if self.var_regex.get():
            kwargs["regexp"] = True

        try:
            pos = self.editor.search(needle, start, **kwargs)
        except tk.TclError:
            pos = None

        if not pos:
            # поиск с начала документа
            try:
                pos = self.editor.search(needle, "1.0" if not backwards else "end",
                                         **kwargs)
            except tk.TclError:
                pos = None
        if not pos:
            self.app.set_status("Не найдено")
            return

        end = f"{pos}+{len(needle)}c"
        self.editor.tag_add("find", pos, end)
        self.editor.mark_set(tk.INSERT, pos)
        self.editor.see(pos)
        self.app.set_status(f"Найдено: {pos}")

    def replace_one(self):
        needle, _ = self._pattern()
        if not needle:
            return
        ranges = self.editor.tag_ranges("find")
        if not ranges:
            self.find_next(False)
            return
        start, end = ranges[0], ranges[1]
        self.editor.delete(start, end)
        self.editor.insert(start, self.entry_replace.get())
        self.editor.tag_remove("find", "1.0", "end")
        self.find_next(False)

    def replace_all(self):
        needle, _ = self._pattern()
        if not needle:
            return
        replacement = self.entry_replace.get()
        content = self.editor.get("1.0", "end-1c")
        if self.var_regex.get():
            import re
            flags = 0 if self.var_case.get() else re.IGNORECASE
            try:
                pattern = re.compile(needle, flags)
            except re.error as e:
                self.app.set_status(f"Ошибка regex: {e}")
                return
            new_content, count = pattern.subn(replacement, content)
        else:
            if self.var_case.get():
                count = content.count(needle)
                new_content = content.replace(needle, replacement)
            else:
                import re
                pattern = re.compile(re.escape(needle), re.IGNORECASE)
                new_content, count = pattern.subn(lambda m: replacement, content)

        if count:
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", new_content)
            self.editor.edit_modified(True)
        self.app.set_status(f"Заменено вхождений: {count}")

# -*- coding: utf-8 -*-
"""Мелкие UI-кирпичики: анимации, центрирование, диалоги, заставка."""

import tkinter as tk

FONT_UI = ("Segoe UI", 10)
FONT_UI_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")


def center(win, w, h):
    """Ставит окно по центру экрана с заданным размером."""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = max(0, (sw - w) // 2)
    y = max(0, (sh - h) // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")


def fade_in(win, steps=12, delay=15, target=0.96):
    """Плавное появление окна. Не падает на платформах без -alpha."""
    try:
        win.attributes("-alpha", 0.0)
    except tk.TclError:
        return

    def _step(i):
        if i > steps:
            return
        try:
            win.attributes("-alpha", target * i / steps)
            win.after(delay, lambda: _step(i + 1))
        except tk.TclError:
            pass

    _step(1)


class StyledDialog(tk.Toplevel):
    """Своё модальное окно в стиле темы (вместо стандартного messagebox)."""

    def __init__(self, parent, theme, title, message, buttons=("OK",)):
        super().__init__(parent)
        self.result = None
        self.theme = theme
        self.overrideredirect(True)
        self.configure(bg=theme["border"])
        self.transient(parent)
        self.grab_set()

        outer = tk.Frame(self, bg=theme["bg_panel"], padx=1, pady=1)
        outer.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        tk.Label(
            outer, text=title, bg=theme["accent"], fg="#fff",
            font=FONT_UI_BOLD, anchor="w", padx=15, pady=8,
        ).pack(fill=tk.X)

        tk.Label(
            outer, text=message, bg=theme["bg_panel"], fg=theme["fg_main"],
            font=FONT_UI, wraplength=380, justify=tk.LEFT, padx=20, pady=20,
        ).pack(fill=tk.BOTH, expand=True)

        row = tk.Frame(outer, bg=theme["bg_panel"])
        row.pack(fill=tk.X, padx=20, pady=(0, 15))
        for b in buttons:
            tk.Button(
                row, text=b, command=lambda v=b: self._click(v),
                bg=theme["accent"], fg="#fff", font=FONT_UI_BOLD,
                relief=tk.FLAT, padx=20, pady=6, cursor="hand2",
                activebackground=theme["accent_green"], activeforeground="#fff",
            ).pack(side=tk.RIGHT, padx=4)

        self.update_idletasks()
        w = max(420, self.winfo_reqwidth())
        h = max(180, self.winfo_reqheight())
        center(self, w, h)
        fade_in(self, steps=8, delay=10)

        self.bind("<Return>", lambda e: self._click(buttons[0]))
        self.bind("<Escape>", lambda e: self._click(buttons[-1]))
        self.protocol("WM_DELETE_WINDOW", lambda: self._click(buttons[-1]))

    def _click(self, value):
        self.result = value
        self.destroy()


def show_dialog(parent, theme, title, message, buttons=("OK",)):
    """Показать модальный диалог и вернуть выбранную кнопку."""
    dlg = StyledDialog(parent, theme, title, message, buttons)
    parent.wait_window(dlg)
    return dlg.result


class Splash:
    """Заставка с полосой загрузки."""

    def __init__(self, root, theme):
        self.alive = True
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.configure(bg=theme["bg_main"])
        center(self.win, 460, 280)
        try:
            self.win.attributes("-topmost", True)
        except tk.TclError:
            pass

        tk.Label(self.win, text="L++", bg=theme["bg_main"], fg=theme["accent"],
                 font=("Segoe UI", 48, "bold")).pack(pady=(40, 0))
        tk.Label(self.win, text="IDE", bg=theme["bg_main"], fg=theme["fg_muted"],
                 font=("Segoe UI", 14)).pack()
        self.label = tk.Label(self.win, text="Загрузка...", bg=theme["bg_main"],
                              fg=theme["fg_muted"], font=("Segoe UI", 9))
        self.label.pack(pady=(25, 8))

        self.track = tk.Frame(self.win, bg=theme["border"], height=6, width=380)
        self.track.pack()
        self.fill = tk.Frame(self.track, bg=theme["accent"], height=6, width=0)
        self.fill.place(x=0, y=0)
        fade_in(self.win, steps=15, delay=20)

    def progress(self, pct, text=None):
        if not self.alive:
            return
        try:
            self.fill.place_configure(width=int(380 * pct))
            if text:
                self.label.config(text=text)
            self.win.update_idletasks()
        except tk.TclError:
            self.alive = False

    def close(self):
        self.alive = False
        try:
            self.win.destroy()
        except tk.TclError:
            pass

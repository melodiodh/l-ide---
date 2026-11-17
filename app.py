# -*- coding: utf-8 -*-
"""Главное окно L++ IDE."""

import os
import queue
import random
import re
import threading
import tkinter as tk
from tkinter import filedialog, simpledialog, ttk

from ..editions import EDITION_ORDER, EDITIONS, get_edition
from ..errors import LppError
from ..interpreter import Interpreter
from ..paths import ADDONS_DIR, EXAMPLES_DIR, load_config, save_config
from ..selftests import run_self_tests
from ..themes import DEFAULT_THEME, THEMES, get_theme
from .find import FindReplace
from .highlight import Highlighter
from .widgets import Splash, center, fade_in, show_dialog

WELCOME_CODE = (
    "// Добро пожаловать в L++ IDE!\n"
    "// F5 — запуск, Shift+F5 — стоп, Ctrl+S — сохранить.\n"
    "// Комментарии: // или #\n\n"
    'вывести("Привет, мир!")\n'
    "для i от 1 до 3 то:\n"
    '    вывести("Итерация:", i)\n'
    "конец\n"
)

UI_FONT = ("Segoe UI", 10)
UI_FONT_BOLD = ("Segoe UI", 10, "bold")
UI_FONT_SMALL = ("Segoe UI", 9)

# Аддоны, которые создают окна Tk: их код обязан выполняться в главном потоке,
# иначе Tkinter падает с "main thread is not in main loop".
GUI_ADDONS = ("lgame", "whooshint", "platidengami", "nftbar", "mixday", "mediacore")


class L_IDE:
    """Собирает интерфейс и связывает его с интерпретатором."""

    def __init__(self, root):
        self.root = root
        self.cfg = load_config()

        self.theme_name = self.cfg.get("theme", DEFAULT_THEME)
        if self.theme_name not in THEMES:
            self.theme_name = DEFAULT_THEME
        self.theme = get_theme(self.theme_name)

        self.edition_name = self.cfg.get("edition", "Ultimate")
        self.edition = get_edition(self.edition_name)
        self.edition_name = self.edition_name if self.edition_name in EDITIONS else "Ultimate"

        self.font_size = int(self.cfg.get("font_size", 14) or 14)
        self.font_code = ("Consolas", self.font_size)

        self.current_file = None
        self.workspace = EXAMPLES_DIR if os.path.isdir(EXAMPLES_DIR) else os.getcwd()

        self._dirty = False
        self._running = False
        self._stop_flag = threading.Event()
        self._highlight_job = None
        self._snapshot = None
        self._find_window = None
        self._ui_queue = queue.Queue()
        self._alive = True
        self._drain_id = None

        self.root.withdraw()
        if self.cfg.get("first_run", True):
            self._choose_edition()

        splash = Splash(self.root, self.theme)
        self._build_main()
        splash.progress(1.0)
        self.root.after(250, splash.close)

        self.root.deiconify()
        self.root.lift()
        self.root.after(200, lambda: self._safe_topmost(False))

        self.root.after(500, self._welcome_once)
        self.root.after(800, self._run_tests_async)
        self.root.after(40, self._drain_ui_queue)

    # ==================================================================
    # Служебное
    # ==================================================================

    def _ui(self, fn):
        """Выполнить fn в главном потоке (безопасно из рабочего потока)."""
        self._ui_queue.put(fn)

    def _drain_ui_queue(self):
        self._drain_id = None
        if not self._alive:
            return
        try:
            while True:
                fn = self._ui_queue.get_nowait()
                try:
                    fn()
                except Exception:
                    pass
        except queue.Empty:
            pass
        try:
            self._drain_id = self.root.after(40, self._drain_ui_queue)
        except tk.TclError:
            self._alive = False

    def _safe_topmost(self, value):
        try:
            self.root.attributes("-topmost", value)
        except tk.TclError:
            pass

    def _save_cfg(self):
        self.cfg.update({
            "theme": self.theme_name,
            "edition": self.edition_name,
            "font_size": self.font_size,
            "first_run": False,
        })
        save_config(self.cfg)

    def set_status(self, text):
        try:
            self.lbl_status.config(text=text)
        except (AttributeError, tk.TclError):
            pass

    def _update_title(self):
        name = os.path.basename(self.current_file) if self.current_file else "без имени"
        mark = " •" if self._dirty else ""
        wm = self.edition.get("watermark", "")
        suffix = f" • {wm}" if wm else ""
        try:
            self.root.title(f"L++ IDE — {self.edition_name}{suffix} — {name}{mark}")
            self.tab_label.config(text=f" {name}{mark}")
        except (AttributeError, tk.TclError):
            pass

    # ==================================================================
    # Выбор издания
    # ==================================================================

    def _choose_edition(self):
        th = self.theme
        win = tk.Toplevel(self.root)
        win.title("Выбор издания L++")
        win.configure(bg=th["bg_main"])
        center(win, 820, 430)
        win.grab_set()
        win.protocol("WM_DELETE_WINDOW", lambda: win.destroy())

        tk.Label(win, text="Выберите издание L++", bg=th["bg_main"], fg=th["fg_main"],
                 font=("Segoe UI", 18, "bold")).pack(pady=(25, 5))
        tk.Label(win, text="Потом можно сменить в меню ☰ → Издание",
                 bg=th["bg_main"], fg=th["fg_muted"], font=UI_FONT_SMALL).pack()

        frame = tk.Frame(win, bg=th["bg_main"])
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        chosen = {"name": None}

        def pick(name):
            chosen["name"] = name
            win.destroy()

        colors = {
            "Home": th["accent_orange"],
            "Ultimate": th["accent_green"],
            "Classic": th["accent_purple"],
        }

        for name in EDITION_ORDER:
            card = tk.Frame(frame, bg=th["bg_panel"], padx=10, pady=10,
                            highlightthickness=2, highlightbackground=colors[name])
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            tk.Label(card, text=name, bg=th["bg_panel"], fg=colors[name],
                     font=("Segoe UI", 12, "bold")).pack(anchor="w")
            tk.Label(card, text=EDITIONS[name]["description"], bg=th["bg_panel"],
                     fg=th["fg_muted"], font=UI_FONT_SMALL, justify=tk.LEFT,
                     wraplength=150).pack(anchor="w", pady=(8, 15))
            tk.Button(card, text="Выбрать", command=lambda n=name: pick(n),
                      bg=colors[name], fg="#fff", relief=tk.FLAT, cursor="hand2",
                      font=UI_FONT_BOLD, pady=6).pack(fill=tk.X, side=tk.BOTTOM)

        # Пасхалка
        egg = tk.Frame(frame, bg=th["bg_panel"], padx=10, pady=10,
                       highlightthickness=2, highlightbackground="#FF0000")
        egg.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tk.Label(egg, text="Build", bg=th["bg_panel"], fg="#FF0000",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(egg, text="ХАКЕРСКАЯ ВЕРСИЯ!\nВзломано!\nНе входить!",
                 bg=th["bg_panel"], fg=th["fg_muted"], font=UI_FONT_SMALL,
                 justify=tk.LEFT).pack(anchor="w", pady=(8, 15))
        tk.Button(egg, text="💀 Взломать", command=lambda: self._hacker_prank(win),
                  bg="#FF0000", fg="#fff", relief=tk.FLAT, cursor="hand2",
                  font=UI_FONT_BOLD, pady=6).pack(fill=tk.X, side=tk.BOTTOM)

        fade_in(win, steps=10, delay=12)
        self.root.wait_window(win)

        if chosen["name"]:
            self.edition_name = chosen["name"]
            self.edition = get_edition(self.edition_name)
        self._save_cfg()

    def _hacker_prank(self, chooser):
        """Пасхалка: псевдо-взлом. Не блокирует интерфейс (в отличие от time.sleep)."""
        try:
            chooser.destroy()
        except tk.TclError:
            pass
        self.root.withdraw()

        hack = tk.Toplevel(self.root)
        hack.configure(bg="black")
        hack.overrideredirect(True)
        try:
            hack.attributes("-fullscreen", True)
            hack.attributes("-topmost", True)
        except tk.TclError:
            pass

        text = tk.Text(hack, bg="black", fg="#00FF00", font=("Consolas", 14),
                       relief=tk.FLAT, bd=0, insertbackground="#00FF00")
        text.pack(fill=tk.BOTH, expand=True)

        ip = ".".join(str(random.randint(1, 255)) for _ in range(4))
        message = (
            "ВНИМАНИЕ: НЕСАНКЦИОНИРОВАННЫЙ ДОСТУП...\n"
            "Скачивание личных данных...\n"
            f"IP: {ip}\n"
            "Пароли: [ОБНАРУЖЕНЫ]\n"
            "Отправка на сервер: 100%\n\n"
            "ПОКА, ХАКЕР."
        )
        chars = list(message)
        finished = {"done": False}

        def finish(event=None):
            if finished["done"]:
                return
            finished["done"] = True
            try:
                hack.destroy()
            except tk.TclError:
                pass
            self._alive = False
            try:
                self.root.destroy()
            except tk.TclError:
                pass

        def step(i=0):
            if finished["done"]:
                return
            if i >= len(chars):
                hack.after(1500, finish)
                return
            text.insert(tk.END, chars[i])
            text.see(tk.END)
            hack.after(18, lambda: step(i + 1))

        hack.bind("<Escape>", finish)
        hack.bind("<Button-1>", finish)
        step()

    # ==================================================================
    # Построение интерфейса
    # ==================================================================

    def _build_main(self):
        th = self.theme
        self.root.configure(bg=th["bg_main"])
        self.root.geometry("1350x850")
        self.root.minsize(900, 560)
        self._set_icon()

        self._build_topbar()
        self._build_body()
        self._build_statusbar()
        self._bind_keys()
        self._restore_or_welcome()

    def _build_topbar(self):
        th = self.theme
        top = tk.Frame(self.root, bg=th["bg_panel"], height=46)
        top.pack(side=tk.TOP, fill=tk.X)

        self.menu_btn = tk.Menubutton(top, text="☰", bg=th["bg_panel"], fg=th["fg_main"],
                                      font=("Segoe UI", 15), relief=tk.FLAT,
                                      activebackground=th["bg_panel"], cursor="hand2")
        self.menu_btn.pack(side=tk.LEFT, padx=8)
        self._build_menu()

        self.btn_run = self._btn(top, "▶ ЗАПУСТИТЬ", self.run_code,
                                 th["accent_green"], side=tk.LEFT, padx=6)
        self.btn_stop = self._btn(top, "⏹ СТОП", self.stop_code,
                                  th["accent_red"], side=tk.LEFT, padx=4)
        if self.edition["allow_themes"]:
            self._btn(top, "🎨 ТЕМА", self.cycle_theme, th["accent_purple"],
                      side=tk.LEFT, padx=4)

        if self.edition["allow_addons"]:
            self._btn(top, "📚 БИБЛИОТЕКИ", self.show_libs, th["bg_panel"],
                      fg=th["fg_main"], side=tk.RIGHT, padx=6)
        self._btn(top, "💾 СОХРАНИТЬ", self.save_file, th["accent"], side=tk.RIGHT, padx=4)
        self._btn(top, "🔎 ПОИСК", self.open_find, th["bg_panel"], fg=th["fg_main"],
                  side=tk.RIGHT, padx=4)

    def _build_menu(self):
        th = self.theme
        self.menu = tk.Menu(self.menu_btn, tearoff=0, bg=th["bg_panel"], fg=th["fg_main"])
        self.menu.add_command(label="Новый (Ctrl+N)", command=self.new_file)
        self.menu.add_command(label="Открыть... (Ctrl+O)", command=self.open_file)
        self.menu.add_command(label="Сохранить (Ctrl+S)", command=self.save_file)
        self.menu.add_command(label="Сохранить как... (Ctrl+Shift+S)", command=self.save_file_as)
        self.menu.add_separator()
        self.menu.add_command(label="Найти и заменить (Ctrl+F)", command=self.open_find)

        theme_menu = tk.Menu(self.menu, tearoff=0, bg=th["bg_panel"], fg=th["fg_main"])
        for name in THEMES:
            theme_menu.add_command(label=name, command=lambda n=name: self.set_theme(n))
        self.menu.add_cascade(label="🎨 Тема", menu=theme_menu)

        edition_menu = tk.Menu(self.menu, tearoff=0, bg=th["bg_panel"], fg=th["fg_main"])
        for name in EDITION_ORDER:
            edition_menu.add_command(label=name, command=lambda n=name: self.set_edition(n))
        self.menu.add_cascade(label="🏷 Издание", menu=edition_menu)

        examples = tk.Menu(self.menu, tearoff=0, bg=th["bg_panel"], fg=th["fg_main"])
        for path in self._example_files():
            examples.add_command(label=os.path.basename(path),
                                 command=lambda p=path: self._load_path(p))
        if not examples.index("end"):
            examples.add_command(label="(нет примеров)", state=tk.DISABLED)
        self.menu.add_cascade(label="📂 Примеры", menu=examples)

        self.menu.add_separator()
        self.menu.add_command(label="Выход", command=self.on_close)
        self.menu_btn["menu"] = self.menu

    def _build_body(self):
        th = self.theme
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=th["border"],
                                    sashwidth=4, borderwidth=0)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # ---- левая панель: файлы ----
        left = tk.Frame(self.paned, bg=th["bg_panel"], width=220)
        self.paned.add(left, width=220, minsize=140)
        tk.Label(left, text="ФАЙЛЫ .lpp", bg=th["bg_panel"], fg=th["fg_muted"],
                 font=UI_FONT_SMALL, anchor="w").pack(fill=tk.X, padx=14, pady=(10, 4))
        self.lbl_workspace = tk.Label(left, text=self._short_workspace(), bg=th["bg_panel"],
                                      fg=th["fg_muted"], font=("Segoe UI", 8),
                                      anchor="w", wraplength=200)
        self.lbl_workspace.pack(fill=tk.X, padx=14)
        self.file_list = tk.Listbox(left, bg=th["bg_panel"], fg=th["fg_main"],
                                    font=UI_FONT, relief=tk.FLAT, highlightthickness=0,
                                    selectbackground=th["accent"], activestyle="none")
        self.file_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.file_list.bind("<Double-Button-1>", self._open_from_list)
        self._refresh_files()

        # ---- центр ----
        center_frame = tk.Frame(self.paned, bg=th["bg_editor"])
        self.paned.add(center_frame, stretch="always")

        tab = tk.Frame(center_frame, bg=th["bg_panel"], height=30)
        tab.pack(fill=tk.X)
        self.tab_label = tk.Label(tab, text=" без имени", bg=th["bg_editor"],
                                  fg=th["fg_main"], font=UI_FONT_SMALL, padx=15, pady=5)
        self.tab_label.pack(side=tk.LEFT)

        # консоль (пакуем ДО редактора, чтобы она держалась снизу)
        self._build_console(center_frame)

        editor_frame = tk.Frame(center_frame, bg=th["bg_editor"])
        editor_frame.pack(fill=tk.BOTH, expand=True)

        self.gutter = tk.Text(editor_frame, width=5, bg=th["bg_editor"], fg=th["fg_muted"],
                              font=self.font_code, state=tk.DISABLED, relief=tk.FLAT,
                              padx=4, takefocus=0, cursor="arrow")
        self.gutter.pack(side=tk.LEFT, fill=tk.Y)

        self.editor = tk.Text(editor_frame, bg=th["bg_editor"], fg=th["fg_main"],
                              font=self.font_code, insertbackground=th["accent"],
                              undo=True, maxundo=-1, relief=tk.FLAT, padx=12, pady=8,
                              wrap=tk.NONE, tabs="    ")
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.vbar = tk.Scrollbar(editor_frame, orient=tk.VERTICAL, command=self.editor.yview,
                                 bg=th["bg_panel"], troughcolor=th["bg_main"], bd=0,
                                 relief=tk.FLAT, width=12)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor.configure(yscrollcommand=self._on_editor_scroll)

        self.hbar = tk.Scrollbar(center_frame, orient=tk.HORIZONTAL,
                                 command=self.editor.xview, bg=th["bg_panel"],
                                 troughcolor=th["bg_main"], bd=0, relief=tk.FLAT)
        self.hbar.pack(fill=tk.X, before=editor_frame)
        self.editor.configure(xscrollcommand=self.hbar.set)

        self.highlighter = Highlighter(self.editor, th, self.font_code)

        self.editor.bind("<KeyRelease>", self.on_key)
        self.editor.bind("<ButtonRelease-1>", self._pos)
        self.editor.bind("<<Modified>>", self._on_modified)
        self.editor.bind("<Return>", self._on_return)
        self.editor.bind("<Tab>", self._on_tab)
        self.editor.bind("<Control-slash>", self.toggle_comment)

    def _build_console(self, parent):
        th = self.theme
        self.console_frame = tk.Frame(parent, bg=th["bg_console"], height=180)
        self.console_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.console_frame.pack_propagate(False)

        hdr = tk.Frame(self.console_frame, bg=th["bg_panel"], height=28)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="ТЕРМИНАЛ", bg=th["bg_panel"], fg=th["fg_muted"],
                 font=UI_FONT_SMALL).pack(side=tk.LEFT, padx=14)
        tk.Button(hdr, text="✖", command=self.clear_console, bg=th["bg_panel"],
                  fg=th["fg_muted"], relief=tk.FLAT, cursor="hand2",
                  font=UI_FONT_SMALL).pack(side=tk.RIGHT, padx=8)

        wrap = tk.Frame(self.console_frame, bg=th["bg_console"])
        wrap.pack(fill=tk.BOTH, expand=True)

        self.console = tk.Text(wrap, bg=th["bg_console"], fg=th["accent_green"],
                               font=("Consolas", 12), state=tk.DISABLED,
                               relief=tk.FLAT, padx=12, pady=6, wrap=tk.WORD)
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        bar = tk.Scrollbar(wrap, orient=tk.VERTICAL, command=self.console.yview,
                           bg=th["bg_panel"], troughcolor=th["bg_console"], bd=0,
                           relief=tk.FLAT, width=12)
        bar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.configure(yscrollcommand=bar.set)

        self.console.tag_configure("err", foreground=th["accent_red"])
        self.console.tag_configure("ok", foreground=th["accent_green"])
        self.console.tag_configure("muted", foreground=th["fg_muted"])

    def _build_statusbar(self):
        th = self.theme
        status = tk.Frame(self.root, bg=th["accent"], height=24)
        status.pack(side=tk.BOTTOM, fill=tk.X)
        wm = self.edition.get("watermark", "")
        text = f"L++ {self.edition_name}" + (f" • {wm}" if wm else "")
        self.lbl_status = tk.Label(status, text=text, bg=th["accent"], fg="#fff",
                                   font=UI_FONT_SMALL)
        self.lbl_status.pack(side=tk.LEFT, padx=14)
        self.lbl_pos = tk.Label(status, text="Стр 1, Кол 1", bg=th["accent"], fg="#fff",
                                font=UI_FONT_SMALL)
        self.lbl_pos.pack(side=tk.RIGHT, padx=14)

    def _bind_keys(self):
        b = self.root.bind
        b("<F5>", lambda e: self.run_code())
        b("<Shift-F5>", lambda e: self.stop_code())
        b("<Control-n>", lambda e: self.new_file())
        b("<Control-s>", lambda e: self.save_file())
        b("<Control-o>", lambda e: self.open_file())
        b("<Control-f>", lambda e: self.open_find())
        b("<Control-Shift-S>", lambda e: self.save_file_as())
        b("<Control-plus>", lambda e: self.zoom(1))
        b("<Control-equal>", lambda e: self.zoom(1))
        b("<Control-minus>", lambda e: self.zoom(-1))
        b("<Control-0>", lambda e: self.zoom(0))
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ==================================================================
    # Восстановление документа / приветствие
    # ==================================================================

    def _restore_or_welcome(self):
        snap = self._snapshot
        self._snapshot = None
        if snap is not None:
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", snap["text"])
            try:
                self.editor.mark_set(tk.INSERT, snap["cursor"])
            except tk.TclError:
                pass
            self.current_file = snap["file"]
            self._dirty = snap["dirty"]
        else:
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", WELCOME_CODE)
            self._dirty = False
        self.editor.edit_modified(False)
        self.editor.edit_reset()
        self._update_title()
        self._do_highlight()
        self._update_gutter()

    def _welcome_once(self):
        if not self.cfg.get("show_welcome", True):
            return
        if not self._alive:
            return
        th = self.theme
        w = tk.Toplevel(self.root)
        w.title("Добро пожаловать")
        w.configure(bg=th["bg_main"])
        center(w, 560, 430)
        w.transient(self.root)

        tk.Label(w, text="L++ IDE", bg=th["bg_main"], fg=th["accent"],
                 font=("Segoe UI", 26, "bold")).pack(pady=(28, 4))
        tk.Label(w, text=f"Издание: {self.edition_name}   •   версия 2.0",
                 bg=th["bg_main"], fg=th["fg_main"], font=("Segoe UI", 11)).pack()

        info = (
            "F5 — запустить          Shift+F5 — остановить\n"
            "Ctrl+S — сохранить      Ctrl+O — открыть\n"
            "Ctrl+F — поиск/замена   Ctrl+/ — закомментировать\n"
            "Ctrl+±  — размер шрифта\n\n"
            "☰ — меню: файлы, темы, издания, примеры\n"
            "📚 — библиотеки (аддоны)   🔎 — поиск"
        )
        tk.Label(w, text=info, bg=th["bg_main"], fg=th["fg_muted"],
                 font=UI_FONT, justify=tk.LEFT).pack(pady=18)

        var = tk.BooleanVar(value=True)
        tk.Checkbutton(w, text="Показывать при запуске", variable=var,
                       bg=th["bg_main"], fg=th["fg_muted"], selectcolor=th["bg_panel"],
                       activebackground=th["bg_main"],
                       command=lambda: self._set_welcome_flag(var.get())).pack()

        tk.Button(w, text="Начать", command=w.destroy, bg=th["accent_green"], fg="#fff",
                  relief=tk.FLAT, padx=30, pady=8, font=("Segoe UI", 11, "bold"),
                  cursor="hand2").pack(pady=12)
        fade_in(w)

    def _set_welcome_flag(self, value):
        self.cfg["show_welcome"] = bool(value)
        self._save_cfg()

    # ==================================================================
    # Мелкие помощники
    # ==================================================================

    def _btn(self, parent, text, cmd, bg, fg="#fff", side=tk.LEFT, padx=5):
        b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg, font=UI_FONT_BOLD,
                      relief=tk.FLAT, padx=14, pady=7, cursor="hand2",
                      activebackground=self.theme["accent_green"], activeforeground="#fff")
        b.pack(side=side, padx=padx)
        return b

    def _set_icon(self):
        try:
            icon = tk.PhotoImage(width=32, height=32)
            icon.put(self.theme["bg_panel"], to=(0, 0, 32, 32))
            icon.put(self.theme["accent"], to=(6, 6, 10, 24))
            icon.put(self.theme["accent_orange"], to=(6, 20, 22, 24))
            icon.put(self.theme["accent"], to=(18, 6, 22, 14))
            icon.put(self.theme["accent"], to=(14, 10, 26, 12))
            self.root.iconphoto(True, icon)
            self._icon = icon
        except tk.TclError:
            pass

    def _short_workspace(self):
        path = self.workspace
        home = os.path.expanduser("~")
        if path.startswith(home):
            path = "~" + path[len(home):]
        return path

    def _example_files(self):
        if not os.path.isdir(EXAMPLES_DIR):
            return []
        return sorted(
            os.path.join(EXAMPLES_DIR, f) for f in os.listdir(EXAMPLES_DIR)
            if f.endswith(".lpp")
        )

    def zoom(self, delta):
        if delta == 0:
            self.font_size = 14
        else:
            self.font_size = max(8, min(40, self.font_size + delta))
        self.font_code = ("Consolas", self.font_size)
        try:
            self.editor.config(font=self.font_code)
            self.gutter.config(font=self.font_code)
            self.highlighter.configure(self.theme, self.font_code)
            self._do_highlight()
        except tk.TclError:
            pass
        self._save_cfg()

    # ==================================================================
    # Тема и издание
    # ==================================================================

    def cycle_theme(self):
        names = list(THEMES)
        idx = (names.index(self.theme_name) + 1) % len(names)
        self.set_theme(names[idx])

    def set_theme(self, name):
        if name not in THEMES:
            return
        if not self.edition["allow_themes"] and name != DEFAULT_THEME:
            show_dialog(self.root, self.theme, "Тема недоступна",
                        f"Смена тем недоступна в издании {self.edition_name}.")
            return

        # запоминаем документ, иначе перестройка окна его сотрёт
        self._snapshot = {
            "text": self.editor.get("1.0", "end-1c"),
            "cursor": self.editor.index(tk.INSERT),
            "dirty": self._dirty,
            "file": self.current_file,
        }
        self.theme_name = name
        self.theme = THEMES[name]
        self._save_cfg()
        self._rebuild()

    def set_edition(self, name):
        if name not in EDITIONS:
            return
        self._snapshot = {
            "text": self.editor.get("1.0", "end-1c"),
            "cursor": self.editor.index(tk.INSERT),
            "dirty": self._dirty,
            "file": self.current_file,
        }
        self.edition_name = name
        self.edition = EDITIONS[name]
        self._save_cfg()
        self._rebuild()

    def _rebuild(self):
        for w in self.root.winfo_children():
            w.destroy()
        self._build_main()

    # ==================================================================
    # Файлы
    # ==================================================================

    def _refresh_files(self):
        try:
            self.file_list.delete(0, tk.END)
            found = sorted(f for f in os.listdir(self.workspace) if f.endswith(".lpp"))
        except OSError:
            found = []
        for f in found:
            self.file_list.insert(tk.END, f" {f}")
        if not found:
            self.file_list.insert(tk.END, " (нет файлов .lpp)")
        try:
            self.lbl_workspace.config(text=self._short_workspace())
        except (AttributeError, tk.TclError):
            pass

    def _open_from_list(self, event=None):
        sel = self.file_list.curselection()
        if not sel:
            return
        name = self.file_list.get(sel[0]).strip()
        path = os.path.join(self.workspace, name)
        if os.path.isfile(path):
            self._load_path(path)

    def new_file(self):
        if not self._confirm_discard():
            return
        self.editor.delete("1.0", tk.END)
        self.current_file = None
        self._dirty = False
        self.editor.edit_modified(False)
        self._update_title()
        self._do_highlight()
        self._update_gutter()
        self.set_status("Новый файл")

    def open_file(self):
        if not self._confirm_discard():
            return
        path = filedialog.askopenfilename(
            initialdir=self.workspace,
            filetypes=[("L++", "*.lpp"), ("Все файлы", "*.*")],
        )
        if path:
            self._load_path(path)

    def _load_path(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            show_dialog(self.root, self.theme, "Ошибка", str(e))
            return
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", text)
        self.current_file = path
        self.workspace = os.path.dirname(os.path.abspath(path))
        self._dirty = False
        self.editor.edit_modified(False)
        self._update_title()
        self._do_highlight()
        self._update_gutter()
        self._refresh_files()
        self.set_status(f"Открыт: {os.path.basename(path)}")

    def save_file(self):
        if not self.current_file:
            return self.save_file_as()
        if not self._check_line_limit():
            return False
        try:
            with open(self.current_file, "w", encoding="utf-8", newline="\n") as f:
                f.write(self.editor.get("1.0", "end-1c"))
        except OSError as e:
            show_dialog(self.root, self.theme, "Ошибка сохранения", str(e))
            return False
        self._dirty = False
        self.editor.edit_modified(False)
        self._update_title()
        self._refresh_files()
        self.set_status(f"Сохранено: {os.path.basename(self.current_file)}")
        return True

    def save_file_as(self):
        path = filedialog.asksaveasfilename(
            initialdir=self.workspace,
            defaultextension=".lpp",
            filetypes=[("L++", "*.lpp")],
        )
        if not path:
            return False
        self.current_file = path
        self.workspace = os.path.dirname(os.path.abspath(path))
        self._update_title()
        return self.save_file()

    def _check_line_limit(self):
        limit = self.edition.get("max_lines", 0)
        if not limit:
            return True
        lines = int(self.editor.index("end-1c").split(".")[0])
        if lines > limit:
            show_dialog(
                self.root, self.theme, "Лимит издания",
                f"В издании {self.edition_name} максимум {limit} строк "
                f"(у вас {lines}).",
            )
            return False
        return True

    def _confirm_discard(self):
        if not self._dirty:
            return True
        answer = show_dialog(self.root, self.theme, "Несохранённые изменения",
                             "Сохранить изменения?", ("Да", "Нет", "Отмена"))
        if answer == "Да":
            return bool(self.save_file())
        return answer == "Нет"

    # ==================================================================
    # Запуск программы
    # ==================================================================

    def run_code(self):
        if self._running:
            self.set_status("Уже выполняется")
            return
        if not self._check_line_limit():
            return

        code = self.editor.get("1.0", "end-1c")
        self.clear_console()
        self._running = True
        self._stop_flag.clear()

        if self._needs_main_thread(code):
            self._run_in_main(code)
        else:
            self._run_in_thread(code)

    def _needs_main_thread(self, code):
        """GUI-аддоны создают окна Tk — только из главного потока."""
        for name in GUI_ADDONS:
            if re.search(rf"\bвключить\s+{re.escape(name)}\b", code):
                return True
        return False

    def _base_dir(self):
        """Папка, относительно которой ищутся файлы из `включить "файл.lpp"`."""
        if self.current_file:
            return os.path.dirname(os.path.abspath(self.current_file))
        return self.workspace

    def _run_in_thread(self, code):
        self.set_status("Выполнение...")

        def worker():
            interp = Interpreter(
                output=lambda s: self._ui(lambda t=s: self._append(t)),
                input_reader=self._gui_input,
                should_stop=self._stop_flag.is_set,
                notice=lambda s: self._ui(lambda t=s: self._append(t, "muted")),
                base_dir=self._base_dir(),
            )
            try:
                interp.run(code)
                self._ui(lambda: self._finish_run("Успешно"))
            except LppError as e:
                self._ui(lambda err=e: self._finish_run(str(err), error=True))
            except Exception as e:  # непредвиденная ошибка Python
                self._ui(lambda err=e: self._finish_run(
                    f"внутренняя ошибка: {type(err).__name__}: {err}", error=True))

        threading.Thread(target=worker, daemon=True).start()

    def _run_in_main(self, code):
        """Режим для программ с окнами: работает в главном потоке.

        Раз в блок операторов вызывается root.update(), поэтому окно IDE
        остаётся живым, а кнопка «Стоп» продолжает реагировать.
        """
        self.set_status("Выполнение (окна аддонов)...")
        self._append("[запуск в главном потоке: нужен для аддонов с окнами]\n", "muted")

        def pump_and_check():
            try:
                self.root.update()
            except tk.TclError:
                return True
            return self._stop_flag.is_set()

        interp = Interpreter(
            output=self._append,
            input_reader=self._gui_input_direct,
            should_stop=pump_and_check,
            notice=lambda s: self._append(s, "muted"),
            base_dir=self._base_dir(),
        )
        try:
            interp.run(code)
            self._finish_run("Успешно")
        except LppError as e:
            self._finish_run(str(e), error=True)
        except Exception as e:
            self._finish_run(f"внутренняя ошибка: {type(e).__name__}: {e}", error=True)

    def stop_code(self):
        if not self._running:
            self.set_status("Нечего останавливать")
            return
        self._stop_flag.set()
        self.set_status("Остановка...")

    def _finish_run(self, message, error=False):
        self._running = False
        if error:
            self._append(f"\n[ОШИБКА]: {message}\n", "err")
            self.set_status("Ошибка")
        else:
            self.set_status(message)

    def _gui_input(self, prompt=""):
        """Вызывается из рабочего потока — диалог показываем в главном."""
        box = {}
        done = threading.Event()

        def task():
            try:
                box["value"] = simpledialog.askstring(
                    "Ввод (L++)", prompt or "Введите значение:", parent=self.root
                )
            except tk.TclError:
                box["value"] = ""
            finally:
                done.set()

        self._ui(task)
        if not done.wait(timeout=120):
            return ""
        return box.get("value") or ""

    def _gui_input_direct(self, prompt=""):
        """То же, но когда код выполняется в главном потоке — напрямую."""
        try:
            value = simpledialog.askstring(
                "Ввод (L++)", prompt or "Введите значение:", parent=self.root
            )
        except tk.TclError:
            return ""
        return value or ""

    # ==================================================================
    # Консоль
    # ==================================================================

    def _append(self, text, tag=None):
        try:
            self.console.config(state=tk.NORMAL)
            if tag:
                self.console.insert(tk.END, text, tag)
            else:
                self.console.insert(tk.END, text)
            self.console.see(tk.END)
            self.console.config(state=tk.DISABLED)
        except tk.TclError:
            pass

    def clear_console(self):
        try:
            self.console.config(state=tk.NORMAL)
            self.console.delete("1.0", tk.END)
            self.console.config(state=tk.DISABLED)
        except tk.TclError:
            pass

    def _run_tests_async(self):
        def worker():
            results = run_self_tests()
            self._ui(lambda: self._render_tests(results))

        threading.Thread(target=worker, daemon=True).start()

    def _render_tests(self, results):
        passed = sum(1 for _, ok, _ in results if ok)
        total = len(results)
        if passed == total:
            self._append(f"✅ Само-тесты: {passed}/{total} прошло\n", "ok")
            return
        self._append(f"⚠️ Само-тесты: {passed}/{total} прошло\n", "err")
        for name, ok, err in results:
            if not ok:
                self._append(f"  ❌ {name}: {err}\n", "err")

    # ==================================================================
    # Редактор
    # ==================================================================

    def _on_editor_scroll(self, first, last):
        try:
            self.gutter.yview_moveto(first)
            self.vbar.set(first, last)
        except tk.TclError:
            pass

    def _on_modified(self, event=None):
        try:
            if self.editor.edit_modified():
                self._dirty = True
                self._update_title()
                self.editor.edit_modified(False)
        except tk.TclError:
            pass

    def _on_return(self, event=None):
        line = self.editor.get("insert linestart", "insert")
        indent = re.match(r"[ \t]*", line).group(0)
        stripped = line.rstrip()
        if stripped.endswith("то:") or stripped.endswith("иначе:") or (
            stripped.endswith(":") and stripped.strip().startswith("функция")
        ):
            indent += "    "
        self.editor.insert("insert", "\n" + indent)
        self.editor.see("insert")
        return "break"

    def _on_tab(self, event=None):
        self.editor.insert("insert", "    ")
        return "break"

    def toggle_comment(self, event=None):
        try:
            first = self.editor.index("sel.first linestart")
            last = self.editor.index("sel.last linestart")
        except tk.TclError:
            first = last = self.editor.index("insert linestart")

        start_line = int(first.split(".")[0])
        end_line = int(last.split(".")[0])

        lines = []
        for ln in range(start_line, end_line + 1):
            lines.append(self.editor.get(f"{ln}.0", f"{ln}.end"))

        commented = all(line.lstrip().startswith("//") or not line.strip() for line in lines)
        for offset, ln in enumerate(range(start_line, end_line + 1)):
            line = lines[offset]
            if not line.strip():
                continue
            if commented:
                new = re.sub(r"^(\s*)//\s?", r"\1", line, count=1)
            else:
                new = re.sub(r"^(\s*)", r"\1// ", line, count=1)
            self.editor.delete(f"{ln}.0", f"{ln}.end")
            self.editor.insert(f"{ln}.0", new)
        return "break"

    def _update_gutter(self):
        content = self.editor.get("1.0", "end-1c")
        count = content.count("\n") + 1 if content else 1
        try:
            self.gutter.config(state=tk.NORMAL, width=len(str(count)) + 2)
            self.gutter.delete("1.0", tk.END)
            self.gutter.insert("1.0", "\n".join(str(i) for i in range(1, count + 1)))
            self.gutter.config(state=tk.DISABLED)
        except tk.TclError:
            pass

    def _pos(self, event=None):
        try:
            line, col = self.editor.index(tk.INSERT).split(".")
            self.lbl_pos.config(text=f"Стр {line}, Кол {int(col) + 1}")
        except (ValueError, tk.TclError):
            pass

    def on_key(self, event=None):
        if self._highlight_job:
            try:
                self.root.after_cancel(self._highlight_job)
            except tk.TclError:
                pass
        self._highlight_job = self.root.after(60, self._do_highlight)
        self._pos()

    def _do_highlight(self):
        self._highlight_job = None
        try:
            self.highlighter.apply()
            self._update_gutter()
            self._on_editor_scroll(*self.editor.yview())
        except tk.TclError:
            pass

    # ==================================================================
    # Поиск
    # ==================================================================

    def open_find(self):
        try:
            if self._find_window is not None and self._find_window.winfo_exists():
                self._find_window.lift()
                self._find_window.focus_force()
                return
        except tk.TclError:
            pass
        self._find_window = FindReplace(self)

    # ==================================================================
    # Библиотеки (аддоны)
    # ==================================================================

    def _load_addons(self):
        try:
            return sorted(f[:-3] for f in os.listdir(ADDONS_DIR) if f.endswith(".py"))
        except OSError:
            return []

    def show_libs(self):
        if not self.edition["allow_addons"]:
            show_dialog(self.root, self.theme, "Недоступно",
                        f"Аддоны недоступны в издании {self.edition_name}.")
            return

        th = self.theme
        win = tk.Toplevel(self.root)
        win.title("Библиотеки")
        center(win, 720, 540)
        win.configure(bg=th["bg_main"])
        fade_in(win, steps=8, delay=10)

        nb = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- встроенные ---
        tab1 = tk.Frame(nb, bg=th["bg_main"])
        nb.add(tab1, text="Встроенные")
        builtin = ["math", "random", "time", "os", "sys", "json", "re"]
        for name in builtin:
            row = tk.Frame(tab1, bg=th["bg_panel"], pady=7, padx=10)
            row.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(row, text=name, bg=th["bg_panel"], fg=th["fg_main"],
                     font=UI_FONT).pack(side=tk.LEFT)
            tk.Label(row, text=f"включить {name}", bg=th["bg_panel"],
                     fg=th["fg_muted"], font=UI_FONT_SMALL).pack(side=tk.RIGHT)

        # --- установленные ---
        tab2 = tk.Frame(nb, bg=th["bg_main"])
        nb.add(tab2, text="Мои аддоны")
        addons = self._load_addons()
        if not addons:
            tk.Label(tab2, text="Пусто", bg=th["bg_main"], fg=th["fg_muted"]).pack(pady=20)
        for name in addons:
            row = tk.Frame(tab2, bg=th["bg_panel"], pady=7, padx=10)
            row.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(row, text=name, bg=th["bg_panel"], fg=th["fg_main"],
                     font=UI_FONT).pack(side=tk.LEFT)
            tk.Label(row, text=f"включить {name}", bg=th["bg_panel"],
                     fg=th["fg_muted"], font=UI_FONT_SMALL).pack(side=tk.RIGHT)

        # --- создать ---
        tab3 = tk.Frame(nb, bg=th["bg_main"])
        nb.add(tab3, text="Создать")
        tk.Label(tab3, text="Имя модуля (латиница, цифры, _):", bg=th["bg_main"],
                 fg=th["fg_main"], font=UI_FONT).pack(anchor="w", padx=18, pady=(10, 4))
        entry_name = tk.Entry(tab3, bg=th["bg_panel"], fg=th["fg_main"],
                              insertbackground=th["fg_main"], relief=tk.FLAT)
        entry_name.pack(fill=tk.X, padx=18, ipady=5)
        tk.Label(tab3, text="Код модуля (Python):", bg=th["bg_main"], fg=th["fg_main"],
                 font=UI_FONT).pack(anchor="w", padx=18, pady=(10, 4))
        code_text = tk.Text(tab3, bg=th["bg_panel"], fg=th["fg_main"], height=10,
                            insertbackground=th["fg_main"], relief=tk.FLAT,
                            font=("Consolas", 10))
        code_text.pack(fill=tk.BOTH, expand=True, padx=18, pady=4)

        def load_py():
            path = filedialog.askopenfilename(filetypes=[("Python", "*.py")])
            if not path:
                return
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except OSError as e:
                show_dialog(win, th, "Ошибка", str(e))
                return
            code_text.delete("1.0", tk.END)
            code_text.insert("1.0", content)
            entry_name.delete(0, tk.END)
            entry_name.insert(0, os.path.splitext(os.path.basename(path))[0])

        def save_lib():
            name = entry_name.get().strip()
            content = code_text.get("1.0", tk.END).strip()
            if not name or not content:
                return
            if not re.match(r"^\w+$", name):
                show_dialog(win, th, "Ошибка", "Имя: латиница, цифры и _")
                return
            try:
                os.makedirs(ADDONS_DIR, exist_ok=True)
                with open(os.path.join(ADDONS_DIR, name + ".py"), "w",
                          encoding="utf-8") as f:
                    f.write(content + "\n")
            except OSError as e:
                show_dialog(win, th, "Ошибка", str(e))
                return
            import sys
            sys.modules.pop(name, None)
            show_dialog(win, th, "Готово", f"Установлено: {name}\nВ коде: включить {name}")
            win.destroy()
            self.show_libs()

        row = tk.Frame(tab3, bg=th["bg_main"])
        row.pack(fill=tk.X, padx=18, pady=10)
        tk.Button(row, text="📂 Загрузить .py", command=load_py, bg=th["accent"],
                  fg="#fff", relief=tk.FLAT, padx=12, pady=4).pack(side=tk.LEFT)
        tk.Button(row, text="💾 Сохранить", command=save_lib, bg=th["accent_green"],
                  fg="#fff", relief=tk.FLAT, padx=12, pady=4).pack(side=tk.RIGHT)

    # ==================================================================
    # Выход
    # ==================================================================

    def on_close(self):
        if self._running:
            if not show_dialog(self.root, self.theme, "Программа выполняется",
                               "Остановить выполнение и выйти?", ("Да", "Нет")) == "Да":
                return
            self._stop_flag.set()
        if not self._confirm_discard():
            return
        self._save_cfg()
        self._alive = False
        # отменяем отложенные callback'и, иначе Tk ругается после destroy
        for attr in ("_drain_id", "_highlight_job"):
            job = getattr(self, attr, None)
            if job:
                try:
                    self.root.after_cancel(job)
                except tk.TclError:
                    pass
                setattr(self, attr, None)
        try:
            self.root.destroy()
        except tk.TclError:
            pass


def _log_crash(text):
    """pythonw не показывает консоль — пишем трейсбек в файл."""
    import traceback
    try:
        from ..paths import CONFIG_DIR
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(os.path.join(CONFIG_DIR, "error.log"), "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 60 + "\n" + text + traceback.format_exc())
    except Exception:
        pass


def main():
    """Точка входа приложения."""
    try:  # аккуратный шрифт на HiDPI-экранах Windows
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    root.title("L++ IDE")
    root.geometry("1350x850")

    try:
        L_IDE(root)
    except Exception as exc:
        _log_crash("Ошибка при запуске IDE\n")
        try:
            from tkinter import messagebox
            messagebox.showerror(
                "L++ IDE — ошибка запуска",
                f"{type(exc).__name__}: {exc}\n\nПодробности: "
                f"%APPDATA%\\LppIDE\\error.log",
            )
        except Exception:
            pass
        return

    try:
        root.mainloop()
    except Exception:
        _log_crash("Ошибка во время работы\n")


if __name__ == "__main__":
    main()

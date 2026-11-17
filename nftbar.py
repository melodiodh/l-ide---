# addons/nftbar.py
# NFTbar — нижняя панель (док) для окон L++.
#
# Было: координаты считались от края ЭКРАНА, но place() работает относительно
# родителя — панель уезжала за пределы окна. Теперь позиция считается от
# размеров родительского окна.

import tkinter as tk

DOCK_MARGIN = 20


class _NftBar:
    def __init__(self, parent, width, height, bg_color, accent_color):
        self.parent = parent
        self.width = width
        self.height = height
        self.accent = accent_color
        self.bg_color = bg_color

        self.frame = tk.Frame(
            parent, bg=bg_color,
            highlightbackground=accent_color, highlightthickness=2,
            padx=10, pady=10,
        )
        self.inner = tk.Frame(self.frame, bg=bg_color)
        self.inner.pack(expand=True)

        self._place()
        # при изменении размера окна — пересчитать позицию
        try:
            parent.bind("<Configure>", self._on_configure, add="+")
        except Exception:
            pass

    # ---------- геометрия ----------

    def _place(self):
        parent = self.parent
        try:
            pw = parent.winfo_width()
            ph = parent.winfo_height()
        except Exception:
            pw, ph = 800, 600
        if pw <= 1 or ph <= 1:          # окно ещё не отрисовано
            pw, ph = 800, 600
        x = max(0, (pw - self.width) // 2)
        y = max(0, ph - self.height - DOCK_MARGIN)
        self.frame.place(x=x, y=y, width=self.width, height=self.height)

    def _on_configure(self, event=None):
        if event is not None and event.widget is not self.parent:
            return
        self._place()

    # ---------- элементы ----------

    def ДобавитьКнопку(self, text, command=None, icon="✨"):
        btn = tk.Button(
            self.inner, text=f"{icon} {text}", command=command,
            bg=self.bg_color, fg="#FFFFFF", font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, activebackground=self.accent, activeforeground="#FFFFFF",
            cursor="hand2", padx=15, pady=5,
        )
        btn.pack(side=tk.LEFT, padx=5)

        btn.bind("<Enter>", lambda e: btn.config(bg=self.accent))
        btn.bind("<Leave>", lambda e: btn.config(bg=self.bg_color))
        return btn

    def ДобавитьРазделитель(self):
        sep = tk.Frame(self.inner, bg=self.accent, width=2, height=20)
        sep.pack(side=tk.LEFT, padx=10)
        return sep

    def ДобавитьИндикатор(self, text="● Online", color="#22C55E"):
        lbl = tk.Label(
            self.inner, text=text, bg=self.bg_color, fg=color,
            font=("Segoe UI", 9, "bold"),
        )
        lbl.pack(side=tk.RIGHT, padx=10)
        return lbl

    # ---------- видимость ----------

    def Скрыть(self):
        self.frame.place_forget()

    def Показать(self):
        self._place()

    def Уничтожить(self):
        try:
            self.frame.destroy()
        except Exception:
            pass


def Панель(parent, width=600, height=60, bg_color="#161B22", accent_color="#58A6FF"):
    """Создаёт нижнюю панель. parent — окно, в которое её встроить."""
    if parent is None:
        parent = tk.Toplevel()
        parent.geometry("800x600")
    return _NftBar(parent, width, height, bg_color, accent_color)

# addons/whooshint.py
# WhooshINT — Beautiful Interface for L++
import tkinter as tk
import tkinter.font as tkfont

class Окно:
    def __init__(self, title="WhooshINT", width=800, height=600, bg="#1E1E1E"):
        self.root = tk.Toplevel()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.root.configure(bg=bg)
        self._bg = bg
        
    def Показать(self):
        """Показывает окно. Внутри IDE не запускает второй mainloop."""
        try:
            self.root.deiconify()
            self.root.lift()
            if tk._default_root is None:
                self.root.mainloop()
        except Exception:
            pass
        
    def Скрыть(self):
        self.root.withdraw()
        
    def Закрыть(self):
        self.root.destroy()

    def ДобавитьТекст(self, text, x, y, size=14, color="#FFFFFF", font_name="Segoe UI"):
        lbl = tk.Label(self.root, text=text, bg=self._bg, fg=color, 
                       font=(font_name, size))
        lbl.place(x=x, y=y)
        return lbl

    def ДобавитьКнопку(self, text, x, y, width=150, height=40, command=None):
        btn = tk.Button(self.root, text=text, command=command,
                        bg="#3B82F6", fg="#FFFFFF", 
                        font=("Segoe UI", 11, "bold"),
                        relief=tk.FLAT, cursor="hand2")
        btn.place(x=x, y=y, width=width, height=height)
        
        # Эффект наведения
        def on_enter(e):
            btn.config(bg="#2563EB")
        def on_leave(e):
            btn.config(bg="#3B82F6")
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def ДобавитьПоле(self, x, y, width=200, height=30, placeholder=""):
        entry = tk.Entry(self.root, bg="#2D2D2D", fg="#FFFFFF", 
                         insertbackground="#FFFFFF", relief=tk.FLAT,
                         font=("Segoe UI", 11))
        entry.place(x=x, y=y, width=width, height=height)
        if placeholder:
            entry.insert(0, placeholder)
            entry.config(fg="#888888")
            def on_focus_in(e):
                if entry.get() == placeholder:
                    entry.delete(0, tk.END)
                    entry.config(fg="#FFFFFF")
            def on_focus_out(e):
                if not entry.get():
                    entry.insert(0, placeholder)
                    entry.config(fg="#888888")
            entry.bind("<FocusIn>", on_focus_in)
            entry.bind("<FocusOut>", on_focus_out)
        return entry

    def ДобавитьКартинку(self, path, x, y):
        try:
            img = tk.PhotoImage(file=path)
            lbl = tk.Label(self.root, image=img, bg=self._bg)
            lbl.image = img
            lbl.place(x=x, y=y)
            return lbl
        except Exception as e:
            print(f"Ошибка загрузки картинки: {e}")
            return None

    def Прямоугольник(self, x, y, width, height, color="#333333"):
        canvas = tk.Canvas(self.root, width=width, height=height, bg=self._bg, 
                           highlightthickness=0)
        canvas.place(x=x, y=y)
        canvas.create_rectangle(0, 0, width, height, fill=color, outline="")
        return canvas

# Утилиты
def Центр(x=0, y=0):
    return x, y

def СлучайныйЦвет():
    import random
    return f"#{random.randint(0,255):02x}{random.randint(0,255):02x}{random.randint(0,255):02x}"
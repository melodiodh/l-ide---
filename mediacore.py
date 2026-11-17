# addons/mixday/mediacore.py
import tkinter as tk
import math
import os

# ==========================================
# РИСОВАНИЕ (Черепашка / Turtle)
# ==========================================
class _Черепашка:
    def __init__(self, w=800, h=600, bg="white"):
        self.root = tk.Toplevel()
        self.root.title("MixDay Turtle")
        self.canvas = tk.Canvas(self.root, width=w, height=h, bg=bg)
        self.canvas.pack()
        self.x = w // 2
        self.y = h // 2
        self.angle = 0
        self.pen_down = True
        self.color = "black"
        self.width = 2

    def Вперед(self, distance):
        rad = math.radians(self.angle)
        nx = self.x + distance * math.cos(rad)
        ny = self.y + distance * math.sin(rad)
        if self.pen_down:
            self.canvas.create_line(self.x, self.y, nx, ny, fill=self.color, width=self.width)
        self.x, self.y = nx, ny
        self.root.update()

    def Назад(self, distance): self.Вперед(-distance)
    def Вправо(self, angle): self.angle += angle
    def Влево(self, angle): self.angle -= angle
    def ПоднятьПеро(self): self.pen_down = False
    def ОпуститьПеро(self): self.pen_down = True
    def Цвет(self, color): self.color = color
    def Толщина(self, w): self.width = w
    def Прыжок(self, x, y): self.x, self.y = x, y

def СоздатьЧерепашку(w=800, h=600, bg="white"):
    return _Черепашка(w, h, bg)

# ==========================================
# ПРОСТАЯ ГРАФИКА (Окна с фигурами)
# ==========================================
class _Графика:
    def __init__(self, w=800, h=600, bg="#0D1117"):
        self.root = tk.Toplevel()
        self.root.title("MixDay Graphics")
        self.canvas = tk.Canvas(self.root, width=w, height=h, bg=bg, highlightthickness=0)
        self.canvas.pack()

    def Круг(self, x, y, radius, color="red"):
        self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill=color, outline="")
        self.root.update()

    def Квадрат(self, x, y, size, color="blue"):
        self.canvas.create_rectangle(x, y, x+size, y+size, fill=color, outline="")
        self.root.update()

    def Линия(self, x1, y1, x2, y2, color="white", width=2):
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
        self.root.update()

    def Текст(self, x, y, text, size=16, color="white"):
        self.canvas.create_text(x, y, text=text, fill=color, font=("Segoe UI", size, "bold"))
        self.root.update()

    def Очистить(self):
        self.canvas.delete("all")

def СоздатьГрафику(w=800, h=600, bg="#0D1117"):
    return _Графика(w, h, bg)

# ==========================================
# ЗВУК (Системные сигналы Windows)
# ==========================================
def ЗвукОшибки():
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONHAND)
    except: pass

def ЗвукВопроса():
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONQUESTION)
    except: pass

def ЗвукИнформации():
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except: pass

def ЗвукПредупреждения():
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except: pass
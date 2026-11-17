# addons/lgame.py
# Lgame — игровой движок для L++
import tkinter as tk
import random
import time

class _GameEngine:
    def __init__(self, title="Lgame Window", width=800, height=600, bg="#0D1117"):
        self.root = tk.Toplevel()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.root.configure(bg=bg)
        
        # Холст для рисования
        self.canvas = tk.Canvas(self.root, width=width, height=height, bg=bg, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.width = width
        self.height = height
        self.running = False
        self.keys_pressed = set()
        
        # Состояние игрока по умолчанию
        self.player_x = width // 2
        self.player_y = height // 2
        self.player_size = 40
        self.player_color = "#58A6FF"
        self.player_speed = 10
        
        # Объекты
        self.sprites = []  # список словарей: {"id": canvas_id, "x": x, "y": y, "w": w, "h": h, "type": "enemy"}
        self.score = 0
        
        # Привязка клавиш
        self.root.bind("<KeyPress>", self._on_key_down)
        self.root.bind("<KeyRelease>", self._on_key_up)
        self.root.protocol("WM_DELETE_WINDOW", self.Закрыть)
        try:
            self.root.focus_set()
        except Exception:
            pass

        # Игровой цикл запускаем отдельно
        self._loop_running = False

    def _on_key_down(self, event):
        self.keys_pressed.add(event.keysym.lower())

    def _on_key_up(self, event):
        self.keys_pressed.discard(event.keysym.lower())

    def _update_loop(self):
        if not self._loop_running:
            return
        
        # Движение игрока
        if "w" in self.keys_pressed or "up" in self.keys_pressed:
            self.player_y -= self.player_speed
        if "s" in self.keys_pressed or "down" in self.keys_pressed:
            self.player_y += self.player_speed
        if "a" in self.keys_pressed or "left" in self.keys_pressed:
            self.player_x -= self.player_speed
        if "d" in self.keys_pressed or "right" in self.keys_pressed:
            self.player_x += self.player_speed
            
        # Ограничение по краям
        self.player_x = max(0, min(self.width - self.player_size, self.player_x))
        self.player_y = max(0, min(self.height - self.player_size, self.player_y))
        
        # Отрисовка
        self._draw()

        # Повтор через 16 мс (~60 FPS)
        try:
            self.root.after(16, self._update_loop)
        except Exception:
            self._loop_running = False

    def Закрыть(self):
        """Останавливает цикл и закрывает окно (без TclError после destroy)."""
        self._loop_running = False
        self.running = False
        try:
            self.root.destroy()
        except Exception:
            pass

    def _draw(self):
        self.canvas.delete("all")
        
        # Рисуем врагов
        for s in self.sprites:
            self.canvas.create_rectangle(s["x"], s["y"], s["x"]+s["w"], s["y"]+s["h"], 
                                          fill="#DA3633", outline="")
        
        # Рисуем игрока
        self.canvas.create_rectangle(self.player_x, self.player_y, 
                                      self.player_x + self.player_size, 
                                      self.player_y + self.player_size, 
                                      fill=self.player_color, outline="#FFFFFF", width=2)
        
        # Рисуем очки
        self.canvas.create_text(20, 20, text=f"Очки: {self.score}", 
                                fill="#FFFFFF", font=("Segoe UI", 16, "bold"), anchor="nw")

    def Запустить(self):
        self.running = True
        self._loop_running = True
        self._update_loop()

    def Остановить(self):
        self.running = False
        self._loop_running = False

    def СпавнВрага(self):
        x = random.randint(50, self.width - 50)
        y = random.randint(50, self.height - 50)
        w = 30
        h = 30
        self.sprites.append({"x": x, "y": y, "w": w, "h": h})
        return len(self.sprites) - 1

    def ПолучитьПозицию(self):
        return (self.player_x, self.player_y)

    def ПроверитьКоллизию(self):
        """Возвращает True, если игрок столкнулся с врагом."""
        px1, py1 = self.player_x, self.player_y
        px2, py2 = px1 + self.player_size, py1 + self.player_size
        for s in self.sprites:
            sx1, sy1 = s["x"], s["y"]
            sx2, sy2 = sx1 + s["w"], sy1 + s["h"]
            if px1 < sx2 and px2 > sx1 and py1 < sy2 and py2 > sy1:
                return True
        return False

    def ДобавитьОчки(self, n):
        self.score += n

    def Очистить(self):
        self.sprites.clear()
        self.score = 0

def СоздатьИгру(title="Lgame", width=800, height=600, bg="#0D1117"):
    return _GameEngine(title, width, height, bg)
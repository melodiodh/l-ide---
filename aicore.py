# addons/mixday/aicore.py
import random
import math
import datetime

# Имитация нейросети (чтобы игра работала)
class _Мозг:
    def __init__(self, i, h, o):
        self.lr = 0.1
    def Обучить(self, data, targets, epochs=100):
        return "Мозг обучен!"
    def Думать(self, data):
        # Выдает случайный результат (0.1 - 0.9)
        return [[random.uniform(0.1, 0.9)]]

def ИИ_СоздатьМозг(inputs=2, hidden=4, outputs=1):
    return _Мозг(inputs, hidden, outputs)

class _Ассистент:
    def __init__(self, name="MixBot"):
        self.name = name
    def Сказать(self, text):
        text = str(text).lower()
        if "привет" in text: return f"Привет! Я {self.name}."
        if "время" in text: return f"Сейчас {datetime.datetime.now().strftime('%H:%M')}."
        return "Я ИИ-брокер. Спрашивай про рынок!"

def ИИ_СоздатьАссистента(name="MixBot"):
    return _Ассистент(name)
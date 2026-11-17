# addons/mixday/helloos.py
import os
import sys
import datetime
import platform

# ==========================================
# СИСТЕМНАЯ ИНФОРМАЦИЯ
# ==========================================
def ИмяОС(): return platform.system()
def ВерсияОС(): return platform.version()
def Архитектура(): return platform.machine()
def ИмяКомпьютера(): return platform.node()
def ИмяПользователя():
    try:
        return os.getlogin()
    except Exception:
        return os.environ.get("USERNAME") or os.environ.get("USER") or "User"
def ТекущаяПапка(): return os.getcwd()
def ПитонВерсия(): return sys.version

# ==========================================
# ФАЙЛОВАЯ СИСТЕМА
# ==========================================
def СоздатьПапку(path):
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False

def УдалитьФайл(path):
    try:
        os.remove(path)
        return True
    except Exception:
        return False

def СуществуетЛи(path):
    return os.path.exists(path)

def СписокФайлов(path="."):
    try:
        return os.listdir(path)
    except Exception:
        return []

def РазмерФайла(path):
    try:
        return os.path.getsize(path)
    except Exception:
        return -1

def ЗаписатьФайл(path, text):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(text))
        return True
    except Exception:
        return False

def ПрочитатьФайл(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

# ==========================================
# ВРЕМЯ И ДАТА
# ==========================================
def Сейчас():
    return datetime.datetime.now().strftime("%H:%M:%S")

def Сегодня():
    return datetime.datetime.now().strftime("%d.%m.%Y")

def Год(): return datetime.datetime.now().year
def Месяц(): return datetime.datetime.now().month
def День(): return datetime.datetime.now().day
def Час(): return datetime.datetime.now().hour
def Минута(): return datetime.datetime.now().minute
def Секунда(): return datetime.datetime.now().second

def ТаймерСекунд(sec):
    """Ждёт указанное количество секунд"""
    import time
    time.sleep(sec)

# ==========================================
# СИСТЕМНЫЕ КОМАНДЫ
# ==========================================
def ОчиститьЭкран():
    os.system('cls' if os.name == 'nt' else 'clear')

def ВыполнитьКоманду(cmd):
    """ВНИМАНИЕ: выполняет произвольную команду ОС."""
    return os.system(cmd)

def ОткрытьСайт(url):
    import webbrowser
    webbrowser.open(url)
    return True

# ==========================================
# ОПАСНЫЕ ОПЕРАЦИИ (с подтверждением)
# ==========================================
def _confirm_power(action):
    """Спрашивает подтверждение, чтобы скрипт не выключил ПК молча.

    Отключить вопрос можно переменной окружения LPP_ALLOW_POWER=1.
    """
    if os.environ.get("LPP_ALLOW_POWER") == "1":
        return True
    try:
        import tkinter as tk
        from tkinter import messagebox
        if tk._default_root is None:
            return False
        return bool(messagebox.askyesno("L++", f"{action}?"))
    except Exception:
        return False

def ВыключитьКомпьютер():
    """ВНИМАНИЕ! Выключает ПК (Windows). Требует подтверждения."""
    if not _confirm_power("Выключить компьютер"):
        return False
    os.system("shutdown /s /t 5")
    return True

def ПерезагрузитьКомпьютер():
    """ВНИМАНИЕ! Перезагружает ПК (Windows). Требует подтверждения."""
    if not _confirm_power("Перезагрузить компьютер"):
        return False
    os.system("shutdown /r /t 5")
    return True

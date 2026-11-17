# addons/mixday/extracore.py
import random

# ==========================================
# СТРОКОВЫЕ ФУНКЦИИ (Уровень 1-5)
# ==========================================
def СтрокаВВерхний(text): return str(text).upper()
def СтрокаВНижний(text): return str(text).lower()
def СтрокаЗаменить(text, old, new): return str(text).replace(str(old), str(new))
def СтрокаРазбить(text, sep=" "): return str(text).split(sep)
def СтрокаСклеить(lst, sep=""): return sep.join(str(x) for x in lst)
def СтрокаДлина(text): return len(str(text))
def СтрокаОбрезать(text): return str(text).strip()
def СтрокаНайти(text, sub): return str(text).find(str(sub))

def СтрокаПалиндром(text):
    s = str(text).lower().replace(" ", "")
    return s == s[::-1]

def СтрокаПеревернуть(text): return str(text)[::-1]

def СтрокаПервыйСимвол(text): return str(text)[0] if text else ""
def СтрокаПоследнийСимвол(text): return str(text)[-1] if text else ""

def СтрокаЗаменитьРегистр(text):
    """Инвертирует регистр: ПрИвЕт -> пРИВЕТ"""
    res = ""
    for c in str(text):
        res += c.lower() if c.isupper() else c.upper()
    return res

def СтрокаПовторить(text, n): return str(text) * int(n)

def СтрокаУдалитьПробелы(text):
    return "".join(str(text).split())

def СтрокаФормат(text, *args):
    """Аналог "Привет, {}!".format("Мир")"""
    try:
        return str(text).format(*args)
    except: return str(text)

# ==========================================
# МАССИВЫ И СПИСКИ (Уровень 1-6)
# ==========================================
def МассивСумма(arr): return sum(arr)
def МассивМин(arr): return min(arr) if arr else 0
def МассивМакс(arr): return max(arr) if arr else 0
def МассивДлина(arr): return len(arr)
def МассивРеверс(arr): return arr[::-1]
def МассивУникальные(arr): return list(set(arr))

def МассивСортировка(arr):
    """Быстрая сортировка (QuickSort)"""
    if len(arr) <= 1: return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return МассивСортировка(left) + middle + МассивСортировка(right)

def МассивПеремешать(arr):
    """Перемешивает список (Fisher-Yates)"""
    a = arr[:]
    random.shuffle(a)
    return a

def МассивСодержит(arr, item): return item in arr

def МассивИндекс(arr, item):
    try: return arr.index(item)
    except ValueError: return -1

def МассивСрез(arr, start, end): return arr[start:end]

def МассивСложить(a, b): return a + b

def МассивКопировать(arr): return arr[:]

def МассивОчистить(arr):
    arr.clear()
    return arr

def МассивПервый(arr): return arr[0] if arr else None
def МассивПоследний(arr): return arr[-1] if arr else None

def МассивСредний(arr):
    if not arr: return 0
    return sum(arr) / len(arr)

def МассивМедиана(arr):
    s = sorted(arr)
    n = len(s)
    if n == 0: return 0
    if n % 2 == 1: return s[n//2]
    return (s[n//2 - 1] + s[n//2]) / 2

def МассивКвадраты(arr): return [x*x for x in arr]
def МассивЧетные(arr): return [x for x in arr if x % 2 == 0]
def МассивНечетные(arr): return [x for x in arr if x % 2 != 0]
def МассивБольше(arr, num): return [x for x in arr if x > num]
def МассивМеньше(arr, num): return [x for x in arr if x < num]

def МассивРазбить(arr, size):
    """Делит массив на куски по size элементов"""
    return [arr[i:i + size] for i in range(0, len(arr), size)]

def МассивСуммаКвадратов(arr): return sum(x*x for x in arr)

# ==========================================
# УТИЛИТЫ ДЛЯ БУДУЩИХ 273 ФУНКЦИЙ
# ==========================================
def ГенераторПароля(length=12):
    import string
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choice(chars) for _ in range(length))

def СлучайныйВыбор(arr):
    return random.choice(arr) if arr else None
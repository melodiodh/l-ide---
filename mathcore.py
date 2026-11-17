# addons/mixday/mathcore.py
import math
import random
import statistics

# ==========================================
# БАЗОВАЯ МАТЕМАТИКА (Уровень 1-3)
# ==========================================
def Сумма(*args): return sum(args)
def Произведение(*args):
    res = 1
    for a in args: res *= a
    return res
def Среднее(*args): return statistics.mean(args)
def Медиана(*args): return statistics.median(args)
def Мода(*args): return statistics.mode(args)
def Дисперсия(*args): return statistics.variance(args)
def Отклонение(*args): return statistics.stdev(args)

# ==========================================
# ГЕОМЕТРИЯ И ТРИГОНОМЕТРИЯ (Уровень 4-6)
# ==========================================
def Пи(): return math.pi
def Е(): return math.e
def Синус(x): return math.sin(x)
def Косинус(x): return math.cos(x)
def Тангенс(x): return math.tan(x)
def Арксинус(x): return math.asin(x)
def Арккосинус(x): return math.acos(x)
def Арктангенс(x): return math.atan(x)
def Гипотенуза(a, b): return math.hypot(a, b)
def Градусы(x): return math.degrees(x)
def Радианы(x): return math.radians(x)

# ==========================================
# АЛГЕБРА И ЧИСЛА (Уровень 7-9)
# ==========================================
def Факториал(n): return math.factorial(n)
def НОД(a, b): return math.gcd(a, b)
def НОК(a, b): return math.lcm(a, b)
def Логарифм(x, base=math.e): return math.log(x, base)
def Логарифм10(x): return math.log10(x)
def Степень(a, b): return math.pow(a, b)
def Корень(x): return math.sqrt(x)
def КореньКуб(x): return math.cbrt(x) if hasattr(math, 'cbrt') else (x ** (1/3))
def Модуль(x): return math.fabs(x)
def Округление(x, n=0): return round(x, n)
def Потолок(x): return math.ceil(x)
def Пол(x): return math.floor(x)
def Остаток(a, b): return math.fmod(a, b)
def Целое(a, b): return a // b

# ==========================================
# ПРОДВИНУТАЯ МАТЕМАТИКА (Уровень 10-13)
# ==========================================
def ПростоеЛи(n):
    if n < 2: return False
    for i in range(2, int(math.isqrt(n)) + 1):
        if n % i == 0: return False
    return True

def Решето(n):
    """Возвращает список простых чисел до n (Решето Эратосфена)"""
    primes = []
    sieve = [True] * (n + 1)
    for p in range(2, n + 1):
        if sieve[p]:
            primes.append(p)
            for i in range(p*p, n+1, p):
                sieve[i] = False
    return primes

def Фибоначчи(n):
    """n-е число Фибоначчи"""
    a, b = 0, 1
    for _ in range(n): a, b = b, a + b
    return a

def ЧислаФибоначчи(n):
    """Список первых n чисел Фибоначчи"""
    res = []
    a, b = 0, 1
    for _ in range(n):
        res.append(a)
        a, b = b, a + b
    return res

def Комбинации(n, k): return math.comb(n, k)
def Перестановки(n, k): return math.perm(n, k)

# ==========================================
# КРИПТОГРАФИЯ И ХЕШИ (Уровень OS)
# ==========================================
import hashlib

def ХешMD5(text):
    return hashlib.md5(str(text).encode()).hexdigest()

def ХешSHA256(text):
    return hashlib.sha256(str(text).encode()).hexdigest()

def Цезарь(text, shift):
    """Шифр Цезаря"""
    res = ""
    for c in text:
        if c.isalpha():
            base = ord('а') if c.islower() else ord('А')
            res += chr((ord(c) - base + shift) % 32 + base)
        else:
            res += c
    return res

def XorШифр(text, key):
    """XOR-шифрование"""
    return ''.join(chr(ord(c) ^ key) for c in text)

def ВСлучайное(a, b): return random.randint(a, b)
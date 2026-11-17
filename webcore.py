# addons/mixday/webcore.py
import urllib.request
import urllib.parse
import json
import socket
import threading
import time
import http.client
import ssl

# ==========================================
# ИНТЕРНЕТ (Уровень 1-10)
# ==========================================
def ПолучитьHTML(url):
    """Скачивает HTML-код страницы"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Ошибка: {e}"

def ПроверитьСайт(url):
    """Возвращает HTTP-код (200 = работает) или 404 при ошибке."""
    try:
        with urllib.request.urlopen(url, timeout=5) as conn:
            return conn.getcode()
    except Exception:
        return 404

def СкачатьКартинку(url, filename):
    """Скачивает файл по прямой ссылке"""
    try:
        urllib.request.urlretrieve(url, filename)
        return f"Скачано: {filename}"
    except Exception as e:
        return f"Ошибка: {e}"

def КодироватьURL(text):
    """Превращает текст в URL-формат (для поиска)"""
    return urllib.parse.quote(str(text))

def ДекодироватьURL(text):
    """Декодирует URL обратно в текст"""
    return urllib.parse.unquote(str(text))

def ПолучитьJSON(url):
    """Скачивает JSON и возвращает его как словарь"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            return data
    except Exception as e:
        return {"error": str(e)}

def ОтправитьЗапрос(url, method="GET", data=None):
    """Отправляет HTTP-запрос (GET, POST, PUT, DELETE)"""
    try:
        if data and isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=data, method=method, headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Ошибка: {e}"

def МоеIP():
    """Возвращает твой IP-адрес в интернете"""
    try:
        with urllib.request.urlopen('https://api.ipify.org', timeout=5) as r:
            return r.read().decode()
    except Exception:
        return "Нет интернета"

def Пинг(url):
    """Проверяет пинг до сервера (приблизительно)"""
    try:
        start = time.time()
        urllib.request.urlopen(url, timeout=5)
        end = time.time()
        return round((end - start) * 1000, 2)
    except:
        return -1

# ==========================================
# ЛОКАЛЬНАЯ СЕТЬ (Bluetooth-симулятор)
# ==========================================
class _BlueDevice:
    def __init__(self, name):
        self.name = name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.port = 12345  # Стандартный порт MixDay
        self.running = False
        self.received = []
        self.connected = False

    def Запустить(self):
        """Начинает слушать сеть на порту 12345"""
        try:
            self.sock.bind(('0.0.0.0', self.port))
            self.sock.listen(5)
            self.running = True
            self.thread = threading.Thread(target=self._listen, daemon=True)
            self.thread.start()
            return f"Устройство '{self.name}' готово к подключению (порт {self.port})"
        except Exception as e:
            return f"Ошибка: {e}"

    def _listen(self):
        while self.running:
            try:
                conn, addr = self.sock.accept()
                self.connected = True
                data = conn.recv(1024).decode('utf-8')
                if data:
                    self.received.append({"from": addr[0], "msg": data})
                conn.close()
            except:
                break

    def Отправить(self, ip, message):
        """Отправляет сообщение на другое устройство по IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((ip, self.port))
            s.sendall(str(message).encode('utf-8'))
            s.close()
            return f"Отправлено на {ip}: {message}"
        except Exception as e:
            return f"Ошибка отправки: {e}"

    def ПолучитьСообщения(self):
        """Возвращает список всех полученных сообщений"""
        return self.received

    def Остановить(self):
        self.running = False
        self.sock.close()
        return "Соединение закрыто"

def СоздатьУстройство(name="MixDayDevice"):
    """Создает Bluetooth-подобное устройство"""
    return _BlueDevice(name)

# ==========================================
# УТИЛИТЫ (СЕТЬ)
# ==========================================
def МойЛокальныйIP():
    """Возвращает IP в локальной сети (Wi-Fi)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def ПортСвободен(port):
    """Проверяет, свободен ли порт"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def СканироватьПорты(ip, start=1, end=100):
    """Сканирует диапазон портов (осторожно, может занять время)"""
    open_ports = []
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            if s.connect_ex((ip, port)) == 0:
                open_ports.append(port)
    return open_ports
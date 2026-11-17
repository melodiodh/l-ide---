# addons/platidengami.py
# PLATIDENGAMI — библиотека для кассовых операций, чеков и приёма оплаты
import tkinter as tk
import random
import datetime

class _Касса:
    def __init__(self, title="PLATIDENGAMI: Терминал оплаты", width=500, height=600, bg="#161B22", accent="#58A6FF"):
        self.root = tk.Toplevel()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.root.configure(bg=bg)
        self.root.resizable(False, False)
        
        self.bg = bg
        self.accent = accent
        self.balance = 0
        self.history = []

        # Заголовок
        tk.Label(self.root, text="💳 PLATIDENGAMI", bg=self.bg, fg=self.accent, 
                 font=("Segoe UI", 20, "bold")).pack(pady=(20, 5))
        tk.Label(self.root, text="Терминал оплаты", bg=self.bg, fg="#8B949E", 
                 font=("Segoe UI", 10)).pack()

        # Поле ввода суммы
        self.frame_input = tk.Frame(self.root, bg=self.bg)
        self.frame_input.pack(pady=30)
        
        tk.Label(self.frame_input, text="Сумма к оплате:", bg=self.bg, fg="#C9D1D9", 
                 font=("Segoe UI", 12)).pack(anchor="w")
        self.entry_amount = tk.Entry(self.frame_input, bg="#0D1117", fg="#FFFFFF", 
                                     font=("Segoe UI", 16), relief=tk.FLAT, width=20, 
                                     insertbackground="#FFFFFF")
        self.entry_amount.pack(pady=5, ipady=5)

        # Поле для денег пользователя
        tk.Label(self.frame_input, text="Вы дали (наличные):", bg=self.bg, fg="#C9D1D9", 
                 font=("Segoe UI", 12)).pack(anchor="w", pady=(10, 0))
        self.entry_given = tk.Entry(self.frame_input, bg="#0D1117", fg="#FFFFFF", 
                                    font=("Segoe UI", 16), relief=tk.FLAT, width=20, 
                                    insertbackground="#FFFFFF")
        self.entry_given.pack(pady=5, ipady=5)

        # Кнопка
        self.btn_pay = tk.Button(self.root, text="ОПЛАТИТЬ", command=self._pay,
                                 bg="#238636", fg="#FFFFFF", font=("Segoe UI", 14, "bold"),
                                 relief=tk.FLAT, pady=10, cursor="hand2")
        self.btn_pay.pack(fill=tk.X, padx=50)

        # Окно чека
        self.log = tk.Text(self.root, bg="#0D1117", fg="#8B949E", font=("Consolas", 10),
                           height=10, relief=tk.FLAT, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

    def _pay(self):
        try:
            amount = float(self.entry_amount.get())
            given = float(self.entry_given.get())
        except ValueError:
            self._log("❌ Ошибка: введите числа, а не буквы.")
            return

        if given < amount:
            self._log(f"❌ Недостаточно средств. Не хватает: {amount - given:.2f} руб.")
            return

        change = given - amount
        self.balance += amount
        
        # Генерация номера чека
        check_id = random.randint(100000, 999999)
        now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        receipt = (
            f"\n--- ЧЕК № {check_id} ---\n"
            f"Дата: {now}\n"
            f"Сумма: {amount:.2f} руб.\n"
            f"Внесено: {given:.2f} руб.\n"
            f"Сдача: {change:.2f} руб.\n"
            f"---------------------\n"
            f"Спасибо за покупку!\n"
        )
        self._log(receipt)
        self.history.append({"id": check_id, "amount": amount, "change": change})

        # Очистка полей
        self.entry_amount.delete(0, tk.END)
        self.entry_given.delete(0, tk.END)

    def _log(self, text):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def Показать(self):
        """Показывает терминал. Внутри IDE не запускает второй mainloop."""
        try:
            self.root.deiconify()
            self.root.lift()
            if tk._default_root is None:
                self.root.mainloop()
        except Exception:
            pass

    def ПолучитьБаланс(self):
        return self.balance

    def ОчиститьИсторию(self):
        self.history.clear()
        self.balance = 0
        self.log.config(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.config(state=tk.DISABLED)

def СоздатьТерминал(title="PLATIDENGAMI", width=500, height=600):
    return _Касса(title, width, height)
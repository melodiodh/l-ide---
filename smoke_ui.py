# -*- coding: utf-8 -*-
"""Дымовой тест GUI: собирает окно, гоняет сценарии и закрывает.

Запуск:  python tests/smoke_ui.py
Окно показывается ненадолго — это нормально.
"""

import os
import sys
import tempfile
import time
import tkinter as tk

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import lpp.ui.app as app_mod  # noqa: E402

FAKE_CFG = {
    "theme": "GitHub Dark",
    "edition": "Ultimate",
    "font_size": 14,
    "show_welcome": False,
    "first_run": False,
    "last_file": None,
}

app_mod.load_config = lambda: dict(FAKE_CFG)
app_mod.save_config = lambda cfg: True

failures = []


def check(name, cond, extra=""):
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {extra}")
        failures.append(name)


def pump(root, seconds=0.6):
    end = time.time() + seconds
    while time.time() < end:
        root.update()
        time.sleep(0.02)


def walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from walk(child)


def check_first_run():
    """Проверяет первый запуск: окно выбора издания и продолжение работы."""
    print("--- первый запуск: выбор издания ---")
    app_mod.load_config = lambda: dict(FAKE_CFG, first_run=True)
    root = tk.Tk()

    def click_ultimate():
        try:
            buttons = [
                w for w in walk(root)
                if isinstance(w, tk.Button) and w.cget("text") == "Выбрать"
            ]
            if len(buttons) >= 2:
                buttons[1].invoke()      # Home, Ultimate, Classic
        except tk.TclError:
            pass

    root.after(600, click_ultimate)
    app = app_mod.L_IDE(root)
    pump(root, 1.2)
    check("окно выбора отработало", app.edition_name == "Ultimate", app.edition_name)
    check("главное окно собралось", hasattr(app, "editor"))
    app._dirty = False
    app.on_close()
    pump(root, 0.3)


def main():
    root = tk.Tk()
    app = app_mod.L_IDE(root)
    pump(root, 1.6)

    print("--- сборка окна ---")
    check("окно видимо", root.winfo_viewable() == 1 or root.state() != "withdrawn")
    check("редактор создан", hasattr(app, "editor"))
    check("консоль создана", hasattr(app, "console"))
    check("нумерация строк", app.gutter.get("1.0", "end-1c").splitlines()[:3] == ["1", "2", "3"])
    check("результат само-тестов", "Само-тесты" in app.console.get("1.0", "end"),
          app.console.get("1.0", "end")[:200])

    print("--- подсветка ---")
    app.editor.delete("1.0", "end")
    app.editor.insert("1.0", 'если 1 < 2 то:\n    вывести("да") // коммент\nконец\n')
    app._do_highlight()
    pump(root, 0.2)
    check("ключевое слово подсвечено", bool(app.editor.tag_ranges("kw")))
    check("строка подсвечена", bool(app.editor.tag_ranges("str")))
    check("комментарий подсвечен", bool(app.editor.tag_ranges("cmt")))
    check("встроенная функция подсвечена", bool(app.editor.tag_ranges("fn")))

    print("--- запуск программы ---")
    app.editor.delete("1.0", "end")
    app.editor.insert("1.0", 'вывести("привет из теста")\n')
    app.run_code()
    pump(root, 1.2)
    out = app.console.get("1.0", "end")
    check("вывод программы", "привет из теста" in out, repr(out[:200]))
    check("статус Успешно", "Успешно" in app.lbl_status.cget("text"), app.lbl_status.cget("text"))

    print("--- ошибка выполнения ---")
    app.editor.delete("1.0", "end")
    app.editor.insert("1.0", "вывести(1/0)\n")
    app.run_code()
    pump(root, 1.0)
    check("ошибка показана", "ОШИБКА" in app.console.get("1.0", "end"))

    print("--- кнопка стоп ---")
    app.editor.delete("1.0", "end")
    app.editor.insert("1.0", "пока истина то:\n    x = 1\nконец\n")
    app.run_code()
    pump(root, 0.4)
    app.stop_code()
    pump(root, 1.2)
    check("остановлено", "остановлено" in app.console.get("1.0", "end").lower()
          or "Прервано" in app.console.get("1.0", "end"),
          app.console.get("1.0", "end")[-200:])

    print("--- смена темы сохраняет текст ---")
    app.editor.delete("1.0", "end")
    marker = 'вывести("не потеряй меня")\n'
    app.editor.insert("1.0", marker)
    app.set_theme("Dracula")
    pump(root, 0.5)
    check("тема применилась", app.theme_name == "Dracula")
    check("текст сохранён", app.editor.get("1.0", "end-1c").strip() == marker.strip(),
          repr(app.editor.get("1.0", "end-1c")[:80]))

    print("--- сохранение и открытие ---")
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "тест.lpp")
    app.current_file = path
    app.editor.delete("1.0", "end")
    app.editor.insert("1.0", 'вывести("файл")\n')
    saved = app.save_file()
    check("файл сохранён", saved and os.path.isfile(path))
    with open(path, "r", encoding="utf-8") as f:
        check("содержимое файла", f.read().strip() == 'вывести("файл")')
    check("флаг изменений сброшен", app._dirty is False)

    app.editor.delete("1.0", "end")
    app._load_path(path)
    pump(root, 0.2)
    check("файл открыт", 'вывести("файл")' in app.editor.get("1.0", "end-1c"))

    print("--- поиск ---")
    app.open_find()
    pump(root, 0.4)
    fw = app._find_window
    check("окно поиска", fw is not None and fw.winfo_exists() == 1)
    fw.entry_find.insert(0, "файл")
    fw.find_next(False)
    pump(root, 0.2)
    check("найдено совпадение", bool(app.editor.tag_ranges("find")))
    fw.close()
    pump(root, 0.2)

    print("--- комментарии и шрифт ---")
    app.editor.delete("1.0", "end")
    app.editor.insert("1.0", "вывести(1)\n")
    app.editor.mark_set(tk.INSERT, "1.0")
    app.toggle_comment()
    check("закомментировано", app.editor.get("1.0", "1.end").startswith("//"),
          app.editor.get("1.0", "1.end"))
    app.toggle_comment()
    check("раскомментировано", not app.editor.get("1.0", "1.end").startswith("//"))

    old = app.font_size
    app.zoom(1)
    check("шрифт увеличен", app.font_size == old + 1)
    app.zoom(0)
    check("шрифт сброшен", app.font_size == 14)

    print("--- автодополнение отступа ---")
    app.editor.delete("1.0", "end")
    app.editor.insert("1.0", "если 1 < 2 то:")
    app.editor.mark_set(tk.INSERT, "end")
    app._on_return()
    check("отступ после 'то:'", app.editor.get("2.0", "2.end") == "    ",
          repr(app.editor.get("2.0", "2.end")))

    print("--- графика из аддона ---")
    app.editor.delete("1.0", "end")
    app.editor.insert("1.0", 'включить lgame\nигра = lgame.СоздатьИгру("Тест", 300, 200)\nвывести("окно создано")\n')
    app.run_code()
    pump(root, 1.5)
    check("аддон создал окно", "окно создано" in app.console.get("1.0", "end"),
          app.console.get("1.0", "end")[-300:])

    print("--- закрытие ---")
    app._dirty = False
    app.on_close()
    pump(root, 0.3)
    try:
        alive = bool(root.winfo_exists())
    except tk.TclError:
        alive = False
    check("окно закрыто", not alive)

    print()
    check_first_run()

    print()
    if failures:
        print(f"ПРОВАЛЕНО: {len(failures)} -> {failures}")
        return 1
    print("ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
